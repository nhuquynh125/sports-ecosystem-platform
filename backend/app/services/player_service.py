"""Player profiles and weekly availability (UC-SH-01, FR-SH-01..03)."""
from datetime import time

from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    PermissionDenied,
    UnprocessableError,
)
from app.core.utils import escape_like
from app.models import PlayerAvailability, PlayerProfile, Sport, User
from app.models.enums import ROLE_ADMIN
from app.schemas.common import PaginationParams
from app.schemas.player import (
    AvailabilitySlotCreate,
    AvailabilitySlotUpdate,
    PlayerProfileCreate,
    PlayerProfileUpdate,
)


def _is_admin(user: User) -> bool:
    return ROLE_ADMIN in user.role_names


# ------------------------------------------------------------------ profiles
def create_profile(db: Session, user: User, data: PlayerProfileCreate) -> PlayerProfile:
    sport = db.get(Sport, data.sport_id)
    if sport is None:
        raise NotFoundError("Sport not found")
    if not sport.is_active:
        raise BusinessRuleError("Sport is not active")
    already = db.scalar(
        select(PlayerProfile.id).where(
            PlayerProfile.user_id == user.id, PlayerProfile.sport_id == data.sport_id
        )
    )
    if already is not None:
        raise ConflictError("A profile for this sport already exists")

    profile = PlayerProfile(user_id=user.id, **data.model_dump())
    db.add(profile)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("A profile for this sport already exists") from None
    db.refresh(profile)
    return profile


def get_profile(db: Session, profile_id: int) -> PlayerProfile:
    profile = db.get(PlayerProfile, profile_id)
    if profile is None:
        raise NotFoundError("Player profile not found")
    return profile


def get_viewable_profile(db: Session, profile_id: int, viewer: User) -> PlayerProfile:
    profile = get_profile(db, profile_id)
    if profile.user_id != viewer.id and not _is_admin(viewer):
        if not profile.is_visible or not profile.user.is_active:
            raise NotFoundError("Player profile not found")  # do not reveal hidden profiles
    return profile


def get_editable_profile(db: Session, profile_id: int, actor: User) -> PlayerProfile:
    profile = get_profile(db, profile_id)
    if profile.user_id != actor.id and not _is_admin(actor):
        raise PermissionDenied()
    return profile


def list_my_profiles(db: Session, user: User) -> list[PlayerProfile]:
    return list(
        db.scalars(
            select(PlayerProfile)
            .where(PlayerProfile.user_id == user.id)
            .order_by(PlayerProfile.created_at, PlayerProfile.id)
        ).all()
    )


def search_profiles(
    db: Session,
    viewer: User,
    params: PaginationParams,
    *,
    sport_id: int | None = None,
    city: str | None = None,
    position: str | None = None,
    skill_level: str | None = None,
    user_id: int | None = None,
    day_of_week: int | None = None,
    available_from: time | None = None,
    available_to: time | None = None,
) -> tuple[list[PlayerProfile], int]:
    """FR-SH-03: search by sport, area, position, level and availability overlap."""
    filters = [User.is_active.is_(True)]
    if not _is_admin(viewer):
        filters.append(or_(PlayerProfile.is_visible.is_(True), PlayerProfile.user_id == viewer.id))
    if sport_id is not None:
        filters.append(PlayerProfile.sport_id == sport_id)
    if city:
        filters.append(func.lower(PlayerProfile.city) == city.strip().lower())
    if position:
        pattern = f"%{escape_like(position.strip())}%"
        filters.append(PlayerProfile.position.ilike(pattern, escape="\\"))
    if skill_level:
        filters.append(PlayerProfile.skill_level == skill_level)
    if user_id is not None:
        filters.append(PlayerProfile.user_id == user_id)

    if day_of_week is not None or available_from is not None or available_to is not None:
        # A slot overlaps the wanted window [from, to) iff slot.start < to AND slot.end > from.
        conditions = [PlayerAvailability.player_profile_id == PlayerProfile.id]
        if day_of_week is not None:
            conditions.append(PlayerAvailability.day_of_week == day_of_week)
        if available_from is not None:
            conditions.append(PlayerAvailability.end_time > available_from)
        if available_to is not None:
            conditions.append(PlayerAvailability.start_time < available_to)
        filters.append(exists().where(and_(*conditions)))

    total = (
        db.scalar(
            select(func.count(PlayerProfile.id))
            .select_from(PlayerProfile)
            .join(User, User.id == PlayerProfile.user_id)
            .where(*filters)
        )
        or 0
    )
    items = db.scalars(
        select(PlayerProfile)
        .join(User, User.id == PlayerProfile.user_id)
        .where(*filters)
        .order_by(PlayerProfile.created_at.desc(), PlayerProfile.id.desc())
        .limit(params.page_size)
        .offset(params.offset)
    ).all()
    return list(items), total


