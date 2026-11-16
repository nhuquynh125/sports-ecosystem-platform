"""
Step 8 Verification Script — SportArena Part 2 (Backend & Scheduling Algorithm)

Tests:
  1. alembic upgrade head (migration 0004 tournament_matches + match_events)
  2. python -m scripts.seed (all seed data including seed_matches)
  3. Full scheduling scenario: 12 teams / 3 groups / min-3-matches per team
     a. No team plays 2 matches on the same day
     b. No (court_id, match_date, time_slot) collision
     c. Every team plays >= min_matches_per_team matches
  4. Submit match results (scores + events) → verify standings math
  5. Top-scorers aggregation

Runs against an embedded PostgreSQL instance so no external DB is required.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def run(cmd: list, env: dict) -> int:
    print(f">>> {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env, capture_output=False)
    return result.returncode


def _fail(msg: str) -> None:
    print(f"\n❌  FAIL: {msg}")
    sys.exit(1)


def verify_schedule(db, tournament_id: int, court_ids: list[int], min_matches: int) -> None:
    """Assert constraint satisfaction for a generated schedule."""
    from collections import defaultdict
    from sqlalchemy import select
    from app.models.match import TournamentMatch

    matches = list(
        db.scalars(
            select(TournamentMatch).where(TournamentMatch.tournament_id == tournament_id)
        ).all()
    )

    if not matches:
        _fail("No matches were generated")

    # --- Constraint 1: no team plays twice on the same date -----------------
    team_dates: dict[int, list] = defaultdict(list)
    for m in matches:
        if m.match_date is not None:
            team_dates[m.home_team_id].append(m.match_date)
            team_dates[m.away_team_id].append(m.match_date)

    for team_id, dates in team_dates.items():
        if len(dates) != len(set(dates)):
            _fail(f"Team {team_id} has 2+ matches on the same date: {dates}")

    print(f"  ✅ No team plays 2 matches on the same day  ({len(matches)} matches total)")

    # --- Constraint 2: no (court, date, slot) collision --------------------
    slot_keys: list[tuple] = []
    for m in matches:
        if m.court_id and m.match_date and m.time_slot:
            key = (m.court_id, m.match_date, m.time_slot)
            slot_keys.append(key)

    if len(slot_keys) != len(set(slot_keys)):
        duplicates = [k for k in set(slot_keys) if slot_keys.count(k) > 1]
        _fail(f"Court/date/slot collision detected: {duplicates[:3]}")

    print("  ✅ No (court, date, slot) collisions")

    # --- Constraint 3: each team plays >= min_matches_per_team -------------
    match_count: dict[int, int] = defaultdict(int)
    for m in matches:
        match_count[m.home_team_id] += 1
        match_count[m.away_team_id] += 1

    for team_id, cnt in match_count.items():
        if cnt < min_matches:
            _fail(f"Team {team_id} has only {cnt} match(es), need >= {min_matches}")

    min_actual = min(match_count.values()) if match_count else 0
    max_actual = max(match_count.values()) if match_count else 0
    print(f"  ✅ All teams play >= {min_matches} matches  (range: {min_actual}–{max_actual})")


def verify_standings_math(db, tournament_id: int) -> None:
    """Submit deterministic results and verify standings computation."""
    from sqlalchemy import select
    from app.models.match import TournamentMatch
    from app.services.match_service import compute_standings

    matches = list(
        db.scalars(
            select(TournamentMatch)
            .where(
                TournamentMatch.tournament_id == tournament_id,
                TournamentMatch.status == "scheduled",
            )
            .limit(6)  # pick first 6 for deterministic test
        ).all()
    )

    if not matches:
        print("  ⚠️  No scheduled matches to test standings math against; skipping")
        return

    # Submit deterministic scores: home wins 2-0 for all 6
    for m in matches:
        m.home_score = 2
        m.away_score = 0
        m.status = "completed"
    db.flush()

    rows = compute_standings(db, tournament_id)
    if not rows:
        _fail("compute_standings returned no rows after completing matches")

    # Validate points arithmetic
    for row in rows:
        expected_pts = row.won * 3 + row.drawn
        if row.points != expected_pts:
            _fail(
                f"Points mismatch for team {row.team_id}: "
                f"got {row.points}, expected {expected_pts}"
            )
        if row.goal_difference != row.goals_for - row.goals_against:
            _fail(f"GD mismatch for team {row.team_id}")

    print(
        f"  ✅ Standings math correct for {len(rows)} team-rows  "
        f"(sample: {rows[0].team_name} — {rows[0].points}pts, "
        f"GD {rows[0].goal_difference:+d})"
    )

    # Verify sort order: descending points, then GD, then GF
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        if a.group_id != b.group_id:
            continue  # different groups are independent
        if (a.points, a.goal_difference, a.goals_for) < (
            b.points,
            b.goal_difference,
            b.goals_for,
        ):
            _fail(
                f"Standings not sorted correctly: {a.team_name} should be above {b.team_name}"
            )

    print("  ✅ Standings sort order (Pts → GD → GF) is correct")


def verify_top_scorers(db, tournament_id: int) -> None:
    """Add goal events and check top-scorers aggregation."""
    from sqlalchemy import select
    from app.models.match import TournamentMatch, MatchEvent
    from app.models.tournament import GroupTeam, TournamentGroup, TournamentTeam
    from app.services.match_service import compute_top_scorers
    from app.models.user import User

    # Pick a completed match
    match = db.scalars(
        select(TournamentMatch).where(
            TournamentMatch.tournament_id == tournament_id,
            TournamentMatch.status == "completed",
        )
    ).first()

    if match is None:
        print("  ⚠️  No completed matches to test top-scorers against; skipping")
        return

    # Get the first user in the DB as a fake player
    user = db.scalars(select(User).limit(1)).first()
    if user is None:
        print("  ⚠️  No users found; skipping top-scorers test")
        return

    # Add 3 goals for user in home team
    for _ in range(3):
        db.add(
            MatchEvent(
                match_id=match.id,
                player_id=user.id,
                team_id=match.home_team_id,
                event_type="goal",
                minute=45,
            )
        )
    db.flush()

    scorers = compute_top_scorers(db, tournament_id)
    if not scorers:
        _fail("compute_top_scorers returned no rows after inserting goal events")

    top = scorers[0]
    if top.goals < 3:
        _fail(f"Expected top scorer to have >= 3 goals, got {top.goals}")

    # Verify descending order
    for i in range(len(scorers) - 1):
        if scorers[i].goals < scorers[i + 1].goals:
            _fail("Top-scorers not sorted descending by goals")

    print(
        f"  ✅ Top-scorers correct: {top.player_name} ({top.team_name}) — {top.goals} goals"
    )


def main_verify(db_url: str) -> None:
    """Run all Step-8 verifications against the given DB URL."""
    import sys
    sys.path.insert(0, str(BACKEND_DIR))

    os.environ["DATABASE_URL"] = db_url

    # Reload settings with new DB URL
    from app.core import database as db_module
    from app.core.config import settings

    # Create a fresh engine / session for the embedded DB
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)

    print("\n──────────────────────────────────────────────")
    print("STEP 8 VERIFICATION: SportArena Part 2")
    print("──────────────────────────────────────────────")

    with Session() as db:
        from sqlalchemy import select, func, text
        from app.models.match import TournamentMatch, MatchEvent
        from app.models.tournament import Tournament, TournamentGroup, TournamentTeam, GroupTeam
        from app.models.team import Team, TeamMember
        from app.models.user import User, Role, UserRole
        from app.models.sport import Sport
        from app.models.venue import Court

        # ── 1. Schema check ──────────────────────────────────────────────
        print("\n[1] Schema check …")
        for table in ("tournament_matches", "match_events"):
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"    {table}: {count} rows ✅")

        # ── 2. Seed data check ───────────────────────────────────────────
        print("\n[2] Seed data check …")
        n_teams = db.scalar(select(func.count(Team.id)))
        n_tournaments = db.scalar(select(func.count(Tournament.id)))
        n_matches = db.scalar(select(func.count(TournamentMatch.id)))
        n_events = db.scalar(select(func.count(MatchEvent.id)))
        print(f"    Teams: {n_teams}, Tournaments: {n_tournaments}, "
              f"Matches: {n_matches}, Events: {n_events}")
        if n_teams < 20:
            _fail(f"Expected >= 20 teams, got {n_teams}")
        if n_tournaments < 8:
            _fail(f"Expected >= 8 tournaments, got {n_tournaments}")
        print("  ✅ Seed data present")

        # ── 3. 12-team / 3-group scheduling scenario ─────────────────────
        print("\n[3] Scheduling: 12 teams / 3 groups / min 3 matches per team …")
        from app.core.security import hash_password
        from app.core.utils import slugify
        import datetime

        # Create a fresh organizer user
        org_role = db.scalar(select(Role).where(Role.name == "organizer"))
        if org_role is None:
            org_role = Role(name="organizer", description="Test organizer")
            db.add(org_role)
            db.flush()

        organizer = User(
            email="verify_step8_org@test.com",
            username="verify_step8_org",
            password_hash=hash_password("Test1234!"),
            full_name="Verify Organizer",
            is_active=True,
        )
        db.add(organizer)
        db.flush()
        db.add(UserRole(user_id=organizer.id, role_id=org_role.id))
        db.flush()

        # Flush and refresh so the selectin relationship loads the UserRole we just added
        db.flush()
        db.refresh(organizer)
        # At this point organizer.role_names is computed from organizer.roles via selectin.
        # We use a simple namespace wrapper for the permission check so the service
        # sees `organizer_user.id` and `organizer_user.role_names` correctly.
        class _OrgProxy:
            def __init__(self, user):
                self.id = user.id
                self.role_names = user.role_names

        organizer_proxy = _OrgProxy(organizer)

        # Sport
        sport = db.scalar(select(Sport).where(Sport.slug == "football"))
        if sport is None:
            sport = db.scalars(select(Sport).limit(1)).first()

        # Tournament
        today = datetime.date.today()
        tournament = Tournament(
            organizer_id=organizer.id,
            sport_id=sport.id,
            name="Step8 Verify 12-Team Tournament",
            format="group_stage",
            status="ongoing",
            max_teams=12,
            start_date=today,
            end_date=today + datetime.timedelta(days=30),
            is_public=True,
        )
        db.add(tournament)
        db.flush()

        # Create 12 player users + teams
        player_role = db.scalar(select(Role).where(Role.name == "player"))
        if player_role is None:
            player_role = Role(name="player", description="Test player")
            db.add(player_role)
            db.flush()

        teams_12: list[Team] = []
        used_slugs: set[str] = set()
        for i in range(12):
            captain = User(
                email=f"verify_cap_{i}@test.com",
                username=f"verify_cap_{i}",
                password_hash=hash_password("Test1234!"),
                full_name=f"Captain {i}",
                is_active=True,
            )
            db.add(captain)
            db.flush()
            db.add(UserRole(user_id=captain.id, role_id=player_role.id))

            base_slug = f"verify-team-{i}"
            slug = base_slug
            counter = 1
            while slug in used_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            used_slugs.add(slug)

            team = Team(
                name=f"Verify Team {i}",
                slug=slug,
                sport_id=sport.id,
                captain_id=captain.id,
            )
            db.add(team)
            db.flush()
            db.add(TeamMember(team_id=team.id, user_id=captain.id, role="captain"))
            teams_12.append(team)

        db.flush()

        # Register all 12 teams (approved)
        tt_list: list[TournamentTeam] = []
        for team in teams_12:
            tt = TournamentTeam(
                tournament_id=tournament.id,
                team_id=team.id,
                registration_status="approved",
                registered_by=team.captain_id,
                reviewed_by=organizer.id,
            )
            db.add(tt)
            db.flush()
            tt_list.append(tt)

        # Create 3 groups: A (4 teams), B (4 teams), C (4 teams)
        group_names = ["Group A", "Group B", "Group C"]
        for g_idx, gname in enumerate(group_names):
            grp = TournamentGroup(
                tournament_id=tournament.id,
                name=gname,
                description=f"{gname} of Step8 test",
            )
            db.add(grp)
            db.flush()
            for seeding, tt in enumerate(tt_list[g_idx * 4: g_idx * 4 + 4], start=1):
                db.add(
                    GroupTeam(
                        group_id=grp.id,
                        tournament_id=tournament.id,
                        tournament_team_id=tt.id,
                        seeding=seeding,
                    )
                )
        db.flush()

        # Find courts (use existing ones from seed or create minimal set)
        courts = db.scalars(
            select(Court).where(Court.is_active == True).limit(3)
        ).all()
        if not courts:
            _fail("No active courts found in DB; run seed first")

        court_ids = [c.id for c in courts]

        # Generate schedule via service
        from app.schemas.match import ScheduleGenerateRequest
        from app.services.schedule_service import generate_schedule

        payload = ScheduleGenerateRequest(
            court_ids=court_ids,
            start_date=today,
            end_date=today + datetime.timedelta(days=29),
            daily_time_slots=["07:00", "08:00", "09:00", "10:00", "11:00"],
            min_matches_per_team=3,
        )

        result = generate_schedule(db, tournament.id, payload, organizer_proxy)
        db.flush()

        print(f"    Schedule generated: {result.matches_created} matches, "
              f"{result.conflicts_skipped} conflicts_skipped")

        if result.matches_created == 0:
            _fail("generate_schedule created 0 matches")

        # Verify constraints
        verify_schedule(db, tournament.id, court_ids, min_matches=3)

        # ── 4. Standings math ────────────────────────────────────────────
        print("\n[4] Standings math …")
        verify_standings_math(db, tournament.id)

        # ── 5. Top scorers ───────────────────────────────────────────────
        print("\n[5] Top scorers …")
        verify_top_scorers(db, tournament.id)

        # Rollback everything — this was a verification-only run
        db.rollback()

    print("\n──────────────────────────────────────────────")
    print("🎉  STEP 8 VERIFICATION PASSED")
    print("──────────────────────────────────────────────\n")


def main() -> None:
    """Entry point: spin up embedded postgres, run migrations + seed, then verify."""
    try:
        from embedded_postgres import PostgresServer
    except ImportError:
        sys.exit("embedded_postgres not installed. Run: pip install embedded-postgres")

    tmpdir = tempfile.mkdtemp(prefix="sports_step8_")
    pgdata = Path(tmpdir) / "pgdata"
    pgdata.mkdir()

    print("⏳ Starting embedded PostgreSQL …")
    pg = PostgresServer(pgdata, cleanup_mode="delete")
    db_url_raw = pg.get_uri(database="postgres")
    db_url = db_url_raw.replace("postgresql://", "postgresql+psycopg2://", 1)
    print(f"   DB URL: {db_url}\n")

    env = {**os.environ, "DATABASE_URL": db_url}

    # 1. Migrations
    code = run([sys.executable, "-m", "alembic", "upgrade", "head"], env)
    if code != 0:
        _fail("alembic upgrade head failed")
    print("✅  alembic upgrade head OK\n")

    # 2. Seed
    code = run([sys.executable, "-m", "scripts.seed"], env)
    if code != 0:
        _fail("python -m scripts.seed failed")
    print("✅  python -m scripts.seed OK\n")

    # 3. In-process verification
    main_verify(db_url)


if __name__ == "__main__":
    main()
