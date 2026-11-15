"""CourtBook venue + court endpoints (UC-CB-01, 02, 05)."""
from datetime import date as Date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession, require_role
from app.core.enums import ROLE_ADMIN, ROLE_VENUE_OWNER
from app.core.timeslots import generate_slots, now_local, slot_end
from app.core.utils import escape_like
from app.models.booking import Booking
from app.models.enums import ACTIVE_BOOKING_STATUSES
from app.models.venue import Court, Venue
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.venue import (
    CourtAvailability,
    CourtCreate,
    CourtRead,
    CourtSlot,
    CourtUpdate,
    OwnerVenueRead,
    VenueAvailability,
    VenueCreate,
    VenueDetail,
    VenueListItem,
    VenueUpdate,
)

router = APIRouter(prefix="/venues", tags=["venues"])

_owner_or_admin = require_role(ROLE_VENUE_OWNER, ROLE_ADMIN)


# ─────────────────────────── public ────────────────────────────────────────

@router.get("", response_model=Page[VenueListItem])
def list_venues(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    sport_id: int | None = Query(None, description="Filter by sport"),
    city: str | None = Query(None, description="Filter by city name"),
    q: str | None = Query(None, description="Keyword search (name / description / address)"),
):
    stmt = (
        select(Venue)
        .where(Venue.is_active.is_(True))
        .distinct()
        .order_by(Venue.name)
    )
    if sport_id:
        stmt = stmt.join(Venue.courts).where(
            Court.sport_id == sport_id, Court.is_active.is_(True)
        )
    if city:
        stmt = stmt.where(func.lower(Venue.city) == city.lower())
    if q:
        escaped = escape_like(q)
        pattern = f"%{escaped}%"
        stmt = stmt.where(
            or_(
                Venue.name.ilike(pattern),
                Venue.description.ilike(pattern),
                Venue.address.ilike(pattern),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.offset(pagination.offset).limit(pagination.page_size)).all()
    return paginate(rows, total or 0, pagination)


@router.get("/{venue_id}", response_model=VenueDetail)
def get_venue(venue_id: int, db: DbSession):
    venue = db.get(Venue, venue_id)
    if venue is None or not venue.is_active:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.get("/{venue_id}/availability", response_model=VenueAvailability)
def get_availability(
    venue_id: int,
    db: DbSession,
    date: Date = Query(..., description="YYYY-MM-DD, venue-local date"),
):
    venue = db.get(Venue, venue_id)
    if venue is None or not venue.is_active:
        raise HTTPException(status_code=404, detail="Venue not found")

    all_slots = generate_slots(venue.open_time, venue.close_time)
    now = now_local()
    today = now.date()

    # Fetch bookings for this venue+date in one query
    booked_query = (
        select(Booking.court_id, Booking.time_slot)
        .join(Court, Court.id == Booking.court_id)
        .where(
            Court.venue_id == venue_id,
            Booking.booking_date == date,
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
        )
    )
    booked_set: set[tuple[int, str]] = set()
    for court_id, ts in db.execute(booked_query):
        booked_set.add((court_id, ts.strftime("%H:%M")))

    courts_availability: list[CourtAvailability] = []
    for court in venue.active_courts:
        slots: list[CourtSlot] = []
        for slot_start in all_slots:
            key = (court.id, slot_start.strftime("%H:%M"))
            # Determine status
            if key in booked_set:
                status = "booked"
            elif date < today or (date == today and slot_start <= now.time()):
                status = "past"
            else:
                status = "available"
            slots.append(CourtSlot(
                start_time=slot_start,
                end_time=slot_end(slot_start),
                status=status,
                price=court.hourly_price,
            ))
        courts_availability.append(CourtAvailability(court=CourtRead.model_validate(court), slots=slots))

    return VenueAvailability(
        venue_id=venue_id,
        date=date,
        slot_minutes=60,
        open_time=venue.open_time,
        close_time=venue.close_time,
        courts=courts_availability,
    )


# ───────────────────────── venue owner / admin ─────────────────────────────

@router.get("/owner/mine", response_model=Page[OwnerVenueRead])
def owner_list_venues(
    db: DbSession,
    owner: Annotated[object, Depends(_owner_or_admin)],
    pagination: Annotated[PaginationParams, Depends()],
):
    stmt = select(Venue).where(Venue.owner_id == owner.id).order_by(Venue.name)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.offset(pagination.offset).limit(pagination.page_size)).all()
    return paginate(rows, total or 0, pagination)


@router.post("", response_model=OwnerVenueRead, status_code=201)
def create_venue(
    payload: VenueCreate,
    db: DbSession,
    owner: Annotated[object, Depends(_owner_or_admin)],
):
    venue = Venue(owner_id=owner.id, **payload.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


@router.patch("/{venue_id}", response_model=OwnerVenueRead)
def update_venue(
    venue_id: int,
    payload: VenueUpdate,
    db: DbSession,
    owner: Annotated[object, Depends(_owner_or_admin)],
):
    venue = db.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    if venue.owner_id != owner.id and "admin" not in owner.role_names:
        raise HTTPException(status_code=403, detail="Not your venue")
    data = payload.model_dump(exclude_unset=True)
    for key, val in data.items():
        setattr(venue, key, val)
    db.commit()
    db.refresh(venue)
    return venue


@router.delete("/{venue_id}", status_code=204)
def delete_venue(
    venue_id: int,
    db: DbSession,
    owner: Annotated[object, Depends(_owner_or_admin)],
):
    venue = db.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    if venue.owner_id != owner.id and "admin" not in owner.role_names:
        raise HTTPException(status_code=403, detail="Not your venue")
    db.delete(venue)
    db.commit()


# ──────────────────────────── courts ───────────────────────────────────────

@router.post("/{venue_id}/courts", response_model=CourtRead, status_code=201)
def create_court(
    venue_id: int,
    payload: CourtCreate,
    db: DbSession,
    owner: Annotated[object, Depends(_owner_or_admin)],
):
    venue = db.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    if venue.owner_id != owner.id and "admin" not in owner.role_names:
        raise HTTPException(status_code=403, detail="Not your venue")
    court = Court(venue_id=venue_id, **payload.model_dump())
    db.add(court)
    db.commit()
    db.refresh(court)
    return court


@router.patch("/{venue_id}/courts/{court_id}", response_model=CourtRead)
def update_court(
    venue_id: int,
    court_id: int,
    payload: CourtUpdate,
    db: DbSession,
    owner: Annotated[object, Depends(_owner_or_admin)],
):
    court = db.get(Court, court_id)
    if court is None or court.venue_id != venue_id:
        raise HTTPException(status_code=404, detail="Court not found")
    venue = db.get(Venue, venue_id)
    if venue.owner_id != owner.id and "admin" not in owner.role_names:
        raise HTTPException(status_code=403, detail="Not your venue")
    data = payload.model_dump(exclude_unset=True)
    for key, val in data.items():
        setattr(court, key, val)
    db.commit()
    db.refresh(court)
    return court


@router.delete("/{venue_id}/courts/{court_id}", status_code=204)
def delete_court(
    venue_id: int,
    court_id: int,
    db: DbSession,
    owner: Annotated[object, Depends(_owner_or_admin)],
):
    court = db.get(Court, court_id)
    if court is None or court.venue_id != venue_id:
        raise HTTPException(status_code=404, detail="Court not found")
    venue = db.get(Venue, venue_id)
    if venue.owner_id != owner.id and "admin" not in owner.role_names:
        raise HTTPException(status_code=403, detail="Not your venue")
    db.delete(court)
    db.commit()