def update_profile(
    db: Session, profile_id: int, actor: User, data: PlayerProfileUpdate
) -> PlayerProfile:
    profile = get_editable_profile(db, profile_id, actor)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db: Session, profile_id: int, actor: User) -> None:
    profile = get_editable_profile(db, profile_id, actor)
    db.delete(profile)  # availability rows go with it (ON DELETE CASCADE)
    db.commit()


# -------------------------------------------------------------- availability
def _overlaps(a_start: time, a_end: time, b_start: time, b_end: time) -> bool:
    return a_start < b_end and b_start < a_end  # half-open intervals


def _assert_free(
    existing: list[PlayerAvailability], day: int, start: time, end: time
) -> None:
    for slot in existing:
        if slot.day_of_week == day and _overlaps(slot.start_time, slot.end_time, start, end):
            raise UnprocessableError("Availability window overlaps an existing window")


def list_slots(db: Session, profile_id: int) -> list[PlayerAvailability]:
    return list(
        db.scalars(
            select(PlayerAvailability)
            .where(PlayerAvailability.player_profile_id == profile_id)
            .order_by(
                PlayerAvailability.day_of_week, PlayerAvailability.start_time, PlayerAvailability.id
            )
        ).all()
    )


def add_slot(
    db: Session, profile: PlayerProfile, data: AvailabilitySlotCreate
) -> PlayerAvailability:
    _assert_free(list_slots(db, profile.id), data.day_of_week, data.start_time, data.end_time)
    slot = PlayerAvailability(
        player_profile_id=profile.id,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


def _get_slot(db: Session, profile: PlayerProfile, slot_id: int) -> PlayerAvailability:
    slot = db.get(PlayerAvailability, slot_id)
    if slot is None or slot.player_profile_id != profile.id:
        raise NotFoundError("Availability slot not found")
    return slot


def update_slot(
    db: Session, profile: PlayerProfile, slot_id: int, data: AvailabilitySlotUpdate
) -> PlayerAvailability:
    slot = _get_slot(db, profile, slot_id)
    changes = data.model_dump(exclude_unset=True)
    day = changes.get("day_of_week", slot.day_of_week)
    start = changes.get("start_time", slot.start_time)
    end = changes.get("end_time", slot.end_time)
    if end <= start:
        raise UnprocessableError("end_time: must be after start_time")
    others = [s for s in list_slots(db, profile.id) if s.id != slot.id]
    _assert_free(others, day, start, end)
    slot.day_of_week, slot.start_time, slot.end_time = day, start, end
    db.commit()
    db.refresh(slot)
    return slot


def delete_slot(db: Session, profile: PlayerProfile, slot_id: int) -> None:
    slot = _get_slot(db, profile, slot_id)
    db.delete(slot)
    db.commit()


def replace_slots(
    db: Session, profile: PlayerProfile, slots: list[AvailabilitySlotCreate]
) -> list[PlayerAvailability]:
    for index, first in enumerate(slots):
        for second in slots[index + 1 :]:
            if first.day_of_week == second.day_of_week and _overlaps(
                first.start_time, first.end_time, second.start_time, second.end_time
            ):
                raise UnprocessableError("slots: availability windows must not overlap")
    db.execute(delete(PlayerAvailability).where(PlayerAvailability.player_profile_id == profile.id))
    for slot in slots:
        db.add(
            PlayerAvailability(
                player_profile_id=profile.id,
                day_of_week=slot.day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
            )
        )
    db.commit()
    return list_slots(db, profile.id)
