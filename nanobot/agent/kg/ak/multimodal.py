"""AK multimodal adapters — image_caption and audio_transcribe.

Both tools use the requesting turn's ``LLMRuntime`` and never fall back
to a different provider/model.  The legacy AK code constructed its own
MiniMax/Groq clients; the plan explicitly forbids that for the native
tools, so the wrappers here only know how to talk to ``LLMProvider``:

* ``image_caption`` issues a multimodal ``chat`` request with a
  ``image_url`` content block.  The capability is gated by
  ``runtime.provider.supports_modality("image", runtime.model)`` — if
  the active runtime cannot consume images, the tool returns
  ``unsupported_capability`` instead of substituting a different model.
* ``audio_transcribe`` does the same for audio.  No provider in the
  current ``LLMProvider`` hierarchy declares audio input support, so
  this tool surfaces the gap as ``unsupported_capability`` until the
  contract is extended; replanning before declaring F4 audio-parity
  complete is explicitly the plan's instruction.

Results are cached via ``ak.cache`` with a key that includes the
provider, model and preset so a later turn served by a different
runtime cannot accidentally return a stale caption.
"""

from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from typing import Any, cast

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from nanobot.agent.kg.ak.cache import CacheStore, CacheUnavailableError, cache_key, file_etag
from nanobot.agent.kg.ak.core import check_bundle_paths, resolve_asset_path
from nanobot.agent.kg.ak.telemetry import track_op
from nanobot.providers.base import ProviderCallContext
from nanobot.utils.llm_runtime import LLMRuntime

from . import UnsupportedCapabilityError

IMAGE_CAPTION_INSTRUCTIONS = (
    "You caption images factually and return STRICT JSON with these keys: "
    '"caption" (1-3 sentences in Portuguese describing what the image shows objectively), '
    '"ocr" (visible text transcribed; empty string if none), '
    '"tags" (3-5 short lowercase tags, no accents), '
    '"description" (1 longer paragraph for search; Portuguese). '
    'Do not invent content. If the image is ambiguous, say so in the caption.'
)
IMAGE_CAPTION_USER_PROMPT = "Descreva esta imagem."
IMAGE_CAPTION_PROCESSOR_VERSION = "image-caption-v1"

SUPPORTED_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
SUPPORTED_AUDIO_SUFFIXES = frozenset({".wav", ".mp3", ".m4a", ".ogg", ".flac"})
MAX_IMAGE_INPUT_BYTES = 20 * 1024 * 1024

_IMAGE_MIMETYPE = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

_AUDIO_MIMETYPE = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}


class ImageDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caption: str = Field(min_length=15, max_length=300)
    ocr: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=8)
    description: str = Field(min_length=30, max_length=600)


class InvalidMultimodalOutputError(RuntimeError):
    """The active model returned content outside the requested typed contract."""


def _require_runtime(runtime: LLMRuntime | None) -> LLMRuntime:
    if runtime is None:
        raise UnsupportedCapabilityError(
            "no LLM runtime selected for this request; multimodal tools need runtime.provider"
        )
    return runtime


def _image_mimetype(suffix: str) -> str:
    return _IMAGE_MIMETYPE.get(suffix.lower(), "application/octet-stream")


def _audio_mimetype(suffix: str) -> str:
    return _AUDIO_MIMETYPE.get(suffix.lower(), "application/octet-stream")


def _runtime_metadata(runtime: LLMRuntime) -> dict[str, str | None]:
    return {
        "provider": runtime.provider.provider_name,
        "model": runtime.model,
        "preset": runtime.model_preset,
    }


def _build_provider_context(runtime: LLMRuntime) -> ProviderCallContext:
    return ProviderCallContext(
        conversation_state=None,
        context_window_tokens=runtime.context_window_tokens,
        session_id=None,
    )


