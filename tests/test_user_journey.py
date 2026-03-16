"""
E2E test: full user journey
  1. Register + verify (auth)
  2. Onboarding quiz → Claude suggests level + paths (mocked)
  3. Browse suggested paths
  4. Complete a lesson → earn XP + badges
  5. Check leaderboard + badges
"""
from unittest.mock import AsyncMock, patch

import asyncpg
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

RAW_DSN = "postgresql://salesleap:salesleap@localhost:5432/salesleap_test"

MOCK_ONBOARDING_RESPONSE = {
    "level": "intermediate",
    "strengths": ["Rapport con clientes", "Conocimiento de producto"],
    "gaps": ["Manejo de objeciones", "Técnicas de cierre"],
    "priority_topics": ["Objeciones", "Cierre", "Follow-up"],
    "explanation": "Tenés buena base pero necesitás mejorar en cierre de ventas.",
    "quick_win_tip": "Antes de cada reunión, prepará 3 respuestas a objeciones comunes.",
}


async def _seed_data(db: AsyncSession):
    """Insert badges, a learning path, module, and lessons for testing."""
    # Badges (same as schema.sql)
    await db.execute(text("""
        INSERT INTO badges (name, description, icon, category, criteria, xp_bonus, rarity) VALUES
        ('Primer paso',     'Completaste tu primera lección',     '🚀', 'onboarding',  '{"lessons_completed": 1}',     50,  'common'),
        ('Bienvenido',      'Completaste el quiz de nivelación',  '👋', 'onboarding',  '{"onboarding_done": true}',    100, 'common'),
        ('Perfeccionista',  'Obtuviste 100%% en un quiz',         '🎯', 'score',       '{"quiz_score": 100}',          100, 'rare'),
        ('Veloz',           'Lección en menos de 3 min',          '⚡', 'speed',       '{"lesson_under_seconds": 180}', 50, 'rare'),
        ('En racha x3',    '3 días seguidos de actividad',        '🔥', 'streak',      '{"streak_days": 3}',           75,  'common')
        ON CONFLICT DO NOTHING
    """))

    # Learning path + module + lessons
    await db.execute(text("""
        INSERT INTO learning_paths (id, title, description, industry, level, is_published)
        VALUES ('a0000000-0000-0000-0000-000000000001', 'Ventas Automotriz Intermedio',
                'Técnicas avanzadas para vendedores de autos', 'auto', 'intermediate', true)
    """))
    await db.execute(text("""
        INSERT INTO modules (id, path_id, title, order_index, xp_reward, is_published)
        VALUES ('b0000000-0000-0000-0000-000000000001',
                'a0000000-0000-0000-0000-000000000001',
                'Manejo de objeciones', 0, 50, true)
    """))
    await db.execute(text("""
        INSERT INTO lessons (id, module_id, title, lesson_type, content, order_index, xp_reward, estimated_minutes, is_published)
        VALUES
        ('c0000000-0000-0000-0000-000000000001',
         'b0000000-0000-0000-0000-000000000001',
         'Tipos de objeciones', 'theory',
         '{"text": "Las objeciones más comunes son precio, tiempo y confianza."}',
         0, 25, 5, true),
        ('c0000000-0000-0000-0000-000000000002',
         'b0000000-0000-0000-0000-000000000001',
         'Quiz: objeciones', 'quiz',
         '{"questions": [{"question": "¿Cuál es la objeción más común?", "options": ["Precio", "Color", "Marca"], "correct": 0}]}',
         1, 30, 3, true)
    """))
    await db.commit()


