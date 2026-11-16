"""CourtBook schemas: venues, courts and availability (UC-CB-01, 02, 05)."""
from datetime import date as Date
from datetime import datetime, time
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
    model_validator,
)

from app.core.timeslots import SLOT_MINUTES, minutes_between
from app.schemas.sport import SportRead

SurfaceType = Literal["grass", "turf", "wood", "hard", "clay", "synthetic"]
SlotStatus = Literal["available", "booked", "past"]

# pydantic v2 writes Decimal as a JSON *string*; the API contract wants plain numbers for money.
JsonDecimal = Annotated[
    Decimal, PlainSerializer(lambda value: float(value), return_type=float, when_used="json")
]


def _naive_minute(value: time | None) -> time | None:
    """Opening hours are local wall-clock times at minute precision: drop zone and seconds."""
    return value.replace(second=0, microsecond=0, tzinfo=None) if value is not None else value


def _check_hours(open_time: time, close_time: time) -> None:
    if close_time <= open_time:
        raise ValueError("close_time must be after open_time")
    if minutes_between(open_time, close_time) < SLOT_MINUTES:
        raise ValueError(f"The venue must be open for at least {SLOT_MINUTES} minutes")


# ------------------------------------------------------------------------------------ courts
class CourtRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venue_id: int
    sport_id: int
    sport: SportRead
    name: str
    surface_type: str | None = None
    capacity: int | None = None
    hourly_price: JsonDecimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CourtCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sport_id: int
    name: str = Field(min_length=1, max_length=100, description="Unique within the venue")
    surface_type: SurfaceType | None = None
    capacity: int | None = Field(default=None, ge=1, le=100, description="Players")
    hourly_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2, description="VND per hour")
    is_active: bool = True


class CourtUpdate(BaseModel):
    """PATCH: `sport_id` is immutable; only sent fields change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    surface_type: SurfaceType | None = None
    capacity: int | None = Field(default=None, ge=1, le=100)
    hourly_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    is_active: bool | None = None

    @field_validator("name", "hourly_price", "is_active")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value


# ----------------------------------------------------------------------------------- venues
class VenueBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    description: str | None = None
    address: str
    city: str
    district: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    open_time: time
    close_time: time
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VenueListItem(VenueBase):
    """Search result card: no court list, just what is needed to compare venues."""

    court_count: int
    min_hourly_price: JsonDecimal | None = None
    sports: list[SportRead]


class VenueDetail(VenueBase):
    """Public detail: ACTIVE courts only."""

    sports: list[SportRead]
    courts: list[CourtRead] = Field(validation_alias="active_courts")


class OwnerVenueRead(VenueBase):
    """Owner / admin view: every court, including deactivated ones."""

    courts: list[CourtRead]


class VenueCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    address: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    phone: str | None = Field(default=None, max_length=30)
    open_time: time = Field(description="Local opening time, e.g. 06:00")
    close_time: time = Field(description="Local closing time, e.g. 22:00")
    is_active: bool = True

    @field_validator("open_time", "close_time")
    @classmethod
    def _minute_precision(cls, value: time) -> time:
        return _naive_minute(value)

    @model_validator(mode="after")
    def _hours(self):
        _check_hours(self.open_time, self.close_time)
        return self


class VenueUpdate(BaseModel):
    """PATCH: only sent fields change. Cross-field rules (hours) are re-checked in the service."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    phone: str | None = Field(default=None, max_length=30)
    open_time: time | None = None
    close_time: time | None = None
    is_active: bool | None = None

    @field_validator("name", "address", "city", "open_time", "close_time", "is_active")
    @classmethod
    def _not_null(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value

    @field_validator("open_time", "close_time")
    @classmethod
    def _minute_precision(cls, value: time) -> time:
        return _naive_minute(value)


# ------------------------------------------------------------------------------ availability
class CourtSlot(BaseModel):
    start_time: time
    end_time: time
    status: SlotStatus = Field(description="available | booked | past (already started)")
    price: JsonDecimal


class CourtAvailability(BaseModel):
    court: CourtRead
    slots: list[CourtSlot]


class VenueAvailability(BaseModel):
    venue_id: int
    date: Date
    slot_minutes: int
    open_time: time
    close_time: time
    courts: list[CourtAvailability]
