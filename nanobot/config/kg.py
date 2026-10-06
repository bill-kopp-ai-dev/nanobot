"""Configuration for the native Percival knowledge graph integration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from pydantic import Field, model_validator

from nanobot.config_base import Base


class PercivalKgConfig(Base):
    """Bundle roots refer to parent directories, not bundle directories."""

    @model_validator(mode="before")
    @classmethod
    def reject_dedicated_enrich_model(cls, value: object) -> object:
        if isinstance(value, dict):
            fields = cast(dict[object, object], value)
            if any(key in fields for key in (
                "cmEnrichModel", "cm_enrich_model", "cmEnrichBaseUrl", "cm_enrich_base_url",
            )):
                raise ValueError(
                    "kg.cmEnrichModel/cmEnrichBaseUrl are obsolete; remove them and "
                    "configure the agent's provider and model or session preset instead"
                )
            return fields
        return value

    mode: Literal["native", "mcp", "both"] = "native"
    cm_root: Path | None = None
    ak_root: Path | None = None
    cm_enrich_enabled: bool = True
    cm_enrich_timeout_s: float = Field(default=45, gt=0)
    ak_image_caption_enabled: bool = True
    ak_audio_transcribe_enabled: bool = True
