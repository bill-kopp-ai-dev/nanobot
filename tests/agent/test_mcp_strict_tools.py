"""Tests for the per-server `strictTools` opt-in on MCP tool schemas.

Why this exists: some models silently degrade nested tool arguments instead
of honouring the declared schema. MiniMax stringifies `array`-of-`object`
parameters and then retries with progressively more malformed payloads —
observed in production as 7 failures out of 13 calls to a single tool, the
bad ones arriving as `'['`, `'½'`, and a JSON string truncated one character
short of valid. Upstream reports point at `strict` as the switch that turns on
schema validation for nested parameters, so the flag needs to reach the wire.

It is opt-in per server because strict mode also constrains the schema itself
(every property in `required`, `additionalProperties: false`), so a provider
following OpenAI semantics may reject a schema it previously accepted.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from nanobot.agent.tools.mcp import MCPToolWrapper
from nanobot.config.schema import MCPServerConfig


def _tool_def(name: str = "memory_batch_link"):
    return SimpleNamespace(
        name=name,
        description="Apply N edges in one round-trip",
        inputSchema={
            "type": "object",
            "properties": {"edges": {"type": "array", "items": {"type": "object"}}},
        },
    )


def test_default_omits_strict_entirely():
    """Servers that have not opted in send the exact payload they sent before."""
    wrapper = MCPToolWrapper(AsyncMock(), "srv", _tool_def())
    assert wrapper.strict is None
    assert "strict" not in wrapper.to_schema()["function"]


def test_opt_in_puts_strict_true_on_the_function_schema():
    wrapper = MCPToolWrapper(AsyncMock(), "srv", _tool_def(), strict_tools=True)
    assert wrapper.strict is True
    assert wrapper.to_schema()["function"]["strict"] is True


def test_opt_out_is_indistinguishable_from_default():
    """`strictTools: false` is the default, not an explicit `strict: false`.

    Sending `strict: false` would be a behaviour change for every server that
    never asked for one, so `False` maps to "omit", not to "send false".
    """
    wrapper = MCPToolWrapper(AsyncMock(), "srv", _tool_def(), strict_tools=False)
    assert wrapper.strict is None
    assert "strict" not in wrapper.to_schema()["function"]


def test_config_defaults_to_off():
    """The flag must not turn itself on for existing configs."""
    assert MCPServerConfig().strict_tools is False


def test_config_accepts_camel_case_from_json():
    """`config.json` is camelCase; the field has to bind from `strictTools`."""
    cfg = MCPServerConfig.model_validate({"command": "x", "strictTools": True})
    assert cfg.strict_tools is True


def test_schema_is_otherwise_untouched_by_the_flag():
    """Turning strict on must not rewrite name/description/parameters."""
    plain = MCPToolWrapper(AsyncMock(), "srv", _tool_def()).to_schema()["function"]
    strict = MCPToolWrapper(
        AsyncMock(), "srv", _tool_def(), strict_tools=True
    ).to_schema()["function"]
    assert {k: v for k, v in strict.items() if k != "strict"} == plain
