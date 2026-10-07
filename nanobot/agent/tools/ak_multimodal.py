"""Native AK multimodal tools (image_caption, audio_transcribe).

Both tools reuse the requesting turn's ``LLMRuntime`` via
``current_request_context().runtime``.  ``image_caption`` issues a
multimodal ``chat`` request when the active provider/model declares
``supports_modality("image") == True``; otherwise the tool returns
``unsupported_capability`` instead of substituting a different model.
``audio_transcribe`` uses the configured Groq Whisper transcription service.
"""

from __future__ import annotations

from typing import Any

import httpx

from nanobot.agent.kg.ak import UnsupportedCapabilityError, to_json
from nanobot.agent.kg.ak.multimodal import (
    InvalidMultimodalOutputError,
    audio_transcribe,
    image_caption,
)
from nanobot.agent.tools.ak_read import AKTool
from nanobot.agent.tools.base import tool_parameters
from nanobot.agent.tools.context import current_request_context


def _runtime_or_error() -> tuple[dict[str, str] | None, Any]:
    request = current_request_context()
    if request is None or request.runtime is None:
        return ({"status": "error", "error_kind": "runtime_unavailable",
                 "error": "no LLM runtime selected for this request"}, None)
    return (None, request.runtime)


@tool_parameters({
    "type": "object",
    "properties": {
        "asset_path": {"type": "string", "minLength": 1, "maxLength": 4096},
    },
    "required": ["asset_path"],
    "additionalProperties": False,
})
class AKImageCaptionTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_image_caption"

    @property
    def description(self) -> str:
        return (
            "Caption an image using this turn's LLM runtime (provider, model and "
            "preset are reused). Returns an explicit unsupported_capability when "
            "the runtime does not declare image input support."
        )

    @classmethod
    def enabled(cls, ctx) -> bool:  # type: ignore[override]
        if not super().enabled(ctx):
            return False
        if ctx.kg_config is not None and not ctx.kg_config.ak_image_caption_enabled:
            return False
        return True

    async def execute(self, **kwargs: Any) -> str:
        unavailable, runtime = _runtime_or_error()
        if unavailable is not None:
            return to_json(unavailable)
        try:
            result = await image_caption(
                self._root(),
                kwargs["asset_path"],
                runtime=runtime,
            )
            return to_json(result)
        except FileNotFoundError as exc:
            return to_json({"status": "error", "error_kind": "asset_missing",
                            "error": str(exc)})
        except ValueError as exc:
            return to_json({"status": "error", "error_kind": "invalid_input",
                            "error": str(exc)})
        except UnsupportedCapabilityError as exc:
            return to_json({"status": "error", "error_kind": "unsupported_capability",
                            "error": str(exc)})
        except InvalidMultimodalOutputError as exc:
            return to_json({"status": "error", "error_kind": "invalid_output",
                            "error": str(exc)})
        except (httpx.HTTPError, RuntimeError) as exc:
            return to_json({"status": "error", "error_kind": "provider_error",
                            "error": str(exc)})


@tool_parameters({
    "type": "object",
    "properties": {
        "asset_path": {"type": "string", "minLength": 1, "maxLength": 4096},
        "language": {"type": "string", "minLength": 2, "maxLength": 8},
    },
    "required": ["asset_path"],
    "additionalProperties": False,
})
class AKAudioTranscribeTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_audio_transcribe"

    @property
    def description(self) -> str:
        return (
            "Transcribe audio in the AK bundle via nanobot's configured Groq "
            "Whisper service. Sends audio to Groq; requires GROQ_API_KEY or "
            "providers.groq.apiKey and transcription.provider=groq."
        )

    @classmethod
    def enabled(cls, ctx) -> bool:  # type: ignore[override]
        if not super().enabled(ctx):
            return False
        if ctx.kg_config is not None and not ctx.kg_config.ak_audio_transcribe_enabled:
            return False
        return True

    async def execute(self, **kwargs: Any) -> str:
        try:
            result = await audio_transcribe(
                self._root(),
                kwargs["asset_path"],
                language=kwargs.get("language"),
            )
            return to_json(result)
        except UnsupportedCapabilityError as exc:
            return to_json({"status": "error", "error_kind": "unsupported_capability",
                            "error": str(exc)})
        except InvalidMultimodalOutputError as exc:
            return to_json({"status": "error", "error_kind": "invalid_output",
                            "error": str(exc)})
        except FileNotFoundError as exc:
            return to_json({"status": "error", "error_kind": "asset_missing",
                            "error": str(exc)})
        except ValueError as exc:
            return to_json({"status": "error", "error_kind": "invalid_input",
                            "error": str(exc)})
        except RuntimeError as exc:
            return to_json({"status": "error", "error_kind": "provider_error",
                            "error": str(exc)})
