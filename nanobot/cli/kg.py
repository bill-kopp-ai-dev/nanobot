"""Native knowledge-graph maintenance CLI; no MCP server or model startup."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar, cast

import typer

from nanobot.agent.kg import maintenance
from nanobot.agent.kg.roots import BundleKind, bundle_root
from nanobot.agent.kg.vendor.okf_bundle_core.lock import LockTimeout
from nanobot.agent.kg.vendor.okf_bundle_core.paths import PathEscapeError, resolve_bundle_arg
from nanobot.config.errors import ConfigLoadError
from nanobot.config.loader import load_config
from nanobot.config.schema import Config
from nanobot.security.workspace_policy import WorkspaceBoundaryError, resolve_allowed_path

app = typer.Typer(help="Inspect and maintain native CM/AK bundles")
bundle_app = typer.Typer(help="Locate or initialize a bundle")
graph_app = typer.Typer(help="Maintain derived graph artifacts")
p11_app = typer.Typer(help="Bootstrap Collective Memory P11 protection")
app.add_typer(bundle_app, name="bundle")
app.add_typer(graph_app, name="graph")
app.add_typer(p11_app, name="p11")
T = TypeVar("T")


@app.callback()
def kg_options(
    ctx: typer.Context,
    config: Path | None = typer.Option(None, "--config", "-c", help="Nanobot config.json"),
    workspace: Path | None = typer.Option(None, "--workspace", "-w", help="Active workspace"),
) -> None:
    """Use --config/--workspace before the KG subcommand."""
    try:
        if config is not None and not config.expanduser().is_file():
            raise FileNotFoundError(f"config file not found: {config}")
        loaded = load_config(config.expanduser() if config else None)
    except (ConfigLoadError, FileNotFoundError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    if workspace is not None:
        loaded.agents.defaults.workspace = str(workspace.expanduser())
    ctx.obj = loaded


def _resolve(ctx: typer.Context, kind: BundleKind, override: Path | None = None) -> Path:
    config: Config = ctx.obj
    workspace = config.workspace_path.resolve()
    layout = maintenance.LAYOUTS[kind]
    if override is None:
        root = bundle_root(kind, config.kg, workspace, use_request_context=False)
    else:
        candidate = override.expanduser()
        if not candidate.is_absolute():
            candidate = workspace / candidate
        root = resolve_bundle_arg(candidate, bundle_name=(".collective-memory" if kind == "cm" else ".acquired-knowledge"), layout=layout)
    if config.tools.restrict_to_workspace:
        root = resolve_allowed_path(root, allowed_root=workspace)
    return root.resolve()


def _run(ctx: typer.Context, kind: BundleKind, override: Path | None, action: Callable[[Path], T]) -> T:
    try:
        root = _resolve(ctx, kind, override)
        return action(root)
    except (OSError, ValueError, WorkspaceBoundaryError, PathEscapeError, LockTimeout) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc


def _show(value: object, *, json_output: bool = False) -> None:
    if json_output:
        typer.echo(json.dumps(value, ensure_ascii=False, indent=2))
    elif isinstance(value, dict):
        for key, item in cast(dict[object, object], value).items():
            typer.echo(f"{key}: {item}")
    else:
        typer.echo(str(value))


@bundle_app.command("path")
def bundle_path(ctx: typer.Context, kind: BundleKind, bundle_root_arg: Path | None = typer.Option(None, "--bundle-root", help="Parent or bundle path")) -> None:
    """Print the selected path, even if the bundle is not initialized."""
    _show(_run(ctx, kind, bundle_root_arg, lambda root: root))


@bundle_app.command("init")
def bundle_init(
    ctx: typer.Context, kind: BundleKind,
    bundle_root_arg: Path | None = typer.Option(None, "--bundle-root", help="Parent or bundle path"),
    yes: bool = typer.Option(False, "--yes", help="Confirm destination non-interactively"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable result"),
) -> None:
    """Create a new bundle layout and GitStore; refuses nonempty roots."""
    root = _run(ctx, kind, bundle_root_arg, lambda path: path)
    if not yes and not typer.confirm(f"Initialize {kind} bundle at {root}?", default=False):
        raise typer.Exit(1)
    _show(_run(ctx, kind, bundle_root_arg, lambda path: maintenance.init_bundle(path, kind)), json_output=json_output)


@graph_app.command("rebuild")
def graph_rebuild(
    ctx: typer.Context, kind: BundleKind,
    bundle_root_arg: Path | None = typer.Option(None, "--bundle-root", help="Parent or bundle path"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable result"),
) -> None:
    """Atomically regenerate graph.json from notes, without LLM labeling."""
    _show(_run(ctx, kind, bundle_root_arg, lambda root: maintenance.rebuild_graph(root, kind)), json_output=json_output)


@p11_app.command("bootstrap")
def p11_bootstrap(
    ctx: typer.Context,
    bundle_root_arg: Path | None = typer.Option(None, "--bundle-root", help="CM parent or bundle path"),
    apply: bool = typer.Option(False, "--apply", help="Write protection marks after review"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Only list candidates (default)"),
    top_degree: int = typer.Option(10, "--top-degree", min=1, help="Number of top-degree hubs"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable result"),
) -> None:
    """Find structurally canonical CM notes and optionally mark protected."""
    if apply and dry_run:
        raise typer.BadParameter("--apply and --dry-run are mutually exclusive")
    result = _run(ctx, "cm", bundle_root_arg,
                  lambda root: maintenance.bootstrap_p11(root, apply=apply, top_degree=top_degree))
    _show(result, json_output=json_output)
    if any("error" in item for item in result.get("applied", [])):
        raise typer.Exit(1)


@app.command("ak-migrate-lateral-links")
def ak_migrate_lateral_links(
    ctx: typer.Context,
    bundle_root_arg: Path | None = typer.Option(None, "--bundle-root", help="AK parent or bundle path"),
    apply: bool = typer.Option(False, "--apply", help="Write and commit migration"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable result"),
) -> None:
    """Move AK lateral links into graph-visible body; dry-run by default."""
    _show(_run(ctx, "ak", bundle_root_arg,
               lambda root: maintenance.migrate_lateral_links(root, apply=apply)), json_output=json_output)


@app.command("doctor")
def doctor(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Machine-readable checks"),
    bundle_root_arg: Path | None = typer.Option(None, "--bundle-root", help="Parent for both bundles (or one named bundle)"),
) -> None:
    """Read-only diagnosis of both roots, Git layout and graph artifacts."""
    config: Config = ctx.obj
    checks: list[dict[str, object]] = []
    for kind in ("cm", "ak"):
        selected: BundleKind = kind
        override = bundle_root_arg
        if override is not None and override.name in (".collective-memory", ".acquired-knowledge"):
            override = override if override.name == (".collective-memory" if kind == "cm" else ".acquired-knowledge") else override.parent
        try:
            root = _resolve(ctx, selected, override)
            maintenance.require_bundle(root, kind)
            if kind == "cm":
                from nanobot.agent.kg.cm.f2 import memory_stats

                health = memory_stats(root)
                summary = {"notes": health["notes_total"], "orphans": len(health["orphans"])}
            else:
                from nanobot.agent.kg.ak.read import source_stats

                health = source_stats(root)
                summary = {key: health[key] for key in ("sources_total", "extracted_total", "orphan_extracted", "broken_file_path")}
            graph_path = root / "graphify-out" / "graph.json"
            if graph_path.is_file():
                from nanobot.agent.kg.graph_data import graph_artifact

                graph_artifact(root, data=True)
                status, detail = "ok", "graph.json readable"
            else:
                status, detail = "warn", "graph.json missing; run nanobot kg graph rebuild " + kind
            checks.append({"bundle": kind, "status": status, "path": str(root), "detail": detail, "health": summary})
        except (OSError, ValueError, WorkspaceBoundaryError, PathEscapeError) as exc:
            checks.append({"bundle": kind, "status": "fail", "path": str(override or config.workspace_path), "detail": str(exc)})
        env_name = "COLLECTIVE_MEMORY_ROOT" if kind == "cm" else "ACQUIRED_KNOWLEDGE_ROOT"
        configured = getattr(config.kg, f"{kind}_root")
        if os.environ.get(env_name) and configured and Path(os.environ[env_name]).expanduser().resolve() != Path(configured).expanduser().resolve():
            checks.append({"bundle": kind, "status": "warn", "path": "", "detail": f"{env_name} overrides kg.{kind}_root"})
    if json_output:
        _show(checks, json_output=True)
    else:
        for item in checks:
            typer.echo(f"[{item['status']}] {item['bundle']}: {item['detail']} ({item['path']})")
    if any(item["status"] == "fail" for item in checks):
        raise typer.Exit(1)
