"""Single-password CLI for the Percival instance.

Wraps the :class:`AccessCredential` and the optional local-recovery path
for the operator's first install or lost-password scenarios. Plain passwords
are never echoed, written to flags, or stored in shell history.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

import typer

from nanobot.access.credential import AccessCredentialError
from nanobot.access.password import (
    PasswordPolicyError,
    PasswordRuleViolation,
    PasswordTooLongError,
    PasswordTooShortError,
)

app = typer.Typer(help="Percival instance password administration")


def _resolve_data_dir(config_path: Path | None) -> Path:
    if config_path is None:
        from nanobot.config.loader import get_config_path

        config_path = get_config_path()
    return config_path.expanduser().resolve(strict=False).parent


def _read_password(prompt: str, *, confirm: bool) -> str:
    while True:
        first = getpass.getpass(prompt)
        if not first:
            typer.echo("password cannot be empty", err=True)
            raise typer.Exit(2)
        if not confirm:
            return first
        second = getpass.getpass("Confirm password: ")
        if first != second:
            typer.echo("passwords do not match", err=True)
            continue
        return first


@app.command("init")
def init(
    config: Path | None = typer.Option(None, "--config", help="Path to this instance's config.json"),
) -> None:
    """Create the instance's single human password (one-time setup)."""
    from nanobot.webui.gateway_auth import AccessController

    data_dir = _resolve_data_dir(config)
    controller = AccessController.from_data_dir(data_dir)
    if controller.has_password():
        typer.echo(
            "An instance password is already configured. Use `auth change` to rotate it.",
            err=True,
        )
        raise typer.Exit(1)
    password = _read_password("Set the Percival instance password: ", confirm=True)
    try:
        controller.setup(password)
    except PasswordPolicyError as exc:
        typer.echo(f"Password rejected: {exc}", err=True)
        raise typer.Exit(1) from exc
    except AccessCredentialError as exc:
        typer.echo(f"Could not persist the password: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo("Percival instance password configured.")


@app.command("change")
def change(
    config: Path | None = typer.Option(None, "--config", help="Path to this instance's config.json"),
) -> None:
    """Rotate the instance's single password (requires the current password)."""
    from nanobot.webui.gateway_auth import AccessController

    data_dir = _resolve_data_dir(config)
    controller = AccessController.from_data_dir(data_dir)
    if not controller.has_password():
        typer.echo(
            "No password is configured yet. Use `auth init` for the first setup.",
            err=True,
        )
        raise typer.Exit(1)
    current = getpass.getpass("Current password: ")
    if not current:
        typer.echo("Current password is required.", err=True)
        raise typer.Exit(2)
    new_password = _read_password("New password: ", confirm=True)
    try:
        controller.credential.set_password(new_password, current_password=current)
    except PasswordPolicyError as exc:
        typer.echo(f"Password rejected: {exc}", err=True)
        raise typer.Exit(1) from exc
    except AccessCredentialError as exc:
        typer.echo(f"Could not rotate the password: {exc}", err=True)
        raise typer.Exit(1) from exc
    # Invalidate any in-memory sessions/elevations in the running gateway.
    controller.sessions.revoke_all()
    controller.elevation.revoke_all()
    typer.echo("Password rotated; existing sessions were revoked.")


@app.command("reset")
def reset(
    config: Path | None = typer.Option(None, "--config", help="Path to this instance's config.json"),
    yes: bool = typer.Option(False, "--yes", help="Skip the interactive confirmation"),
) -> None:
    """Replace a lost or compromised password via local recovery.

    Requires direct access to the persisted verifier and the host filesystem.
    No remote or web endpoint can perform this operation; this CLI must run
    with the same OS user that owns the verifier file.
    """
    from nanobot.webui.gateway_auth import AccessController

    data_dir = _resolve_data_dir(config)
    controller = AccessController.from_data_dir(data_dir)
    if not yes and sys.stdin.isatty():
        typer.confirm(
            "This replaces the instance password and revokes all sessions. "
            "Anyone able to reach this machine can do the same. Continue?",
            default=False,
            abort=True,
        )
    new_password = _read_password("New password: ", confirm=True)
    try:
        controller.local_recover(new_password)
    except PasswordPolicyError as exc:
        typer.echo(f"Password rejected: {exc}", err=True)
        raise typer.Exit(1) from exc
    except AccessCredentialError as exc:
        typer.echo(f"Could not reset the password: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo("Password reset; existing sessions were revoked.")


@app.command("status")
def status(
    config: Path | None = typer.Option(None, "--config", help="Path to this instance's config.json"),
) -> None:
    """Report whether an instance password is configured."""
    from nanobot.webui.gateway_auth import AccessController

    data_dir = _resolve_data_dir(config)
    controller = AccessController.from_data_dir(data_dir)
    if controller.has_password():
        typer.echo("Percival instance password is configured.")
    else:
        typer.echo("No Percival instance password is configured yet. Run `auth init`.")


__all__ = [
    "PasswordPolicyError",
    "PasswordRuleViolation",
    "PasswordTooLongError",
    "PasswordTooShortError",
    "app",
]
