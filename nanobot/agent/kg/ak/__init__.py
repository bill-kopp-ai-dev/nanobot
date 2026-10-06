"""Native acquire-knowledge services (AK) shared by tools and gateway adapters."""

from __future__ import annotations

import json
from typing import Any


class UnsupportedCapabilityError(Exception):
    """Raised when the active provider/model cannot consume a requested modality.

    Multimodal AK tools (image_caption, audio_transcribe) call
    ``runtime.provider.supports_modality(modality, model)`` and surface this
    error when the check returns ``False``.  The legacy AK code used a
    deterministic stub (FakeVisionAgent) when the MiniMax key was absent, but
    the plan requires that native tools reuse the requesting turn's runtime
    and never substitute a different model — a stub would silently return
    placeholder text and look like a real caption.
    """


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


__all__ = ["UnsupportedCapabilityError", "to_json"]
