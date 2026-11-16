"""SportArena tournament tables: tournaments, tournament_teams, groups (ERD §5)."""
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    REGISTRATION_STATUSES,
    TOURNAMENT_FORMATS,
    TOURNAMENT_STATUSES,
    in_check,
)


class Tournament(Base):
    __tablename__ = "tournaments"
    __table_args__ = (
        CheckConstraint(in_check("status", TOURNAMENT_STATUSES), name="ck_tournaments_status"),
        CheckConstraint(in_check("format", TOURNAMENT_FORMATS), name="ck_tournaments_format"),
        CheckConstraint(
            "max_teams IS NULL OR max_teams >= 2", name="ck_tournaments_max_teams"
        ),
        CheckConstraint(
            "registration_deadline IS NULL OR registration_deadline <= start_date",
            name="ck_tournaments_reg_deadline",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    organizer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    format: Mapped[str] = mapped_column(String(30), nullable=False, default="group_stage")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    max_teams: Mapped[int | None] = mapped_column(SmallInteger)
    prize_pool: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    registration_deadline: Mapped[date | None] = mapped_column(Date)
    rules: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # relationships
    organizer: Mapped["User"] = relationship("User", foreign_keys=[organizer_id], lazy="selectin")  # type: ignore[name-defined]
    sport: Mapped["Sport"] = relationship("Sport", lazy="selectin")  # type: ignore[name-defined]
    registrations: Mapped[list["TournamentTeam"]] = relationship(
        "TournamentTeam", back_populates="tournament", lazy="selectin",
        cascade="all, delete-orphan"
    )
    groups: Mapped[list["TournamentGroup"]] = relationship(
        "TournamentGroup", back_populates="tournament", lazy="selectin",
        cascade="all, delete-orphan"
    )


class TournamentTeam(Base):
    """Junction: a team registered for a tournament (with approval workflow)."""
    __tablename__ = "tournament_teams"
    __table_args__ = (
        UniqueConstraint("tournament_id", "team_id", name="uq_tournament_teams_tournament_team"),
        CheckConstraint(
            in_check("registration_status", REGISTRATION_STATUSES),
            name="ck_tournament_teams_status",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    registration_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    registered_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(String(255))
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # relationships
    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="registrations")
    team: Mapped["Team"] = relationship("Team", lazy="selectin")  # type: ignore[name-defined]
    registrar: Mapped["User"] = relationship("User", foreign_keys=[registered_by], lazy="selectin")  # type: ignore[name-defined]


class TournamentGroup(Base):
    """A named group within a tournament (e.g. 'Group A')."""
    __tablename__ = "tournament_groups"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id", "name", name="uq_tournament_groups_tournament_name"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # relationships
    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="groups")
    group_teams: Mapped[list["GroupTeam"]] = relationship(
        "GroupTeam", back_populates="group", lazy="selectin",
        cascade="all, delete-orphan"
    )


class GroupTeam(Base):
    """Junction: a registered team assigned to a group."""
    __tablename__ = "group_teams"
    __table_args__ = (
        UniqueConstraint(
            "group_id", "tournament_team_id", name="uq_group_teams_group_tt"
        ),
        UniqueConstraint(
            "tournament_id", "tournament_team_id", name="uq_group_teams_tournament_tt"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tournament_groups.id", ondelete="CASCADE"), nullable=False
    )
    tournament_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False
    )
    tournament_team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tournament_teams.id", ondelete="CASCADE"), nullable=False
    )
    seeding: Mapped[int | None] = mapped_column(Integer)

    # relationships
    group: Mapped["TournamentGroup"] = relationship("TournamentGroup", back_populates="group_teams")
    tournament_team: Mapped["TournamentTeam"] = relationship("TournamentTeam", lazy="selectin")
