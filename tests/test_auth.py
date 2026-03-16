"""
Test del flujo completo de auth:
  1. POST /api/auth/request-link  → crea usuario + magic token
  2. POST /api/auth/verify        → verifica token, devuelve JWT
  3. GET  /api/users/me           → perfil autenticado con JWT
  4. Casos de error: token reusado, token inválido, sin auth
  5. Auto-asociación de empresa por dominio de email
"""
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AuthToken, User


async def test_full_auth_flow(client: AsyncClient, db: AsyncSession):
    """Happy path: request-link → verify → get user."""

    # ── 1. Request magic link ────────────────────────────────
    resp = await client.post(
        "/api/auth/request-link",
        json={"email": "test@example.com", "full_name": "Test User"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Magic link enviado. Revisá tu email."

    # Verify user was created in DB
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one()
    assert user.full_name == "Test User"
    assert user.email_verified is False
    assert user.role.value == "learner"

    # Get the token from DB
    token_result = await db.execute(
        select(AuthToken).where(AuthToken.user_id == user.id)
    )
    auth_token = token_result.scalar_one()
    magic_token = auth_token.token

    # ── 2. Verify token → get JWT ────────────────────────────
    resp = await client.post(
        "/api/auth/verify",
        json={"token": magic_token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["is_new_user"] is True
    assert data["onboarding_done"] is False
    assert "access_token" in data

    jwt = data["access_token"]
    user_id = data["user_id"]

    # ── 3. GET /users/me with JWT ────────────────────────────
    resp = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    assert resp.status_code == 200
    profile = resp.json()
    assert profile["id"] == user_id
    assert profile["email"] == "test@example.com"
    assert profile["full_name"] == "Test User"
    assert profile["total_xp"] == 0
    assert profile["level"] == 1
    assert profile["experience_level"] == "beginner"


async def test_verify_reused_token(client: AsyncClient, db: AsyncSession):
    """Using the same magic token twice should fail."""

    # Create user + token
    resp = await client.post(
        "/api/auth/request-link",
        json={"email": "reuse@example.com", "full_name": "Reuse Test"},
    )
    assert resp.status_code == 200

    result = await db.execute(select(User).where(User.email == "reuse@example.com"))
    user = result.scalar_one()
    token_result = await db.execute(
        select(AuthToken).where(AuthToken.user_id == user.id)
    )
    magic_token = token_result.scalar_one().token

    # First verify — should succeed
    resp = await client.post("/api/auth/verify", json={"token": magic_token})
    assert resp.status_code == 200

    # Second verify — should fail
    resp = await client.post("/api/auth/verify", json={"token": magic_token})
    assert resp.status_code == 400
    assert "ya utilizado" in resp.json()["detail"]


async def test_verify_invalid_token(client: AsyncClient):
    """A random token should be rejected."""
    resp = await client.post(
        "/api/auth/verify",
        json={"token": "totally-fake-token-12345"},
    )
    assert resp.status_code == 400


async def test_users_me_without_auth(client: AsyncClient):
    """GET /users/me without a token should return 403."""
    resp = await client.get("/api/users/me")
    assert resp.status_code == 403


async def test_users_me_with_bad_jwt(client: AsyncClient):
    """GET /users/me with an invalid JWT should return 401."""
    resp = await client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert resp.status_code == 401


async def test_company_auto_association(client: AsyncClient, db: AsyncSession):
    """User with matching email domain should be auto-associated to company."""

    # Create a company with email_domain
    await db.execute(
        text(
            "INSERT INTO companies (name, slug, email_domain, industry) "
            "VALUES ('Toyota CBA', 'toyota-cba', 'toyota.com.ar', 'auto')"
        )
    )
    await db.commit()

    # Register user with matching domain
    resp = await client.post(
        "/api/auth/request-link",
        json={"email": "vendedor@toyota.com.ar", "full_name": "Vendedor Toyota"},
    )
    assert resp.status_code == 200

    # Need a fresh session to see committed data from the endpoint
    result = await db.execute(
        select(User).where(User.email == "vendedor@toyota.com.ar")
    )
    user = result.scalar_one()
    assert user.company_id is not None
    assert user.industry == "auto"
