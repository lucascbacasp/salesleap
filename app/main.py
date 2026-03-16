"""
SalesLeap — FastAPI main application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers import auth, users, companies, paths, modules, lessons, progress, gamification, ai_coach, onboarding


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
