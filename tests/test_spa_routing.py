"""
SPA catch-all: sirve index.html en las rutas de React Router sin comerse
la API, y sin dejar leer archivos fuera de static/.
"""
from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.routing import Mount
from starlette.testclient import TestClient

from app.main import RESERVED_PREFIXES, app as real_app, mount_spa, resolve_spa_file


@pytest.fixture
def static_dir(tmp_path: Path) -> Path:
    """A minimal `web/dist` build, with a secret sitting next to it."""
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("<html>SPA INDEX</html>")
    (static / "assets" / "app.js").write_text("console.log('app')")
    (static / "favicon.svg").write_text("<svg/>")
    (tmp_path / "secret.txt").write_text("SECRET-DO-NOT-LEAK")
    return static


@pytest.fixture
def spa_client(static_dir: Path) -> TestClient:
    """App wired like production: docs disabled, API routes, then the SPA."""
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/api/users/me")
    async def _me():
        return {"ok": True}

    @app.get("/health")
    async def _health():
        return {"status": "ok"}

    assert mount_spa(app, static_dir) is True
    return TestClient(app)


# ── El bug reportado: GET /login daba 404 ───────────────────

@pytest.mark.parametrize(
    "route", ["/login", "/dashboard", "/admin", "/onboarding-journey", "/path/abc-123"]
)
def test_client_routes_return_index(spa_client: TestClient, route: str):
    resp = spa_client.get(route)
    assert resp.status_code == 200
    assert "SPA INDEX" in resp.text


def test_real_files_are_served(spa_client: TestClient):
    assert spa_client.get("/favicon.svg").text == "<svg/>"
    assert spa_client.get("/assets/app.js").status_code == 200


# ── El catch-all no debe tragarse la API ni las docs ────────

def test_api_routes_still_win(spa_client: TestClient):
    resp = spa_client.get("/api/users/me")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert spa_client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize(
    "route", ["/api/does-not-exist", "/api/users/nope", "/docs", "/openapi.json"]
)
def test_unknown_reserved_routes_404(spa_client: TestClient, route: str):
    """Antes devolvían index.html con 200, escondiendo el error real."""
    resp = spa_client.get(route)
    assert resp.status_code == 404
    assert "SPA INDEX" not in resp.text


def test_reserved_prefixes_cover_every_registered_route():
    """Guard: cualquier ruta nueva de primer nivel tiene que sumarse al set."""
    for route in real_app.routes:
        path = getattr(route, "path", "")
        if isinstance(route, Mount) or path in ("/", "/{full_path:path}"):
            continue
        assert path.lstrip("/").split("/", 1)[0] in RESERVED_PREFIXES, path


# ── Path traversal ──────────────────────────────────────────

def test_encoded_traversal_does_not_escape_static(spa_client: TestClient):
    """`%2e%2e` esquiva la normalización del cliente; el server debe frenarlo."""
    resp = spa_client.get("/%2e%2e/secret.txt")
    assert resp.status_code == 200
    assert "SECRET-DO-NOT-LEAK" not in resp.text
    assert "SPA INDEX" in resp.text


def test_deep_traversal_cannot_read_system_files(spa_client: TestClient):
    resp = spa_client.get("/" + "%2e%2e/" * 20 + "etc/passwd")
    assert resp.status_code == 200
    assert "root:" not in resp.text
    assert "SPA INDEX" in resp.text


def test_resolve_spa_file(static_dir: Path):
    assert resolve_spa_file(static_dir, "favicon.svg") == (static_dir / "favicon.svg").resolve()
    assert resolve_spa_file(static_dir, "") is None            # el directorio no es archivo
    assert resolve_spa_file(static_dir, "login") is None        # ruta de React Router
    assert resolve_spa_file(static_dir, "../secret.txt") is None
    assert resolve_spa_file(static_dir, "../" * 20 + "etc/passwd") is None


# ── Sin build no se registra el catch-all, pero se avisa ────

def test_missing_build_logs_error(tmp_path: Path, caplog):
    app = FastAPI()
    assert mount_spa(app, tmp_path / "no-such-dir") is False
    assert "SPA catch-all NOT registered" in caplog.text
