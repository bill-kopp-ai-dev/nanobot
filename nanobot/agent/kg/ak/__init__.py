"""Native acquire-knowledge services (AK) shared by tools and gateway adapters."""

from __future__ import annotations

import json
from typing import Any


class UnsupportedCapabilityError(Exception):
    """Raised when the active provider/model cannot consume a requested modality.

    Image captioning requires a compatible turn runtime. Audio transcription
    requires the explicitly configured Groq Whisper service. Neither tool
    substitutes a stub result when its required provider is unavailable.
    """


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


__all__ = ["UnsupportedCapabilityError", "to_json"]
