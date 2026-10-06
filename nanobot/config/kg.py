"""Configuration for the native Percival knowledge graph integration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field

from nanobot.config_base import Base


class PercivalKgConfig(Base):
    """Bundle roots refer to parent directories, not bundle directories."""

    mode: Literal["native", "mcp", "both"] = "native"
    cm_root: Path | None = None
    ak_root: Path | None = None
    cm_enrich_enabled: bool = True
    cm_enrich_timeout_s: float = Field(default=45, gt=0)
    cm_enrich_model: str = "MiniMax-M3"
    cm_enrich_base_url: str | None = None
    ak_image_caption_enabled: bool = True
    ak_audio_transcribe_enabled: bool = True
