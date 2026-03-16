from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SalesLeap"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/salesleap"

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
