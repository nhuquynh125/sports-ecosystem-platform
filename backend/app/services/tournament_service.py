"""Business logic for Tournament management, registration and groups."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, PermissionDenied
from app.models.team import Team, TeamMember
from app.models.tournament import GroupTeam, Tournament, TournamentGroup, TournamentTeam
from app.models.user import User
from app.schemas.tournament import GroupCreate, RegistrationDecision, TournamentCreate


# ── Tournament CRUD ────────────────────────────────────────────────────────────

def create_tournament(db: Session, payload: TournamentCreate, organizer: User) -> Tournament:
    t = Tournament(
        organizer_id=organizer.id,
        sport_id=payload.sport_id,
        name=payload.name,
        description=payload.description,
        format=payload.format,
        status="open",
        max_teams=payload.max_teams,
        prize_pool=payload.prize_pool,
        location=payload.location,
        start_date=payload.start_date,
        end_date=payload.end_date,
        registration_deadline=payload.registration_deadline,
        rules=payload.rules,
        is_public=payload.is_public,
    )
    db.add(t)
    db.flush()
    db.refresh(t)
    return t


def list_tournaments(
    db: Session,
    sport_id: int | None = None,
    status: str | None = None,
) -> list[Tournament]:
    q = select(Tournament)
    if sport_id:
        q = q.where(Tournament.sport_id == sport_id)
    if status:
        q = q.where(Tournament.status == status)
    return list(db.scalars(q.order_by(Tournament.created_at.desc())).all())


def get_tournament(db: Session, tournament_id: int) -> Tournament:
    t = db.get(Tournament, tournament_id)
    if t is None:
        raise NotFoundError("Tournament not found")
    return t


# ── Registration ───────────────────────────────────────────────────────────────

def register_team(db: Session, tournament_id: int, captain: User) -> TournamentTeam:
    tournament = get_tournament(db, tournament_id)

    if tournament.status not in ("open", "registration_closed"):
        raise BusinessRuleError("Tournament is not accepting registrations")

    # Find the team captained by this user
    team = db.scalar(
        select(Team).where(Team.captain_id == captain.id, Team.is_active == True)  # noqa: E712
    )
    if team is None:
        raise BusinessRuleError("You must be a team captain to register a team")

    # Check sport matches
    if team.sport_id != tournament.sport_id:
        raise BusinessRuleError("Team sport does not match tournament sport")

    # Check already registered
    existing = db.scalar(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.team_id == team.id,
        )
    )
    if existing:
        raise ConflictError("Team is already registered for this tournament")

    # Check capacity
    if tournament.max_teams is not None:
        approved_count = db.scalar(
            select(TournamentTeam)
            .where(
                TournamentTeam.tournament_id == tournament_id,
                TournamentTeam.registration_status == "approved",
            )
        )
        # count instead
        from sqlalchemy import func
        approved_count = db.scalar(
            select(func.count(TournamentTeam.id)).where(
                TournamentTeam.tournament_id == tournament_id,
                TournamentTeam.registration_status == "approved",
            )
        )
        if approved_count >= tournament.max_teams:
            raise BusinessRuleError("Tournament is full")

    reg = TournamentTeam(
        tournament_id=tournament_id,
        team_id=team.id,
        registration_status="pending",
        registered_by=captain.id,
    )
    db.add(reg)
    db.flush()
    db.refresh(reg)
    return reg


def decide_registration(
    db: Session,
    tournament_id: int,
    team_id: int,
    payload: RegistrationDecision,
    organizer: User,
) -> TournamentTeam:
    tournament = get_tournament(db, tournament_id)

    # Only organizer or admin
    if tournament.organizer_id != organizer.id and "admin" not in organizer.role_names:
        raise PermissionDenied("Only the tournament organizer can review registrations")

    reg = db.scalar(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.team_id == team_id,
        )
    )
    if reg is None:
        raise NotFoundError("Registration not found")

    if reg.registration_status != "pending":
        raise BusinessRuleError("Registration has already been decided")

    if payload.action == "approve":
        reg.registration_status = "approved"
    else:
        reg.registration_status = "rejected"
        reg.rejection_reason = payload.rejection_reason

    reg.reviewed_by = organizer.id
    reg.reviewed_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(reg)
    return reg


# ── Groups ─────────────────────────────────────────────────────────────────────

def create_group(
    db: Session,
    tournament_id: int,
    payload: GroupCreate,
    organizer: User,
) -> TournamentGroup:
    tournament = get_tournament(db, tournament_id)

    if tournament.organizer_id != organizer.id and "admin" not in organizer.role_names:
        raise PermissionDenied("Only the tournament organizer can create groups")

    # Duplicate group name check
    existing = db.scalar(
        select(TournamentGroup).where(
            TournamentGroup.tournament_id == tournament_id,
            TournamentGroup.name == payload.name,
        )
    )
    if existing:
        raise ConflictError(f"Group '{payload.name}' already exists in this tournament")

    group = TournamentGroup(
        tournament_id=tournament_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(group)
    db.flush()

    # Assign teams
    for tt_id in payload.team_ids:
        # Verify the tournament_team belongs to this tournament and is approved
        tt = db.get(TournamentTeam, tt_id)
        if tt is None or tt.tournament_id != tournament_id:
            raise NotFoundError(f"TournamentTeam {tt_id} not found in this tournament")
        if tt.registration_status != "approved":
            raise BusinessRuleError(
                f"Team registration {tt_id} must be approved before group assignment"
            )
        # Check not already in another group
        existing_gt = db.scalar(
            select(GroupTeam).where(
                GroupTeam.tournament_id == tournament_id,
                GroupTeam.tournament_team_id == tt_id,
            )
        )
        if existing_gt:
            raise ConflictError(f"Team registration {tt_id} is already assigned to a group")

        db.add(
            GroupTeam(
                group_id=group.id,
                tournament_id=tournament_id,
                tournament_team_id=tt_id,
            )
        )

    db.flush()
    db.refresh(group)
    return group
