"""F9 guidance is discoverable with the real, non-recursive skills loader."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from nanobot.agent.skills import SkillsLoader, valid_skill_metadata
from nanobot.cli.commands import app

KG_SKILLS = (
    "cm-overview", "cm-notes-write", "cm-link", "cm-capture-session",
    "cm-audit-health", "cm-rebuild-graph", "ak-atomize", "ak-link",
    "ak-onboard-source", "ak-audit-health", "ak-commit-policy", "ak-rebuild-graph",
)


@pytest.mark.parametrize("name", KG_SKILLS)
def test_native_kg_skill_is_discovered_and_loadable(tmp_path: Path, name: str) -> None:
    loader = SkillsLoader(tmp_path)
    entry = next(s for s in loader.list_skills() if s["name"] == name)
    assert entry["source"] == "builtin"
    assert valid_skill_metadata(loader.get_skill_metadata(name) or {}, name)
    assert loader.load_skill(name)
    assert loader.load_skills_for_context([name]).startswith(f"### Skill: {name}")


@pytest.mark.parametrize("name,kind", [("cm-rebuild-graph", "cm"), ("ak-rebuild-graph", "ak")])
def test_documented_native_graph_command_exists(tmp_path: Path, name: str, kind: str) -> None:
    guidance = SkillsLoader(tmp_path).load_skill(name)
    assert guidance and f"nanobot kg graph rebuild {kind} --json" in guidance
    runner = CliRunner()
    assert runner.invoke(app, ["kg", "graph", "rebuild", "--help"]).exit_code == 0
    assert runner.invoke(app, ["kg", "graph", "rebuild", kind, "--help"]).exit_code == 0
    assert runner.invoke(app, ["kg", "doctor", "--help"]).exit_code == 0
