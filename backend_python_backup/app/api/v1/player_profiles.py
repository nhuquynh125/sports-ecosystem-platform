from datetime import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import CurrentUser, DbSession, require_role
from app.models import User
from app.models.enums import ROLE_PLAYER
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.player import (
    AvailabilityReplace,
    AvailabilitySlotCreate,
    AvailabilitySlotRead,
    AvailabilitySlotUpdate,
    PlayerProfileCreate,
    PlayerProfileRead,
    PlayerProfileUpdate,
    SkillLevel,
)
from app.services import player_service

router = APIRouter(prefix="/player-profiles", tags=["Player profiles"])

PlayerUser = Annotated[User, Depends(require_role(ROLE_PLAYER))]


@router.post("", response_model=PlayerProfileRead, status_code=201, summary="Create my profile for a sport")
def create_profile(payload: PlayerProfileCreate, user: PlayerUser, db: DbSession):
    """One profile per user and sport (409 if it already exists). Requires the `player` role."""
    return player_service.create_profile(db, user, payload)


@router.get("", response_model=Page[PlayerProfileRead], summary="Search players")
def search_profiles(
    viewer: CurrentUser,
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
    sport_id: int | None = None,
    city: Annotated[str | None, Query(max_length=100, description="Playing area (exact, case-insensitive)")] = None,
    position: Annotated[str | None, Query(max_length=50)] = None,
    skill_level: SkillLevel | None = None,
    user_id: int | None = None,
    day_of_week: Annotated[int | None, Query(ge=1, le=7, description="1=Mon..7=Sun")] = None,
    available_from: Annotated[time | None, Query(description="HH:MM[:SS]")] = None,
    available_to: Annotated[time | None, Query(description="HH:MM[:SS]")] = None,
):
    """FR-SH-03. Hidden profiles and locked accounts are excluded (except your own)."""
    items, total = player_service.search_profiles(
        db,
        viewer,
        params,
        sport_id=sport_id,
        city=city,
        position=position,
        skill_level=skill_level,
        user_id=user_id,
        day_of_week=day_of_week,
        available_from=available_from,
        available_to=available_to,
    )
    return paginate(items, total, params)


@router.get("/me", response_model=list[PlayerProfileRead], summary="My profiles")
def my_profiles(user: CurrentUser, db: DbSession):
    return player_service.list_my_profiles(db, user)


@router.get("/{profile_id}", response_model=PlayerProfileRead, summary="Get a profile")
def get_profile(profile_id: int, viewer: CurrentUser, db: DbSession):
    return player_service.get_viewable_profile(db, profile_id, viewer)


@router.patch("/{profile_id}", response_model=PlayerProfileRead, summary="Update a profile")
def update_profile(profile_id: int, payload: PlayerProfileUpdate, actor: CurrentUser, db: DbSession):
    return player_service.update_profile(db, profile_id, actor, payload)


@router.delete(
    "/{profile_id}", status_code=204, response_class=Response, summary="Delete a profile"
)
def delete_profile(profile_id: int, actor: CurrentUser, db: DbSession):
    player_service.delete_profile(db, profile_id, actor)
    return Response(status_code=204)


# ------------------------------------------------------- weekly availability
@router.get(
    "/{profile_id}/availability",
    response_model=list[AvailabilitySlotRead],
    summary="Weekly availability of a profile",
)
def list_availability(profile_id: int, viewer: CurrentUser, db: DbSession):
    profile = player_service.get_viewable_profile(db, profile_id, viewer)
    return player_service.list_slots(db, profile.id)


@router.post(
    "/{profile_id}/availability",
    response_model=AvailabilitySlotRead,
    status_code=201,
    summary="Add one weekly slot",
)
def add_availability(
    profile_id: int, payload: AvailabilitySlotCreate, actor: CurrentUser, db: DbSession
):
    profile = player_service.get_editable_profile(db, profile_id, actor)
    return player_service.add_slot(db, profile, payload)


@router.put(
    "/{profile_id}/availability",
    response_model=list[AvailabilitySlotRead],
    summary="Replace the whole weekly schedule",
)
def replace_availability(
    profile_id: int, payload: AvailabilityReplace, actor: CurrentUser, db: DbSession
):
    profile = player_service.get_editable_profile(db, profile_id, actor)
    return player_service.replace_slots(db, profile, payload.slots)


@router.patch(
    "/{profile_id}/availability/{slot_id}",
    response_model=AvailabilitySlotRead,
    summary="Update one weekly slot",
)
def update_availability(
    profile_id: int,
    slot_id: int,
    payload: AvailabilitySlotUpdate,
    actor: CurrentUser,
    db: DbSession,
):
    profile = player_service.get_editable_profile(db, profile_id, actor)
    return player_service.update_slot(db, profile, slot_id, payload)


@router.delete(
    "/{profile_id}/availability/{slot_id}",
    status_code=204,
    response_class=Response,
    summary="Delete one weekly slot",
)
def delete_availability(profile_id: int, slot_id: int, actor: CurrentUser, db: DbSession):
    profile = player_service.get_editable_profile(db, profile_id, actor)
    player_service.delete_slot(db, profile, slot_id)
    return Response(status_code=204)
