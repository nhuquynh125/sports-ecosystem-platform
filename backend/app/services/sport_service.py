"""Sports catalogue (FR-CORE-08)."""
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.core.utils import escape_like, slugify
from app.models import PlayerProfile, Sport
from app.schemas.sport import SportCreate, SportUpdate


def list_sports(db: Session, include_inactive: bool = False, q: str | None = None) -> list[Sport]:
    stmt = select(Sport).order_by(Sport.name)
    if not include_inactive:
        stmt = stmt.where(Sport.is_active.is_(True))
    if q:
        stmt = stmt.where(Sport.name.ilike(f"%{escape_like(q.strip())}%", escape="\\"))
    return list(db.scalars(stmt).all())


def get_sport(db: Session, sport_id: int, active_only: bool = False) -> Sport:
    sport = db.get(Sport, sport_id)
    if sport is None or (active_only and not sport.is_active):
        raise NotFoundError("Sport not found")
    return sport


def _ensure_unique(db: Session, name: str, slug: str, exclude_id: int | None = None) -> None:
    stmt = select(Sport.name, Sport.slug).where(
        or_(func.lower(Sport.name) == name.lower(), Sport.slug == slug)
    )
    if exclude_id is not None:
        stmt = stmt.where(Sport.id != exclude_id)
    row = db.execute(stmt).first()
    if row is not None:
        if row.name.lower() == name.lower():
            raise ConflictError("Sport name already exists")
        raise ConflictError("Sport slug already exists")


def create_sport(db: Session, data: SportCreate) -> Sport:
    slug = data.slug or slugify(data.name)
    if not slug:
        raise UnprocessableError("slug: could not be generated from the name")
    _ensure_unique(db, data.name, slug)
    sport = Sport(
        name=data.name,
        slug=slug,
        description=data.description,
        icon_url=data.icon_url,
        is_active=data.is_active,
    )
    db.add(sport)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Sport name or slug already exists") from None
    db.refresh(sport)
    return sport


def update_sport(db: Session, sport_id: int, data: SportUpdate) -> Sport:
    sport = get_sport(db, sport_id)
    changes = data.model_dump(exclude_unset=True)
    _ensure_unique(
        db,
        changes.get("name", sport.name),
        changes.get("slug", sport.slug),
        exclude_id=sport.id,
    )
    for field, value in changes.items():
        setattr(sport, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Sport name or slug already exists") from None
    db.refresh(sport)
    return sport


def delete_sport(db: Session, sport_id: int) -> None:
    sport = get_sport(db, sport_id)
    in_use = db.scalar(
        select(func.count(PlayerProfile.id)).where(PlayerProfile.sport_id == sport.id)
    )
    if in_use:
        raise ConflictError("Sport is in use; deactivate it instead")
    try:
        db.delete(sport)
        db.commit()
    except IntegrityError:  # referenced by a later module (courts, tournaments, ...)
        db.rollback()
        raise ConflictError("Sport is in use; deactivate it instead") from None