async def _register_and_login(client: AsyncClient) -> str:
    """Register a user, grab the token from DB, verify it, return JWT."""
    await client.post(
        "/api/auth/request-link",
        json={"email": "journey@test.com", "full_name": "Journey User"},
    )
    # Grab token directly from DB
    conn = await asyncpg.connect(RAW_DSN)
    try:
        row = await conn.fetchrow(
            "SELECT token FROM auth_tokens ORDER BY created_at DESC LIMIT 1"
        )
    finally:
        await conn.close()

    resp = await client.post("/api/auth/verify", json={"token": row["token"]})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_full_user_journey(client: AsyncClient, db: AsyncSession):
    """Complete user journey: auth → onboarding → lesson → XP + badges."""

    # ── Seed test data ───────────────────────────────────────
    await _seed_data(db)

    # ── 1. Auth ──────────────────────────────────────────────
    jwt = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {jwt}"}

    # Confirm user starts clean
    resp = await client.get("/api/users/me", headers=headers)
    assert resp.status_code == 200
    me = resp.json()
    assert me["total_xp"] == 0
    assert me["onboarding_done"] is False

    # ── 2. Onboarding quiz (Claude mocked) ───────────────────
    with patch(
        "app.routers.onboarding.ai_coach.generate_onboarding_suggestion",
        new_callable=AsyncMock,
        return_value=MOCK_ONBOARDING_RESPONSE,
    ):
        resp = await client.post(
            "/api/onboarding/quiz",
            headers=headers,
            json={
                "industry": "auto",
                "experience_years": 3,
                "answers": [
                    {"question": "¿Cómo manejás una objeción de precio?",
                     "answer": "Muestro el valor antes de hablar de precio"},
                    {"question": "¿Qué hacés cuando el cliente dice 'lo pienso'?",
                     "answer": "Pregunto qué lo haría decidir hoy"},
                ],
            },
        )
    assert resp.status_code == 200
    onboarding = resp.json()
    assert onboarding["level"] == "intermediate"
    assert len(onboarding["strengths"]) == 2
    assert len(onboarding["gaps"]) == 2
    assert "quick_win_tip" in onboarding
    # Should suggest the path we seeded
    assert len(onboarding["suggested_path_ids"]) == 1

    # Verify user profile was updated
    resp = await client.get("/api/users/me", headers=headers)
    me = resp.json()
    assert me["onboarding_done"] is True
    assert me["experience_level"] == "intermediate"
    assert me["industry"] == "auto"

    # ── 3. Browse paths ──────────────────────────────────────
    resp = await client.get("/api/paths/?industry=auto&level=intermediate", headers=headers)
    assert resp.status_code == 200
    paths = resp.json()
    assert len(paths) >= 1
    assert paths[0]["title"] == "Ventas Automotriz Intermedio"

    # ── 4. Get module detail ─────────────────────────────────
    resp = await client.get(
        "/api/modules/b0000000-0000-0000-0000-000000000001", headers=headers
    )
    assert resp.status_code == 200
    module = resp.json()
    assert module["title"] == "Manejo de objeciones"
    assert len(module["lessons"]) == 2

    # ── 5. Get lesson detail ─────────────────────────────────
    lesson_id = "c0000000-0000-0000-0000-000000000001"
    resp = await client.get(f"/api/lessons/{lesson_id}", headers=headers)
    assert resp.status_code == 200
    lesson = resp.json()
    assert lesson["title"] == "Tipos de objeciones"

    # ── 6. Complete first lesson → XP + badges ───────────────
    resp = await client.post(
        f"/api/lessons/{lesson_id}/complete",
        headers=headers,
        json={"score": 100, "time_spent_sec": 120},
    )
    assert resp.status_code == 200
    result = resp.json()

    # XP: 25 (lesson) + badge bonuses
    assert result["xp_earned"] == 25
    assert result["total_xp"] > 25  # includes badge XP bonuses
    assert result["streak_current"] == 1

    # Should earn: "Primer paso" (1 lesson), "Bienvenido" (onboarding done),
    # "Perfeccionista" (score 100), "Veloz" (120s < 180s)
    badges = result["badges_earned"]
    assert "Primer paso" in badges
    assert "Bienvenido" in badges
    assert "Perfeccionista" in badges
    assert "Veloz" in badges

    # ── 7. Complete second lesson (no duplicate badges) ──────
    lesson2_id = "c0000000-0000-0000-0000-000000000002"
    resp = await client.post(
        f"/api/lessons/{lesson2_id}/complete",
        headers=headers,
        json={"score": 80, "time_spent_sec": 200},
    )
    assert resp.status_code == 200
    result2 = resp.json()
    # Should NOT re-earn the same badges
    assert "Primer paso" not in result2["badges_earned"]
    assert "Bienvenido" not in result2["badges_earned"]
    # XP should keep accumulating
    assert result2["total_xp"] > result["total_xp"]

    # ── 8. Try completing same lesson again → should fail ────
    resp = await client.post(
        f"/api/lessons/{lesson_id}/complete",
        headers=headers,
        json={"score": 100, "time_spent_sec": 60},
    )
    assert resp.status_code == 400
    assert "ya completada" in resp.json()["detail"]

    # ── 9. Check leaderboard ─────────────────────────────────
    resp = await client.get("/api/gamification/leaderboard", headers=headers)
    assert resp.status_code == 200
    leaderboard = resp.json()
    assert len(leaderboard) >= 1
    assert leaderboard[0]["full_name"] == "Journey User"
    assert leaderboard[0]["rank"] == 1

    # ── 10. Check earned badges ──────────────────────────────
    resp = await client.get("/api/gamification/badges", headers=headers)
    assert resp.status_code == 200
    my_badges = resp.json()
    badge_names = [b["name"] for b in my_badges]
    assert "Primer paso" in badge_names
    assert "Bienvenido" in badge_names
    assert "Perfeccionista" in badge_names
    assert "Veloz" in badge_names

    # ── 11. Check progress ───────────────────────────────────
    resp = await client.get("/api/progress/me", headers=headers)
    assert resp.status_code == 200
    progress = resp.json()
    assert progress["total_lessons_completed"] == 2
    assert progress["total_xp"] > 0
    assert progress["streak"] == 1
