"""Player profiles and weekly availability (ERD §3)."""
from datetime import datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
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
from app.models.enums import PREFERRED_SIDES, SKILL_LEVELS, in_check
from app.models.sport import Sport
from app.models.user import User


class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "sport_id", name="uq_player_profiles_user_id_sport_id"),
        CheckConstraint(in_check("skill_level", SKILL_LEVELS), name="skill_level"),
        CheckConstraint(
            "preferred_side IS NULL OR " + in_check("preferred_side", PREFERRED_SIDES),
            name="preferred_side",
        ),
        CheckConstraint("height_cm IS NULL OR height_cm > 0", name="height_cm"),
        CheckConstraint("weight_kg IS NULL OR weight_kg > 0", name="weight_kg"),
        Index("ix_player_profiles_sport_city_level", "sport_id", "city", "skill_level"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[str | None] = mapped_column(String(50))
    skill_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="beginner", server_default="beginner"
    )
    preferred_side: Mapped[str | None] = mapped_column(String(10))
    height_cm: Mapped[int | None] = mapped_column(SmallInteger)
    weight_kg: Mapped[int | None] = mapped_column(SmallInteger)
    city: Mapped[str | None] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text)
    is_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    sport: Mapped[Sport] = relationship(Sport, lazy="joined")
    user: Mapped[User] = relationship(User, lazy="joined")


class PlayerAvailability(Base):
    __tablename__ = "player_availability"
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 1 AND 7", name="day_of_week"),
        CheckConstraint("end_time > start_time", name="time_order"),
        Index("ix_player_availability_profile_day", "player_profile_id", "day_of_week"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    player_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1=Mon .. 7=Sun
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
