"""Tournament management endpoints – /api/v1/tournaments."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, get_current_user, require_role
from app.models.user import User
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.tournament import (
    GroupCreate,
    GroupOut,
    RegistrationDecision,
    RegistrationOut,
    TournamentCreate,
    TournamentDetailOut,
    TournamentOut,
)
from app.services import tournament_service

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def _sport_ref(sport) -> dict:
    return {"id": sport.id, "name": sport.name, "slug": sport.slug}


def _organizer_ref(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
    }


def _team_ref(team) -> dict:
    return {"id": team.id, "name": team.name, "slug": team.slug, "logo_url": team.logo_url}


def _reg_out(reg) -> dict:
    return {
        "id": reg.id,
        "team": _team_ref(reg.team),
        "registration_status": reg.registration_status,
        "registered_at": reg.registered_at,
        "reviewed_at": reg.reviewed_at,
        "rejection_reason": reg.rejection_reason,
    }


def _group_team_out(gt) -> dict:
    return {
        "id": gt.id,
        "tournament_team_id": gt.tournament_team_id,
        "team": _team_ref(gt.tournament_team.team),
        "seeding": gt.seeding,
    }


def _group_out(g) -> dict:
    return {
        "id": g.id,
        "name": g.name,
        "description": g.description,
        "created_at": g.created_at,
        "teams": [_group_team_out(gt) for gt in g.group_teams],
    }


def _tournament_out(t) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "sport": _sport_ref(t.sport),
        "organizer": _organizer_ref(t.organizer),
        "description": t.description,
        "format": t.format,
        "status": t.status,
        "max_teams": t.max_teams,
        "prize_pool": t.prize_pool,
        "location": t.location,
        "start_date": t.start_date,
        "end_date": t.end_date,
        "registration_deadline": t.registration_deadline,
        "is_public": t.is_public,
        "registered_team_count": len(t.registrations),
        "created_at": t.created_at,
    }


@router.post(
    "",
    response_model=TournamentOut,
    status_code=201,
    dependencies=[Depends(require_role(["organizer", "admin"]))],
)
def create_tournament(
    payload: TournamentCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Organizer or admin creates a new tournament."""
    t = tournament_service.create_tournament(db, payload, current_user)
    db.commit()
    db.refresh(t)
    return _tournament_out(t)


@router.get("", response_model=Page[TournamentOut])
def list_tournaments(
    db: DbSession,
    sport_id: int | None = Query(None, description="Filter by sport ID"),
    status: str | None = Query(None, description="Filter by status"),
    params: PaginationParams = Depends(),
):
    """List tournaments, optionally filtered by sport and/or status."""
    tournaments = tournament_service.list_tournaments(db, sport_id=sport_id, status=status)
    items = [_tournament_out(t) for t in tournaments]
    total = len(items)
    sliced = items[params.offset: params.offset + params.page_size]
    return paginate(sliced, total, params)


@router.get("/{tournament_id}", response_model=TournamentDetailOut)
def get_tournament(tournament_id: int, db: DbSession):
    """Get a tournament with registered teams and groups."""
    t = tournament_service.get_tournament(db, tournament_id)
    return {
        **_tournament_out(t),
        "rules": t.rules,
        "registrations": [_reg_out(r) for r in t.registrations],
        "groups": [_group_out(g) for g in t.groups],
    }


@router.post("/{tournament_id}/register", response_model=RegistrationOut, status_code=201)
def register_team(
    tournament_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    """Team captain registers their team for the tournament."""
    reg = tournament_service.register_team(db, tournament_id, current_user)
    db.commit()
    db.refresh(reg)
    return _reg_out(reg)


@router.patch(
    "/{tournament_id}/registrations/{team_id}",
    response_model=RegistrationOut,
)
def decide_registration(
    tournament_id: int,
    team_id: int,
    payload: RegistrationDecision,
    db: DbSession,
    current_user: CurrentUser,
):
    """Organizer approves or rejects a team registration."""
    reg = tournament_service.decide_registration(
        db, tournament_id, team_id, payload, current_user
    )
    db.commit()
    db.refresh(reg)
    return _reg_out(reg)


@router.post("/{tournament_id}/groups", response_model=GroupOut, status_code=201)
def create_group(
    tournament_id: int,
    payload: GroupCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Organizer creates a group and assigns approved teams into it."""
    group = tournament_service.create_group(db, tournament_id, payload, current_user)
    db.commit()
    db.refresh(group)
    return _group_out(group)
