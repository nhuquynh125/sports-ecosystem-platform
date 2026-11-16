from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=201, summary="Register an account")
def register(payload: RegisterRequest, db: DbSession):
    """UC-AUTH-01. `role` defaults to `player`; `admin` is never self-assignable (403)."""
    return auth_service.register_user(db, payload)


@router.post("/login", response_model=TokenResponse, summary="Log in and get a JWT")
def login(payload: LoginRequest, db: DbSession):
    """UC-AUTH-02. Returns a short-lived Bearer access token (default 15 minutes)."""
    user = auth_service.authenticate(db, str(payload.email), payload.password)
    token, expires_in = create_access_token(user.id, user.role_names)
    return TokenResponse(
        access_token=token, expires_in=expires_in, user=UserRead.model_validate(user)
    )
