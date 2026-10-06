"""F4 registration: native AK tools are discovered by ToolLoader and obey mode."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.agent.tools.ak_multimodal import AKAudioTranscribeTool, AKImageCaptionTool
from nanobot.agent.tools.ak_read import AKSourceSearchTool
from nanobot.agent.tools.context import RequestContext, ToolContext, request_context
from nanobot.agent.tools.loader import ToolLoader
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.kg import PercivalKgConfig
from nanobot.config.schema import ToolsConfig
from nanobot.providers.base import GenerationSettings
from nanobot.utils.llm_runtime import LLMRuntime

AK_NATIVE_NAMES = {
    "ak_source_ingest", "ak_source_read", "ak_source_list", "ak_source_search",
    "ak_source_stats", "ak_get_laterally_isolated_notes",
    "ak_image_caption", "ak_audio_transcribe",
}


def _ctx(workspace: Path, *, mode: str = "native",
         config_overrides: dict | None = None) -> ToolContext:
    cfg = PercivalKgConfig(mode=mode)
    if config_overrides:
        for key, value in config_overrides.items():
            setattr(cfg, key, value)
    return ToolContext(config=ToolsConfig(), workspace=str(workspace), kg_config=cfg)


def test_loader_registers_eight_ak_tools_in_native_mode(tmp_path: Path) -> None:
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
async def test_audio_transcribe_tool_returns_unsupported_capability(tmp_path: Path) -> None:
    bundle = tmp_path / ".acquired-knowledge"
    (bundle / "sources").mkdir(parents=True)
    (bundle / "sources" / "voice.mp3").write_bytes(b"fake")
    runtime_request = RequestContext(
        channel="websocket", chat_id="audio-test",
        runtime=_unsupported_runtime(),
    )
    ctx = _ctx(tmp_path, mode="native")
    tool = AKAudioTranscribeTool.create(ctx)
    with request_context(runtime_request):
        payload = json.loads(await tool.execute(asset_path="sources/voice.mp3"))
    assert payload["status"] == "error"
    assert payload["error_kind"] == "unsupported_capability"


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
