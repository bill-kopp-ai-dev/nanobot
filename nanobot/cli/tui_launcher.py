"""Launch the TypeScript terminal client against the local gateway."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from nanobot import __version__
from nanobot.cli.process_identity import named_executable
from nanobot.cli.runtime_config import _model_display
from nanobot.cli.webui_support import (
    _gateway_health_ready,
    _gateway_health_url,
    _gateway_instance_command,
    _host_for_local_browser,
    _webui_endpoint_reachable,
)
from nanobot.config.paths import get_data_dir
from nanobot.config.schema import Config
from nanobot.webui.session_identity import is_webui_session_key, webui_chat_id

if TYPE_CHECKING:
    from nanobot.gateway import GatewayClientLease


class TuiUnavailableError(RuntimeError):
    """Raised when the native TypeScript TUI cannot run on this installation."""


class TuiSessionError(ValueError):
    """Raised when a session selector cannot be opened by the native TUI."""


# Keep in sync with TUI_DETACH_EXIT_CODE in tui/src/index.ts.
_TUI_DETACH_EXIT_CODE = 90
_GATEWAY_READY_TIMEOUT_S = 20.0
_GATEWAY_READY_POLL_S = 0.1


@dataclass(frozen=True)
class _GatewayHandle:
    base_url: str
    lease: GatewayClientLease | None = None


def launch_tui(
    config: Config,
    *,
    config_path: Path,
    workspace_override: str | None,
    session_id: str | None,
    theme: str,
) -> int:
    """Run the native TUI against the shared local gateway."""
    chat_id = _initial_tui_chat_id(session_id)
    tui_workspace = _initial_tui_workspace(workspace_override)
    command = resolve_tui_command()
    base_url, _bootstrap_secret_unused = _tui_gateway_connection(config)
    gateway: _GatewayHandle | None = None
    process: subprocess.Popen[Any] | None = None
    try:
        env = os.environ.copy()
        env.pop("NANOBOT_TUI_WS_URL", None)
        env.pop("NANOBOT_TUI_API_TOKEN", None)
        env.pop("NANOBOT_TUI_DESKTOP_RESOLVER", None)
        env.pop("NANOBOT_TUI_DESKTOP_TARGET", None)
        env.update(
            {
                "NANOBOT_TUI_BOOTSTRAP_URL": f"{base_url}/webui/bootstrap",
                "NANOBOT_TUI_HEALTH_URL": _gateway_health_url(
                    config.gateway.host,
                    config.gateway.port,
                ),
                "NANOBOT_TUI_API_URL": base_url,
                "NANOBOT_TUI_LOGIN_URL": f"{base_url}/auth/login",
                "NANOBOT_TUI_MODEL": _model_display(config)[0],
                "NANOBOT_TUI_MODEL_PRESET": config.agents.defaults.model_preset or "default",
                "NANOBOT_TUI_WORKSPACE": str(tui_workspace),
                "NANOBOT_TUI_VERSION": __version__,
                "NANOBOT_TUI_ACCESS": (
                    "workspace access" if config.tools.restrict_to_workspace else "full access"
                ),
                "NANOBOT_TUI_THEME": theme,
                "NANOBOT_TUI_GATEWAY_STOP_COMMAND": _gateway_instance_command(
                    "stop",
                    config_path=config_path,
                    workspace=workspace_override,
                ),
            }
        )
        # The TUI obtains a short-lived session via the new login endpoint; the
        # password is prompted interactively by the TUI itself and never
        # crosses this process boundary. The legacy env-var is cleared to
        # avoid accidental reuse by a stale bun build.
        env.pop("NANOBOT_TUI_BOOTSTRAP_SECRET", None)
        if chat_id:
            env["NANOBOT_TUI_CHAT_ID"] = chat_id
        else:
            env.pop("NANOBOT_TUI_CHAT_ID", None)
        try:
            process = subprocess.Popen(command, env=env)
        except OSError as exc:
            raise TuiUnavailableError(f"could not start the native TUI: {exc}") from exc
        gateway = _ensure_gateway(
            config,
            config_path=config_path,
            workspace_override=workspace_override,
            wait_until_ready=False,
        )
        exit_code = process.wait()
        if exit_code == _TUI_DETACH_EXIT_CODE:
            lease = gateway.lease
            if lease is not None:
                lease.mark_persistent()
            return 0
        return exit_code
    except BaseException:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise
    finally:
        lease = getattr(gateway, "lease", None) if gateway is not None else None
        if lease is not None:
            # Returning to the shell must not wait for process termination. The
            # gateway's client monitor observes the released last lease and owns
            # the orderly on-demand shutdown.
            lease.release(wait_for_stop=False)


def resolve_tui_command(*, data_dir: Path | None = None) -> list[str]:
    override = os.environ.get("NANOBOT_TUI_BIN", "").strip()
    if override:
        executable = Path(override).expanduser().resolve(strict=False)
        if not executable.is_file():
            raise TuiUnavailableError(f"NANOBOT_TUI_BIN does not exist: {executable}")
        return [str(executable)]

    suffix = ".exe" if os.name == "nt" else ""
    system = {"Windows": "win32", "Darwin": "darwin", "Linux": "linux"}.get(
        platform.system(),
        platform.system().lower(),
    )
    machine = {"x86_64": "x64", "AMD64": "x64", "aarch64": "arm64"}.get(
        platform.machine(),
        platform.machine().lower(),
    )
    if system == "win32" and machine == "arm64":
        raise TuiUnavailableError(
            "the native TUI is not available on Windows ARM64 because Bun FFI is disabled "
            "on that platform; use the classic prompt until the upstream runtime supports it"
        )
    asset = f"nanobot-tui-{system}-{machine}{suffix}"
    source_dir = _source_checkout_tui_dir()
    if source_dir is not None:
        bun = shutil.which("bun")
        if not bun:
            raise TuiUnavailableError(
                "this source checkout requires Bun to run its matching TUI; "
                "install Bun, then run `nanobot agent` again"
            )
        return _resolve_source_tui_command(source_dir, bun, data_dir=data_dir)

    packaged = Path(__file__).resolve().parents[1] / "tui" / "bin" / asset
    if packaged.is_file():
        return [str(packaged)]

    raise TuiUnavailableError(
        f"no native TUI is installed for nanobot {__version__} on this platform; "
        "install a matching TUI from an operator-approved distribution and set "
        "NANOBOT_TUI_BIN, or use `nanobot agent --classic`"
    )


def _source_checkout_tui_dir() -> Path | None:
    """Return this checkout's TUI source, never a neighboring unrelated directory."""
    return _tui_source_dir(Path(__file__).resolve().parents[2])


