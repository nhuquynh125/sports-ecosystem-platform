"""SportHub pickup-match business logic (Module 3)."""
from __future__ import annotations

from datetime import date, time
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, PermissionDenied
from app.models.notification import Notification
from app.models.pickup_match import MatchPlayer, PickupMatch, PickupRating
from app.schemas.pickup_match import PickupMatchCreate, RatingCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_match_or_404(db: Session, match_id: int) -> PickupMatch:
    match = db.get(PickupMatch, match_id)
    if match is None:
        raise NotFoundError("Pickup match not found")
    return match


def _parse_time(time_str: str) -> time:
    h, m = map(int, time_str.split(":"))
    return time(h, m)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_match(db: Session, payload: PickupMatchCreate, host_user) -> PickupMatch:
    """Create a new pickup match and auto-enroll the host."""
    match = PickupMatch(
        host_id=host_user.id,
        sport_id=payload.sport_id,
        venue_id=payload.venue_id,
        area=payload.area,
        skill_level=payload.skill_level,
        match_date=payload.match_date,
        time_slot=_parse_time(payload.time_slot),
        max_players=payload.max_players,
        description=payload.description,
        status="open",
    )
    db.add(match)
    db.flush()

    # Auto-enroll host as participant
    db.add(MatchPlayer(match_id=match.id, user_id=host_user.id, status="joined"))
    db.flush()
    db.refresh(match)
    return match


def list_matches(
    db: Session,
    sport_id: int | None = None,
    area: str | None = None,
    skill_level: str | None = None,
    match_date: date | None = None,
    status: str | None = "open",
    limit: int = 50,
    offset: int = 0,
) -> list[PickupMatch]:
    stmt = select(PickupMatch)
    if sport_id is not None:
        stmt = stmt.where(PickupMatch.sport_id == sport_id)
    if area:
        stmt = stmt.where(PickupMatch.area.ilike(f"%{area}%"))
    if skill_level:
        stmt = stmt.where(PickupMatch.skill_level == skill_level)
    if match_date:
        stmt = stmt.where(PickupMatch.match_date == match_date)
    if status:
        stmt = stmt.where(PickupMatch.status == status)
    stmt = stmt.order_by(PickupMatch.match_date, PickupMatch.time_slot).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_match(db: Session, match_id: int) -> PickupMatch:
    return _get_match_or_404(db, match_id)


# ---------------------------------------------------------------------------
# Join / Leave
# ---------------------------------------------------------------------------

def join_match(db: Session, match_id: int, user) -> MatchPlayer:
    """Add `user` to the match roster; enforces capacity and duplicate checks."""
    match = _get_match_or_404(db, match_id)

    if match.status not in ("open", "full"):
        raise BusinessRuleError(f"Cannot join a match with status '{match.status}'")

    # Duplicate check
    existing = db.scalar(
        select(MatchPlayer).where(
            MatchPlayer.match_id == match_id,
            MatchPlayer.user_id == user.id,
            MatchPlayer.status == "joined",
        )
    )
    if existing:
        raise ConflictError("You have already joined this match")

    # Capacity check
    if match.current_player_count >= match.max_players:
        raise BusinessRuleError("Match is full – no more players can join")

    # Re-join: update existing left/removed row
    any_row = db.scalar(
        select(MatchPlayer).where(
            MatchPlayer.match_id == match_id,
            MatchPlayer.user_id == user.id,
        )
    )
    if any_row:
        any_row.status = "joined"
        db.flush()
        player_row = any_row
    else:
        player_row = MatchPlayer(match_id=match_id, user_id=user.id, status="joined")
        db.add(player_row)
        db.flush()

    # Update match status
    new_count = match.current_player_count
    if new_count >= match.max_players and match.status == "open":
        match.status = "full"
        db.flush()

    # Notify host (not when host joins their own match)
    if match.host_id != user.id:
        db.add(Notification(
            user_id=match.host_id,
            type="match_join",
            title="New player joined your match",
            body=(
                f"{user.full_name} joined your {match.sport.name} pickup match "
                f"on {match.match_date.strftime('%d/%m/%Y')} at {match.area}."
            ),
            data={"match_id": match.id, "deep_link": f"/matches/{match.id}"},
        ))
        db.flush()

    db.refresh(player_row)
    return player_row


