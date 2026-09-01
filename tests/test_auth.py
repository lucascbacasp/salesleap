"""
Test del flujo completo de auth (demo mode):
  1. POST /api/auth/request-link  → crea usuario + devuelve JWT directo
  2. GET  /api/users/me           → perfil autenticado con JWT
  3. Casos de error: sin auth, JWT inválido
  4. Auto-asociación de empresa por dominio de email
"""
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User


async def test_full_auth_flow(client: AsyncClient, db: AsyncSession):
    """Happy path: request-link returns JWT → get user."""

    # ── 1. Request link (demo mode: returns JWT directly) ──
    resp = await client.post(
        "/api/auth/request-link",
        json={"email": "test@example.com", "full_name": "Test User"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["is_new_user"] is True
    assert data["onboarding_done"] is False

    jwt = data["access_token"]
    user_id = data["user_id"]

    # Verify user was created in DB
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one()
    assert user.full_name == "Test User"
    assert user.email_verified is True
    assert user.role.value == "learner"

    # ── 2. GET /users/me with JWT ──────────────────────────
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


async def test_returning_user(client: AsyncClient, db: AsyncSession):
    """A returning user should get onboarding_done reflecting their state."""

    # First login
    resp = await client.post(
        "/api/auth/request-link",
        json={"email": "returning@example.com", "full_name": "Return User"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_new_user"] is True

    # Second login (same email)
    resp = await client.post(
        "/api/auth/request-link",
        json={"email": "returning@example.com"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


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

    result = await db.execute(
        select(User).where(User.email == "vendedor@toyota.com.ar")
    )
    user = result.scalar_one()
    assert user.company_id is not None
    assert user.industry == "auto"


async def test_unknown_domain_is_rejected(client: AsyncClient, db: AsyncSession):
    """Un email cuyo dominio no matchea ninguna Company activa → 403, sin crear usuario."""
    resp = await client.post(
        "/api/auth/request-link",
        json={"email": "intruso@dominio-no-registrado.com"},
    )
    assert resp.status_code == 403

    result = await db.execute(
        select(User).where(User.email == "intruso@dominio-no-registrado.com")
    )
    assert result.scalar_one_or_none() is None


async def test_inactive_company_domain_is_rejected(client: AsyncClient, db: AsyncSession):
    """El dominio sólo habilita el alta si la empresa está activa."""
    await db.execute(
        text(
            "INSERT INTO companies (name, slug, email_domain, industry, is_active) "
            "VALUES ('Baja SA', 'baja-sa', 'baja.app', 'auto', false)"
        )
    )
    await db.commit()

    resp = await client.post(
        "/api/auth/request-link", json={"email": "alguien@baja.app"}
    )
    assert resp.status_code == 403


async def test_known_domain_auto_registers(client: AsyncClient, db: AsyncSession):
    """Un email nuevo de un dominio registrado se crea y queda ligado a la empresa."""
    await db.execute(
        text(
            "INSERT INTO companies (name, slug, email_domain, industry) "
            "VALUES ('Servagrop', 'servagrop', 'agro.app', 'alimentaria')"
        )
    )
    await db.commit()

    resp = await client.post(
        "/api/auth/request-link",
        json={"email": "nuevo@agro.app", "full_name": "Nuevo Operario"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    result = await db.execute(select(User).where(User.email == "nuevo@agro.app"))
    user = result.scalar_one()
    assert user.company_id is not None
    assert user.industry == "alimentaria"


async def test_email_lookup_is_case_insensitive(client: AsyncClient, db: AsyncSession):
    """"TEST@Example.com" es el mismo usuario que "test@example.com".

    El SELECT era case-sensitive: no encontraba la fila del usuario y caía en
    el alta automática, que para un dominio sin empresa termina en 403.
    """
    resp = await client.post(
        "/api/auth/request-link", json={"email": "  TEST@Example.com  "}
    )
    assert resp.status_code == 200

    result = await db.execute(
        select(func.count()).select_from(User).where(User.email == "test@example.com")
    )
    assert result.scalar_one() == 1

    # Ningún usuario quedó guardado con mayúsculas (no se creó un duplicado)
    result = await db.execute(
        select(func.count()).select_from(User).where(User.email != func.lower(User.email))
    )
    assert result.scalar_one() == 0


async def test_mixed_case_email_on_registered_domain_does_not_duplicate(
    client: AsyncClient, db: AsyncSession
):
    """Mismo bug, peor síntoma: con dominio registrado el alta automática
    chocaba contra el UNIQUE de users.email y devolvía 500."""
    await db.execute(
        text(
            "INSERT INTO companies (name, slug, email_domain, industry) "
            "VALUES ('Servagrop', 'servagrop', 'agro.app', 'alimentaria')"
        )
    )
    await db.commit()

    first = await client.post(
        "/api/auth/request-link",
        json={"email": "javier@agro.app", "full_name": "Javier"},
    )
    assert first.status_code == 200

    again = await client.post(
        "/api/auth/request-link", json={"email": "Javier@Agro.app"}
    )
    assert again.status_code == 200
    assert again.json()["user_id"] == first.json()["user_id"]

    result = await db.execute(
        select(func.count()).select_from(User).where(User.email == "javier@agro.app")
    )
    assert result.scalar_one() == 1
