"""
SalesLeap — Async SQLAlchemy engine + session factory
"""
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    """Called on app startup — engine warmup with retries for cloud deploys."""
    for attempt in range(1, 6):
        try:
            async with engine.begin():
                pass
            logger.info("Database connected (attempt %d)", attempt)
            return
        except Exception as e:
            logger.warning("DB connection attempt %d/5 failed: %s", attempt, e)
            if attempt < 5:
                await asyncio.sleep(attempt * 2)
    logger.error("Could not connect to database after 5 attempts — app will start anyway")
