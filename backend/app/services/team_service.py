"""Business logic for Team management."""
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, PermissionDenied
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "team"


def _unique_slug(db: Session, name: str, exclude_id: int | None = None) -> str:
    base = _slugify(name)
    slug = base
    counter = 1
    while True:
        q = select(Team).where(Team.slug == slug)
        if exclude_id:
            q = q.where(Team.id != exclude_id)
        if db.scalar(q) is None:
            return slug
        slug = f"{base}-{counter}"
        counter += 1


# ── Team CRUD ──────────────────────────────────────────────────────────────────

def create_team(db: Session, payload: TeamCreate, captain: User) -> Team:
    slug = _unique_slug(db, payload.name)
    team = Team(
        name=payload.name,
        slug=slug,
        sport_id=payload.sport_id,
        captain_id=captain.id,
        description=payload.description,
        logo_url=payload.logo_url,
        city=payload.city,
    )
    db.add(team)
    db.flush()
    # Captain is auto-added as a "captain" member
    db.add(TeamMember(team_id=team.id, user_id=captain.id, role="captain"))
    db.flush()
    db.refresh(team)
    return team


def list_teams(db: Session, sport_id: int | None = None) -> list[Team]:
    q = select(Team).where(Team.is_active == True)  # noqa: E712
    if sport_id:
        q = q.where(Team.sport_id == sport_id)
    return list(db.scalars(q.order_by(Team.name)).all())


def get_team(db: Session, team_id: int) -> Team:
    team = db.get(Team, team_id)
    if team is None or not team.is_active:
        raise NotFoundError("Team not found")
    return team


def get_my_teams(db: Session, user: User) -> list[Team]:
    q = (
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user.id, Team.is_active == True)  # noqa: E712
        .order_by(Team.name)
    )
    return list(db.scalars(q).all())


# ── Membership ─────────────────────────────────────────────────────────────────

def _require_captain(team: Team, user: User) -> None:
    if team.captain_id != user.id and "admin" not in user.role_names:
        raise PermissionDenied("Only the team captain can perform this action")


def add_member(db: Session, team_id: int, user_id: int, actor: User) -> TeamMember:
    team = get_team(db, team_id)
    _require_captain(team, actor)

    # Check user exists
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise NotFoundError("User not found")

    # Check already member
    existing = db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == user_id
        )
    )
    if existing:
        raise ConflictError("User is already a team member")

    member = TeamMember(team_id=team_id, user_id=user_id, role="member")
    db.add(member)
    db.flush()
    db.refresh(member)
    return member


def remove_member(db: Session, team_id: int, user_id: int, actor: User) -> None:
    team = get_team(db, team_id)
    _require_captain(team, actor)

    if user_id == team.captain_id:
        raise BusinessRuleError("Cannot remove the team captain")

    member = db.scalar(
        select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.user_id == user_id
        )
    )
    if member is None:
        raise NotFoundError("Member not found")

    db.delete(member)
    db.flush()
