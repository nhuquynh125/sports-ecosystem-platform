"""Player profile and weekly availability schemas (UC-SH-01)."""
from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.sport import SportRead
from app.schemas.user import UserPublic

SkillLevel = Literal["beginner", "intermediate", "advanced", "pro"]
PreferredSide = Literal["left", "right", "both"]


class PlayerProfileCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sport_id: int = Field(description="The sport this profile is for (one profile per sport)")
    position: str | None = Field(default=None, max_length=50)
    skill_level: SkillLevel = "beginner"
    preferred_side: PreferredSide | None = Field(default=None, description="Foot or hand")
    height_cm: int | None = Field(default=None, ge=50, le=260)
    weight_kg: int | None = Field(default=None, ge=20, le=300)
    city: str | None = Field(default=None, max_length=100, description="Playing area")
    bio: str | None = Field(default=None, max_length=2000)
    is_visible: bool = True


class PlayerProfileUpdate(BaseModel):
    """PATCH: `sport_id` is immutable; only sent fields change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    position: str | None = Field(default=None, max_length=50)
    skill_level: SkillLevel | None = None
    preferred_side: PreferredSide | None = None
    height_cm: int | None = Field(default=None, ge=50, le=260)
    weight_kg: int | None = Field(default=None, ge=20, le=300)
    city: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    is_visible: bool | None = None

    @field_validator("skill_level", "is_visible")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value


class PlayerProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    sport_id: int
    position: str | None = None
    skill_level: str
    preferred_side: str | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    city: str | None = None
    bio: str | None = None
    is_visible: bool
    created_at: datetime
    updated_at: datetime
    sport: SportRead
    user: UserPublic


class _SlotTimes(BaseModel):
    @field_validator("start_time", "end_time", mode="after", check_fields=False)
    @classmethod
    def _naive(cls, value: time | None) -> time | None:
        # Availability is a recurring local wall-clock window: drop any UTC offset.
        return value.replace(tzinfo=None) if value is not None else value


class AvailabilitySlotCreate(_SlotTimes):
    day_of_week: int = Field(ge=1, le=7, description="1 = Monday ... 7 = Sunday")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def _order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AvailabilitySlotUpdate(_SlotTimes):
    day_of_week: int | None = Field(default=None, ge=1, le=7)
    start_time: time | None = None
    end_time: time | None = None

    @field_validator("day_of_week", "start_time", "end_time", mode="after")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value


class AvailabilitySlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_profile_id: int
    day_of_week: int
    start_time: time
    end_time: time
    created_at: datetime


class AvailabilityReplace(BaseModel):
    """PUT: replaces the whole weekly schedule of a profile."""

    slots: list[AvailabilitySlotCreate] = Field(max_length=50)
