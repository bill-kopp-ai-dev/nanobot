"""A lost MCP response does not prove a paid research operation never ran."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mcp.types import ResourceTemplate

from nanobot.agent.tools.mcp import MCPResourceTemplateWrapper, MCPToolWrapper
from nanobot.agent.tools.registry import is_tool_error_result


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["research_deep", "research_write_report"])
async def test_research_transport_loss_is_not_replayed(name):
    session = AsyncMock()
    session.call_tool.side_effect = ConnectionResetError("lost after upstream accepted")
    wrapper = MCPToolWrapper(session, "percival_docker_deep-research", SimpleNamespace(
        name=name, description="research", inputSchema={"type": "object"},
    ))
    result = await wrapper.execute()
    assert session.call_tool.await_count == 1
    assert is_tool_error_result(result)
    assert "unknown" in result.lower()


@pytest.mark.asyncio
async def test_research_resource_cache_miss_is_not_replayed():
    session = AsyncMock()
    session.read_resource.side_effect = ConnectionResetError("lost after cache miss")
    wrapper = MCPResourceTemplateWrapper(session, "percival_docker_deep-research", ResourceTemplate(
        name="research", uriTemplate="research://{topic}",
    ))
    result = await wrapper.execute(topic="fixture")
    assert session.read_resource.await_count == 1
    assert is_tool_error_result(result)
