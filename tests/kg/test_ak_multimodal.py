"""F4 multimodal: image_caption and audio_transcribe consume the turn runtime.

The two tools must never substitute a different model — when the
provider/model cannot consume the requested modality they raise
``UnsupportedCapabilityError`` (mapped to ``unsupported_capability``
in the tool response).  Image captions flow through
``runtime.provider.chat_with_retry`` with a multimodal
``image_url`` block.  Audio is currently a documented gap and the
tests prove the runtime check fires.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.agent.kg.ak import UnsupportedCapabilityError
from nanobot.agent.kg.ak.multimodal import (
    MAX_IMAGE_INPUT_BYTES,
    audio_transcribe,
    image_caption,
)
from nanobot.providers.base import GenerationSettings, LLMProvider, LLMResponse
from nanobot.providers.openai_compat_provider import OpenAICompatProvider
from nanobot.utils.llm_runtime import LLMRuntime


def _png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa3\x9bZ\xdf"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _write_image(root: Path) -> Path:
    assets = root / "sources"
    assets.mkdir(parents=True, exist_ok=True)
    image = assets / "captionable.png"
    image.write_bytes(_png())
    return image


def _write_audio(root: Path) -> Path:
    assets = root / "sources"
    assets.mkdir(parents=True, exist_ok=True)
    audio = assets / "voice.mp3"
    audio.write_bytes(b"\x49\x44\x33\x03\x00\x00\x00\x00\x00\x00")
    return audio


def _vision_runtime(model: str = "selected-vision", preset: str | None = None) -> LLMRuntime:
    provider = MagicMock(spec=LLMProvider)
    provider.provider_name = "openai"
    provider.supports_modality = MagicMock(side_effect=lambda modality, model=None: modality == "image")
    provider.generation = GenerationSettings(temperature=0.1, max_tokens=256)
    provider.chat_with_retry = AsyncMock(return_value=LLMResponse(
        content=json.dumps({
            "caption": "imagem factual curta para testes",
            "ocr": "OCR-EXAMPLE",
            "tags": ["teste", "fake"],
            "description": "Descrição mais longa para busca, somente para validar o pipeline.",
        }),
    ))
    return LLMRuntime.capture(provider, model, context_window_tokens=8192, model_preset=preset)


def _text_only_runtime() -> LLMRuntime:
    provider = MagicMock(spec=LLMProvider)
    provider.provider_name = "text-only"
    provider.supports_modality = MagicMock(return_value=False)
    provider.generation = GenerationSettings()
    provider.chat_with_retry = AsyncMock()
    return LLMRuntime.capture(provider, "no-vision", context_window_tokens=4096)


@pytest.mark.asyncio
async def test_image_caption_runs_through_runtime_provider_with_captured_model(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    bundle.mkdir()
    image = _write_image(bundle)
    selected = _vision_runtime(model="vision-large", preset="default")

    result = await image_caption(bundle, str(image), runtime=selected)
    assert result["caption"].startswith("imagem factual")
    assert result["tags"] == ["teste", "fake"]
    assert result["provider"] == "openai"
    assert result["model"] == "vision-large"
    assert result["preset"] == "default"
    assert result["cached"] is False

    selected.provider.chat_with_retry.assert_awaited_once()
    call_kwargs = selected.provider.chat_with_retry.await_args.kwargs
    assert call_kwargs["model"] == "vision-large"
    assert call_kwargs["temperature"] == 0.1
    assert call_kwargs["max_tokens"] == 256
    user_content = call_kwargs["messages"][1]["content"]
    assert any(block.get("type") == "image_url" for block in user_content)


@pytest.mark.asyncio
async def test_image_caption_rejects_when_runtime_lacks_image_capability(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    bundle.mkdir()
    image = _write_image(bundle)
    text_only = _text_only_runtime()

    with pytest.raises(UnsupportedCapabilityError) as exc:
        await image_caption(bundle, str(image), runtime=text_only)
    assert "does not support image input" in str(exc.value)
    text_only.provider.chat_with_retry.assert_not_called()


@pytest.mark.asyncio
async def test_image_caption_rejects_when_runtime_missing(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    bundle.mkdir()
    image = _write_image(bundle)
    with pytest.raises(UnsupportedCapabilityError):
        await image_caption(bundle, str(image), runtime=None)


@pytest.mark.asyncio
async def test_image_caption_rejects_oversized_image_before_provider_call(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    assets = bundle / "sources"
    assets.mkdir(parents=True)
    image = assets / "large.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    with image.open("r+b") as handle:
        handle.truncate(MAX_IMAGE_INPUT_BYTES + 1)
    selected = _vision_runtime()
    with pytest.raises(ValueError, match="input limit"):
        await image_caption(bundle, str(image), runtime=selected)
    selected.provider.chat_with_retry.assert_not_called()


@pytest.mark.asyncio
async def test_image_caption_invalid_output_raises(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    bundle.mkdir()
    image = _write_image(bundle)
    provider = MagicMock(spec=LLMProvider)
    provider.provider_name = "openai"
    provider.supports_modality = MagicMock(return_value=True)
    provider.generation = GenerationSettings()
    provider.chat_with_retry = AsyncMock(return_value=LLMResponse(content="not json"))
    runtime = LLMRuntime.capture(provider, "vision", context_window_tokens=4096)
    with pytest.raises(RuntimeError, match="invalid_output"):
        await image_caption(bundle, str(image), runtime=runtime)


@pytest.mark.asyncio
async def test_image_caption_error_finish_reason_raises(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    bundle.mkdir()
    image = _write_image(bundle)
    provider = MagicMock(spec=LLMProvider)
    provider.provider_name = "openai"
    provider.supports_modality = MagicMock(return_value=True)
    provider.generation = GenerationSettings()
    provider.chat_with_retry = AsyncMock(return_value=LLMResponse(
        content="refusal text", finish_reason="refusal", error_kind="refusal",
    ))
    runtime = LLMRuntime.capture(provider, "vision", context_window_tokens=4096)
    with pytest.raises(RuntimeError, match="finish_reason"):
        await image_caption(bundle, str(image), runtime=runtime)


@pytest.mark.asyncio
async def test_audio_transcribe_returns_unsupported_for_any_current_runtime(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    bundle.mkdir()
    audio = _write_audio(bundle)
    runtime = _vision_runtime()
    with pytest.raises(UnsupportedCapabilityError) as exc:
        await audio_transcribe(bundle, str(audio), runtime=runtime)
    assert "audio" in str(exc.value)


@pytest.mark.asyncio
async def test_audio_transcribe_rejects_missing_runtime(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    bundle.mkdir()
    audio = _write_audio(bundle)
    with pytest.raises(UnsupportedCapabilityError):
        await audio_transcribe(bundle, str(audio), runtime=None)


def test_supports_modality_default_returns_false() -> None:
    from nanobot.providers.unconfigured_provider import UnconfiguredProvider

    provider = UnconfiguredProvider(default_model="placeholder")
    assert provider.supports_modality("image") is False
    assert provider.supports_modality("audio") is False


def test_openai_compat_modality_is_model_specific() -> None:
    provider = OpenAICompatProvider(
        api_key="test",
        default_model="gpt-4o",
        provider_name="openai",
    )
    assert provider.supports_modality("image", "gpt-4o") is True
    assert provider.supports_modality("image", "some-text-only-model") is False
    assert provider.supports_modality("audio", "gpt-4o") is False


@pytest.mark.asyncio
async def test_caption_cache_does_not_cross_model_identity(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    bundle.mkdir()
    image = _write_image(bundle)
    first = _vision_runtime(model="vision-model-a")
    second = _vision_runtime(model="vision-model-b")

    await image_caption(bundle, str(image), runtime=first)
    await image_caption(bundle, str(image), runtime=second)

    first.provider.chat_with_retry.assert_awaited_once()
    second.provider.chat_with_retry.assert_awaited_once()
