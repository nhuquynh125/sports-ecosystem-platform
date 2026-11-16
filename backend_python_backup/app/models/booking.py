"""CourtBook: bookings (ERD §4, adapted to slot bookings - see backend/README "Decisions").

One booking = one ``SLOT_MINUTES`` slot of one court on one date. The database guarantees that a
slot cannot be held twice by a unique index on ``(court_id, booking_date, time_slot)`` restricted
to rows that occupy the slot (``confirmed`` / ``completed``). A ``cancelled`` row keeps the
history but no longer blocks the slot. A violation raises SQLSTATE 23505, which the service maps
to HTTP 409 ``{"detail": "Time slot is already booked"}``.
"""
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.timeslots import slot_end
from app.models.enums import (
    ACTIVE_BOOKING_STATUSES,
    BOOKING_STATUS_CONFIRMED,
    BOOKING_STATUSES,
    in_check,
)
from app.models.sport import Sport
from app.models.user import User
from app.models.venue import Court


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("booking_code", name="uq_bookings_booking_code"),
        CheckConstraint(in_check("status", BOOKING_STATUSES), name="status"),
        CheckConstraint("total_price >= 0", name="total_price"),
        # The double-booking guard. Partial: only rows that occupy the slot are unique.
        Index(
            "uq_bookings_court_id_booking_date_time_slot",
            "court_id",
            "booking_date",
            "time_slot",
            unique=True,
            postgresql_where=text(in_check("status", ACTIVE_BOOKING_STATUSES)),
        ),
        Index("ix_bookings_user_id_booking_date", "user_id", "booking_date"),
        Index("ix_bookings_court_id_booking_date", "court_id", "booking_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    booking_code: Mapped[str] = mapped_column(String(20), nullable=False)
    court_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("courts.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)  # venue-local calendar date
    time_slot: Mapped[time] = mapped_column(Time, nullable=False)  # venue-local slot START
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)  # price snapshot
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BOOKING_STATUS_CONFIRMED,
        server_default=BOOKING_STATUS_CONFIRMED,
    )
    note: Mapped[str | None] = mapped_column(String(255))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    court: Mapped[Court] = relationship(Court)
    user: Mapped[User] = relationship(User)

    # ---- derived values used by the response schemas ---------------------------------------
    @property
    def end_time(self) -> time:
        return slot_end(self.time_slot)

    @property
    def court_name(self) -> str:
        return self.court.name

    @property
    def sport(self) -> Sport:
        return self.court.sport

    @property
    def venue_id(self) -> int:
        return self.court.venue_id

    @property
    def venue_name(self) -> str:
        return self.court.venue.name
