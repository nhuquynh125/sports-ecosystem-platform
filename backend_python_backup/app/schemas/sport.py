"""Sports catalogue schemas."""
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None = None
    icon_url: str | None = None
    is_active: bool


class SportCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    slug: str | None = Field(default=None, max_length=100, description="Generated from name if omitted")
    description: str | None = Field(default=None, max_length=500)
    icon_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True

    @field_validator("slug")
    @classmethod
    def _slug_format(cls, value):
        if value is not None and not _SLUG_RE.match(value):
            raise ValueError("Slug must be lowercase letters, digits and single hyphens")
        return value


class SportUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    icon_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None

    @field_validator("name", "slug", "is_active")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value

    @field_validator("slug")
    @classmethod
    def _slug_format(cls, value):
        if value is not None and not _SLUG_RE.match(value):
            raise ValueError("Slug must be lowercase letters, digits and single hyphens")
        return value
