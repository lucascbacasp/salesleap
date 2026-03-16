"""
SalesLeap — JWT + magic link helpers
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"


def create_magic_token() -> str:
    return secrets.token_urlsafe(48)


def create_jwt(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str) -> UUID | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return UUID(user_id)
    except JWTError:
        return None