def leave_match(db: Session, match_id: int, user) -> None:
    """Remove `user` from the match."""
    match = _get_match_or_404(db, match_id)

    if match.status in ("completed", "cancelled"):
        raise BusinessRuleError("Cannot leave a completed or cancelled match")

    if match.host_id == user.id:
        raise BusinessRuleError(
            "The host cannot leave their own match. Cancel the match instead."
        )

    row = db.scalar(
        select(MatchPlayer).where(
            MatchPlayer.match_id == match_id,
            MatchPlayer.user_id == user.id,
            MatchPlayer.status == "joined",
        )
    )
    if row is None:
        raise NotFoundError("You are not currently in this match")

    row.status = "left"
    db.flush()

    # Reopen if was full
    if match.status == "full":
        match.status = "open"
        db.flush()


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------

def create_rating(
    db: Session, match_id: int, payload: RatingCreate, rater_user
) -> PickupRating:
    """Allow a match participant to rate a teammate/opponent post-completion."""
    match = _get_match_or_404(db, match_id)

    if match.status != "completed":
        raise BusinessRuleError("Ratings can only be submitted after the match is completed")

    # Rater must have participated
    rater_row = db.scalar(
        select(MatchPlayer).where(
            MatchPlayer.match_id == match_id,
            MatchPlayer.user_id == rater_user.id,
        )
    )
    if rater_row is None:
        raise PermissionDenied("Only match participants can submit ratings")

    # Rated user must have participated
    rated_row = db.scalar(
        select(MatchPlayer).where(
            MatchPlayer.match_id == match_id,
            MatchPlayer.user_id == payload.rated_user_id,
        )
    )
    if rated_row is None:
        raise BusinessRuleError("The rated user did not participate in this match")

    if payload.rated_user_id == rater_user.id:
        raise BusinessRuleError("You cannot rate yourself")

    # Duplicate check
    existing = db.scalar(
        select(PickupRating).where(
            PickupRating.match_id == match_id,
            PickupRating.rater_id == rater_user.id,
            PickupRating.rated_user_id == payload.rated_user_id,
        )
    )
    if existing:
        raise ConflictError("You have already rated this player for this match")

    rating = PickupRating(
        match_id=match_id,
        rater_id=rater_user.id,
        rated_user_id=payload.rated_user_id,
        skill_score=payload.skill_score,
        punctuality_score=payload.punctuality_score,
        comment=payload.comment,
    )
    db.add(rating)
    db.flush()
    db.refresh(rating)
    return rating


# ---------------------------------------------------------------------------
# Aggregated stats helpers (used by Smart Match AI)
# ---------------------------------------------------------------------------

def get_user_avg_rating(db: Session, user_id: int) -> float:
    """Average skill_score across all ratings received by this user (0.0 if none)."""
    result = db.scalar(
        select(func.avg(PickupRating.skill_score)).where(
            PickupRating.rated_user_id == user_id
        )
    )
    return float(result) if result is not None else 0.0


def get_user_on_time_rate(db: Session, user_id: int) -> float:
    """Fraction of completed matches attended (on-time rate). 0.0 if no history."""
    total = db.scalar(
        select(func.count(MatchPlayer.id)).where(
            MatchPlayer.user_id == user_id,
            MatchPlayer.status == "joined",
        )
    ) or 0

    attended = db.scalar(
        select(func.count(MatchPlayer.id)).where(
            MatchPlayer.user_id == user_id,
            MatchPlayer.attended == True,  # noqa: E712
        )
    ) or 0

    return float(attended) / float(total) if total > 0 else 0.0
