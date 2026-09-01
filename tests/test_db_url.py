"""
Traducción de la URL de Postgres: asyncpg no entiende las opciones de libpq
que reparten los proveedores gestionados (Supabase, Neon, ...).
"""
import ssl

import pytest

from app.core.database import build_engine_args

BASE = "postgresql+asyncpg://u:p@db.example.com:5432/postgres"


def test_plain_url_is_untouched_and_has_no_ssl():
    url, args = build_engine_args(BASE)
    assert url == BASE
    assert "ssl" not in args
    assert args["timeout"] == 5


@pytest.mark.parametrize("mode", ["require", "verify-ca", "verify-full"])
def test_sslmode_is_stripped_from_the_url(mode):
    """asyncpg tira TypeError si le llega sslmode como parámetro."""
    url, args = build_engine_args(f"{BASE}?sslmode={mode}")
    assert "sslmode" not in url
    assert isinstance(args["ssl"], ssl.SSLContext)


def test_require_encrypts_without_verifying():
    _, args = build_engine_args(f"{BASE}?sslmode=require")
    assert args["ssl"].verify_mode == ssl.CERT_NONE
    assert args["ssl"].check_hostname is False


def test_verify_full_validates_the_certificate():
    _, args = build_engine_args(f"{BASE}?sslmode=verify-full")
    assert args["ssl"].verify_mode == ssl.CERT_REQUIRED
    assert args["ssl"].check_hostname is True


@pytest.mark.parametrize("mode", ["prefer", "allow", "disable"])
def test_negotiated_modes_do_not_force_tls(mode):
    """prefer/allow/disable no fuerzan TLS — si no, se rompe un Postgres local."""
    url, args = build_engine_args(f"{BASE}?sslmode={mode}")
    assert "sslmode" not in url
    assert "ssl" not in args


def test_other_libpq_only_params_are_stripped():
    url, _ = build_engine_args(f"{BASE}?channel_binding=require&target_session_attrs=rw")
    assert "channel_binding" not in url
    assert "target_session_attrs" not in url


def test_unknown_params_survive():
    """Sólo se filtran las opciones de libpq; el resto va a asyncpg."""
    url, _ = build_engine_args(f"{BASE}?application_name=salesleap")
    assert "application_name=salesleap" in url


def test_db_ssl_setting_forces_tls_without_sslmode(monkeypatch):
    from app.core import database

    monkeypatch.setattr(database.settings, "DB_SSL", True)
    _, args = build_engine_args(BASE)
    assert args["ssl"].verify_mode == ssl.CERT_NONE
