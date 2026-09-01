from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SalesLeap"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/salesleap"
    # Keep the pool small: managed Postgres (Supabase free, Neon, ...) caps
    # connections, and every uvicorn worker opens its own pool.
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    # Force TLS to the database. Not needed for a local/docker Postgres; most
    # managed providers require it. A "?sslmode=" in DATABASE_URL also turns
    # it on — see app/core/database.py.
    DB_SSL: bool = False

    # Seeding on startup: "auto" (default) seeds only when the database is
    # still empty, "always" re-runs it on every boot (local dev), "never"
    # skips it. On a scale-to-zero host, "always" would re-run the whole
    # seed on every cold start.
    AUTO_SEED: str = "auto"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Anthropic (Claude API — motor de IA del producto)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Auth (magic link)
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
    JWT_EXPIRE_HOURS: int = 168  # 7 días

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "https://salesleap.app"]

    # Email (para magic links)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM: str = "noreply@salesleap.app"

    # Storage (uploads de empresas)
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
