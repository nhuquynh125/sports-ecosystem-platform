"""Shared FastAPI dependencies: DB session, authentication, RBAC (ARCH §7)."""
from collections.abc import Callable, Iterable
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDenied
from app.core.security import decode_access_token
from app.models import User

# auto_error=False: we raise our own 401 so the body is always {"detail": "..."}.
bearer_scheme = HTTPBearer(auto_error=False, description="Paste the `access_token` from /auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def _resolve_user(token: str, db: Session) -> User:
    try:
        claims = decode_access_token(token)
        user_id = int(claims["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise AuthenticationError("Could not validate credentials") from None
    user = db.get(User, user_id)
    if user is None:
        raise AuthenticationError("Could not validate credentials")
    if not user.is_active:
        raise PermissionDenied("Account is disabled")
    return user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    """Authenticate the Bearer token and load the user (roles come from the DB, not the token,
    so a revoked role or a locked account takes effect immediately)."""
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    return _resolve_user(credentials.credentials, db)


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> User | None:
    """For public routes that behave differently for signed-in users."""
    if credentials is None:
        return None
    return _resolve_user(credentials.credentials, db)


def require_role(*roles: str | Iterable[str]) -> Callable[..., User]:
    """Build a dependency that admits users holding AT LEAST ONE of the given roles.

    Both call styles work: ``require_role("admin", "coach")`` and ``require_role(["admin"])``.
    """
    allowed: set[str] = set()
    for item in roles:
        if isinstance(item, str):
            allowed.add(item)
        else:
            allowed.update(item)

    def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if not allowed.intersection(user.role_names):
            raise PermissionDenied()
        return user

    return dependency


require_roles = require_role  # name used in ARCH §7

CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
