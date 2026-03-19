"""
SalesLeap — FastAPI main application
"""
import logging
import copy as _copy
import random
from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select, text

from app.core.config import settings
from app.core.database import async_session, engine, init_db
from app.routers import auth, users, companies, paths, modules, lessons, progress, gamification, ai_coach, onboarding

logger = logging.getLogger(__name__)


async def _auto_seed():
    """
    Runs automatically on every startup.
    Each block is fully idempotent — safe to run on every deploy.
    Order:
      1. schema.sql  (tables)
      2. base content (companies / paths / modules / lessons)
      3. seed-demo   (admin.app  — SalesLeap Demo + 3 salespeople)
      4. seed-auto   (auto.app   — Auto Demo + 4 salespeople)
      5. seed-industria (industria.app — onboarding path)
    """
    from pathlib import Path as _Path
    schema_path = _Path(__file__).parent.parent / "schema.sql"

    # ── 1. schema.sql ──────────────────────────────────────────
    try:
        schema_sql = schema_path.read_text()
        async with engine.begin() as conn:
            raw = await conn.get_raw_connection()
            await raw.driver_connection.execute(schema_sql)
        logger.info("startup: schema.sql applied")
    except Exception as e:
        if "already exists" not in str(e):
            logger.warning(f"startup: schema.sql — {e}")

    async with async_session() as db:
        # ── 2. base content ────────────────────────────────────
        try:
            from seed import COMPANIES, AUTO_PATH, INMOB_PATH, AUTO_MODULES, INMOB_MODULES
            from app.models.models import Company, LearningPath, Module, Lesson

            r = await db.execute(text("SELECT COUNT(*) FROM learning_paths"))
            if not r.scalar():
                for c in COMPANIES:
                    db.add(Company(**c))
                await db.flush()
                for path_data in [AUTO_PATH, INMOB_PATH]:
                    db.add(LearningPath(**path_data))
                await db.flush()
                for mods in [_copy.deepcopy(AUTO_MODULES), _copy.deepcopy(INMOB_MODULES)]:
                    for mod_data in mods:
                        lessons_data = mod_data.pop("lessons")
                        mod = Module(**mod_data)
                        db.add(mod)
                        await db.flush()
                        for ld in lessons_data:
                            db.add(Lesson(module_id=mod.id, is_published=True, **ld))
                await db.commit()
                logger.info("startup: base content seeded")
            else:
                logger.info("startup: base content already exists")
        except Exception as e:
            logger.error(f"startup: base content error — {e}")
            await db.rollback()

    # ── 3. seed-demo (admin.app) ───────────────────────────────
    try:
        from seed import COMPANIES as _C
        from app.models.models import (
            Company, User, UserRole, UserLessonProgress, UserPathProgress,
            DailyStreak, Lesson, Module as _Module, ProgressStatus,
        )
        import uuid as _uuid

        DEMO_COMPANY_ID = _uuid.UUID("a0000000-0000-0000-0000-000000000099")
        AUTO_PATH_ID    = _uuid.UUID("b0000000-0000-0000-0000-000000000001")

        async with async_session() as db:
            co = (await db.execute(select(Company).where(Company.email_domain == "admin.app"))).scalar_one_or_none()
            if not co:
                from app.models.models import Company as _Co
                db.add(_Co(
                    id=DEMO_COMPANY_ID, name="SalesLeap Demo", slug="salesleap-demo",
                    email_domain="admin.app", industry="auto", plan="pro",
                    is_active=True, settings={},
                ))
                await db.flush()

            DEMO_USERS = [
                {"email": "lucas@admin.app",  "full_name": "Lucas García",    "role": UserRole.learner,
                 "lessons_total": 8, "lessons_this_week": 5, "streak": 4, "xp_base": 40},
                {"email": "andres@admin.app", "full_name": "Andrés Martínez", "role": UserRole.learner,
                 "lessons_total": 5, "lessons_this_week": 2, "streak": 1, "xp_base": 35},
                {"email": "kun@admin.app",    "full_name": "Sergio Agüero",   "role": UserRole.learner,
                 "lessons_total": 2, "lessons_this_week": 0, "streak": 0, "xp_base": 30},
                {"email": "admin@admin.app",  "full_name": "Admin",           "role": UserRole.admin,
                 "lessons_total": 0, "lessons_this_week": 0, "streak": 0, "xp_base": 0},
            ]

            lessons_res = await db.execute(
                select(Lesson).join(_Module, Lesson.module_id == _Module.id)
                .where(_Module.path_id == AUTO_PATH_ID, Lesson.is_published.is_(True))
                .order_by(_Module.order_index, Lesson.order_index)
            )
            all_lessons = lessons_res.scalars().all()

            today = date.today()
            monday = today - timedelta(days=today.weekday())

            for u_data in DEMO_USERS:
                u = (await db.execute(select(User).where(User.email == u_data["email"]))).scalar_one_or_none()
                if not u:
                    u = User(
                        email=u_data["email"], full_name=u_data["full_name"],
                        role=u_data["role"], company_id=DEMO_COMPANY_ID,
                        industry="auto", experience_level="beginner",
                        email_verified=True, onboarding_done=True, is_active=True,
                    )
                    db.add(u)
                    await db.flush()
                else:
                    u.company_id = DEMO_COMPANY_ID
                    u.onboarding_done = True

                if u_data["role"] == UserRole.learner and all_lessons and u_data["lessons_total"] > 0:
                    await db.execute(text("DELETE FROM user_lesson_progress WHERE user_id = :uid"), {"uid": u.id})
                    await db.execute(text("DELETE FROM user_path_progress WHERE user_id = :uid"), {"uid": u.id})
                    await db.execute(text("DELETE FROM daily_streaks WHERE user_id = :uid"), {"uid": u.id})

                    total = min(u_data["lessons_total"], len(all_lessons))
                    this_week = u_data["lessons_this_week"]
                    older = total - this_week
                    total_xp = 0

                    for i in range(total):
                        xp = random.randint(u_data["xp_base"] - 10, u_data["xp_base"] + 15)
                        total_xp += xp
                        if i < older:
                            comp_at = datetime.now(timezone.utc) - timedelta(days=random.randint(7, 14), hours=random.randint(1, 12))
                        else:
                            day_off = random.randint(0, min((today - monday).days, 6))
                            comp_at = datetime(monday.year, monday.month, monday.day, random.randint(8, 20), random.randint(0, 59), tzinfo=timezone.utc) + timedelta(days=day_off)
                        db.add(UserLessonProgress(
                            user_id=u.id, lesson_id=all_lessons[i].id,
                            status=ProgressStatus.completed,
                            score=random.randint(70, 100), attempts=random.randint(1, 3),
                            time_spent_sec=random.randint(120, 600), completed_at=comp_at,
                        ))

                    db.add(UserPathProgress(
                        user_id=u.id, path_id=AUTO_PATH_ID,
                        status=ProgressStatus.in_progress,
                        started_at=datetime.now(timezone.utc) - timedelta(days=14),
                        xp_earned=total_xp,
                    ))
                    for day_off in range(min(this_week, (today - monday).days + 1)):
                        db.add(DailyStreak(
                            user_id=u.id, activity_date=monday + timedelta(days=day_off),
                            xp_earned=random.randint(30, 50), lessons_done=random.randint(1, 3),
                        ))
                    u.total_xp = total_xp
                    u.level = max(1, total_xp // 500 + 1)
                    u.streak_current = u_data["streak"]
                    u.streak_max = max(u_data["streak"], 5)
                    u.last_activity_at = (
                        datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 4))
                        if u_data["streak"] > 0
                        else datetime.now(timezone.utc) - timedelta(days=random.randint(3, 7))
                    )

            await db.commit()
            logger.info("startup: seed-demo (admin.app) applied")
    except Exception as e:
        logger.error(f"startup: seed-demo error — {e}")

    # ── 4. seed-auto (auto.app) ────────────────────────────────
    try:
        from seed import AUTO_APP_COMPANY, AUTO_APP_USERS, AUTO_APP_SALESPEOPLE
        from app.models.models import (
            Company, LearningPath, User, UserRole, UserPathProgress,
            UserLessonProgress, UserBadge, Badge, DailyStreak,
            Module as _Module2, Lesson as _Lesson2, ProgressStatus,
        )
        import uuid as _uuid2

        AUTO_PATH_ID2 = _uuid2.UUID("b0000000-0000-0000-0000-000000000001")

        async with async_session() as db:
            if not (await db.execute(select(Company).where(Company.email_domain == "auto.app"))).scalar_one_or_none():
                db.add(Company(**AUTO_APP_COMPANY))
                await db.flush()

            path_ok = (await db.execute(select(LearningPath).where(LearningPath.id == AUTO_PATH_ID2))).scalar_one_or_none()
            if not path_ok:
                logger.warning("startup: auto path not found, skipping seed-auto")
            else:
                # base users (Pablo + Admin)
                for u_data in AUTO_APP_USERS:
                    u = (await db.execute(select(User).where(User.email == u_data["email"]))).scalar_one_or_none()
                    if not u:
                        u = User(
                            email=u_data["email"], full_name=u_data["full_name"],
                            role=UserRole(u_data["role"]), company_id=AUTO_APP_COMPANY["id"],
                            industry="auto", experience_level="beginner",
                            email_verified=True, onboarding_done=u_data["onboarding_done"], is_active=True,
                        )
                        db.add(u)
                        await db.flush()
                    else:
                        u.company_id = AUTO_APP_COMPANY["id"]
                        u.email_verified = True
                        u.role = UserRole(u_data["role"])
                        u.onboarding_done = u_data["onboarding_done"]

                    if u_data["role"] == "learner":
                        if not (await db.execute(select(UserPathProgress).where(
                            UserPathProgress.user_id == u.id,
                            UserPathProgress.path_id == AUTO_PATH_ID2,
                        ))).scalar_one_or_none():
                            db.add(UserPathProgress(
                                user_id=u.id, path_id=AUTO_PATH_ID2,
                                status=ProgressStatus.in_progress,
                                started_at=datetime.now(timezone.utc),
                            ))
                await db.flush()

                # salespeople with rich data
                lessons_res2 = await db.execute(
                    select(_Lesson2).join(_Module2, _Lesson2.module_id == _Module2.id)
                    .where(_Module2.path_id == AUTO_PATH_ID2, _Lesson2.is_published.is_(True))
                    .order_by(_Module2.order_index, _Lesson2.order_index)
                )
                all_lessons2 = lessons_res2.scalars().all()
                badge_map = {b.name: b for b in (await db.execute(select(Badge))).scalars().all()}
                today2 = date.today()
                monday2 = today2 - timedelta(days=today2.weekday())

                for sp in AUTO_APP_SALESPEOPLE:
                    u = (await db.execute(select(User).where(User.email == sp["email"]))).scalar_one_or_none()
                    if not u:
                        u = User(
                            email=sp["email"], full_name=sp["full_name"],
                            role=UserRole.learner, company_id=AUTO_APP_COMPANY["id"],
                            industry="auto", experience_level="beginner",
                            email_verified=True, onboarding_done=True, is_active=True,
                        )
                        db.add(u)
                        await db.flush()
                    else:
                        u.company_id = AUTO_APP_COMPANY["id"]
                        u.onboarding_done = True

                    await db.flush()
                    await db.execute(text("DELETE FROM user_lesson_progress WHERE user_id = :uid"), {"uid": u.id})
                    await db.execute(text("DELETE FROM user_path_progress WHERE user_id = :uid"), {"uid": u.id})
                    await db.execute(text("DELETE FROM daily_streaks WHERE user_id = :uid"), {"uid": u.id})
                    await db.execute(text("DELETE FROM user_badges WHERE user_id = :uid"), {"uid": u.id})

                    total = min(sp["lessons_total"], len(all_lessons2))
                    this_week = sp["lessons_this_week"]
                    older = total - this_week
                    total_xp = 0

                    for i in range(total):
                        xp = random.randint(sp["xp_base"] - 8, sp["xp_base"] + 12)
                        total_xp += xp
                        if i < older:
                            comp_at = datetime.now(timezone.utc) - timedelta(days=random.randint(7, 21), hours=random.randint(1, 10))
                        else:
                            day_off = min(i - older, (today2 - monday2).days)
                            comp_at = datetime(monday2.year, monday2.month, monday2.day, random.randint(8, 20), random.randint(0, 59), tzinfo=timezone.utc) + timedelta(days=day_off)
                        db.add(UserLessonProgress(
                            user_id=u.id, lesson_id=all_lessons2[i].id,
                            status=ProgressStatus.completed,
                            score=random.randint(72, 100), attempts=random.randint(1, 3),
                            time_spent_sec=random.randint(90, 540), completed_at=comp_at,
                        ))

                    db.add(UserPathProgress(
                        user_id=u.id, path_id=AUTO_PATH_ID2,
                        status=ProgressStatus.in_progress,
                        started_at=datetime.now(timezone.utc) - timedelta(days=21),
                        xp_earned=total_xp,
                    ))
                    for day_off in range(min(this_week, (today2 - monday2).days + 1)):
                        db.add(DailyStreak(
                            user_id=u.id, activity_date=monday2 + timedelta(days=day_off),
                            xp_earned=random.randint(35, 55), lessons_done=random.randint(1, 3),
                        ))
                    for badge_name in sp["badge_names"]:
                        badge = badge_map.get(badge_name)
                        if badge:
                            db.add(UserBadge(
                                user_id=u.id, badge_id=badge.id,
                                earned_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 14)),
                                context={},
                            ))
                    u.total_xp = total_xp
                    u.level = max(1, total_xp // 500 + 1)
                    u.streak_current = sp["streak"]
                    u.streak_max = sp["streak_max"]
                    u.last_activity_at = (
                        datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 6))
                        if sp["streak"] > 0
                        else datetime.now(timezone.utc) - timedelta(days=random.randint(4, 10))
                    )

            await db.commit()
            logger.info("startup: seed-auto (auto.app) applied")
    except Exception as e:
        logger.error(f"startup: seed-auto error — {e}")

    # ── 5. seed-industria (industria.app) ──────────────────────
    try:
        from seed import INDUSTRIA_COMPANY, ONBOARDING_PATH, ONBOARDING_MODULES, INDUSTRIA_USERS
        from app.models.models import (
            Company, LearningPath, Module as _ModI, Lesson as _LesI,
            User, UserRole, UserPathProgress, ProgressStatus,
        )

        async with async_session() as db:
            if not (await db.execute(select(Company).where(Company.email_domain == "industria.app"))).scalar_one_or_none():
                db.add(Company(**INDUSTRIA_COMPANY))
                await db.flush()

            if not (await db.execute(select(LearningPath).where(LearningPath.id == ONBOARDING_PATH["id"]))).scalar_one_or_none():
                db.add(LearningPath(**ONBOARDING_PATH))
                await db.flush()

            existing_mods = (await db.execute(select(_ModI).where(_ModI.path_id == ONBOARDING_PATH["id"]))).scalars().all()
            if not existing_mods:
                for mod_data in _copy.deepcopy(ONBOARDING_MODULES):
                    lessons_data = mod_data.pop("lessons")
                    mod = _ModI(**mod_data)
                    db.add(mod)
                    await db.flush()
                    for ld in lessons_data:
                        db.add(_LesI(module_id=mod.id, is_published=True, **ld))

            for u_data in INDUSTRIA_USERS:
                u = (await db.execute(select(User).where(User.email == u_data["email"]))).scalar_one_or_none()
                if not u:
                    u = User(
                        email=u_data["email"], full_name=u_data["full_name"],
                        role=UserRole(u_data["role"]), company_id=INDUSTRIA_COMPANY["id"],
                        industry="manufactura", experience_level="beginner",
                        email_verified=True, onboarding_done=u_data["onboarding_done"], is_active=True,
                    )
                    db.add(u)
                    await db.flush()
                else:
                    u.company_id = INDUSTRIA_COMPANY["id"]
                    u.email_verified = True

                if u_data["role"] == "learner":
                    if not (await db.execute(select(UserPathProgress).where(
                        UserPathProgress.user_id == u.id,
                        UserPathProgress.path_id == ONBOARDING_PATH["id"],
                    ))).scalar_one_or_none():
                        db.add(UserPathProgress(
                            user_id=u.id, path_id=ONBOARDING_PATH["id"],
                            status=ProgressStatus.in_progress,
                            started_at=datetime.now(timezone.utc),
                        ))

            # onboarding badges
            NEW_BADGES = [
                ("Orientado",    "Completaste el mapa del área en tu primer día",   "🗺️", "onboarding", '{"onboarding_lesson": "El mapa del área"}',              75,  "common"),
                ("En acción",    "Completaste tu primer ticket real",                "⚙️", "onboarding", '{"onboarding_lesson": "Primer ticket real"}',            100, "rare"),
                ("Especialista", "Certificado como Operador Junior",                 "🎓", "onboarding", '{"onboarding_lesson": "Certificación: Operador Junior"}', 150, "epic"),
            ]
            for name, desc, icon, cat, criteria_json, xp_bonus, rarity in NEW_BADGES:
                if not (await db.execute(text("SELECT 1 FROM badges WHERE name = :n"), {"n": name})).scalar_one_or_none():
                    await db.execute(
                        text("INSERT INTO badges (name, description, icon, category, criteria, xp_bonus, rarity) VALUES (:name, :desc, :icon, :cat, CAST(:criteria AS jsonb), :xp, :rarity)"),
                        {"name": name, "desc": desc, "icon": icon, "cat": cat, "criteria": criteria_json, "xp": xp_bonus, "rarity": rarity},
                    )

            await db.commit()
            logger.info("startup: seed-industria (industria.app) applied")
    except Exception as e:
        logger.error(f"startup: seed-industria error — {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _auto_seed()
    yield


app = FastAPI(
    title="SalesLeap API",
    version="1.0.0",
    description="Plataforma de capacitación gamificada para vendedores",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(onboarding.router,    prefix="/api/onboarding",    tags=["onboarding"])
app.include_router(users.router,         prefix="/api/users",         tags=["users"])
app.include_router(companies.router,     prefix="/api/companies",     tags=["companies"])
app.include_router(paths.router,         prefix="/api/paths",         tags=["learning-paths"])
app.include_router(modules.router,       prefix="/api/modules",       tags=["modules"])
app.include_router(lessons.router,       prefix="/api/lessons",       tags=["lessons"])
app.include_router(progress.router,      prefix="/api/progress",      tags=["progress"])
app.include_router(gamification.router,  prefix="/api/gamification",  tags=["gamification"])
app.include_router(ai_coach.router,      prefix="/api/coach",         tags=["ai-coach"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "salesleap-api"}


@app.post("/api/admin/init-db")
async def admin_init_db(x_admin_key: str = Header(...)):
    """Run schema.sql + seed data. Protected by SECRET_KEY."""
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    schema_path = Path(__file__).parent.parent / "schema.sql"
    if not schema_path.exists():
        raise HTTPException(status_code=500, detail="schema.sql not found")

    results = []

    # Run schema.sql
    try:
        schema_sql = schema_path.read_text()
        async with engine.begin() as conn:
            # Get the underlying asyncpg connection which supports multi-statement execute
            raw_conn = await conn.get_raw_connection()
            await raw_conn.driver_connection.execute(schema_sql)
        results.append("schema.sql executed successfully")
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            results.append("schema.sql: tables already exist (OK)")
        else:
            results.append(f"schema.sql error: {error_msg}")

    # Run seed data
    try:
        from seed import COMPANIES, AUTO_PATH, INMOB_PATH, AUTO_MODULES, INMOB_MODULES
        import copy
        from app.models.models import Company, LearningPath, Module, Lesson

        async with async_session() as db:
            # Check if already seeded
            r = await db.execute(text("SELECT COUNT(*) FROM learning_paths"))
            count = r.scalar()
            if count and count > 0:
                results.append(f"seed: already has {count} paths, skipping")
            else:
                for c in COMPANIES:
                    db.add(Company(**c))
                await db.flush()

                for path_data in [AUTO_PATH, INMOB_PATH]:
                    db.add(LearningPath(**path_data))
                await db.flush()

                for modules_data in [copy.deepcopy(AUTO_MODULES), copy.deepcopy(INMOB_MODULES)]:
                    for mod_data in modules_data:
                        lessons_data = mod_data.pop("lessons")
                        module = Module(**mod_data)
                        db.add(module)
                        await db.flush()
                        for lesson_data in lessons_data:
                            db.add(Lesson(module_id=module.id, is_published=True, **lesson_data))

                await db.commit()
                results.append("seed: 2 companies, 2 paths, 6 modules, 24 lessons created")
    except Exception as e:
        results.append(f"seed error: {str(e)}")

    return {"results": results}


@app.post("/api/admin/seed-demo")
async def admin_seed_demo(x_admin_key: str = Header(...)):
    """Create demo company + salespeople with fake progress for admin panel demo."""
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    import uuid
    import random
    from datetime import datetime, date, timedelta, timezone
    from app.models.models import (
        Company, User, UserRole, UserLessonProgress, UserPathProgress,
        DailyStreak, Lesson, Module, ProgressStatus,
    )
    from sqlalchemy import select, func

    results = []

    async with async_session() as db:
        # ── 1. Create or get company "SalesLeap Demo" with domain admin.app ──
        company_result = await db.execute(
            select(Company).where(Company.email_domain == "admin.app")
        )
        company = company_result.scalar_one_or_none()

        if not company:
            company = Company(
                id=uuid.UUID("a0000000-0000-0000-0000-000000000099"),
                name="SalesLeap Demo",
                slug="salesleap-demo",
                email_domain="admin.app",
                industry="auto",
                plan="pro",
                is_active=True,
                settings={},
            )
            db.add(company)
            await db.flush()
            results.append("Company 'SalesLeap Demo' created")
        else:
            results.append("Company 'SalesLeap Demo' already exists")

        # ── 2. Create or update the 3 salespeople + admin ──
        DEMO_USERS = [
            {"email": "lucas@admin.app", "full_name": "Lucas García", "role": UserRole.learner},
            {"email": "andres@admin.app", "full_name": "Andrés Martínez", "role": UserRole.learner},
            {"email": "kun@admin.app", "full_name": "Sergio Agüero", "role": UserRole.learner},
            {"email": "admin@admin.app", "full_name": "Admin", "role": UserRole.admin},
        ]

        users_created = []
        for u_data in DEMO_USERS:
            u_result = await db.execute(select(User).where(User.email == u_data["email"]))
            user = u_result.scalar_one_or_none()
            if not user:
                user = User(
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    company_id=company.id,
                    industry="auto",
                    experience_level="beginner",
                    email_verified=True,
                    onboarding_done=True,
                    is_active=True,
                )
                db.add(user)
                await db.flush()
                results.append(f"User '{u_data['full_name']}' created")
            else:
                # Update existing user to belong to this company
                user.company_id = company.id
                user.industry = "auto"
                user.onboarding_done = True
                if u_data["role"] == UserRole.admin:
                    user.role = UserRole.admin
                results.append(f"User '{u_data['full_name']}' updated")

            users_created.append(user)

        await db.flush()

        # ── 3. Get all published lessons from the auto path ──
        auto_path_id = uuid.UUID("b0000000-0000-0000-0000-000000000001")
        lessons_result = await db.execute(
            select(Lesson)
            .join(Module, Lesson.module_id == Module.id)
            .where(Module.path_id == auto_path_id, Lesson.is_published.is_(True))
            .order_by(Module.order_index, Lesson.order_index)
        )
        all_lessons = lessons_result.scalars().all()

        if not all_lessons:
            results.append("ERROR: No lessons found — run init-db first")
            return {"results": results}

        results.append(f"Found {len(all_lessons)} lessons in auto path")

        # ── 4. Generate progress for each salesperson (not admin) ──
        today = date.today()
        monday = today - timedelta(days=today.weekday())  # this week's Monday

        # Different profiles for variety:
        # Lucas: star performer — 8 lessons done, 5 this week, 4-day streak
        # Andrés: moderate — 5 lessons done, 2 this week, 1-day streak
        # Kun: slacker — 2 lessons done, 0 this week, 0 streak
        PROFILES = [
            {
                "user_idx": 0,  # Lucas
                "lessons_total": 8,
                "lessons_this_week": 5,
                "streak": 4,
                "xp_base": 40,
            },
            {
                "user_idx": 1,  # Andrés
                "lessons_total": 5,
                "lessons_this_week": 2,
                "streak": 1,
                "xp_base": 35,
            },
            {
                "user_idx": 2,  # Kun
                "lessons_total": 2,
                "lessons_this_week": 0,
                "streak": 0,
                "xp_base": 30,
            },
        ]

        for profile in PROFILES:
            user = users_created[profile["user_idx"]]
            total_lessons = min(profile["lessons_total"], len(all_lessons))
            this_week = profile["lessons_this_week"]

            # Clear existing progress for this user
            await db.execute(
                text("DELETE FROM user_lesson_progress WHERE user_id = :uid"),
                {"uid": user.id},
            )
            await db.execute(
                text("DELETE FROM user_path_progress WHERE user_id = :uid"),
                {"uid": user.id},
            )
            await db.execute(
                text("DELETE FROM daily_streaks WHERE user_id = :uid"),
                {"uid": user.id},
            )

            total_xp = 0
            # Create completed lessons — older ones first, then this week's
            older_count = total_lessons - this_week
            for i in range(total_lessons):
                lesson = all_lessons[i]
                xp = random.randint(profile["xp_base"] - 10, profile["xp_base"] + 15)
                total_xp += xp

                if i < older_count:
                    # Completed last week or earlier
                    days_ago = random.randint(7, 14)
                    completed_at = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(1, 12))
                else:
                    # Completed this week
                    day_offset = random.randint(0, min((today - monday).days, 6))
                    completed_at = datetime(
                        monday.year, monday.month, monday.day,
                        random.randint(8, 20), random.randint(0, 59),
                        tzinfo=timezone.utc,
                    ) + timedelta(days=day_offset)

                progress = UserLessonProgress(
                    user_id=user.id,
                    lesson_id=lesson.id,
                    status=ProgressStatus.completed,
                    score=random.randint(70, 100),
                    attempts=random.randint(1, 3),
                    time_spent_sec=random.randint(120, 600),
                    completed_at=completed_at,
                )
                db.add(progress)

            # Create path progress
            path_progress = UserPathProgress(
                user_id=user.id,
                path_id=auto_path_id,
                status=ProgressStatus.in_progress if total_lessons < len(all_lessons) else ProgressStatus.completed,
                started_at=datetime.now(timezone.utc) - timedelta(days=14),
                xp_earned=total_xp,
            )
            db.add(path_progress)

            # Create daily streaks for this week
            for day_offset in range(min(this_week, (today - monday).days + 1)):
                streak_date = monday + timedelta(days=day_offset)
                daily_xp = random.randint(30, 50)
                streak = DailyStreak(
                    user_id=user.id,
                    activity_date=streak_date,
                    xp_earned=daily_xp,
                    lessons_done=random.randint(1, 3),
                )
                db.add(streak)

            # Update user stats
            user.total_xp = total_xp
            user.level = max(1, total_xp // 500 + 1)
            user.streak_current = profile["streak"]
            user.streak_max = max(profile["streak"], 5)
            user.last_activity_at = (
                datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 4))
                if profile["streak"] > 0
                else datetime.now(timezone.utc) - timedelta(days=random.randint(3, 7))
            )

            results.append(
                f"{user.full_name}: {total_lessons} lessons, {this_week} this week, "
                f"streak={profile['streak']}, xp={total_xp}, level={user.level}"
            )

        await db.commit()
        results.append("Demo data seeded successfully!")

    return {"results": results}


@app.post("/api/admin/seed-industria")
async def admin_seed_industria(x_admin_key: str = Header(...)):
    """Seed Industria Demo company + onboarding journey (7-day gamified path) + 2 users."""
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    import copy
    from datetime import datetime, timezone
    from app.models.models import (
        Company, LearningPath, Module, Lesson, User, UserRole,
        UserPathProgress, ProgressStatus,
    )

    results = []

    try:
        from seed import INDUSTRIA_COMPANY, ONBOARDING_PATH, ONBOARDING_MODULES, INDUSTRIA_USERS

        async with async_session() as db:
            # ── 1. Company ──
            company_result = await db.execute(
                select(Company).where(Company.email_domain == "industria.app")
            )
            if not company_result.scalar_one_or_none():
                db.add(Company(**INDUSTRIA_COMPANY))
                await db.flush()
                results.append("Company 'Industria Demo' created")
            else:
                results.append("Company 'Industria Demo' already exists")

            # ── 2. Onboarding path ──
            path_result = await db.execute(
                select(LearningPath).where(LearningPath.id == ONBOARDING_PATH["id"])
            )
            if not path_result.scalar_one_or_none():
                db.add(LearningPath(**ONBOARDING_PATH))
                await db.flush()
                results.append("Onboarding path created")
            else:
                results.append("Onboarding path already exists")

            # ── 3. Modules + lessons ──
            # First, check how many modules currently exist for this path
            existing_mods_result = await db.execute(
                select(Module).where(Module.path_id == ONBOARDING_PATH["id"])
            )
            existing_mods = existing_mods_result.scalars().all()

            if existing_mods:
                # Already have modules for this path — skip (idempotent)
                total_lessons = sum(1 for _ in existing_mods)  # rough count for reporting
                results.append(f"Modules already exist for onboarding path ({len(existing_mods)} modules)")
            else:
                total_lessons = 0
                for mod_data in copy.deepcopy(ONBOARDING_MODULES):
                    lessons_data = mod_data.pop("lessons")
                    module = Module(**mod_data)
                    db.add(module)
                    await db.flush()
                    for lesson_data in lessons_data:
                        db.add(Lesson(module_id=module.id, is_published=True, **lesson_data))
                        total_lessons += 1
                results.append(f"{total_lessons} lessons created across {len(ONBOARDING_MODULES)} modules")

            # ── 4. Users ──
            for u_data in INDUSTRIA_USERS:
                u_result = await db.execute(
                    select(User).where(User.email == u_data["email"])
                )
                user = u_result.scalar_one_or_none()
                if not user:
                    user = User(
                        email=u_data["email"],
                        full_name=u_data["full_name"],
                        role=UserRole(u_data["role"]),
                        company_id=INDUSTRIA_COMPANY["id"],
                        industry="manufactura",
                        experience_level="beginner",
                        email_verified=True,
                        onboarding_done=u_data["onboarding_done"],
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()
                    results.append(f"User '{u_data['full_name']}' ({u_data['email']}) created")
                else:
                    # BUG 2 fix: update company_id for existing users
                    user.company_id = INDUSTRIA_COMPANY["id"]
                    user.industry = "manufactura"
                    user.email_verified = True
                    results.append(f"User '{u_data['full_name']}' updated (company assigned)")

                # BUG 3+4 fix: ensure onboarding path is assigned for learners
                # (for both new and existing users)
                if u_data["role"] == "learner":
                    path_check = await db.execute(
                        select(UserPathProgress).where(
                            UserPathProgress.user_id == user.id,
                            UserPathProgress.path_id == ONBOARDING_PATH["id"],
                        )
                    )
                    if not path_check.scalar_one_or_none():
                        db.add(UserPathProgress(
                            user_id=user.id,
                            path_id=ONBOARDING_PATH["id"],
                            status=ProgressStatus.in_progress,
                            started_at=datetime.now(timezone.utc),
                        ))
                        results.append(f"  → Onboarding path assigned to {u_data['email']}")
                    else:
                        results.append(f"  → Onboarding path already assigned to {u_data['email']}")

            # ── 5. Insert new onboarding badges (idempotent) ──
            # BUG 1 fix: use CAST(:criteria AS jsonb) instead of :criteria::jsonb
            NEW_BADGES = [
                ("Orientado",    "Completaste el mapa del área en tu primer día",    "🗺️", "onboarding", '{"onboarding_lesson": "El mapa del área"}',              75,  "common"),
                ("En acción",    "Completaste tu primer ticket real",                 "⚙️", "onboarding", '{"onboarding_lesson": "Primer ticket real"}',            100, "rare"),
                ("Especialista", "Certificado como Operador Junior",                  "🎓", "onboarding", '{"onboarding_lesson": "Certificación: Operador Junior"}', 150, "epic"),
            ]
            badges_added = 0
            for name, desc, icon, cat, criteria_json, xp_bonus, rarity in NEW_BADGES:
                exists = await db.execute(
                    text("SELECT 1 FROM badges WHERE name = :n"),
                    {"n": name}
                )
                if not exists.scalar_one_or_none():
                    await db.execute(
                        text("""
                            INSERT INTO badges (name, description, icon, category, criteria, xp_bonus, rarity)
                            VALUES (:name, :desc, :icon, :cat, CAST(:criteria AS jsonb), :xp, :rarity)
                        """),
                        {"name": name, "desc": desc, "icon": icon, "cat": cat,
                         "criteria": criteria_json, "xp": xp_bonus, "rarity": rarity}
                    )
                    badges_added += 1
            results.append(f"{badges_added} new onboarding badges added")

            await db.commit()
            results.append("✅ Industria Demo seeded successfully!")

    except Exception as e:
        results.append(f"ERROR: {str(e)}")

    return {"results": results}


@app.post("/api/admin/seed-auto")
async def admin_seed_auto(x_admin_key: str = Header(...)):
    """Seed Auto Demo: empresa + Pablo + Admin + 4 vendedores con datos de demo."""
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    import uuid as _uuid
    import random
    from datetime import datetime, date, timedelta, timezone
    from app.models.models import (
        Company, LearningPath, Module, Lesson, User, UserRole,
        UserPathProgress, UserLessonProgress, UserBadge, Badge,
        DailyStreak, ProgressStatus,
    )

    results = []

    try:
        from seed import AUTO_APP_COMPANY, AUTO_APP_USERS, AUTO_APP_SALESPEOPLE

        AUTO_PATH_ID = _uuid.UUID("b0000000-0000-0000-0000-000000000001")

        async with async_session() as db:
            # ── 1. Empresa ──
            company_result = await db.execute(
                select(Company).where(Company.email_domain == "auto.app")
            )
            if not company_result.scalar_one_or_none():
                db.add(Company(**AUTO_APP_COMPANY))
                await db.flush()
                results.append("Company 'Auto Demo' creada")
            else:
                results.append("Company 'Auto Demo' ya existe")

            # ── 2. Verificar que el path automotriz existe ──
            path_result = await db.execute(
                select(LearningPath).where(LearningPath.id == AUTO_PATH_ID)
            )
            if not path_result.scalar_one_or_none():
                results.append("ERROR: Path 'Venta Consultiva Automotriz' no existe — corré init-db primero")
                return {"results": results}

            # ── 3. Usuarios base (Pablo + Admin) ──
            for u_data in AUTO_APP_USERS:
                u_result = await db.execute(
                    select(User).where(User.email == u_data["email"])
                )
                user = u_result.scalar_one_or_none()
                if not user:
                    user = User(
                        email=u_data["email"],
                        full_name=u_data["full_name"],
                        role=UserRole(u_data["role"]),
                        company_id=AUTO_APP_COMPANY["id"],
                        industry="auto",
                        experience_level="beginner",
                        email_verified=True,
                        onboarding_done=u_data["onboarding_done"],
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()
                    results.append(f"Usuario '{u_data['full_name']}' ({u_data['email']}) creado")
                else:
                    user.company_id = AUTO_APP_COMPANY["id"]
                    user.industry = "auto"
                    user.email_verified = True
                    user.role = UserRole(u_data["role"])
                    user.onboarding_done = u_data["onboarding_done"]
                    results.append(f"Usuario '{u_data['full_name']}' actualizado")

                if u_data["role"] == "learner":
                    path_check = await db.execute(
                        select(UserPathProgress).where(
                            UserPathProgress.user_id == user.id,
                            UserPathProgress.path_id == AUTO_PATH_ID,
                        )
                    )
                    if not path_check.scalar_one_or_none():
                        db.add(UserPathProgress(
                            user_id=user.id,
                            path_id=AUTO_PATH_ID,
                            status=ProgressStatus.in_progress,
                            started_at=datetime.now(timezone.utc),
                        ))
                        results.append(f"  → Path asignado a {u_data['email']}")

            await db.flush()

            # ── 4. Obtener todas las lecciones del path automotriz ──
            lessons_result = await db.execute(
                select(Lesson)
                .join(Module, Lesson.module_id == Module.id)
                .where(Module.path_id == AUTO_PATH_ID, Lesson.is_published.is_(True))
                .order_by(Module.order_index, Lesson.order_index)
            )
            all_lessons = lessons_result.scalars().all()
            if not all_lessons:
                results.append("ERROR: no hay lecciones — corré init-db primero")
                return {"results": results}
            results.append(f"Path tiene {len(all_lessons)} lecciones disponibles")

            # ── 5. Obtener badges por nombre para asignarlos ──
            badges_result = await db.execute(select(Badge))
            badge_map = {b.name: b for b in badges_result.scalars().all()}

            # ── 6. Crear/actualizar los 4 vendedores con datos de demo ──
            today = date.today()
            monday = today - timedelta(days=today.weekday())

            for sp in AUTO_APP_SALESPEOPLE:
                # Crear o recuperar usuario
                u_result = await db.execute(select(User).where(User.email == sp["email"]))
                user = u_result.scalar_one_or_none()
                if not user:
                    user = User(
                        email=sp["email"],
                        full_name=sp["full_name"],
                        role=UserRole.learner,
                        company_id=AUTO_APP_COMPANY["id"],
                        industry="auto",
                        experience_level="beginner",
                        email_verified=True,
                        onboarding_done=True,
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()
                else:
                    user.company_id = AUTO_APP_COMPANY["id"]
                    user.industry = "auto"
                    user.email_verified = True
                    user.onboarding_done = True

                await db.flush()

                # Limpiar progress anterior (idempotente)
                await db.execute(
                    text("DELETE FROM user_lesson_progress WHERE user_id = :uid"),
                    {"uid": user.id},
                )
                await db.execute(
                    text("DELETE FROM user_path_progress WHERE user_id = :uid"),
                    {"uid": user.id},
                )
                await db.execute(
                    text("DELETE FROM daily_streaks WHERE user_id = :uid"),
                    {"uid": user.id},
                )
                await db.execute(
                    text("DELETE FROM user_badges WHERE user_id = :uid"),
                    {"uid": user.id},
                )

                total = min(sp["lessons_total"], len(all_lessons))
                this_week = sp["lessons_this_week"]
                older = total - this_week
                total_xp = 0

                for i in range(total):
                    lesson = all_lessons[i]
                    xp = random.randint(sp["xp_base"] - 8, sp["xp_base"] + 12)
                    total_xp += xp

                    if i < older:
                        days_ago = random.randint(7, 21)
                        completed_at = datetime.now(timezone.utc) - timedelta(
                            days=days_ago, hours=random.randint(1, 10)
                        )
                    else:
                        day_offset = min(i - older, (today - monday).days)
                        completed_at = datetime(
                            monday.year, monday.month, monday.day,
                            random.randint(8, 20), random.randint(0, 59),
                            tzinfo=timezone.utc,
                        ) + timedelta(days=day_offset)

                    db.add(UserLessonProgress(
                        user_id=user.id,
                        lesson_id=lesson.id,
                        status=ProgressStatus.completed,
                        score=random.randint(72, 100),
                        attempts=random.randint(1, 3),
                        time_spent_sec=random.randint(90, 540),
                        completed_at=completed_at,
                    ))

                # Path progress
                db.add(UserPathProgress(
                    user_id=user.id,
                    path_id=AUTO_PATH_ID,
                    status=ProgressStatus.completed if total >= len(all_lessons) else ProgressStatus.in_progress,
                    started_at=datetime.now(timezone.utc) - timedelta(days=21),
                    xp_earned=total_xp,
                ))

                # Daily streaks para esta semana
                for day_offset in range(min(this_week, (today - monday).days + 1)):
                    streak_date = monday + timedelta(days=day_offset)
                    db.add(DailyStreak(
                        user_id=user.id,
                        activity_date=streak_date,
                        xp_earned=random.randint(35, 55),
                        lessons_done=random.randint(1, 3),
                    ))

                # Badges
                for badge_name in sp["badge_names"]:
                    badge = badge_map.get(badge_name)
                    if badge:
                        db.add(UserBadge(
                            user_id=user.id,
                            badge_id=badge.id,
                            earned_at=datetime.now(timezone.utc) - timedelta(
                                days=random.randint(1, 14)
                            ),
                            context={},
                        ))

                # Actualizar stats del usuario
                user.total_xp = total_xp
                user.level = max(1, total_xp // 500 + 1)
                user.streak_current = sp["streak"]
                user.streak_max = sp["streak_max"]
                user.last_activity_at = (
                    datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 6))
                    if sp["streak"] > 0
                    else datetime.now(timezone.utc) - timedelta(days=random.randint(4, 10))
                )

                results.append(
                    f"{sp['full_name']} ({sp['email']}): "
                    f"{total} lecciones, {this_week} esta semana, "
                    f"racha={sp['streak']}d, xp={total_xp}, "
                    f"badges={sp['badge_names']}"
                )

            await db.commit()
            results.append("✅ Auto Demo seeded successfully!")

    except Exception as e:
        results.append(f"ERROR: {str(e)}")

    return {"results": results}


# ── Serve React SPA (must be AFTER all API routes) ──────────
STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Serve other static files at root (favicon, etc.)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA — any non-API route returns index.html."""
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
