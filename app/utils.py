import secrets
import string
from datetime import datetime, timezone

from .models import Link


def generate_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def is_expired(link: Link) -> bool:
    if link.expires_at is None:
        return False
    expires = link.expires_at
    if expires.tzinfo is None:  # SQLite returns naive datetimes
        expires = expires.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires