from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_role
from app.models import User
from app.models.enums import ROLE_ADMIN
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.user import AdminUserRolesUpdate, AdminUserStatusUpdate, UserRead
from app.services import user_service

router = APIRouter(prefix="/admin", tags=["Admin"])

AdminUser = Annotated[User, Depends(require_role(ROLE_ADMIN))]


@router.get("/users", response_model=Page[UserRead], summary="List / search users")
def list_users(
    _: AdminUser,
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
    q: Annotated[str | None, Query(max_length=100, description="Matches e-mail, username, name")] = None,
    role: Annotated[str | None, Query(description="Filter by role name")] = None,
    is_active: Annotated[bool | None, Query(description="Filter locked/unlocked")] = None,
):
    items, total = user_service.list_users(db, params, q=q, role=role, is_active=is_active)
    return paginate(items, total, params)


@router.get("/users/{user_id}", response_model=UserRead, summary="Get one user")
def get_user(user_id: int, _: AdminUser, db: DbSession):
    return user_service.get_user(db, user_id)


@router.patch(
    "/users/{user_id}/status", response_model=UserRead, summary="Lock / unlock a user"
)
def set_user_status(
    user_id: int, payload: AdminUserStatusUpdate, admin: AdminUser, db: DbSession
):
    """`{"is_active": false}` locks, `{"is_active": true}` unlocks, an empty body toggles."""
    return user_service.set_status(db, admin, user_id, payload.is_active)


@router.put("/users/{user_id}/roles", response_model=UserRead, summary="Replace a user's roles")
def set_user_roles(
    user_id: int, payload: AdminUserRolesUpdate, admin: AdminUser, db: DbSession
):
    return user_service.set_roles(db, admin, user_id, payload.roles)