def _tui_source_dir(project_root: Path) -> Path | None:
    project_root = project_root.resolve(strict=False)
    source_dir = project_root / "tui"
    if (project_root / "pyproject.toml").is_file() and (source_dir / "package.json").is_file():
        return source_dir
    return None


def _resolve_source_tui_command(
    source_dir: Path, bun: str, *, data_dir: Path | None = None,
) -> list[str]:
    dependency = source_dir / "node_modules" / "@opentui" / "core"
    try:
        install = subprocess.run(
            [bun, "install", "--frozen-lockfile"],
            cwd=source_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise TuiUnavailableError(f"could not install TUI dependencies: {exc}") from exc
    if install.returncode != 0 or not dependency.is_dir():
        detail = (install.stderr or install.stdout).strip().splitlines()
        suffix = f": {detail[-1]}" if detail else ""
        raise TuiUnavailableError(f"could not install TUI dependencies{suffix}")
    executable = named_executable(
        bun,
        name="nanobot-tui",
        directory=(data_dir if data_dir is not None else get_data_dir()) / "run" / "executables",
    )
    return [executable, str(source_dir / "src" / "index.ts")]


def _ensure_gateway(
    config: Config,
    *,
    config_path: Path,
    workspace_override: str | None,
    wait_until_ready: bool = True,
) -> _GatewayHandle:
    from nanobot.gateway import (
        GatewayClientLease,
        GatewayInstance,
        GatewayRuntime,
    )

    base_url, _bootstrap_secret = _tui_gateway_connection(config)
    _ = _bootstrap_secret  # retained for legacy callers; the new model does not use it
    instance = GatewayInstance.resolve(
        config_path=config_path,
        workspace=workspace_override,
    )
    runtime = GatewayRuntime(paths=instance.paths)
    lease = GatewayClientLease(runtime, kind="tui")
    lease.acquire()
    try:
        def ready(status: object) -> bool:
            management_ready = getattr(status, "ready", None)
            if not isinstance(management_ready, bool):
                management_ready = _gateway_health_ready(
                    config.gateway.host,
                    config.gateway.port,
                )
            return _webui_endpoint_reachable(base_url) and management_ready

        def wait_for_ready(log_path: object) -> _GatewayHandle:
            deadline = time.monotonic() + _GATEWAY_READY_TIMEOUT_S
            while time.monotonic() < deadline:
                current = runtime.status()
                if not current.running:
                    break
                if current.port not in {None, config.gateway.port}:
                    break
                if ready(current):
                    return _GatewayHandle(base_url=base_url, lease=lease)
                time.sleep(_GATEWAY_READY_POLL_S)

            current = runtime.status()
            if current.running:
                raise TuiUnavailableError(
                    "local gateway process is running but its WebSocket/WebUI listener "
                    "is unavailable; channel recovery did not restore it. "
                    "Run `nanobot gateway status` and inspect logs at "
                    f"{log_path}; if it remains degraded, run `nanobot gateway restart`."
                )
            raise TuiUnavailableError(
                f"local gateway did not become ready; logs: {log_path}"
            )

        status = runtime.status()
        if status.running:
            if status.port not in {None, config.gateway.port}:
                raise TuiUnavailableError(
                    "the matching gateway instance is running on a different port; "
                    "restart it or use `nanobot agent --classic`"
                )
            if not wait_until_ready:
                return _GatewayHandle(base_url=base_url, lease=lease)
            if ready(status):
                return _GatewayHandle(base_url=base_url, lease=lease)
            return wait_for_ready(status.log_path)
        elif _webui_endpoint_reachable(base_url):
            raise TuiUnavailableError(
                "the configured gateway port belongs to a different nanobot instance; "
                "stop that instance or use `nanobot agent --classic`"
            )

        result = lease.ensure_on_demand_gateway(
            instance.start_options(port=config.gateway.port)
        )
        if not result.ok and result.message != "gateway_already_running":
            raise TuiUnavailableError(
                f"could not start the local gateway ({result.message}); "
                f"logs: {result.status.log_path}"
            )

        if result.message == "gateway_already_running" and result.status.port not in {
            None,
            config.gateway.port,
        }:
            raise TuiUnavailableError(
                "the matching gateway instance is running on a different port; "
                "restart it or use `nanobot agent --classic`"
            )
        if not wait_until_ready:
            return _GatewayHandle(base_url=base_url, lease=lease)
        return wait_for_ready(result.status.log_path)
    except BaseException:
        lease.release(timeout_s=5)
        raise


def _tui_gateway_connection(config: Config) -> tuple[str, str]:
    """Read the gateway base URL without consulting any secret.

    Returns ``(base_url, "")``; the empty second element is preserved for
    callers that previously expected a shared bootstrap secret. The TUI now
    authenticates with the instance password via the new ``/auth/login``
    endpoint, so the gateway URL is the only value it needs up front.
    """
    raw: object = getattr(config.channels, "websocket", None)
    settings = cast(dict[str, Any], raw) if isinstance(raw, dict) else {}
    host = _host_for_local_browser(str(settings.get("host") or "127.0.0.1"))
    try:
        port = int(settings.get("port") or 8765)
    except (TypeError, ValueError):
        port = 8765
    return f"http://{host}:{port}", ""


def _websocket_chat_id(session_id: str) -> str | None:
    """Map the CLI selector to the WebSocket namespace used by the native TUI."""
    if is_webui_session_key(session_id):
        return webui_chat_id(session_id)
    if ":" in session_id:
        raise TuiSessionError(
            "the native TUI can open only WebSocket sessions; use --classic to resume "
            f"{session_id!r}"
        )
    return session_id or None


def _initial_tui_chat_id(session_id: str | None) -> str | None:
    """Start fresh unless the caller explicitly selects a TUI chat."""
    if session_id is not None:
        return _websocket_chat_id(session_id)
    return None


def _initial_tui_workspace(workspace_override: str | None) -> Path:
    """Use the launch directory unless the caller explicitly selects a workspace."""
    workspace = Path(workspace_override) if workspace_override is not None else Path.cwd()
    return workspace.expanduser().resolve(strict=False)
