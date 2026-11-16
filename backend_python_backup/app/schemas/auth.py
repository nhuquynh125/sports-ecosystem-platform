"""Registration / login schemas (UC-AUTH-01, UC-AUTH-02)."""
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user import UserRead, _check_password_strength

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    username: str = Field(min_length=3, max_length=50, description="Letters, digits, _ . -")
    password: str = Field(min_length=8, max_length=128, description="Letters and digits, >= 8")
    full_name: str = Field(min_length=1, max_length=150)
    role: str = Field(
        default="player",
        description="player | venue_owner | organizer | coach (admin is never self-assignable)",
    )

    @field_validator("username")
    @classmethod
    def _username_chars(cls, value: str) -> str:
        if not _USERNAME_RE.match(value):
            raise ValueError("Username may only contain letters, digits, '_', '.' and '-'")
        return value

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        return _check_password_strength(value)

    @field_validator("role")
    @classmethod
    def _role_lower(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access-token lifetime in seconds")
    user: UserRead
