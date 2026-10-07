"""Hatch build hook that bundles the webui (Vite) into nanobot/web/dist.

Triggered automatically by `python -m build` (and any other hatch-driven build)
so published wheels and sdists ship a fresh webui without requiring developers
to remember `cd webui && bun run build` beforehand.

Behavior:

- Skips for editable installs (`pip install -e .`). Editable mode is for Python
  development; webui contributors use `cd webui && bun run dev` (Vite HMR) and
  do not need a packaged `dist/`.
- No-op when `webui/package.json` is absent (e.g. installing from an sdist that
  already contains a prebuilt `nanobot/web/dist/`).
- Skips when `NANOBOT_SKIP_WEBUI_BUILD=1` is set.
- Reuses `nanobot/web/dist/` only when it is already fresh, unless
  `NANOBOT_FORCE_WEBUI_BUILD=1` is set.
- Uses `bun` when available, otherwise falls back to `npm`. The chosen tool
  performs `install` followed by `run build`.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _load_webui_build_module() -> ModuleType:
    from nanobot.webui import build as webui_build

    return webui_build


class WebUIBuildHook(BuildHookInterface):
    PLUGIN_NAME = "webui-build"

    def initialize(self, version: str, build_data: dict) -> None:  # noqa: D401
        root = Path(self.root)
        webui_dir = root / "webui"
        package_json = webui_dir / "package.json"
        dist_dir = root / "nanobot" / "web" / "dist"
        index_html = dist_dir / "index.html"

        # `pip install -e .` builds an editable wheel; skip the (slow) webui
        # bundle since editable installs target Python development and webui
        # work uses `bun run dev` instead.
        if self.target_name == "wheel" and version == "editable":
            self.app.display_info(
                "[webui-build] skipped for editable install "
                "(use `cd webui && bun run build` to bundle webui manually)"
            )
            return

        self._vendor_kg_core(root)
        self._build_kg_interface(root)

        if os.environ.get("NANOBOT_SKIP_WEBUI_BUILD") == "1":
            self.app.display_info("[webui-build] skipped via NANOBOT_SKIP_WEBUI_BUILD=1")
            return

        if not package_json.is_file():
            self.app.display_info(
                "[webui-build] no webui/ source tree, assuming prebuilt nanobot/web/dist/"
            )
            return

        webui_build = _load_webui_build_module()
        status = webui_build.inspect_webui_bundle(source_dir=webui_dir, dist_dir=dist_dir)
        force = os.environ.get("NANOBOT_FORCE_WEBUI_BUILD") == "1"
        if not status.needs_build and not force:
            self.app.display_info(
                f"[webui-build] reusing existing build at {dist_dir} "
                "(already fresh; set NANOBOT_FORCE_WEBUI_BUILD=1 to rebuild)"
            )
            return

        if status.needs_build and not force:
            self.app.display_info(
                f"[webui-build] {webui_build.describe_webui_bundle_status(status)}"
            )

        try:
            webui_build.build_webui_bundle(
                source_dir=webui_dir,
                dist_dir=dist_dir,
                output=self.app.display_info,
            )
        except webui_build.WebUIBuildError as exc:
            raise RuntimeError(
                "[webui-build] "
                f"{exc}. Install `bun` or `npm`, or set NANOBOT_SKIP_WEBUI_BUILD=1 to bypass."
            ) from exc

        if not index_html.is_file():
            raise RuntimeError(
                f"[webui-build] build finished but {index_html} is missing; "
                "check webui/vite.config.ts outDir."
            )
        self.app.display_info(f"[webui-build] webui ready at {dist_dir}")

    def _vendor_kg_core(self, root: Path) -> None:
        """Materialize a pinned core snapshot for both source and wheel builds."""
        vendor = root / "nanobot" / "agent" / "kg" / "vendor"
        target = vendor / "okf_bundle_core"
        license_file = vendor / "LICENSE.okf-bundle-core"
        manifest_file = vendor / "SOURCE.json"
        source_setting = os.environ.get("PERCIVAL_KG_CORE_SOURCE", "").strip()
        if source_setting:
            source = Path(source_setting).expanduser().resolve()
            package = source / "src" / "okf_bundle_core"
            if not package.is_dir() or not (source / "LICENSE").is_file():
                raise RuntimeError("[kg-vendor] source needs src/okf_bundle_core and LICENSE")
            if target.exists():
                raise RuntimeError(
                    "[kg-vendor] snapshot already exists; unset PERCIVAL_KG_CORE_SOURCE "
                    "to reuse it, or review/remove the old snapshot before updating"
                )
            vendor.mkdir(parents=True, exist_ok=True)
            shutil.copytree(package, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copy2(source / "LICENSE", license_file)
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=source, capture_output=True,
                text=True, check=False, timeout=5,
            ) if shutil.which("git") else None
            files = {
                file.name: hashlib.sha256(file.read_bytes()).hexdigest()
                for file in sorted(target.glob("*.py"))
            }
            manifest = {
                "source": "https://github.com/bill-kopp-ai-dev/okf-bundle-core",
                "revision": revision.stdout.strip() if revision and revision.returncode == 0 else None,
                "upstream_python_sha256": files,
                "vendor_python_sha256": files,
                "patched_files": [],
            }
            manifest_file.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        if not (target / "__init__.py").is_file() or not license_file.is_file() or not manifest_file.is_file():
            raise RuntimeError(
                "[kg-vendor] missing vendored core; set PERCIVAL_KG_CORE_SOURCE="
                "<okf-bundle-core checkout> or include the reviewed snapshot in the sdist"
            )
        manifest = json.loads(manifest_file.read_text())
        current_files = {
            file.name: hashlib.sha256(file.read_bytes()).hexdigest()
            for file in sorted(target.glob("*.py"))
        }
        patched_files = sorted(
            name for name, digest in current_files.items()
            if digest != manifest["upstream_python_sha256"].get(name)
        )
        if (current_files != manifest.get("vendor_python_sha256")
                or patched_files != sorted(manifest.get("patched_files", []))
                or set(current_files) != set(manifest["upstream_python_sha256"])):
            raise RuntimeError(
                "[kg-vendor] snapshot differs from SOURCE.json; review changes and "
                "update hashes and PATCHES.md before building"
            )
        self.app.display_info(f"[kg-vendor] core ready at {target}")

    def _build_kg_interface(self, root: Path) -> None:
        """Ship a prebuilt SPA in both archives, or fail rather than ship a broken link.

        A release sdist contains the built assets and builds its wheel without
        needing a sibling checkout. For a development build without a snapshot,
        the source must be supplied explicitly; no implicit ~/Projects lookup.
        """
        target = root / "nanobot" / "web" / "kg-interface"
        index = target / "index.html"
        source_setting = os.environ.get("PERCIVAL_KG_SPA_SOURCE", "").strip()
        source = Path(source_setting).expanduser().resolve() if source_setting else root / "spa"
        force = os.environ.get("PERCIVAL_FORCE_KG_SPA_BUILD") == "1"
        skip = os.environ.get("PERCIVAL_SKIP_KG_SPA_BUILD") == "1"

        if skip and not index.is_file():
            raise RuntimeError("[kg-build] skip requested but prebuilt kg-interface/index.html is missing")
        # Never replace files that no longer match the last reviewed snapshot.
        # A refresh may remove hashed assets from that snapshot, but it must
        # not silently discard unrelated files placed in the target directory.
        if index.is_file():
            self._verify_kg_interface(target)
        if source.joinpath("package.json").is_file() and not skip and (force or not index.is_file()):
            if shutil.which("bun") is None:
                raise RuntimeError("[kg-build] bun is required to build the KG SPA source")
            try:
                subprocess.run(["bun", "run", "build"], cwd=source, check=True, timeout=300)
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise RuntimeError("[kg-build] SPA build failed") from exc
            output = source / "dist"
            if not output.joinpath("index.html").is_file() or not source.joinpath("LICENSE").is_file():
                raise RuntimeError("[kg-build] source build must include dist/index.html and LICENSE")
            output_files = {str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()}
            existing_files = {
                str(path.relative_to(target)) for path in target.rglob("*")
                if path.is_file() and path.name != "SOURCE.json"
            } if target.is_dir() else set()
            stale = existing_files - output_files - {"LICENSE"}
            for name in stale:
                (target / name).unlink()
            shutil.copytree(output, target, dirs_exist_ok=True)
            shutil.copy2(source / "LICENSE", target / "LICENSE")
            lock = source / "bun.lock"
            revision_result = (
                subprocess.run(
                    ["git", "rev-parse", "HEAD"], cwd=source, capture_output=True,
                    text=True, check=False, timeout=5,
                ) if shutil.which("git") else None
            )
            status_result = (
                subprocess.run(
                    ["git", "status", "--porcelain", "--untracked-files=normal"],
                    cwd=source, capture_output=True, text=True, check=False, timeout=5,
                ) if shutil.which("git") else None
            )
            manifest = {
                "source": "https://github.com/bill-kopp-ai-dev/spa",
                "revision": revision_result.stdout.strip() if revision_result and revision_result.returncode == 0 else None,
                "dirty": bool(status_result.stdout.strip()) if status_result and status_result.returncode == 0 else None,
                "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.is_file() else None,
                "index_sha256": hashlib.sha256(index.read_bytes()).hexdigest(),
                "asset_sha256": {
                    str(path.relative_to(target)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted(target.rglob("*")) if path.is_file() and path.name != "SOURCE.json"
                },
            }
            (target / "SOURCE.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")

        if not index.is_file() or not (target / "LICENSE").is_file() or not (target / "SOURCE.json").is_file():
            raise RuntimeError(
                "[kg-build] KG SPA snapshot missing: provide PERCIVAL_KG_SPA_SOURCE="
                "<source> for the source build, or bundle prebuilt "
                "nanobot/web/kg-interface/{index.html,LICENSE,SOURCE.json} in the sdist"
            )
        self._verify_kg_interface(target)
        self.app.display_info(f"[kg-build] SPA ready at {target}")

    @staticmethod
    def _verify_kg_interface(target: Path) -> None:
        index = target / "index.html"
        manifest = json.loads((target / "SOURCE.json").read_text())
        if hashlib.sha256(index.read_bytes()).hexdigest() != manifest.get("index_sha256"):
            raise RuntimeError("[kg-build] SPA index.html differs from SOURCE.json; rebuild the snapshot")
        current_assets = {
            str(path.relative_to(target)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(target.rglob("*")) if path.is_file() and path.name != "SOURCE.json"
        }
        if current_assets != manifest.get("asset_sha256"):
            raise RuntimeError("[kg-build] SPA assets differ from SOURCE.json; review the snapshot")
