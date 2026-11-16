"""CourtBook schemas: bookings (UC-CB-03, 04, 06, 07)."""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

from app.schemas.venue import CourtRead

JsonDecimal = Annotated[
    Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")
]


class BookingCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    court_id: int
    booking_date: date = Field(description="YYYY-MM-DD, venue-local wall-clock date")
    time_slot: time = Field(description="Slot start time, e.g. 14:00")
    note: str | None = Field(default=None, max_length=255)


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    booking_code: str
    court_id: int
    court: CourtRead
    user_id: int
    booking_date: date
    time_slot: time
    end_time: time            # from property
    total_price: JsonDecimal
    status: str
    note: str | None = None
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    # venue-level shortcuts (from properties)
    venue_id: int
    venue_name: str
    court_name: str


class BookingCancelPayload(BaseModel):
    cancel_reason: str | None = Field(default=None, max_length=255)
