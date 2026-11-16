"""Password hashing and JWT access tokens."""
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS
)
_dummy_hash: str | None = None


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def verify_against_dummy(password: str) -> None:
    """Spend the same time as a real verification (login for an unknown e-mail)."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password(secrets.token_urlsafe(16))
    verify_password(password, _dummy_hash)


def create_access_token(user_id: int, roles: list[str]) -> tuple[str, int]:
    """Return ``(token, expires_in_seconds)``. Claims: sub, roles, iat, exp, jti (ARCH §7.1)."""
    now = datetime.now(timezone.utc)
    lifetime = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {
        "sub": str(user_id),
        "roles": list(roles),
        "iat": now,
        "exp": now + lifetime,
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> dict:
    """Decode and validate a token. Raises ``jwt.PyJWTError`` (expired, tampered, malformed)."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub"]},
    )