def _build_image_data_url(asset: Path) -> str:
    suffix = asset.suffix.lower()
    mime = _image_mimetype(suffix)
    b64 = base64.b64encode(asset.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _build_audio_data_url(asset: Path) -> str:
    suffix = asset.suffix.lower()
    mime = _audio_mimetype(suffix)
    b64 = base64.b64encode(asset.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _parse_caption_payload(content: str) -> dict[str, Any]:
    """Parse a JSON object out of the model's response.

    Returns ``{"_parse_error": "invalid_output"}`` when the model emits text
    that is not a JSON object — strings, arrays, and bare tokens all map
    to the same error so the caller can flag ``invalid_output``.
    """
    text = (content or "").strip()
    if not text:
        return {"_parse_error": "empty content"}
    for candidate in (text, text.removeprefix("```json").removesuffix("```").strip()):
        try:
            parsed: Any = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return cast(dict[str, Any], parsed)
        return {"_parse_error": "invalid_output"}
    try:
        import json_repair

        parsed = json_repair.loads(text)
    except Exception:
        return {"_parse_error": "invalid_output"}
    if isinstance(parsed, dict):
        return cast(dict[str, Any], parsed)
    return {"_parse_error": "invalid_output"}


def _read_caption_cache(cache: CacheStore, key: str) -> ImageDescription | None:
    cached = cache.get(key)
    if cached is None:
        return None
    try:
        return ImageDescription.model_validate(cached)
    except (ValidationError, TypeError, ValueError):
        cache.delete(key)
        return None


def _safe_cache(root: Path) -> CacheStore | None:
    """Return the AK cache, or ``None`` when diskcache is unavailable."""
    try:
        from .cache import get_cache
        return get_cache(root)
    except CacheUnavailableError:
        return None


async def image_caption(
    root: Path,
    asset_path: str,
    *,
    runtime: LLMRuntime | None,
) -> dict[str, Any]:
    """Caption an image using the requesting turn's runtime.

    Failure modes:

    * ``runtime_unavailable`` — no ``LLMRuntime`` on the request.
    * ``unsupported_capability`` — the provider/model cannot consume
      images (the default for text-only providers).
    * ``invalid_output`` — model returned text that is not a caption.
    """
    runtime = _require_runtime(runtime)
    await asyncio.to_thread(check_bundle_paths, root, write=True)
    asset = await asyncio.to_thread(resolve_asset_path, root, asset_path)
    if asset.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"unsupported image type: {asset.suffix!r}")
    size = await asyncio.to_thread(lambda: asset.stat().st_size)
    if size > MAX_IMAGE_INPUT_BYTES:
        raise ValueError(f"image exceeds {MAX_IMAGE_INPUT_BYTES} byte input limit")
    if not runtime.provider.supports_modality("image", runtime.model):
        raise UnsupportedCapabilityError(
            f"runtime provider={runtime.provider.provider_name!r} model={runtime.model!r} "
            "does not support image input"
        )

    metadata = _runtime_metadata(runtime)
    cache = await asyncio.to_thread(_safe_cache, root)
    etag = await asyncio.to_thread(file_etag, asset)
    key = cache_key(
        "image_caption",
        etag,
        **metadata,
        parser_version=IMAGE_CAPTION_PROCESSOR_VERSION,
    )
    with track_op(root, "image_caption", asset_path=asset_path, **metadata) as ctx:
        if cache is not None:
            cached = await asyncio.to_thread(_read_caption_cache, cache, key)
            if cached is not None:
                ctx["cache_hit"] = True
                ctx["cost_usd"] = 0.0
                return {**cached.model_dump(),
                        "cached": True, **metadata}
        ctx["cache_hit"] = False
        response = await runtime.provider.chat_with_retry(
            messages=[
                {"role": "system", "content": IMAGE_CAPTION_INSTRUCTIONS},
                {"role": "user", "content": [
                    {"type": "text", "text": IMAGE_CAPTION_USER_PROMPT},
                    {"type": "image_url", "image_url": {"url": await asyncio.to_thread(_build_image_data_url, asset)}},
                ]},
            ],
            model=runtime.model,
            temperature=runtime.generation.temperature,
            max_tokens=runtime.generation.max_tokens,
            reasoning_effort=runtime.generation.reasoning_effort,
            provider_context=_build_provider_context(runtime),
        )
        if response.finish_reason in {"error", "refusal", "content_filter"}:
            ctx["error_kind"] = response.error_kind or response.finish_reason
            raise RuntimeError(
                f"image_caption: provider returned finish_reason={response.finish_reason!r}"
            )
        if response.has_tool_calls or not response.content:
            raise InvalidMultimodalOutputError("image_caption: provider did not return caption text")
        parsed = _parse_caption_payload(response.content)
        if "_parse_error" in parsed:
            raise InvalidMultimodalOutputError("image_caption: invalid_output from model")
        try:
            description = ImageDescription.model_validate(parsed)
        except ValidationError as exc:
            raise InvalidMultimodalOutputError("image_caption: invalid_output (schema mismatch)") from exc
        result = {
            **description.model_dump(),
            "cached": False,
            **metadata,
        }
        if cache is not None:
            try:
                await asyncio.to_thread(cache.set, key, description.model_dump(), expire=86400 * 7)
            except Exception:
                logger.warning("ak.cache.set failed for image_caption")
        ctx["cost_usd"] = 0.0001
        return result


async def audio_transcribe(
    root: Path,
    asset_path: str,
    *,
    language: str = "pt",
    runtime: LLMRuntime | None,
) -> dict[str, Any]:
    """Transcribe audio using the requesting turn's runtime.

    Currently the LLM chat interface has no provider that declares
    audio input support, so this tool always raises
    ``UnsupportedCapabilityError``.  The plan's F4 instruction is to
    flag the gap explicitly rather than substitute a different model.
    """
    runtime = _require_runtime(runtime)
    await asyncio.to_thread(check_bundle_paths, root, write=True)
    asset = await asyncio.to_thread(resolve_asset_path, root, asset_path)
    if asset.suffix.lower() not in SUPPORTED_AUDIO_SUFFIXES:
        raise ValueError(f"unsupported audio type: {asset.suffix!r}")
    if not runtime.provider.supports_modality("audio", runtime.model):
        raise UnsupportedCapabilityError(
            f"runtime provider={runtime.provider.provider_name!r} model={runtime.model!r} "
            "does not support audio input via LLMProvider.chat; replan F4 audio parity"
        )
    metadata = _runtime_metadata(runtime)
    with track_op(root, "audio_transcribe", asset_path=asset_path, language=language, **metadata) as ctx:
        ctx["cache_hit"] = False
        response = await runtime.provider.chat_with_retry(
            messages=[
                {"role": "system", "content": "You are a speech transcription service."},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Transcreva este áudio em {language}."},
                    {"type": "input_audio", "input_audio": {"data": await asyncio.to_thread(_build_audio_data_url, asset)}},
                ]},
            ],
            model=runtime.model,
            temperature=0.0,
            max_tokens=runtime.generation.max_tokens,
            provider_context=_build_provider_context(runtime),
        )
        if response.finish_reason in {"error", "refusal", "content_filter"}:
            ctx["error_kind"] = response.error_kind or response.finish_reason
            raise RuntimeError(
                f"audio_transcribe: provider returned finish_reason={response.finish_reason!r}"
            )
        if response.has_tool_calls or not response.content:
            raise RuntimeError("audio_transcribe: provider did not return transcript text")
        ctx["cost_usd"] = 0.0001
        return {"text": response.content.strip(), "language": language,
                "duration_seconds": 0.0, "cached": False, **metadata}


__all__ = [
    "IMAGE_CAPTION_INSTRUCTIONS",
    "IMAGE_CAPTION_PROCESSOR_VERSION",
    "SUPPORTED_AUDIO_SUFFIXES",
    "SUPPORTED_IMAGE_SUFFIXES",
    "audio_transcribe",
    "image_caption",
]
