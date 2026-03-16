"""
SalesLeap — Async SQLAlchemy engine + session factory
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

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
    """Called on app startup — engine warmup."""
    try:
        async with engine.begin():
            pass
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("DB not available at startup: %s", e)
