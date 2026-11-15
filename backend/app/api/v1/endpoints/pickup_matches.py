"""SportHub pickup-match REST endpoints (Module 3).

Routes:
  POST   /matches                      – create a pickup match
  GET    /matches                      – list / filter pickup matches
  GET    /matches/{id}                 – get one match
  POST   /matches/{id}/join            – join a match
  DELETE /matches/{id}/leave           – leave a match
  POST   /matches/{id}/ratings         – rate a teammate after completion
  POST   /ai/smart-match               – AI player recommendations
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.pickup_match import (
    MatchPlayerOut,
    PickupMatchCreate,
    PickupMatchOut,
    RatingCreate,
    RatingOut,
    SmartMatchRequest,
    SmartMatchResponse,
)
from app.services import pickup_match_service

router = APIRouter(tags=["SportHub – Pickup Matches"])


# ---------------------------------------------------------------------------
# Pickup Matches CRUD
# ---------------------------------------------------------------------------

@router.post(
    "/matches",
    response_model=PickupMatchOut,
    status_code=201,
    summary="Create a pickup match",
)
def create_match(
    payload: PickupMatchCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    match = pickup_match_service.create_match(db, payload, current_user)
    db.commit()
    db.refresh(match)
    return PickupMatchOut.from_model(match)


@router.get(
    "/matches",
    response_model=list[PickupMatchOut],
    summary="List pickup matches (filterable)",
)
def list_matches(
    db: DbSession,
    sport_id: int | None = Query(None),
    area: str | None = Query(None, description="City or district (partial match)"),
    skill_level: str | None = Query(None, description="beginner|intermediate|advanced|pro"),
    match_date: date | None = Query(None),
    status: str | None = Query("open", description="Filter by status (default: open)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    matches = pickup_match_service.list_matches(
        db,
        sport_id=sport_id,
        area=area,
        skill_level=skill_level,
        match_date=match_date,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [PickupMatchOut.from_model(m) for m in matches]


@router.get(
    "/matches/{match_id}",
    response_model=PickupMatchOut,
    summary="Get a single pickup match",
)
def get_match(match_id: int, db: DbSession):
    match = pickup_match_service.get_match(db, match_id)
    return PickupMatchOut.from_model(match)


# ---------------------------------------------------------------------------
# Join / Leave
# ---------------------------------------------------------------------------

@router.post(
    "/matches/{match_id}/join",
    response_model=MatchPlayerOut,
    status_code=201,
    summary="Join a pickup match",
)
def join_match(match_id: int, db: DbSession, current_user: CurrentUser):
    player_row = pickup_match_service.join_match(db, match_id, current_user)
    db.commit()
    db.refresh(player_row)
    return player_row


@router.delete(
    "/matches/{match_id}/leave",
    status_code=204,
    summary="Leave a pickup match",
)
def leave_match(match_id: int, db: DbSession, current_user: CurrentUser):
    pickup_match_service.leave_match(db, match_id, current_user)
    db.commit()


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------

@router.post(
    "/matches/{match_id}/ratings",
    response_model=RatingOut,
    status_code=201,
    summary="Rate a player after match completion",
)
def rate_player(
    match_id: int,
    payload: RatingCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    rating = pickup_match_service.create_rating(db, match_id, payload, current_user)
    db.commit()
    db.refresh(rating)
    return rating


# ---------------------------------------------------------------------------
# AI Smart Match
# ---------------------------------------------------------------------------

@router.post(
    "/ai/smart-match",
    response_model=SmartMatchResponse,
    summary="AI Smart Match v1 – ranked player recommendations",
    tags=["AI"],
)
def smart_match(payload: SmartMatchRequest, db: DbSession):
    from app.ai.smart_match import recommend_players
    return recommend_players(db, payload.match_id, top_n=payload.top_n)
