"""
Traducción de la URL de Postgres: asyncpg no entiende las opciones de libpq
que reparten los proveedores gestionados (Supabase, Neon, ...).
"""
import ssl

import pytest

from sqlalchemy.pool import NullPool

from app.core.database import build_engine_kwargs

BASE = "postgresql+asyncpg://u:p@db.example.com:5432/postgres"


def ca(url):
    """connect_args de una URL."""
    return build_engine_kwargs(url)[1]["connect_args"]


def test_plain_url_is_untouched_and_has_no_ssl():
    url, kwargs = build_engine_kwargs(BASE)
    assert url == BASE
    assert "ssl" not in kwargs["connect_args"]
    assert kwargs["connect_args"]["timeout"] == 5


@pytest.mark.parametrize("mode", ["require", "verify-ca", "verify-full"])
def test_sslmode_is_stripped_from_the_url(mode):
    """asyncpg tira TypeError si le llega sslmode como parámetro."""
    url, kwargs = build_engine_kwargs(f"{BASE}?sslmode={mode}")
    assert "sslmode" not in url
    assert isinstance(kwargs["connect_args"]["ssl"], ssl.SSLContext)


def test_require_encrypts_without_verifying():
    args = ca(f"{BASE}?sslmode=require")
    assert args["ssl"].verify_mode == ssl.CERT_NONE
    assert args["ssl"].check_hostname is False


def test_verify_full_validates_the_certificate():
    args = ca(f"{BASE}?sslmode=verify-full")
    assert args["ssl"].verify_mode == ssl.CERT_REQUIRED
    assert args["ssl"].check_hostname is True


@pytest.mark.parametrize("mode", ["prefer", "allow", "disable"])
def test_negotiated_modes_do_not_force_tls(mode):
    """prefer/allow/disable no fuerzan TLS — si no, se rompe un Postgres local."""
    url, kwargs = build_engine_kwargs(f"{BASE}?sslmode={mode}")
    assert "sslmode" not in url
    assert "ssl" not in kwargs["connect_args"]


def test_other_libpq_only_params_are_stripped():
    url, _ = build_engine_kwargs(f"{BASE}?channel_binding=require&target_session_attrs=rw")
    assert "channel_binding" not in url
    assert "target_session_attrs" not in url


def test_unknown_params_survive():
    """Sólo se filtran las opciones de libpq; el resto va a asyncpg."""
    url, _ = build_engine_kwargs(f"{BASE}?application_name=salesleap")
    assert "application_name=salesleap" in url


def test_db_ssl_setting_forces_tls_without_sslmode(monkeypatch):
    from app.core import database

    monkeypatch.setattr(database.settings, "DB_SSL", True)
    assert ca(BASE)["ssl"].verify_mode == ssl.CERT_NONE


# ── Pooler en modo transacción ──────────────────────────────
#
# El dialecto asyncpg llama a prepare() para toda sentencia. Detrás de un
# pooler que multiplexa clientes sobre una misma conexión, los nombres
# numerados chocan → DuplicatePreparedStatementError.

POOLED = "postgresql+asyncpg://u:p@aws-0-us-east-1.pooler.supabase.com:6543/postgres"


def test_transaction_pooler_disables_prepared_statements():
    _, kwargs = build_engine_kwargs(POOLED)
    args = kwargs["connect_args"]
    assert args["statement_cache_size"] == 0
    assert args["prepared_statement_cache_size"] == 0


def test_transaction_pooler_uses_unique_statement_names():
    args = build_engine_kwargs(POOLED)[1]["connect_args"]
    name_func = args["prepared_statement_name_func"]
    assert name_func() != name_func()


def test_transaction_pooler_uses_nullpool_without_pool_size():
    """NullPool no acepta pool_size: pasarle ambos revienta con TypeError."""
    _, kwargs = build_engine_kwargs(POOLED)
    assert kwargs["poolclass"] is NullPool
    assert "pool_size" not in kwargs
    assert "max_overflow" not in kwargs


def test_session_pooler_keeps_a_normal_pool():
    """El session pooler (5432) sí soporta prepared statements."""
    session_pooler = POOLED.replace(":6543", ":5432")
    _, kwargs = build_engine_kwargs(session_pooler)
    assert "poolclass" not in kwargs
    assert kwargs["pool_size"] == 5
    assert kwargs["pool_pre_ping"] is True
    assert "prepared_statement_name_func" not in kwargs["connect_args"]


def test_setting_forces_pooler_mode_on_a_nonstandard_port(monkeypatch):
    from app.core import database

    monkeypatch.setattr(database.settings, "DB_TRANSACTION_POOLER", True)
    _, kwargs = build_engine_kwargs(BASE)
    assert kwargs["poolclass"] is NullPool
