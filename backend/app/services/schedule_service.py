"""Schedule service: Circle-Method round-robin fixture generation."""
from __future__ import annotations

from datetime import date, time, timedelta
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError, PermissionDenied
from app.schemas.match import ScheduleGenerateOut, ScheduleGenerateRequest


# ---------------------------------------------------------------------------
# Circle Method algorithm
# ---------------------------------------------------------------------------

class MatchSlot(NamedTuple):
    home_team_id: int
    away_team_id: int
    group_id: int


def circle_method_rounds(team_ids: list[int]) -> list[list[tuple[int, int]]]:
    """Return list of rounds; each round is a list of (home_id, away_id) pairs.

    Handles an odd number of teams by inserting a 'bye' (id=0).
    Each team meets every other team exactly once (round-robin).
    """
    teams = list(team_ids)
    if len(teams) % 2 == 1:
        teams.append(0)  # bye sentinel
    n = len(teams)
    rounds: list[list[tuple[int, int]]] = []
    for _ in range(n - 1):
        round_matches: list[tuple[int, int]] = []
        for i in range(n // 2):
            home = teams[i]
            away = teams[n - 1 - i]
            if home != 0 and away != 0:  # skip byes
                round_matches.append((home, away))
        rounds.append(round_matches)
        # Rotate: keep teams[0] fixed, shift the rest clockwise
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    return rounds


# ---------------------------------------------------------------------------
# Main schedule generation service
# ---------------------------------------------------------------------------

def generate_schedule(
    db: Session,
    tournament_id: int,
    payload: ScheduleGenerateRequest,
    organizer_user,
) -> ScheduleGenerateOut:
    """Generate a round-robin schedule for every group in the tournament.

    Algorithm:
    1. For each group, collect team IDs and run circle_method_rounds().
    2. Flatten all fixture pairs (with group_id) into a work queue.
    3. Assign slots by iterating dates × time_slots × court_ids and picking
       the first slot where neither team is already busy and the court/slot is free.
    4. Bulk-insert TournamentMatch rows; count conflicts_skipped.

    Permission: tournament.organizer_id == organizer_user.id OR admin role.
    Idempotent: existing scheduled (non-completed) matches are deleted first.
    """
    # Deferred imports to avoid circulars at module load
    from app.models.match import TournamentMatch
    from app.models.tournament import GroupTeam, Tournament, TournamentGroup, TournamentTeam

    # --- Fetch tournament & check permission ---
    tournament = db.get(Tournament, tournament_id)
    if tournament is None:
        raise NotFoundError("Tournament not found")

    is_admin = "admin" in getattr(organizer_user, "role_names", [])
    if tournament.organizer_id != organizer_user.id and not is_admin:
        raise PermissionDenied("Only the tournament organizer can generate the schedule")

    # --- Validate payload dates ---
    if payload.end_date < payload.start_date:
        raise BusinessRuleError("end_date must be on or after start_date")
    if not payload.court_ids:
        raise BusinessRuleError("At least one court_id is required")
    if not payload.daily_time_slots:
        raise BusinessRuleError("At least one daily_time_slot is required")

    # --- Parse time slots once ---
    parsed_time_slots: list[time] = []
    for slot_str in payload.daily_time_slots:
        try:
            h, m = slot_str.strip().split(":")
            parsed_time_slots.append(time(int(h), int(m)))
        except (ValueError, AttributeError):
            raise BusinessRuleError(f"Invalid time slot format: '{slot_str}'. Expected HH:MM")

    # --- Delete existing scheduled (non-completed) matches to allow regeneration ---
    existing = db.scalars(
        select(TournamentMatch).where(
            TournamentMatch.tournament_id == tournament_id,
            TournamentMatch.status.in_(["scheduled", "ongoing", "postponed", "cancelled"]),
        )
    ).all()
    for m in existing:
        db.delete(m)
    db.flush()

    # --- Collect all fixture pairs from all groups ---
    groups = db.scalars(
        select(TournamentGroup).where(TournamentGroup.tournament_id == tournament_id)
    ).all()

    all_fixtures: list[MatchSlot] = []
    for group in groups:
        # group_teams → tournament_team_id → team_id
        group_teams = db.scalars(
            select(GroupTeam).where(GroupTeam.group_id == group.id)
        ).all()
        tt_ids = [gt.tournament_team_id for gt in group_teams]
        team_ids: list[int] = []
        for tt_id in tt_ids:
            tt = db.get(TournamentTeam, tt_id)
            if tt is not None:
                team_ids.append(tt.team_id)

        if len(team_ids) < 2:
            continue  # Can't schedule a group with fewer than 2 teams

        rounds = circle_method_rounds(team_ids)
        for round_matches in rounds:
            for home_id, away_id in round_matches:
                all_fixtures.append(MatchSlot(home_id, away_id, group.id))

    # --- Build the slot grid: dates × time_slots × courts ---
    all_dates: list[date] = []
    cur = payload.start_date
    while cur <= payload.end_date:
        all_dates.append(cur)
        cur += timedelta(days=1)

    if not all_dates:
        raise BusinessRuleError("No available dates between start_date and end_date")

    # Tracking structures
    # team_busy_on_date[team_id] = set of dates where that team already has a match
    team_busy_on_date: dict[int, set[date]] = {}
    # used_court_slots = set of (court_id, date, "HH:MM") tuples
    used_court_slots: set[tuple[int, date, str]] = set()

    matches_created = 0
    conflicts_skipped = 0
    new_matches: list[TournamentMatch] = []

    for fixture in all_fixtures:
        home_id = fixture.home_team_id
        away_id = fixture.away_team_id
        group_id = fixture.group_id

        assigned = False
        for d in all_dates:
            if assigned:
                break
            # Check team availability on this date
            home_busy = d in team_busy_on_date.get(home_id, set())
            away_busy = d in team_busy_on_date.get(away_id, set())
            if home_busy or away_busy:
                continue

            for t_slot in parsed_time_slots:
                if assigned:
                    break
                slot_str = t_slot.strftime("%H:%M")

                for court_id in payload.court_ids:
                    slot_key = (court_id, d, slot_str)
                    if slot_key in used_court_slots:
                        continue

                    # Slot is free — assign it
                    team_busy_on_date.setdefault(home_id, set()).add(d)
                    team_busy_on_date.setdefault(away_id, set()).add(d)
                    used_court_slots.add(slot_key)

                    new_matches.append(
                        TournamentMatch(
                            tournament_id=tournament_id,
                            group_id=group_id,
                            home_team_id=home_id,
                            away_team_id=away_id,
                            court_id=court_id,
                            match_date=d,
                            time_slot=t_slot,
                            status="scheduled",
                        )
                    )
                    matches_created += 1
                    assigned = True
                    break  # found a court for this date/slot

        if not assigned:
            conflicts_skipped += 1

    # Bulk insert
    for m in new_matches:
        db.add(m)
    db.flush()

    return ScheduleGenerateOut(
        matches_created=matches_created,
        conflicts_skipped=conflicts_skipped,
    )
