"""Match results, standings, and top-scorer services."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError, PermissionDenied
from app.schemas.match import MatchResultSubmit, StandingRow, TopScorerRow


# ---------------------------------------------------------------------------
# List matches
# ---------------------------------------------------------------------------

def list_matches(db: Session, tournament_id: int):
    """Return all matches for a tournament ordered by match_date, time_slot."""
    from app.models.match import TournamentMatch

    return list(
        db.scalars(
            select(TournamentMatch)
            .where(TournamentMatch.tournament_id == tournament_id)
            .order_by(TournamentMatch.match_date, TournamentMatch.time_slot)
        ).all()
    )


# ---------------------------------------------------------------------------
# Submit result
# ---------------------------------------------------------------------------

def submit_result(
    db: Session,
    tournament_id: int,
    match_id: int,
    payload: MatchResultSubmit,
    organizer_user,
):
    """Record the final score and events for a match.

    - Verifies the match belongs to the tournament.
    - Checks the caller is the tournament organizer or an admin.
    - Sets home_score, away_score, status='completed'.
    - Replaces existing MatchEvent rows with the submitted ones.
    """
    from app.models.match import MatchEvent, TournamentMatch
    from app.models.tournament import Tournament

    # Fetch match
    match = db.get(TournamentMatch, match_id)
    if match is None or match.tournament_id != tournament_id:
        raise NotFoundError("Match not found in this tournament")

    # Permission check: organizer or admin
    tournament = db.get(Tournament, tournament_id)
    is_admin = "admin" in getattr(organizer_user, "role_names", [])
    if tournament.organizer_id != organizer_user.id and not is_admin:
        raise PermissionDenied("Only the tournament organizer can submit match results")

    # Can only record result for non-cancelled matches
    if match.status == "cancelled":
        raise BusinessRuleError("Cannot submit result for a cancelled match")

    # Set scores and mark completed
    match.home_score = payload.home_score
    match.away_score = payload.away_score
    match.status = "completed"

    # Replace events: delete existing, insert new
    for event in list(match.events):
        db.delete(event)
    db.flush()

    for ev in payload.events:
        db.add(
            MatchEvent(
                match_id=match_id,
                player_id=ev.player_id,
                team_id=ev.team_id,
                event_type=ev.event_type,
                minute=ev.minute,
                notes=ev.notes,
            )
        )

    db.flush()
    db.refresh(match)
    return match


# ---------------------------------------------------------------------------
# Standings
# ---------------------------------------------------------------------------

def compute_standings(db: Session, tournament_id: int) -> list[StandingRow]:
    """Compute group standings for all groups in a tournament.

    For each completed match in a group:
      - Win  → 3 pts for winner
      - Draw → 1 pt each
      - Loss → 0 pts
    Tracks GF, GA, GD.  Sorted: points DESC → GD DESC → GF DESC.
    Returns a flat list of StandingRow across all groups.
    """
    from app.models.match import TournamentMatch
    from app.models.tournament import GroupTeam, TournamentGroup, TournamentTeam

    groups = db.scalars(
        select(TournamentGroup).where(TournamentGroup.tournament_id == tournament_id)
    ).all()

    rows: list[StandingRow] = []

    for group in groups:
        # Collect team_ids in this group
        group_teams = db.scalars(
            select(GroupTeam).where(GroupTeam.group_id == group.id)
        ).all()
        team_ids: set[int] = set()
        tt_to_team: dict[int, int] = {}
        for gt in group_teams:
            tt = db.get(TournamentTeam, gt.tournament_team_id)
            if tt:
                team_ids.add(tt.team_id)
                tt_to_team[gt.tournament_team_id] = tt.team_id

        if not team_ids:
            continue

        # stat buckets
        played: dict[int, int] = defaultdict(int)
        won: dict[int, int] = defaultdict(int)
        drawn: dict[int, int] = defaultdict(int)
        lost: dict[int, int] = defaultdict(int)
        gf: dict[int, int] = defaultdict(int)
        ga: dict[int, int] = defaultdict(int)
        points: dict[int, int] = defaultdict(int)
        team_names: dict[int, str] = {}

        # Fetch completed matches in this group where both teams belong to the group
        matches = db.scalars(
            select(TournamentMatch).where(
                TournamentMatch.tournament_id == tournament_id,
                TournamentMatch.group_id == group.id,
                TournamentMatch.status == "completed",
                TournamentMatch.home_score.is_not(None),
                TournamentMatch.away_score.is_not(None),
            )
        ).all()

        for m in matches:
            if m.home_team_id not in team_ids or m.away_team_id not in team_ids:
                continue  # safety: skip cross-group matches

            h = m.home_team_id
            a = m.away_team_id
            hs = m.home_score  # type: ignore[assignment]
            as_ = m.away_score  # type: ignore[assignment]

            # Cache team names from loaded relationship
            if h not in team_names and m.home_team:
                team_names[h] = m.home_team.name
            if a not in team_names and m.away_team:
                team_names[a] = m.away_team.name

            played[h] += 1
            played[a] += 1
            gf[h] += hs
            gf[a] += as_
            ga[h] += as_
            ga[a] += hs

            if hs > as_:
                won[h] += 1
                lost[a] += 1
                points[h] += 3
            elif hs < as_:
                won[a] += 1
                lost[h] += 1
                points[a] += 3
            else:
                drawn[h] += 1
                drawn[a] += 1
                points[h] += 1
                points[a] += 1

        # Fill names for teams that never played yet
        for tid in team_ids:
            if tid not in team_names:
                # Try to get name from team relationship on any group_team
                for gt in group_teams:
                    tt = db.get(TournamentTeam, gt.tournament_team_id)
                    if tt and tt.team_id == tid and tt.team:
                        team_names[tid] = tt.team.name
                        break
                else:
                    team_names[tid] = f"Team {tid}"

        # Sort and emit
        sorted_teams = sorted(
            team_ids,
            key=lambda tid: (
                -points[tid],
                -(gf[tid] - ga[tid]),  # GD descending
                -gf[tid],
            ),
        )
        for tid in sorted_teams:
            gd = gf[tid] - ga[tid]
            rows.append(
                StandingRow(
                    team_id=tid,
                    team_name=team_names.get(tid, f"Team {tid}"),
                    group_id=group.id,
                    group_name=group.name,
                    played=played[tid],
                    won=won[tid],
                    drawn=drawn[tid],
                    lost=lost[tid],
                    goals_for=gf[tid],
                    goals_against=ga[tid],
                    goal_difference=gd,
                    points=points[tid],
                )
            )

    return rows


# ---------------------------------------------------------------------------
# Top scorers
# ---------------------------------------------------------------------------

def compute_top_scorers(db: Session, tournament_id: int) -> list[TopScorerRow]:
    """Return top scorers (goals only) for the tournament, sorted by goals DESC.

    Queries match_events for event_type='goal', joins to match to scope
    by tournament_id.  Groups by player_id + team_id.
    """
    from app.models.match import MatchEvent, TournamentMatch
    from app.models.team import Team
    from app.models.user import User

    # Aggregate: (player_id, team_id) → goal count
    stmt = (
        select(
            MatchEvent.player_id,
            MatchEvent.team_id,
            func.count(MatchEvent.id).label("goals"),
        )
        .join(TournamentMatch, MatchEvent.match_id == TournamentMatch.id)
        .where(
            TournamentMatch.tournament_id == tournament_id,
            MatchEvent.event_type == "goal",
            MatchEvent.player_id.is_not(None),
        )
        .group_by(MatchEvent.player_id, MatchEvent.team_id)
        .order_by(func.count(MatchEvent.id).desc())
    )

    result = db.execute(stmt).all()

    rows: list[TopScorerRow] = []
    for player_id, team_id, goals in result:
        # Fetch player name
        player = db.get(User, player_id)
        player_name = (
            player.full_name.strip()
            if player and player.full_name
            else (player.username if player else f"Player {player_id}")
        )

        # Fetch team name
        team = db.get(Team, team_id)
        team_name = team.name if team else f"Team {team_id}"

        rows.append(
            TopScorerRow(
                player_id=player_id,
                player_name=player_name,
                team_id=team_id,
                team_name=team_name,
                goals=goals,
            )
        )

    return rows
