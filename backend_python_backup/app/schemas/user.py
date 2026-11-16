"""User and account schemas."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _check_password_strength(value: str) -> str:
    """SRS NFR-SEC-02: >= 8 characters with letters and digits. bcrypt reads 72 bytes at most."""
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes long")
    if not any(ch.isalpha() for ch in value) or not any(ch.isdigit() for ch in value):
        raise ValueError("Password must contain both letters and digits")
    return value


class UserPublic(BaseModel):
    """What other users may see (NFR-SEC-08: e-mail and phone stay private)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    avatar_url: str | None = None


class UserRead(BaseModel):
    """Full account view: the owner and admins only."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    date_of_birth: date | None = None
    is_active: bool
    allow_scouting: bool
    roles: list[str]
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("roles", mode="before")
    @classmethod
    def _role_names(cls, value):
        return [getattr(role, "name", role) for role in value]


class UserUpdate(BaseModel):
    """PATCH /users/me - only the fields that were sent are changed."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)
    date_of_birth: date | None = None
    allow_scouting: bool | None = None

    @field_validator("full_name", "allow_scouting")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def _not_in_future(cls, value):
        if value is not None and value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _strength(cls, value):
        return _check_password_strength(value)


class AdminUserStatusUpdate(BaseModel):
    """PATCH /admin/users/{id}/status. Omit `is_active` to toggle."""

    is_active: bool | None = None


class AdminUserRolesUpdate(BaseModel):
    roles: list[str] = Field(min_length=1, max_length=5)
