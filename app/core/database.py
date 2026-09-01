"""
SalesLeap — Async SQLAlchemy engine + session factory
"""
import asyncio
import logging
import ssl
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# libpq options asyncpg does not understand. Managed providers hand out URLs
# carrying them, and asyncpg raises TypeError on the unexpected keyword rather
# than ignoring it, so they have to come off the URL. "sslmode" is handled
# separately below because it changes how we connect; these are just dropped.
_LIBPQ_ONLY_PARAMS = ("channel_binding", "target_session_attrs", "options")


# Transaction-mode poolers (Supabase/Supavisor and PgBouncer both default to
# 6543) multiplex several clients onto one server connection.
TRANSACTION_POOLER_PORT = 6543


def build_engine_kwargs(url: str) -> tuple[str, dict]:
    """Split a Postgres URL into (url asyncpg accepts, create_async_engine kwargs).

    Honours libpq's "?sslmode=" the way libpq defines it: "require" encrypts
    without validating the certificate, "verify-ca"/"verify-full" also
    validate it. "prefer"/"allow"/"disable" are dropped without forcing TLS —
    asyncpg already negotiates it when the server offers it. settings.DB_SSL
    forces the "require" behaviour when the URL says nothing.

    Also picks the pooling strategy: a transaction-mode pooler needs prepared
    statements disabled and NullPool, which is incompatible with pool_size.
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

    kwargs: dict = {"connect_args": connect_args}

    if parsed.port == TRANSACTION_POOLER_PORT or settings.DB_TRANSACTION_POOLER:
        # The asyncpg dialect calls Connection.prepare() for *every* statement,
        # and asyncpg names them in numeric order. Behind a transaction pooler
        # those names collide across clients sharing a server connection:
        #     asyncpg.exceptions.DuplicatePreparedStatementError
        # Unique names plus no caching is the combination SQLAlchemy documents
        # for PgBouncer; it applies verbatim to Supabase's Supavisor.
        connect_args["statement_cache_size"] = 0
        connect_args["prepared_statement_cache_size"] = 0
        connect_args["prepared_statement_name_func"] = lambda: f"__asyncpg_{uuid4()}__"
        # SQLAlchemy warns that without NullPool the prepared statements pile
        # up on the pooler side. NullPool takes no pool_size/max_overflow.
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        # A pooled/managed Postgres drops idle connections behind our back;
        # without these the first query after an idle period fails instead of
        # reconnecting.
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 1800

    clean_url = urlunsplit(parsed._replace(query=urlencode(params)))
    return clean_url, kwargs


_url, _engine_kwargs = build_engine_kwargs(settings.DATABASE_URL)

engine = create_async_engine(_url, echo=settings.DEBUG, **_engine_kwargs)

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
