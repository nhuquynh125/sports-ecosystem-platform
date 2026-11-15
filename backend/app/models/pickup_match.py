"""SportHub Module 3: casual pickup matches, participants, and post-match ratings (ERD §7)."""
from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SKILL_LEVELS, in_check

PICKUP_MATCH_STATUSES = ("open", "full", "ongoing", "completed", "cancelled")
MATCH_PLAYER_STATUSES = ("joined", "left", "removed")


class PickupMatch(Base):
    """A casual pickup / open-invitation match posted by a host."""

    __tablename__ = "pickup_matches"
    __table_args__ = (
        CheckConstraint(
            in_check("skill_level", SKILL_LEVELS), name="skill_level"
        ),
        CheckConstraint(
            in_check("status", PICKUP_MATCH_STATUSES), name="status"
        ),
        CheckConstraint("max_players >= 2", name="max_players_min"),
        Index("ix_pickup_matches_sport_id", "sport_id"),
        Index("ix_pickup_matches_match_date", "match_date"),
        Index("ix_pickup_matches_status", "status"),
        Index("ix_pickup_matches_area", "area"),
        Index("ix_pickup_matches_host_id", "host_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    host_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id", ondelete="RESTRICT"), nullable=False
    )
    venue_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("venues.id", ondelete="SET NULL"), nullable=True
    )
    area: Mapped[str] = mapped_column(String(150), nullable=False)  # city / district free text
    skill_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="intermediate", server_default="intermediate"
    )
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    time_slot: Mapped[time] = mapped_column(Time, nullable=False)
    max_players: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=10)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open", server_default="open"
    )
    description: Mapped[str | None] = mapped_column(Text)
    chat_room_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("chat_rooms.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # relationships
    host: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[host_id], lazy="selectin"
    )
    sport: Mapped["Sport"] = relationship(  # type: ignore[name-defined]
        "Sport", lazy="selectin"
    )
    venue: Mapped["Venue | None"] = relationship(  # type: ignore[name-defined]
        "Venue", lazy="selectin"
    )
    players: Mapped[list["MatchPlayer"]] = relationship(
        "MatchPlayer",
        back_populates="match",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def current_player_count(self) -> int:
        return sum(1 for p in self.players if p.status == "joined")


class MatchPlayer(Base):
    """Join table between pickup matches and player users."""

    __tablename__ = "match_players"
    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_players_match_id_user_id"),
        CheckConstraint(
            in_check("status", MATCH_PLAYER_STATUSES), name="status"
        ),
        Index("ix_match_players_match_id", "match_id"),
        Index("ix_match_players_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pickup_matches.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="joined", server_default="joined"
    )
    attended: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # relationships
    match: Mapped["PickupMatch"] = relationship("PickupMatch", back_populates="players")
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[user_id], lazy="selectin"
    )


class PickupRating(Base):
    """Post-match rating: one player rates another after match completion."""

    __tablename__ = "pickup_ratings"
    __table_args__ = (
        UniqueConstraint(
            "match_id", "rater_id", "rated_user_id",
            name="uq_pickup_ratings_match_rater_rated"
        ),
        CheckConstraint("skill_score BETWEEN 1 AND 5", name="skill_score"),
        CheckConstraint("punctuality_score BETWEEN 1 AND 5", name="punctuality_score"),
        CheckConstraint("rater_id != rated_user_id", name="no_self_rating"),
        Index("ix_pickup_ratings_match_id", "match_id"),
        Index("ix_pickup_ratings_rater_id", "rater_id"),
        Index("ix_pickup_ratings_rated_user_id", "rated_user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pickup_matches.id", ondelete="CASCADE"), nullable=False
    )
    rater_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rated_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    skill_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)       # 1-5
    punctuality_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-5
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # relationships
    match: Mapped["PickupMatch"] = relationship("PickupMatch", foreign_keys=[match_id])
    rater: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[rater_id], lazy="selectin"
    )
    rated_user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[rated_user_id], lazy="selectin"
    )
