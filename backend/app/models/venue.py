"""CourtBook: venues and their courts (ERD §4)."""
from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SURFACE_TYPES, in_check
from app.models.sport import Sport


class Venue(Base):
    __tablename__ = "venues"
    __table_args__ = (
        CheckConstraint("close_time > open_time", name="time_order"),
        CheckConstraint("latitude IS NULL OR latitude BETWEEN -90 AND 90", name="latitude"),
        CheckConstraint("longitude IS NULL OR longitude BETWEEN -180 AND 180", name="longitude"),
        Index("ix_venues_owner_id", "owner_id"),
        Index("ix_venues_city_district", "city", "district"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    phone: Mapped[str | None] = mapped_column(String(30))
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Services refuse to delete a court that has bookings (FK is RESTRICT), so the ORM cascade
    # only ever removes booking-free courts together with their venue.
    courts: Mapped[list["Court"]] = relationship(
        back_populates="venue",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Court.id",
    )

    # ---- derived values used by the response schemas ---------------------------------------
    @property
    def active_courts(self) -> list["Court"]:
        return [court for court in self.courts if court.is_active]

    @property
    def court_count(self) -> int:
        return len(self.active_courts)

    @property
    def min_hourly_price(self) -> Decimal | None:
        prices = [court.hourly_price for court in self.active_courts]
        return min(prices) if prices else None

    @property
    def sports(self) -> list[Sport]:
        distinct = {court.sport_id: court.sport for court in self.active_courts}
        return sorted(distinct.values(), key=lambda sport: sport.name)


class Court(Base):
    __tablename__ = "courts"
    __table_args__ = (
        UniqueConstraint("venue_id", "name", name="uq_courts_venue_id_name"),
        CheckConstraint("hourly_price >= 0", name="hourly_price"),
        CheckConstraint("capacity IS NULL OR capacity > 0", name="capacity"),
        CheckConstraint(
            "surface_type IS NULL OR " + in_check("surface_type", SURFACE_TYPES), name="surface_type"
        ),
        Index("ix_courts_venue_id", "venue_id"),
        Index("ix_courts_sport_id", "sport_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("venues.id", ondelete="RESTRICT"), nullable=False
    )
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    surface_type: Mapped[str | None] = mapped_column(String(20))
    capacity: Mapped[int | None] = mapped_column(SmallInteger)  # players
    hourly_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # `venue` stays lazy: eager-loading it from here would make Venue.courts <-> Court.venue a
    # loader cycle. Queries that need it ask for it explicitly (see booking_service).
    venue: Mapped[Venue] = relationship(back_populates="courts")
    sport: Mapped[Sport] = relationship(Sport, lazy="joined")
