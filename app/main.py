"""
SalesLeap — FastAPI main application
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import async_session, engine, init_db
from app.routers import auth, users, companies, paths, modules, lessons, progress, gamification, ai_coach, onboarding

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
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
        # Split by statements and execute (asyncpg can't handle multiple statements at once)
        async with engine.begin() as conn:
            # Use raw_connection for multi-statement SQL
            raw = await conn.get_raw_connection()
            await raw.execute(schema_sql)
        results.append("schema.sql executed successfully")
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            results.append(f"schema.sql: tables already exist (OK)")
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
