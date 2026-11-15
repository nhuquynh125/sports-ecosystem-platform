"""CourtBook booking endpoints (UC-CB-03, 04, 06)."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import exc, func, select
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, DbSession, require_role
from app.core.config import settings
from app.core.enums import ROLE_ADMIN, ROLE_VENUE_OWNER
from app.core.timeslots import generate_slots, now_local, slot_start_at
from app.models.booking import Booking
from app.models.enums import (
    ACTIVE_BOOKING_STATUSES,
    BOOKING_STATUS_CANCELLED,
    BOOKING_STATUS_CONFIRMED,
)
from app.models.venue import Court, Venue
from app.schemas.booking import BookingCancelPayload, BookingCreate, BookingOut
from app.schemas.common import Page, PaginationParams, paginate
from app.core.utils import generate_booking_code

router = APIRouter(prefix="/bookings", tags=["bookings"])

_owner_or_admin = require_role(ROLE_VENUE_OWNER, ROLE_ADMIN)


def _load_booking(db, booking_id: int) -> Booking:
    booking = db.scalar(
        select(Booking)
        .options(joinedload(Booking.court).joinedload(Court.venue))
        .where(Booking.id == booking_id)
    )
    return booking


# ─────────────────────── player endpoints ──────────────────────────────────

@router.post("", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate, db: DbSession, current_user: CurrentUser):
    # Validate court exists
    court = db.scalar(
        select(Court).options(joinedload(Court.venue)).where(Court.id == payload.court_id)
    )
    if court is None or not court.is_active:
        raise HTTPException(status_code=404, detail="Court not found or inactive")
    if not court.venue.is_active:
        raise HTTPException(status_code=400, detail="Venue is not active")

    # Validate slot
    valid_slots = generate_slots(court.venue.open_time, court.venue.close_time)
    if payload.time_slot not in valid_slots:
        raise HTTPException(status_code=400, detail="Invalid time slot for this venue")

    # Validate booking is not in the past
    now = now_local()
    slot_dt = slot_start_at(payload.booking_date, payload.time_slot)
    if slot_dt <= now:
        raise HTTPException(status_code=400, detail="Cannot book a slot in the past")

    # Validate advance booking window
    days_ahead = (payload.booking_date - now.date()).days
    if days_ahead > settings.BOOKING_MAX_ADVANCE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot book more than {settings.BOOKING_MAX_ADVANCE_DAYS} days in advance",
        )

    total_price = court.hourly_price  # 1 slot = 1 hour

    booking = Booking(
        booking_code=generate_booking_code(),
        court_id=payload.court_id,
        user_id=current_user.id,
        booking_date=payload.booking_date,
        time_slot=payload.time_slot,
        total_price=total_price,
        status=BOOKING_STATUS_CONFIRMED,
        note=payload.note,
    )
    db.add(booking)
    try:
        db.commit()
    except exc.IntegrityError as e:
        db.rollback()
        err_str = str(e.orig).lower()
        if "uq_bookings_court_id_booking_date_time_slot" in err_str or "unique" in err_str:
            raise HTTPException(status_code=409, detail="Time slot is already booked") from None
        if "booking_code" in err_str:
            raise HTTPException(status_code=500, detail="Booking code collision; please retry") from None
        raise

    db.refresh(booking)
    return _load_booking(db, booking.id)


@router.get("/me", response_model=Page[BookingOut])
def my_bookings(
    db: DbSession,
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
):
    stmt = (
        select(Booking)
        .options(joinedload(Booking.court).joinedload(Court.venue))
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.booking_date.desc(), Booking.time_slot.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.offset(pagination.offset).limit(pagination.page_size)).unique().all()
    return paginate(rows, total or 0, pagination)


@router.delete("/{booking_id}", status_code=204)
def cancel_booking(
    booking_id: int,
    db: DbSession,
    current_user: CurrentUser,
    payload: BookingCancelPayload | None = None,
):
    booking = _load_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id and "admin" not in current_user.role_names:
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status not in ACTIVE_BOOKING_STATUSES:
        raise HTTPException(status_code=400, detail="Booking is already cancelled or completed")

    # Cutoff check
    now = now_local()
    slot_dt = slot_start_at(booking.booking_date, booking.time_slot)
    hours_until = (slot_dt - now).total_seconds() / 3600
    if hours_until < settings.BOOKING_CANCEL_CUTOFF_HOURS and "admin" not in current_user.role_names:
        raise HTTPException(
            status_code=400,
            detail=f"Bookings cannot be cancelled within {settings.BOOKING_CANCEL_CUTOFF_HOURS} hours of the slot",
        )

    booking.status = BOOKING_STATUS_CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)
    if payload:
        booking.cancel_reason = payload.cancel_reason
    db.commit()


# ──────────────── owner view of venue bookings ─────────────────────────────

@router.get("/venue/{venue_id}", response_model=Page[BookingOut])
def venue_bookings(
    venue_id: int,
    db: DbSession,
    owner: Annotated[object, Depends(_owner_or_admin)],
    pagination: Annotated[PaginationParams, Depends()],
):
    venue = db.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    if venue.owner_id != owner.id and "admin" not in owner.role_names:
        raise HTTPException(status_code=403, detail="Not your venue")
    stmt = (
        select(Booking)
        .options(joinedload(Booking.court).joinedload(Court.venue))
        .join(Court, Court.id == Booking.court_id)
        .where(Court.venue_id == venue_id)
        .order_by(Booking.booking_date.desc(), Booking.time_slot.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.offset(pagination.offset).limit(pagination.page_size)).unique().all()
    return paginate(rows, total or 0, pagination)
