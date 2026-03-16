"""
SalesLeap — Email service (magic link delivery)
"""
from app.core.config import settings


async def send_magic_link(email: str, token: str) -> None:
    """Envía magic link al usuario. TODO: implementar con aiosmtplib."""
    link = f"https://salesleap.app/auth/verify?token={token}"
    # TODO: enviar vía SMTP
    print(f"[DEV] Magic link para {email}: {link}")
