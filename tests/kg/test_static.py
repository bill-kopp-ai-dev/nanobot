"""Packaged SPA paths must never fall through to the unrelated WebUI shell."""

from pathlib import Path

from nanobot.webui.kg_static import serve_kg_static


async def test_kg_static_serves_only_bundled_files_and_html_routes(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html>KG shell</html>")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index-Abcd1234.js").write_text("console.log('KG')")
    assert b"KG shell" in (await serve_kg_static(
        "/kg-interface", root=tmp_path, accepts_html=True,
    )).body
    assert b"KG shell" in (await serve_kg_static(
        "/kg-interface/notes", root=tmp_path, accepts_html=True,
    )).body
    script = await serve_kg_static(
        "/kg-interface/assets/index-Abcd1234.js", root=tmp_path, accepts_html=False,
    )
    assert script.headers["Content-Type"].startswith("application/javascript")
    assert script.headers["Cache-Control"].endswith("immutable")
    assert (await serve_kg_static(
        "/kg-interface/assets/missing.js", root=tmp_path, accepts_html=True,
    )).status_code == 404
    assert (await serve_kg_static(
        "/kg-interface/api/memory/notes", root=tmp_path, accepts_html=True,
    )).status_code == 404
    assert (await serve_kg_static(
        "/kg-interface/..%2Fprivate", root=tmp_path, accepts_html=True,
    )).status_code == 403


async def test_kg_static_rejects_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "static"
    root.mkdir()
    (root / "index.html").write_text("<html>KG shell</html>")
    (root / "secret.js").symlink_to(tmp_path / "private.js")
    (tmp_path / "private.js").write_text("secret")
    assert (await serve_kg_static(
        "/kg-interface/secret.js", root=root, accepts_html=True,
    )).status_code == 403
