"""Pydantic v2 schemas for SportHub pickup match APIs (Module 3)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared / small sub-schemas
# ---------------------------------------------------------------------------

class UserSummary(BaseModel):
    id: int
    username: str
    full_name: str
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class SportSummary(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Pickup Match – request bodies
# ---------------------------------------------------------------------------

class PickupMatchCreate(BaseModel):
    sport_id: int
    venue_id: int | None = None
    area: str = Field(..., min_length=2, max_length=150)
    skill_level: Literal["beginner", "intermediate", "advanced", "pro"] = "intermediate"
    match_date: date
    time_slot: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM")
    max_players: int = Field(default=10, ge=2, le=100)
    description: str | None = Field(None, max_length=1000)

    @field_validator("match_date")
    @classmethod
    def _date_not_in_past(cls, v: date) -> date:
        from datetime import date as _date
        if v < _date.today():
            raise ValueError("match_date must be today or in the future")
        return v


class PickupMatchUpdate(BaseModel):
    area: str | None = Field(None, min_length=2, max_length=150)
    skill_level: Literal["beginner", "intermediate", "advanced", "pro"] | None = None
    match_date: date | None = None
    time_slot: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    max_players: int | None = Field(None, ge=2, le=100)
    description: str | None = Field(None, max_length=1000)
    status: Literal["open", "full", "ongoing", "completed", "cancelled"] | None = None


# ---------------------------------------------------------------------------
# Pickup Match – response schemas
# ---------------------------------------------------------------------------

class MatchPlayerOut(BaseModel):
    id: int
    user_id: int
    user: UserSummary
    status: str
    attended: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


class PickupMatchOut(BaseModel):
    id: int
    host_id: int
    host: UserSummary
    sport_id: int
    sport: SportSummary
    venue_id: int | None
    area: str
    skill_level: str
    match_date: date
    time_slot: str        # "HH:MM"
    max_players: int
    current_player_count: int
    status: str
    description: str | None
    chat_room_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, m: object) -> "PickupMatchOut":
        from datetime import time as dt_time
        ts = getattr(m, "time_slot", None)
        time_slot_str = ts.strftime("%H:%M") if isinstance(ts, dt_time) else str(ts)
        return cls(
            id=m.id,  # type: ignore[attr-defined]
            host_id=m.host_id,  # type: ignore[attr-defined]
            host=UserSummary.model_validate(m.host),  # type: ignore[attr-defined]
            sport_id=m.sport_id,  # type: ignore[attr-defined]
            sport=SportSummary.model_validate(m.sport),  # type: ignore[attr-defined]
            venue_id=m.venue_id,  # type: ignore[attr-defined]
            area=m.area,  # type: ignore[attr-defined]
            skill_level=m.skill_level,  # type: ignore[attr-defined]
            match_date=m.match_date,  # type: ignore[attr-defined]
            time_slot=time_slot_str,
            max_players=m.max_players,  # type: ignore[attr-defined]
            current_player_count=m.current_player_count,  # type: ignore[attr-defined]
            status=m.status,  # type: ignore[attr-defined]
            description=m.description,  # type: ignore[attr-defined]
            chat_room_id=m.chat_room_id,  # type: ignore[attr-defined]
            created_at=m.created_at,  # type: ignore[attr-defined]
        )


# ---------------------------------------------------------------------------
# Ratings – request / response
# ---------------------------------------------------------------------------

class RatingCreate(BaseModel):
    rated_user_id: int
    skill_score: int = Field(..., ge=1, le=5)
    punctuality_score: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None, max_length=500)


class RatingOut(BaseModel):
    id: int
    match_id: int
    rater_id: int
    rated_user_id: int
    skill_score: int
    punctuality_score: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# AI Smart Match – request / response
# ---------------------------------------------------------------------------

class SmartMatchRequest(BaseModel):
    match_id: int
    top_n: int = Field(default=10, ge=1, le=50)


class FeatureBreakdown(BaseModel):
    sport_match: float
    skill_level_proximity: float
    area_match: float
    availability_overlap_ratio: float
    on_time_attendance_rate: float
    avg_rating: float


class PlayerRecommendation(BaseModel):
    user_id: int
    username: str
    full_name: str
    avatar_url: str | None
    suitability_pct: float = Field(..., description="0-100")
    feature_breakdown: FeatureBreakdown


class SmartMatchResponse(BaseModel):
    match_id: int
    recommendations: list[PlayerRecommendation]
