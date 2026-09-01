"""
SalesLeap — Async SQLAlchemy engine + session factory
"""
import asyncio
import logging
import ssl
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

# libpq options asyncpg does not understand. Managed providers hand out URLs
# carrying them, and asyncpg raises TypeError on the unexpected keyword rather
# than ignoring it, so they have to come off the URL. "sslmode" is handled
# separately below because it changes how we connect; these are just dropped.
_LIBPQ_ONLY_PARAMS = ("channel_binding", "target_session_attrs", "options")


def build_engine_args(url: str) -> tuple[str, dict]:
    """Split a Postgres URL into (url asyncpg accepts, connect_args).

    Honours libpq's "?sslmode=" the way libpq defines it: "require" encrypts
    without validating the certificate, "verify-ca"/"verify-full" also
    validate it. "prefer"/"allow"/"disable" are dropped without forcing TLS —
    asyncpg already negotiates it when the server offers it. settings.DB_SSL
    forces the "require" behaviour when the URL says nothing.
    """
    parsed = urlsplit(url)
    params = dict(parse_qsl(parsed.query))
    sslmode = params.pop("sslmode", None)
    for leftover in _LIBPQ_ONLY_PARAMS:
        params.pop(leftover, None)

    connect_args: dict = {"timeout": 5}  # asyncpg connection timeout: 5s max
    if sslmode in ("verify-ca", "verify-full"):
        connect_args["ssl"] = ssl.create_default_context()
    elif sslmode == "require" or settings.DB_SSL:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = context

    clean_url = urlunsplit(parsed._replace(query=urlencode(params)))
    return clean_url, connect_args


_url, _connect_args = build_engine_args(settings.DATABASE_URL)

engine = create_async_engine(
    _url,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    # A pooled/managed Postgres drops idle connections behind our back; without
    # these, the first query after an idle period fails instead of reconnecting.
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args=_connect_args,
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
    for attempt in range(1, 4):
        try:
            async with engine.begin():
                pass
            logger.info("Database connected (attempt %d)", attempt)
            return
        except Exception as e:
            logger.warning("DB connection attempt %d/3 failed: %s", attempt, e)
            if attempt < 3:
                await asyncio.sleep(2)
    logger.error("Could not connect to database after 3 attempts — app will start anyway")
