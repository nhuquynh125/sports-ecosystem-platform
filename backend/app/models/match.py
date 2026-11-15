"""SportArena match tables: tournament_matches, match_events (ERD §6)."""
from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    SmallInteger,
    String,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import in_check

MATCH_STATUSES = ("scheduled", "ongoing", "completed", "cancelled", "postponed")
MATCH_EVENT_TYPES = ("goal", "assist", "yellow_card", "red_card", "own_goal")


class TournamentMatch(Base):
    """A single match within a tournament (may belong to a group)."""

    __tablename__ = "tournament_matches"
    __table_args__ = (
        CheckConstraint(in_check("status", MATCH_STATUSES), name="ck_tournament_matches_status"),
        # Partial unique index on (court_id, match_date, time_slot) WHERE all three are NOT NULL
        # is defined in migration as `uq_tournament_matches_court_date_slot`.
        # A model-level UniqueConstraint is intentionally omitted because SQLAlchemy
        # cannot express partial unique constraints natively.
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False
    )
    group_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tournament_groups.id", ondelete="SET NULL")
    )
    home_team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    court_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("courts.id", ondelete="SET NULL")
    )
    match_date: Mapped[date | None] = mapped_column(Date)
    # time_slot stores wall-clock start time (same convention as CourtBook bookings)
    time_slot: Mapped[time | None] = mapped_column(Time)
    home_score: Mapped[int | None] = mapped_column(Integer)  # NULL = not played yet
    away_score: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # relationships
    tournament: Mapped["Tournament"] = relationship(  # type: ignore[name-defined]
        "Tournament", lazy="selectin"
    )
    group: Mapped["TournamentGroup | None"] = relationship(  # type: ignore[name-defined]
        "TournamentGroup", lazy="selectin"
    )
    home_team: Mapped["Team"] = relationship(  # type: ignore[name-defined]
        "Team", foreign_keys=[home_team_id], lazy="selectin"
    )
    away_team: Mapped["Team"] = relationship(  # type: ignore[name-defined]
        "Team", foreign_keys=[away_team_id], lazy="selectin"
    )
    court: Mapped["Court | None"] = relationship(  # type: ignore[name-defined]
        "Court", lazy="selectin"
    )
    events: Mapped[list["MatchEvent"]] = relationship(
        "MatchEvent", back_populates="match", lazy="selectin", cascade="all, delete-orphan"
    )


class MatchEvent(Base):
    """An in-match event (goal, card, assist…) attributed to a player and team."""

    __tablename__ = "match_events"
    __table_args__ = (
        CheckConstraint(
            in_check("event_type", MATCH_EVENT_TYPES), name="ck_match_events_event_type"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tournament_matches.id", ondelete="CASCADE"), nullable=False
    )
    # player_id is nullable – own goals or manual corrections may lack a linked user
    player_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    minute: Mapped[int | None] = mapped_column(SmallInteger)  # 1-120, nullable for extra time
    notes: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # relationships
    match: Mapped["TournamentMatch"] = relationship("TournamentMatch", back_populates="events")
    player: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[player_id], lazy="selectin"
    )
    team: Mapped["Team"] = relationship(  # type: ignore[name-defined]
        "Team", foreign_keys=[team_id], lazy="selectin"
    )
