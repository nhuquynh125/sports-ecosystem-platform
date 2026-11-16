from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.schemas.user import PasswordChange, UserPublic, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead, summary="Current account")
def read_me(current_user: CurrentUser):
    return current_user


@router.patch("/me", response_model=UserRead, summary="Update own account")
def update_me(payload: UserUpdate, current_user: CurrentUser, db: DbSession):
    return user_service.update_me(db, current_user, payload)


@router.post(
    "/me/password",
    status_code=204,
    response_class=Response,
    summary="Change own password",
)
def change_password(payload: PasswordChange, current_user: CurrentUser, db: DbSession):
    user_service.change_password(db, current_user, payload.current_password, payload.new_password)
    return Response(status_code=204)


@router.delete(
    "/me",
    status_code=204,
    response_class=Response,
    summary="Delete own account (anonymises personal data)",
)
def delete_me(current_user: CurrentUser, db: DbSession):
    user_service.delete_account(db, current_user)
    return Response(status_code=204)


@router.get("/{user_id}", response_model=UserPublic, summary="Public view of a user")
def read_user(user_id: int, _: CurrentUser, db: DbSession):
    """Only non-sensitive fields; admins use `/admin/users/{id}` for the full record."""
    user = user_service.get_user(db, user_id)
    if not user.is_active:
        raise NotFoundError("User not found")  # locked / deleted accounts are not browsable
    return user
