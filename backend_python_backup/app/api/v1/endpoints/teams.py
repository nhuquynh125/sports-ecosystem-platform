"""Team management endpoints – /api/v1/teams."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, get_current_user, require_role
from app.models.user import User
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.team import TeamCreate, TeamDetailOut, TeamMemberAdd, TeamMemberOut, TeamOut
from app.services import team_service

router = APIRouter(prefix="/teams", tags=["teams"])


def _team_out(team) -> dict:
    """Flatten nested ORM objects to dict for TeamOut / TeamDetailOut."""
    base = {
        "id": team.id,
        "name": team.name,
        "slug": team.slug,
        "sport": {"id": team.sport.id, "name": team.sport.name, "slug": team.sport.slug},
        "captain": {
            "id": team.captain.id,
            "username": team.captain.username,
            "full_name": team.captain.full_name,
            "avatar_url": team.captain.avatar_url,
        },
        "description": team.description,
        "logo_url": team.logo_url,
        "city": team.city,
        "is_active": team.is_active,
        "created_at": team.created_at,
        "member_count": len(team.members),
    }
    return base


def _member_out(m) -> dict:
    return {
        "id": m.id,
        "user_id": m.user_id,
        "username": m.user.username,
        "full_name": m.user.full_name,
        "avatar_url": m.user.avatar_url,
        "role": m.role,
        "joined_at": m.joined_at,
    }


@router.post("", response_model=TeamDetailOut, status_code=201)
def create_team(
    payload: TeamCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Create a new team. The calling user becomes the captain."""
    team = team_service.create_team(db, payload, current_user)
    db.commit()
    db.refresh(team)
    return {**_team_out(team), "members": [_member_out(m) for m in team.members]}


@router.get("", response_model=Page[TeamOut])
def list_teams(
    db: DbSession,
    sport_id: int | None = Query(None),
    params: PaginationParams = Depends(),
):
    """List teams, optionally filtered by sport."""
    teams = team_service.list_teams(db, sport_id=sport_id)
    items = [_team_out(t) for t in teams]
    total = len(items)
    sliced = items[params.offset: params.offset + params.page_size]
    return paginate(sliced, total, params)


@router.get("/me", response_model=list[TeamOut])
def my_teams(db: DbSession, current_user: CurrentUser):
    """Return all teams the current user belongs to."""
    teams = team_service.get_my_teams(db, current_user)
    return [_team_out(t) for t in teams]


@router.get("/{team_id}", response_model=TeamDetailOut)
def get_team(team_id: int, db: DbSession):
    """Get a team by ID including full member list."""
    team = team_service.get_team(db, team_id)
    return {**_team_out(team), "members": [_member_out(m) for m in team.members]}


@router.post("/{team_id}/members", response_model=TeamMemberOut, status_code=201)
def add_member(
    team_id: int,
    payload: TeamMemberAdd,
    db: DbSession,
    current_user: CurrentUser,
):
    """Captain adds a member to their team."""
    member = team_service.add_member(db, team_id, payload.user_id, current_user)
    db.commit()
    db.refresh(member)
    return _member_out(member)


@router.delete("/{team_id}/members/{user_id}", status_code=204)
def remove_member(
    team_id: int,
    user_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    """Captain removes a member from their team."""
    team_service.remove_member(db, team_id, user_id, current_user)
    db.commit()
