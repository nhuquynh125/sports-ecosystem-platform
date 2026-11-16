"""Registration and authentication (UC-AUTH-01, UC-AUTH-02)."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    PermissionDenied,
    UnprocessableError,
)
from app.core.security import hash_password, verify_against_dummy, verify_password
from app.models import Role, User, UserRole
from app.models.enums import ROLE_ADMIN, SELF_ASSIGNABLE_ROLES
from app.schemas.auth import RegisterRequest
from app.services import notification_service

_BAD_CREDENTIALS = "Incorrect email or password"  # identical for unknown e-mail / wrong password


def register_user(db: Session, data: RegisterRequest) -> User:
    if data.role == ROLE_ADMIN:
        raise PermissionDenied("The 'admin' role cannot be self-assigned")
    if data.role not in SELF_ASSIGNABLE_ROLES:
        allowed = ", ".join(SELF_ASSIGNABLE_ROLES)
        raise UnprocessableError(f"role: must be one of {allowed}")

    email = str(data.email).lower()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise ConflictError("Email already registered")
    if db.scalar(select(User.id).where(User.username == data.username)) is not None:
        raise ConflictError("Username already taken")

    role = db.scalar(select(Role).where(Role.name == data.role))
    if role is None:  # the migration seeds roles; this means the DB is misconfigured
        raise RuntimeError(f"Role '{data.role}' is missing - run `alembic upgrade head`")

    user = User(
        email=email,
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    try:
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        notification_service.notify(
            db,
            user.id,
            "welcome",
            "Welcome to Sports Ecosystem",
            f"Hi {user.full_name}, your account is ready. Complete your profile to get started.",
            {"deep_link": "/profile"},
        )
        db.commit()
    except IntegrityError:
        db.rollback()  # lost a race against a concurrent registration (unique constraints)
        raise ConflictError("Email or username already registered") from None
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        verify_against_dummy(password)  # keep timing similar; avoid account enumeration
        raise AuthenticationError(_BAD_CREDENTIALS)
    if not verify_password(password, user.password_hash):
        raise AuthenticationError(_BAD_CREDENTIALS)
    if not user.is_active:
        raise PermissionDenied("Account is disabled")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user

