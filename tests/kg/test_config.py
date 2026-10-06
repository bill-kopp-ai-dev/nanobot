"""Bundle roots are scoped to each request and respect filesystem capabilities."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from nanobot.agent.kg.roots import allowed_bundle_root, bundle_root
from nanobot.agent.tools.context import RequestContext, request_context
from nanobot.config.kg import PercivalKgConfig
from nanobot.config.schema import Config
from nanobot.security.workspace_policy import WorkspaceBoundaryError


def test_config_aliases_and_timeout() -> None:
    config = Config.model_validate({"kg": {"mode": "both", "cmEnrichTimeoutS": 12}})
    assert config.kg.mode == "both"
    assert config.kg.cm_enrich_timeout_s == 12
    assert Config().kg.mode == "native"
    with pytest.raises(ValidationError):
        PercivalKgConfig(cm_enrich_timeout_s=0)
    with pytest.raises(ValidationError):
        PercivalKgConfig(mode="disabled")


def test_bundle_root_uses_request_workspace_and_legacy_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = PercivalKgConfig()
    default, other = tmp_path / "default", tmp_path / "other"
    assert bundle_root("cm", config, default) == default / ".collective-memory"
    with request_context(RequestContext(channel="websocket", chat_id="one", workspace=other)):
        assert bundle_root("cm", config, default) == other / ".collective-memory"
    assert bundle_root("ak", config, default) == default / ".acquired-knowledge"
    monkeypatch.setenv("COLLECTIVE_MEMORY_ROOT", str(other))
    assert bundle_root("cm", PercivalKgConfig(cm_root=default), default) == other / ".collective-memory"


def test_explicit_external_root_requires_separate_read_write_capability(tmp_path: Path) -> None:
    workspace, parent = tmp_path / "workspace", tmp_path / "external"
    config = PercivalKgConfig(cm_root=parent)
    root = parent / ".collective-memory"
    with pytest.raises(WorkspaceBoundaryError):
        allowed_bundle_root("cm", config, workspace, restrict_to_workspace=True)
    assert allowed_bundle_root(
        "cm", config, workspace, restrict_to_workspace=True,
        extra_read_roots=(parent,),
    ) == root
    with pytest.raises(WorkspaceBoundaryError):
        allowed_bundle_root(
            "cm", config, workspace, restrict_to_workspace=True,
            extra_read_roots=(parent,), write=True,
        )
    assert allowed_bundle_root(
        "cm", config, workspace, restrict_to_workspace=True,
        extra_write_roots=(parent,), write=True,
    ) == root


def test_symlink_root_cannot_escape_workspace(tmp_path: Path) -> None:
    workspace, outside = tmp_path / "workspace", tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (workspace / ".collective-memory").symlink_to(outside, target_is_directory=True)
    with pytest.raises(WorkspaceBoundaryError):
        allowed_bundle_root("cm", PercivalKgConfig(), workspace, restrict_to_workspace=True)
