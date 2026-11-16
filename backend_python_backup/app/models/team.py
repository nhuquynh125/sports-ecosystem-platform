"""SportArena team tables: teams, team_members (ERD §5)."""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TEAM_MEMBER_ROLES, in_check


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("slug", name="uq_teams_slug"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(110), nullable=False)
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id", ondelete="RESTRICT"), nullable=False
    )
    captain_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # relationships
    sport: Mapped["Sport"] = relationship("Sport", lazy="selectin")  # type: ignore[name-defined]
    captain: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[captain_id], lazy="selectin"
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="team", lazy="selectin",
        cascade="all, delete-orphan"
    )


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        CheckConstraint(
            in_check("role", TEAM_MEMBER_ROLES), name="ck_team_members_role"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # relationships
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")  # type: ignore[name-defined]
