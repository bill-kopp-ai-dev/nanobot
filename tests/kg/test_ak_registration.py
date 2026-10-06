"""Native AK tools are discovered by ToolLoader and obey mode."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from nanobot.agent.tools.ak_multimodal import AKAudioTranscribeTool, AKImageCaptionTool
from nanobot.agent.tools.ak_read import AKSourceSearchTool
from nanobot.agent.tools.context import RequestContext, ToolContext, request_context
from nanobot.agent.tools.loader import ToolLoader
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.audio.transcription import EffectiveTranscriptionConfig
from nanobot.config.kg import PercivalKgConfig
from nanobot.config.schema import ToolsConfig
from nanobot.providers.base import GenerationSettings
from nanobot.utils.llm_runtime import LLMRuntime

AK_NATIVE_NAMES = {
    "ak_source_ingest", "ak_source_read", "ak_source_list", "ak_source_search",
    "ak_source_stats", "ak_get_laterally_isolated_notes",
    "ak_image_caption", "ak_audio_transcribe",
    "ak_note_write_extracted", "ak_note_link", "ak_note_batch_link",
    "ak_graph_neighbors", "ak_graph_shortest_path", "ak_source_forget",
}


def _ctx(workspace: Path, *, mode: str = "native",
         config_overrides: dict | None = None) -> ToolContext:
    cfg = PercivalKgConfig(mode=mode)
    if config_overrides:
        for key, value in config_overrides.items():
            setattr(cfg, key, value)
    return ToolContext(config=ToolsConfig(), workspace=str(workspace), kg_config=cfg)


def test_loader_registers_fourteen_ak_tools_in_native_mode(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, mode="native")
    registry = ToolRegistry()
    ToolLoader().load(ctx, registry)
    registered = {name for name in registry.tool_names if name.startswith("ak_")}
    assert registered == AK_NATIVE_NAMES


def test_loader_registers_ak_tools_in_both_mode(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, mode="both")
    registry = ToolRegistry()
    ToolLoader().load(ctx, registry)
    assert AK_NATIVE_NAMES <= set(registry.tool_names)


def test_loader_suppresses_ak_tools_in_mcp_mode(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, mode="mcp")
    registry = ToolRegistry()
    ToolLoader().load(ctx, registry)
    assert not (set(registry.tool_names) & AK_NATIVE_NAMES)


def test_image_caption_disabled_when_flag_false(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, mode="native", config_overrides={"ak_image_caption_enabled": False})
    registry = ToolRegistry()
    ToolLoader().load(ctx, registry)
    assert "ak_image_caption" not in registry.tool_names
    assert "ak_audio_transcribe" in registry.tool_names


def test_audio_transcribe_disabled_when_flag_false(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, mode="native", config_overrides={"ak_audio_transcribe_enabled": False})
    registry = ToolRegistry()
    ToolLoader().load(ctx, registry)
    assert "ak_audio_transcribe" not in registry.tool_names


@pytest.mark.asyncio
async def test_image_caption_tool_returns_runtime_unavailable_without_context(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, mode="native")
    tool = AKImageCaptionTool.create(ctx)
    payload = json.loads(await tool.execute(asset_path="sources/does-not-exist.png"))
    assert payload["status"] == "error"
    assert payload["error_kind"] == "runtime_unavailable"


@pytest.mark.asyncio
async def test_audio_transcribe_tool_returns_unsupported_without_groq_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    (bundle / "sources").mkdir(parents=True)
    (bundle / "sources" / "voice.mp3").write_bytes(b"fake")
    runtime_request = RequestContext(
        channel="websocket", chat_id="audio-test",
        runtime=_unsupported_runtime(),
    )
    ctx = _ctx(tmp_path, mode="native")
    tool = AKAudioTranscribeTool.create(ctx)
    monkeypatch.setattr(
        "nanobot.agent.kg.ak.multimodal.resolve_transcription_config",
        lambda _cfg: replace(_groq_settings(), api_key=""),
    )
    with request_context(runtime_request):
        payload = json.loads(await tool.execute(asset_path="sources/voice.mp3"))
    assert payload["status"] == "error"
    assert payload["error_kind"] == "unsupported_capability"


def _groq_settings() -> EffectiveTranscriptionConfig:
    return EffectiveTranscriptionConfig(
        enabled=True, provider="groq", model="whisper-large-v3", language=None,
        api_key="gsk-test", api_base="https://api.groq.com/openai/v1",
        max_duration_sec=120, max_upload_mb=25,
    )


@pytest.mark.asyncio
async def test_audio_transcribe_tool_succeeds_without_chat_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    (bundle / "sources").mkdir(parents=True)
    (bundle / "sources" / "voice.mp3").write_bytes(b"ID3 test audio")
    monkeypatch.setattr(
        "nanobot.agent.kg.ak.multimodal.resolve_transcription_config",
        lambda _cfg: _groq_settings(),
    )
    transcript = AsyncMock(return_value="Áudio transcrito.")
    monkeypatch.setattr("nanobot.agent.kg.ak.multimodal.transcribe_audio_file", transcript)
    tool = AKAudioTranscribeTool.create(_ctx(tmp_path))
    payload = json.loads(await tool.execute(asset_path="sources/voice.mp3"))
    assert payload["text"] == "Áudio transcrito."
    assert payload["provider"] == "groq"
    transcript.assert_awaited_once()


@pytest.mark.asyncio
async def test_audio_transcribe_tool_posts_groq_multipart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    (bundle / "sources").mkdir(parents=True)
    (bundle / "sources" / "voice.mp3").write_bytes(b"ID3 test audio")
    monkeypatch.setattr(
        "nanobot.agent.kg.ak.multimodal.resolve_transcription_config",
        lambda _cfg: _groq_settings(),
    )
    response = httpx.Response(
        200, json={"text": "Olá, mundo."},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/audio/transcriptions"),
    )
    post = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    payload = json.loads(await AKAudioTranscribeTool.create(_ctx(tmp_path)).execute(
        asset_path="sources/voice.mp3", language="pt",
    ))
    assert payload["text"] == "Olá, mundo."
    assert payload["model"] == "whisper-large-v3"
    kwargs = post.await_args.kwargs
    assert kwargs["url"] == "https://api.groq.com/openai/v1/audio/transcriptions"
    assert kwargs["headers"]["Authorization"] == "Bearer gsk-test"
    assert kwargs["files"]["model"] == (None, "whisper-large-v3")
    assert kwargs["files"]["language"] == (None, "pt")
    assert kwargs["files"]["file"] == ("voice.mp3", b"ID3 test audio", "audio/mpeg")


@pytest.mark.asyncio
async def test_source_search_tool_reports_no_hits_for_blank_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    (bundle / "notes").mkdir(parents=True)
    ctx = _ctx(tmp_path, mode="native")
    tool = AKSourceSearchTool.create(ctx)
    payload = json.loads(await tool.execute(query="needle"))
    assert payload == []


def _unsupported_runtime():
    provider = MagicMock()
    provider.provider_name = "stub"
    provider.supports_modality = MagicMock(return_value=False)
    provider.generation = GenerationSettings()
    provider.chat_with_retry = AsyncMock()
    return LLMRuntime.capture(provider, "no-audio", context_window_tokens=2048)
