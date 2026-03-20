"""
Shared test fixtures — isolated test DB.

Each endpoint call gets its own session+connection (NullPool).
Tables are truncated between tests via a raw asyncpg connection.
"""
from typing import AsyncGenerator

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import get_session
from app.main import app

TEST_DATABASE_URL = (
    "postgresql+asyncpg://salesleap:salesleap@localhost:5432/salesleap_test"
)
RAW_DSN = "postgresql://salesleap:salesleap@localhost:5432/salesleap_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

_TRUNCATE_SQL = (
    "TRUNCATE quiz_answers, quiz_sessions, user_lesson_progress, "
    "user_path_progress, user_badges, daily_streaks, onboarding_results, "
    "notifications, auth_tokens, lessons, modules, learning_paths, "
    "company_documents, users, companies RESTART IDENTITY CASCADE"
)


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    """Truncate all app tables after each test using a raw asyncpg connection."""
    yield
    conn = await asyncpg.connect(RAW_DSN)
    try:
        await conn.execute(_TRUNCATE_SQL)
    finally:
        await conn.close()


# Users that the auth/journey tests need pre-seeded (auth now requires existing users)
_TEST_USERS = [
    ("test@example.com",       "Test User",       "learner"),
    ("returning@example.com",  "Return User",     "learner"),
    ("journey@test.com",       "Journey User",    "learner"),
    ("vendedor@toyota.com.ar", "Vendedor Toyota", "learner"),
]


@pytest_asyncio.fixture(autouse=True)
async def _seed_test_users(_clean_tables):
    """Pre-seed static test users so auth (403 restriction) doesn't block tests.

    Depends on _clean_tables so it always runs AFTER the previous test's
    truncate and BEFORE the current test's setup.
    """
    conn = await asyncpg.connect(RAW_DSN)
    try:
        for email, full_name, role in _TEST_USERS:
            await conn.execute(
                """
                INSERT INTO users
                    (email, full_name, role, is_active, email_verified, onboarding_done)
                VALUES ($1, $2, $3::user_role, true, false, false)
                ON CONFLICT (email) DO NOTHING
                """,
                email, full_name, role,
            )
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Standalone session for direct DB assertions in tests."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient that routes endpoint DB calls to the test database."""

    async def _override_get_session():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
