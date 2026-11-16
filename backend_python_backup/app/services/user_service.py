"""Account management and administration (UC-AUTH-03, UC-AUTH-04)."""
import secrets

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError, UnprocessableError
from app.core.security import hash_password, verify_password
from app.core.utils import escape_like
from app.models import Role, User, UserRole
from app.models.enums import ROLE_ADMIN
from app.schemas.common import PaginationParams
from app.schemas.user import UserUpdate
from app.services import notification_service


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return user


# ---------------------------------------------------------------- own account
def update_me(db: Session, user: User, data: UserUpdate) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise BusinessRuleError("Current password is incorrect")
    user.password_hash = hash_password(new_password)
    db.commit()


def delete_account(db: Session, user: User) -> None:
    """NFR-CMP-01: anonymise personal data, keep the row so aggregate statistics survive."""
    if ROLE_ADMIN in user.role_names and _other_active_admins(db, user.id) == 0:
        raise BusinessRuleError("At least one active admin is required")
    user.email = f"deleted-{user.id}@deleted.invalid"
    user.username = f"deleted-{user.id}"
    user.full_name = "Deleted user"
    user.phone = None
    user.avatar_url = None
    user.date_of_birth = None
    user.allow_scouting = False
    user.is_active = False
    user.password_hash = hash_password(secrets.token_urlsafe(32))  # unusable
    db.commit()


# --------------------------------------------------------------------- admin
def _other_active_admins(db: Session, excluding_user_id: int) -> int:
    return (
        db.scalar(
            select(func.count(User.id))
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.name == ROLE_ADMIN, User.is_active.is_(True), User.id != excluding_user_id)
        )
        or 0
    )


def list_users(
    db: Session,
    params: PaginationParams,
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[User], int]:
    filters = []
    if q:
        pattern = f"%{escape_like(q.strip())}%"
        filters.append(
            or_(
                User.email.ilike(pattern, escape="\\"),
                User.username.ilike(pattern, escape="\\"),
                User.full_name.ilike(pattern, escape="\\"),
            )
        )
    if role:
        filters.append(User.roles.any(Role.name == role))
    if is_active is not None:
        filters.append(User.is_active.is_(is_active))

    total = db.scalar(select(func.count(User.id)).where(*filters)) or 0
    items = db.scalars(
        select(User)
        .where(*filters)
        .order_by(User.created_at.desc(), User.id.desc())
        .limit(params.page_size)
        .offset(params.offset)
    ).all()
    return list(items), total


def set_status(db: Session, actor: User, user_id: int, is_active: bool | None) -> User:
    """Lock / unlock. `is_active=None` toggles the current state."""
    user = get_user(db, user_id)
    target = (not user.is_active) if is_active is None else is_active

    if not target:
        if user.id == actor.id:
            raise BusinessRuleError("You cannot lock your own account")
        if ROLE_ADMIN in user.role_names and _other_active_admins(db, user.id) == 0:
            raise BusinessRuleError("At least one active admin is required")

    changed = user.is_active != target
    user.is_active = target
    if changed and target:
        notification_service.notify(
            db, user.id, "account_unlocked", "Your account has been re-enabled"
        )
    db.commit()
    db.refresh(user)
    return user


def set_roles(db: Session, actor: User, user_id: int, role_names: list[str]) -> User:
    user = get_user(db, user_id)
    wanted = set(role_names)
    roles = list(db.scalars(select(Role).where(Role.name.in_(wanted))).all())
    if len(roles) != len(wanted):
        known = {role.name for role in roles}
        unknown = ", ".join(sorted(wanted - known))
        raise UnprocessableError(f"roles: unknown role(s): {unknown}")

    if (
        ROLE_ADMIN in user.role_names
        and ROLE_ADMIN not in wanted
        and _other_active_admins(db, user.id) == 0
    ):
        raise BusinessRuleError("At least one admin is required")

    current = {
        row.role_id: row for row in db.scalars(select(UserRole).where(UserRole.user_id == user.id))
    }
    wanted_ids = {role.id for role in roles}
    for role_id, row in current.items():
        if role_id not in wanted_ids:
            db.delete(row)
    for role in roles:
        if role.id not in current:
            db.add(UserRole(user_id=user.id, role_id=role.id, assigned_by=actor.id))

    notification_service.notify(
        db,
        user.id,
        "roles_changed",
        "Your roles were updated",
        "Your access level changed. Sign in again to refresh your session.",
        {"roles": sorted(wanted)},
    )
    db.commit()
    db.refresh(user)
    return user
