#!/usr/bin/env python
"""Seed the database with realistic demo data.

    cd backend
    python scripts/seed.py                 # 300 users, aborts if users already exist
    python scripts/seed.py --reset         # wipe seeded tables (keeps `roles`) and re-seed
    python scripts/seed.py --users 500 --seed 7

Creates: 7 sports, N users across all five roles (+ some multi-role users), player profiles
(1-3 sports each) with weekly availability, a welcome notification per user, and a few direct
chat rooms with messages.

Every seeded account uses the SAME demo password (DEMO_PASSWORD) - development only.
The password is hashed once and reused, which keeps seeding fast (bcrypt is deliberately slow).
"""
import argparse
import random
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make `app` importable

try:
    from faker import Faker
except ImportError:  # pragma: no cover
    sys.exit("Faker is not installed. Run: pip install -e '.[dev]'")

from sqlalchemy import func, select, text  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.core.utils import generate_booking_code, slugify  # noqa: E402
from app.models import (  # noqa: E402
    ChatMessage,
    ChatRoom,
    ChatRoomMember,
    GroupTeam,
    MatchPlayer,
    Notification,
    PickupMatch,
    PickupRating,
    PlayerAvailability,
    PlayerProfile,
    Role,
    Sport,
    Team,
    TeamMember,
    Tournament,
    TournamentGroup,
    TournamentTeam,
    User,
    UserRole,
)
from app.models.enums import ROLE_NAMES  # noqa: E402
from app.models.venue import Court, Venue  # noqa: E402
from app.models.booking import Booking  # noqa: E402
from app.models.enums import BOOKING_STATUS_CONFIRMED  # noqa: E402

DEMO_PASSWORD = "Password123!"

ROLE_DESCRIPTIONS = {
    "admin": "Operates the platform: users, roles, approvals, catalogue",
    "player": "Books courts, keeps a profile, joins teams and matches",
    "venue_owner": "Owns venues and courts, manages bookings",
    "organizer": "Creates tournaments and reviews registrations",
    "coach": "Uses statistics and AI scouting, manages watchlists",
}

# name, description, selection weight, positions, (mean height cm, sd)
SPORTS = [
    ("Football", "Association football (5, 7 and 11-a-side)", 35,
     ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"], (170, 7)),
    ("Badminton", "Singles and doubles badminton", 20, ["Singles", "Doubles"], (167, 7)),
    ("Basketball", "5-on-5 and 3x3 basketball", 15, ["PG", "SG", "SF", "PF", "C"], (176, 8)),
    ("Tennis", "Singles and doubles tennis", 10, ["Singles", "Doubles"], (171, 7)),
    ("Volleyball", "Indoor and beach volleyball", 10,
     ["Setter", "Outside Hitter", "Middle Blocker", "Opposite", "Libero"], (172, 8)),
    ("Table Tennis", "Table tennis", 5, ["Attacker", "Defender", "All-round"], (168, 7)),
    ("Pickleball", "Singles and doubles pickleball", 5, ["Singles", "Doubles"], (168, 7)),
]

CITIES = [("Đà Nẵng", 35), ("Hồ Chí Minh", 25), ("Hà Nội", 20), ("Huế", 8), ("Hải Phòng", 6),
          ("Cần Thơ", 6)]
SKILLS = [("beginner", 30), ("intermediate", 40), ("advanced", 22), ("pro", 8)]
SIDES = [("right", 75), ("left", 15), ("both", 10)]

WEEKDAY_WINDOWS = [(time(18, 0), time(21, 0)), (time(17, 30), time(20, 30)),
                   (time(19, 0), time(22, 0)), (time(6, 0), time(8, 0))]
WEEKEND_WINDOWS = [(time(6, 0), time(9, 0)), (time(8, 0), time(11, 0)),
                   (time(15, 0), time(18, 0)), (time(16, 0), time(20, 0))]

BIO_TEMPLATES = [
    "Weekend {sport} player in {city}, looking for a regular group.",
    "Played {sport} for years and want to keep improving. Based in {city}.",
    "Casual {sport} after work. Friendly games only, open to new teams.",
    "Looking for a team or training partners for {sport} around {city}.",
    "Competitive {sport} player, available evenings. Happy to join tournaments.",
]
CHAT_LINES = [
    "Hi! Are you free for a game this Saturday?",
    "Sure, what time works for you?",
    "How about 17:00 at a court near the centre?",
    "Works for me. I'll bring a friend.",
    "Great, see you there!",
    "Can we move it 30 minutes later?",
    "No problem, 17:30 then.",
    "Thanks for the game yesterday, it was fun.",
]

DEMO_ACCOUNTS = [  # (email, username, full name, roles)
    ("admin@example.com", "admin", "Demo Admin", {"admin"}),
    ("owner@example.com", "demo_owner", "Demo Venue Owner", {"venue_owner"}),
    ("organizer@example.com", "demo_organizer", "Demo Organizer", {"organizer"}),
    ("coach@example.com", "demo_coach", "Demo Coach", {"coach", "player"}),
    ("player@example.com", "demo_player", "Demo Player", {"player"}),
]


def weighted(rnd: random.Random, options):
    return rnd.choices([o[0] for o in options], weights=[o[-1] for o in options])[0]


def build_role_plan(total: int, rnd: random.Random) -> list[set[str]]:
    """Role sets for `total` users: demo accounts first, then ~1% admin, 8% owners, 5% organizers,
    10% coaches, rest players; a share of staff also play."""
    scale = total / 300
    extra = {
        "admin": max(0, round(3 * scale) - 1),
        "venue_owner": max(0, round(25 * scale) - 1),
        "organizer": max(0, round(15 * scale) - 1),
        "coach": max(0, round(30 * scale) - 1),
    }
    plan = [set(account[3]) for account in DEMO_ACCOUNTS]
    rest: list[set[str]] = []
    for role, count in extra.items():
        rest += [{role} for _ in range(count)]
    rest += [{"player"} for _ in range(max(0, total - len(plan) - len(rest)))]
    rnd.shuffle(rest)
    for roles in rest:
        if "coach" in roles and rnd.random() < 0.4:
            roles.add("player")
        elif "organizer" in roles and rnd.random() < 0.3:
            roles.add("player")
        elif "venue_owner" in roles and rnd.random() < 0.1:
            roles.add("player")
    return (plan + rest)[:total]


def seed_courtbook(db, users: list, sports: list, rnd: random.Random) -> None:
    """Seed venues, courts and sample bookings for CourtBook."""
    from datetime import date, timedelta

    # Map sport names → Sport objects
    sport_map = {s.name: s for s in sports}
    # Find demo owner and player
    owner_user = next((u for u in users if u.email == "owner@example.com"), None)
    player_user = next((u for u in users if u.email == "player@example.com"), None)
    if owner_user is None or player_user is None:
        print("WARNING: seed_courtbook: demo owner/player not found, skipping courtbook seed")
        return

    VENUES_DATA = [
        # (name, city, district, address, open_h, close_h, sport_names, prices)
        ("Sân cầu lông Đà Nẵng Sport", "Đà Nẵng", "Hải Châu",
         "123 Trần Phú, Hải Châu", 6, 22,
         [("Badminton", 200000), ("Badminton", 220000)]),
        ("Nhà thi đấu Phú Thọ", "Hồ Chí Minh", "Quận 11",
         "1 Lữ Gia, Phường 15, Quận 11", 5, 23,
         [("Badminton", 250000), ("Badminton", 270000), ("Table Tennis", 150000)]),
        ("Sân bóng đá Mỹ Đình Mini", "Hà Nội", "Nam Từ Liêm",
         "Đường Mỹ Đình, Nam Từ Liêm", 6, 22,
         [("Football", 500000), ("Football", 550000), ("Football", 480000)]),
        ("Sân tennis Huế Sport Club", "Huế", "Thành phố Huế",
         "15 Lê Lợi, TP Huế", 6, 20,
         [("Tennis", 300000), ("Tennis", 320000)]),
        ("Trung tâm thể thao Hải Phòng", "Hải Phòng", "Ngô Quyền",
         "50 Điện Biên Phủ, Ngô Quyền", 7, 21,
         [("Basketball", 400000), ("Volleyball", 350000)]),
        ("Sân pickleball Cần Thơ", "Cần Thơ", "Ninh Kiều",
         "88 Nguyễn Trãi, Ninh Kiều", 6, 22,
         [("Pickleball", 180000), ("Pickleball", 200000)]),
        ("Sân cầu lông Hoàng Anh", "Đà Nẵng", "Thanh Khê",
         "45 Điện Biên Phủ, Thanh Khê", 5, 23,
         [("Badminton", 210000), ("Badminton", 230000), ("Badminton", 240000)]),
        ("Trung tâm bóng rổ Sài Gòn", "Hồ Chí Minh", "Quận 1",
         "10 Nguyễn Du, Quận 1", 7, 22,
         [("Basketball", 450000), ("Basketball", 480000)]),
        ("Sân bóng đá Cỏ nhân tạo Thủ Đô", "Hà Nội", "Hoàn Kiếm",
         "22 Hàng Bài, Hoàn Kiếm", 6, 22,
         [("Football", 520000), ("Football", 540000)]),
        ("CLB Bóng chuyền Huế", "Huế", "Phú Nhuận",
         "30 Phạm Văn Đồng, Huế", 7, 21,
         [("Volleyball", 280000), ("Volleyball", 300000)]),
        ("Sân Tennis Đông Khê", "Hải Phòng", "Lê Chân",
         "120 Tô Hiệu, Lê Chân", 6, 20,
         [("Tennis", 350000), ("Tennis", 370000)]),
        ("Sân bóng bàn Cần Thơ Academy", "Cần Thơ", "Bình Thuỷ",
         "5 Ngô Quyền, Bình Thuỷ", 7, 22,
         [("Table Tennis", 120000), ("Table Tennis", 130000), ("Table Tennis", 110000)]),
        ("Sân cầu lông Ánh Dương", "Hồ Chí Minh", "Bình Thạnh",
         "77 Đinh Tiên Hoàng, Bình Thạnh", 6, 23,
         [("Badminton", 230000), ("Badminton", 250000)]),
        ("Nhà thi đấu Thanh Hoà", "Hà Nội", "Đống Đa",
         "5 Lê Duẩn, Đống Đa", 5, 22,
         [("Badminton", 190000), ("Volleyball", 310000), ("Table Tennis", 140000)]),
        ("Sân Pickleball Đà Nẵng Sunrise", "Đà Nẵng", "Sơn Trà",
         "88 Võ Nguyên Giáp, Sơn Trà", 6, 21,
         [("Pickleball", 220000), ("Pickleball", 240000), ("Tennis", 310000)]),
        ("Sân bóng đá Thái Sơn Nam", "Hồ Chí Minh", "Quận 8",
         "200 Phạm Thế Hiển, Quận 8", 6, 22,
         [("Football", 490000), ("Football", 510000), ("Football", 530000)]),
    ]

    venues_created: list[Venue] = []
    all_courts: list[Court] = []

    for (vname, city, district, address, open_h, close_h, sport_courts) in VENUES_DATA:
        venue = Venue(
            owner_id=owner_user.id,
            name=vname,
            address=address,
            city=city,
            district=district,
            open_time=time(open_h, 0),
            close_time=time(close_h, 0),
            is_active=True,
        )
        db.add(venue)
        db.flush()
        venues_created.append(venue)

        for idx, (sport_name, price) in enumerate(sport_courts, start=1):
            sport_obj = sport_map.get(sport_name)
            if sport_obj is None:
                continue
            court = Court(
                venue_id=venue.id,
                sport_id=sport_obj.id,
                name=f"Sân {idx}",
                surface_type=rnd.choice(["hard", "turf", "wood", "synthetic"]),
                capacity=rnd.choice([2, 4, 6, 10]),
                hourly_price=price,
                is_active=True,
            )
            db.add(court)
            all_courts.append(court)
        db.flush()

    # Build sample bookings (20+) for future dates
    today = date.today()
    booker_pool = [player_user] + [
        u for u in users if u.email not in ("owner@example.com", "admin@example.com") and u.is_active
    ]
    booker_pool = booker_pool[:30]  # limit pool size

    booked_slots: set[tuple[int, date, str]] = set()
    booking_count = 0
    attempts = 0
    while booking_count < 25 and attempts < 500:
        attempts += 1
        court = rnd.choice(all_courts)
        # Pick a date 1–30 days from today
        bdate = today + timedelta(days=rnd.randint(1, 30))
        # Pick a slot from venue open/close (hourly, simplified)
        venue_q = next((v for v in venues_created if v.id == court.venue_id), None)
        if venue_q is None:
            continue
        from app.core.timeslots import generate_slots
        slots = generate_slots(venue_q.open_time, venue_q.close_time)
        if not slots:
            continue
        tslot = rnd.choice(slots)
        slot_key = (court.id, bdate, tslot.strftime("%H:%M"))
        if slot_key in booked_slots:
            continue
        booked_slots.add(slot_key)

        booker = rnd.choice(booker_pool)
        booking = Booking(
            booking_code=generate_booking_code(),
            court_id=court.id,
            user_id=booker.id,
            booking_date=bdate,
            time_slot=tslot,
            total_price=court.hourly_price,
            status=BOOKING_STATUS_CONFIRMED,
        )
        db.add(booking)
        booking_count += 1

    db.flush()
    print(f"CourtBook: seeded {len(venues_created)} venues, {len(all_courts)} courts, {booking_count} bookings.")


def seed_sportarena(db, users: list, sports: list, rnd: random.Random) -> None:
    """Seed 20+ teams with members and 5+ tournaments in open/grouped states."""
    import re
    import unicodedata
    from app.models.team import Team, TeamMember
    from app.models.tournament import GroupTeam, Tournament, TournamentGroup, TournamentTeam

    def _slugify(text: str) -> str:
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return text or "team"

    def _unique_slug(base: str, used: set) -> str:
        slug = base
        counter = 1
        while slug in used:
            slug = f"{base}-{counter}"
            counter += 1
        used.add(slug)
        return slug

    # Sport shortlist for teams
    sport_map = {s.name: s for s in sports}
    football = sport_map.get("Football")
    badminton = sport_map.get("Badminton")
    basketball = sport_map.get("Basketball")
    tennis = sport_map.get("Tennis")
    volleyball = sport_map.get("Volleyball")

    # Identify organizer and player users
    active_players = [u for u in users if "player" in u.role_names and u.is_active]
    organizers = [u for u in users if "organizer" in u.role_names and u.is_active]
    demo_organizer = next((u for u in users if u.email == "organizer@example.com"), None)
    demo_player = next((u for u in users if u.email == "player@example.com"), None)

    if not active_players:
        print("WARNING: seed_sportarena: no active players found, skipping")
        return

    # -- Build 24 teams --------------------------------------------------------
    TEAM_DATA = [
        ("Đà Nẵng Falcons", football, "Đà Nẵng"),
        ("Sài Gòn Thunder", football, "Hồ Chí Minh"),
        ("Hà Nội United", football, "Hà Nội"),
        ("Miền Trung Warriors", football, "Huế"),
        ("Dragon FC", football, "Đà Nẵng"),
        ("Phoenix Squad", football, "Hồ Chí Minh"),
        ("Coast Strikers", football, "Đà Nẵng"),
        ("Capital Wolves", football, "Hà Nội"),
        ("Sunrise Shuttlers", badminton, "Đà Nẵng"),
        ("Saigon Smash", badminton, "Hồ Chí Minh"),
        ("Hanoi Feathers", badminton, "Hà Nội"),
        ("Net Masters", badminton, "Huế"),
        ("Mekong Hoops", basketball, "Cần Thơ"),
        ("City Ballers", basketball, "Hồ Chí Minh"),
        ("Northern Court", basketball, "Hà Nội"),
        ("Da Nang Dunkers", basketball, "Đà Nẵng"),
        ("Riverside Aces", tennis, "Hồ Chí Minh"),
        ("Green Court", tennis, "Hà Nội"),
        ("Coastal Rackets", tennis, "Đà Nẵng"),
        ("Hue Baseline", tennis, "Huế"),
        ("Viet Spikers", volleyball, "Hà Nội"),
        ("Beach Blockers", volleyball, "Đà Nẵng"),
        ("Central Net", volleyball, "Huế"),
        ("South Setters", volleyball, "Hồ Chí Minh"),
    ]

    used_slugs: set[str] = set()
    teams: list[Team] = []
    team_captains: list[User] = []

    player_pool = list(active_players)
    rnd.shuffle(player_pool)
    captain_pool = player_pool[:24]  # one captain per team

    for idx, (tname, sport_obj, city) in enumerate(TEAM_DATA):
        if sport_obj is None:
            continue
        captain = captain_pool[idx % len(captain_pool)]
        slug = _unique_slug(_slugify(tname), used_slugs)
        team = Team(
            name=tname,
            slug=slug,
            sport_id=sport_obj.id,
            captain_id=captain.id,
            city=city,
            description=f"Competitive {sport_obj.name} team based in {city}.",
        )
        db.add(team)
        db.flush()
        teams.append(team)
        team_captains.append(captain)

        # Captain as member
        db.add(TeamMember(team_id=team.id, user_id=captain.id, role="captain"))

        # 3-6 extra members (avoid duplicating captain)
        members_added = {captain.id}
        candidates = [u for u in player_pool if u.id not in members_added]
        rnd.shuffle(candidates)
        for member_user in candidates[: rnd.randint(3, 6)]:
            db.add(TeamMember(team_id=team.id, user_id=member_user.id, role="member"))
            members_added.add(member_user.id)

    db.flush()
    print(f"SportArena: seeded {len(teams)} teams.")

    # -- Build 8 tournaments ---------------------------------------------------
    from datetime import date, timedelta
    today = date.today()

    if demo_organizer is None:
        demo_organizer = organizers[0] if organizers else users[0]

    TOURNAMENT_DATA = [
        # (name, sport, status, format, max_teams, offset_days)
        ("Đà Nẵng Football Cup 2026", football, "open", "group_stage", 16, 30),
        ("Saigon Basketball League S2", basketball, "open", "round_robin", 12, 45),
        ("Vietnam Badminton Open 2026", badminton, "open", "single_elimination", 32, 60),
        ("Hanoi Tennis Masters", tennis, "open", "single_elimination", 8, 25),
        ("Central Volleyball Championship", volleyball, "open", "group_stage", 8, 40),
        ("Football 7-a-side Premier", football, "registration_closed", "group_stage", 12, 15),
        ("Da Nang Basketball Clash", basketball, "ongoing", "round_robin", 8, -5),
        ("National Badminton Cup", badminton, "ongoing", "group_stage", 16, -10),
    ]

    organizer_cycle = organizers if organizers else [demo_organizer]
    tournaments: list[Tournament] = []

    for i, (tname, sport_obj, status, fmt, max_t, offset) in enumerate(TOURNAMENT_DATA):
        if sport_obj is None:
            continue
        org = organizer_cycle[i % len(organizer_cycle)]
        start = today + timedelta(days=offset)
        reg_deadline = start - timedelta(days=7) if offset > 7 else None
        t = Tournament(
            organizer_id=org.id,
            sport_id=sport_obj.id,
            name=tname,
            description=f"Official {sport_obj.name} tournament – {tname}.",
            format=fmt,
            status=status,
            max_teams=max_t,
            location=rnd.choice(["Đà Nẵng", "Hồ Chí Minh", "Hà Nội", "Huế"]),
            start_date=start,
            end_date=start + timedelta(days=rnd.randint(2, 14)),
            registration_deadline=reg_deadline,
            rules="Standard rules apply. Contact organizer for details.",
            is_public=True,
        )
        db.add(t)
        db.flush()
        tournaments.append(t)

    db.flush()
    print(f"SportArena: seeded {len(tournaments)} tournaments.")

    # -- Register teams and approve some ----------------------------------------
    # Group teams by sport for matching
    sport_teams: dict[int, list[Team]] = {}
    for team in teams:
        sport_teams.setdefault(team.sport_id, []).append(team)

    registrations_created = 0
    groups_created = 0

    for tournament in tournaments:
        eligible = sport_teams.get(tournament.sport_id, [])
        if not eligible:
            continue

        rnd.shuffle(eligible)
        to_register = eligible[: min(tournament.max_teams or 8, len(eligible))]

        tt_list: list[TournamentTeam] = []
        for team in to_register:
            captain = db.get(type(team.captain), team.captain_id)  # type: ignore[arg-type]
            # Use actual captain user object
            from sqlalchemy import select as sa_select
            from app.models.user import User as UserModel
            captain_obj = db.scalar(sa_select(UserModel).where(UserModel.id == team.captain_id))
            if captain_obj is None:
                continue

            status = "pending"
            if tournament.status in ("registration_closed", "ongoing"):
                status = rnd.choice(["approved", "approved", "approved", "rejected"])
            elif tournament.status == "open":
                status = rnd.choice(["pending", "pending", "approved"])

            tt = TournamentTeam(
                tournament_id=tournament.id,
                team_id=team.id,
                registration_status=status,
                registered_by=captain_obj.id,
                reviewed_by=tournament.organizer_id if status != "pending" else None,
                reviewed_at=datetime.now(timezone.utc) if status != "pending" else None,
                rejection_reason="Roster incomplete." if status == "rejected" else None,
            )
            db.add(tt)
            db.flush()
            tt_list.append(tt)
            registrations_created += 1

        # For tournaments in registration_closed or ongoing, create groups
        if tournament.status in ("registration_closed", "ongoing") and tournament.format in (
            "group_stage", "round_robin"
        ):
            approved_tts = [tt for tt in tt_list if tt.registration_status == "approved"]
            if len(approved_tts) >= 4:
                # Split into groups A and B
                mid = len(approved_tts) // 2
                for grp_name, grp_tts in [("Group A", approved_tts[:mid]), ("Group B", approved_tts[mid:])]:
                    grp = TournamentGroup(
                        tournament_id=tournament.id,
                        name=grp_name,
                        description=f"{grp_name} of {tournament.name}",
                    )
                    db.add(grp)
                    db.flush()
                    groups_created += 1
                    for seeding, tt in enumerate(grp_tts, start=1):
                        db.add(GroupTeam(
                            group_id=grp.id,
                            tournament_id=tournament.id,
                            tournament_team_id=tt.id,
                            seeding=seeding,
                        ))
                db.flush()

    print(
        f"SportArena: seeded {registrations_created} registrations, "
        f"{groups_created} groups."
    )


def seed_matches(db, users: list, sports: list, rnd: random.Random) -> None:
    """Seed tournament matches and match events for ongoing tournaments."""
    from datetime import date, timedelta, time as dt_time
    from app.models.match import TournamentMatch, MatchEvent
    from app.models.tournament import TournamentGroup, GroupTeam, TournamentTeam
    from app.models.team import TeamMember
    from app.models.venue import Court
    from app.services import schedule_service
    from sqlalchemy import select as sa_select

    today = date.today()
    TIME_SLOTS = ["07:00", "08:00", "09:00", "10:00"]

    # Find ongoing tournaments
    from app.models.tournament import Tournament
    ongoing_tournaments = db.scalars(
        sa_select(Tournament).where(Tournament.status == "ongoing")
    ).all()

    total_matches = 0
    total_events = 0

    for tournament in ongoing_tournaments:
        # Get groups for this tournament
        groups = db.scalars(
            sa_select(TournamentGroup).where(TournamentGroup.tournament_id == tournament.id)
        ).all()
        if not groups:
            continue

        # Get courts matching this tournament's sport
        courts = db.scalars(
            sa_select(Court).where(Court.sport_id == tournament.sport_id, Court.is_active == True)
        ).all()
        if not courts:
            courts = db.scalars(sa_select(Court).where(Court.is_active == True)).all()

        # Determine start date
        base_date = tournament.start_date if tournament.start_date else today - timedelta(days=5)

        # Track used slots to avoid collisions
        court_date_slot_used: set[tuple[int, date, str]] = set()
        team_date_used: set[tuple[int, date]] = set()

        for group in groups:
            # Get team IDs for this group via GroupTeam → TournamentTeam
            group_teams = db.scalars(
                sa_select(GroupTeam).where(GroupTeam.group_id == group.id)
            ).all()
            team_ids: list[int] = []
            for gt in group_teams:
                tt = db.get(TournamentTeam, gt.tournament_team_id)
                if tt:
                    team_ids.append(tt.team_id)

            if len(team_ids) < 2:
                continue

            # Generate round-robin fixtures using circle method
            rounds = schedule_service.circle_method_rounds(team_ids)

            for round_idx, round_fixtures in enumerate(rounds):
                match_date = base_date + timedelta(days=round_idx)
                slot_cycle_idx = 0

                for home_id, away_id in round_fixtures:
                    # Find an available slot
                    assigned_court = None
                    assigned_slot = None
                    slot_attempts = 0
                    while slot_attempts < len(TIME_SLOTS) * len(courts):
                        slot = TIME_SLOTS[slot_cycle_idx % len(TIME_SLOTS)]
                        court = courts[slot_cycle_idx % len(courts)]
                        slot_cycle_idx += 1
                        slot_attempts += 1

                        # Check no team plays twice that day
                        if (home_id, match_date) in team_date_used:
                            continue
                        if (away_id, match_date) in team_date_used:
                            continue
                        # Check court+date+slot not already taken
                        if (court.id, match_date, slot) in court_date_slot_used:
                            continue

                        assigned_court = court
                        assigned_slot = slot
                        break

                    if assigned_court is None:
                        # Fallback: skip slot checks for this match
                        assigned_court = rnd.choice(courts)
                        assigned_slot = rnd.choice(TIME_SLOTS)

                    # Register used slots
                    court_date_slot_used.add((assigned_court.id, match_date, assigned_slot))
                    team_date_used.add((home_id, match_date))
                    team_date_used.add((away_id, match_date))

                    # Parse time slot
                    slot_h, slot_m = map(int, assigned_slot.split(":"))
                    time_slot_obj = dt_time(slot_h, slot_m)

                    is_past = match_date < today
                    status = "completed" if is_past else "scheduled"

                    home_score = rnd.randint(0, 4) if is_past else None
                    away_score = rnd.randint(0, 4) if is_past else None

                    match = TournamentMatch(
                        tournament_id=tournament.id,
                        group_id=group.id,
                        home_team_id=home_id,
                        away_team_id=away_id,
                        court_id=assigned_court.id,
                        match_date=match_date,
                        time_slot=time_slot_obj,
                        home_score=home_score,
                        away_score=away_score,
                        status=status,
                    )
                    db.add(match)
                    db.flush()
                    total_matches += 1

                    if is_past and home_score is not None and away_score is not None:
                        # Create goal events for completed matches
                        for team_id, score in [(home_id, home_score), (away_id, away_score)]:
                            # Get team members to assign as scorers
                            members = db.scalars(
                                sa_select(TeamMember).where(TeamMember.team_id == team_id)
                            ).all()
                            player_ids = [m.user_id for m in members] if members else []

                            for _ in range(score):
                                minute = rnd.randint(1, 90)
                                player_id = rnd.choice(player_ids) if player_ids else None
                                event = MatchEvent(
                                    match_id=match.id,
                                    player_id=player_id,
                                    team_id=team_id,
                                    event_type="goal",
                                    minute=minute,
                                )
                                db.add(event)
                                total_events += 1

    db.flush()
    print(f"SportArena Matches: seeded {total_matches} matches, {total_events} goal events.")


def seed_sporthub(db, users: list, sports: list, rnd: random.Random) -> None:
    """Seed 25+ pickup matches, participants, and post-match ratings for SportHub."""
    from datetime import date, timedelta, time as dt_time
    from app.models.pickup_match import MatchPlayer, PickupMatch, PickupRating
    from app.models.venue import Venue
    from sqlalchemy import select as sa_select

    today = date.today()
    sport_map = {s.name: s for s in sports}

    # Collect active players
    active_players = [u for u in users if u.is_active and "player" in u.role_names]
    if len(active_players) < 10:
        print("WARNING: seed_sporthub: not enough players, skipping")
        return

    rnd.shuffle(active_players)

    # Pick some venues for matches
    venues = db.scalars(sa_select(Venue).limit(16)).all()

    AREAS = [
        "Hải Châu, Đà Nẵng", "Thanh Khê, Đà Nẵng", "Sơn Trà, Đà Nẵng",
        "Quận 1, Hồ Chí Minh", "Quận 7, Hồ Chí Minh", "Bình Thạnh, Hồ Chí Minh",
        "Hoàn Kiếm, Hà Nội", "Đống Đa, Hà Nội", "Cầu Giấy, Hà Nội",
        "TP Huế", "Ngô Quyền, Hải Phòng", "Ninh Kiều, Cần Thơ",
    ]

    PICKUP_MATCH_DATA = [
        # (sport_name, skill_level, time_hhmm, days_offset, max_players, description)
        ("Football",     "beginner",     "17:00", -15, 10, "5v5 chill game"),
        ("Football",     "intermediate", "18:00", -10, 14, "7v7 pickup"),
        ("Football",     "advanced",     "19:00", -7,  10, "Competitive 5v5"),
        ("Football",     "beginner",     "16:00", -5,  10, "Weekend 5v5"),
        ("Football",     "intermediate", "07:00",  5,  14, "Morning 7v7"),
        ("Football",     "advanced",     "18:30",  7,  10, "Evening competitive"),
        ("Football",     "pro",          "19:30",  10, 10, "High-level 5v5"),
        ("Badminton",    "beginner",     "18:00", -12, 4,  "Friendly doubles"),
        ("Badminton",    "intermediate", "19:00", -8,  4,  "Mixed doubles"),
        ("Badminton",    "advanced",     "07:00", -3,  6,  "Early morning session"),
        ("Badminton",    "beginner",     "17:30",  3,  4,  "Casual singles"),
        ("Badminton",    "intermediate", "19:00",  6,  8,  "Doubles tournament prep"),
        ("Basketball",   "intermediate", "18:00", -14, 10, "3-on-3 half court"),
        ("Basketball",   "advanced",     "19:00", -6,  10, "Full court 5v5"),
        ("Basketball",   "beginner",     "17:00", -2,  6,  "Casual 3v3"),
        ("Basketball",   "intermediate", "20:00",  4,  10, "Evening 5v5"),
        ("Tennis",       "intermediate", "07:00", -11, 4,  "Morning doubles"),
        ("Tennis",       "advanced",     "16:00", -4,  4,  "Competitive singles"),
        ("Tennis",       "beginner",     "08:00",  8,  4,  "Friendly set"),
        ("Volleyball",   "intermediate", "17:00", -9,  12, "Indoor volleyball"),
        ("Volleyball",   "beginner",     "16:00", -1,  12, "Beach-style casual"),
        ("Volleyball",   "advanced",     "18:00",  9,  12, "Competitive indoor"),
        ("Table Tennis", "beginner",     "19:00", -13, 4,  "Ping pong meetup"),
        ("Table Tennis", "intermediate", "18:00", -3,  6,  "Round-robin doubles"),
        ("Pickleball",   "beginner",     "07:30",  2,  8,  "Intro pickleball"),
        ("Pickleball",   "intermediate", "17:00",  12, 8,  "Competitive pickle"),
        ("Football",     "intermediate", "19:00", -18, 14, "Classic 7v7"),
    ]

    matches_created: list = []
    area_cycle = list(AREAS)
    rnd.shuffle(area_cycle)

    for idx, (sport_name, skill, time_str, day_offset, max_p, desc) in enumerate(PICKUP_MATCH_DATA):
        sport_obj = sport_map.get(sport_name)
        if sport_obj is None:
            continue
        host = active_players[idx % len(active_players)]
        area = area_cycle[idx % len(area_cycle)]
        venue = venues[idx % len(venues)] if venues else None
        h, m = map(int, time_str.split(":"))

        is_past = day_offset < 0
        status = "completed" if is_past else ("open" if day_offset > 2 else "ongoing")

        match = PickupMatch(
            host_id=host.id,
            sport_id=sport_obj.id,
            venue_id=venue.id if venue else None,
            area=area,
            skill_level=skill,
            match_date=today + timedelta(days=day_offset),
            time_slot=dt_time(h, m),
            max_players=max_p,
            status=status,
            description=f"{desc} – {area}",
        )
        db.add(match)
        db.flush()

        # Enroll host
        db.add(MatchPlayer(match_id=match.id, user_id=host.id, status="joined",
                           attended=is_past))

        # 2–8 extra participants (avoid host duplicate)
        joined_ids = {host.id}
        candidates = [u for u in active_players if u.id not in joined_ids]
        rnd.shuffle(candidates)
        how_many = rnd.randint(2, min(8, max_p - 1, len(candidates)))
        for player in candidates[:how_many]:
            db.add(MatchPlayer(
                match_id=match.id,
                user_id=player.id,
                status="joined",
                attended=is_past and rnd.random() < 0.8,
            ))
            joined_ids.add(player.id)

        db.flush()
        matches_created.append(match)

    print(f"SportHub: seeded {len(matches_created)} pickup matches.")

    # ---- Post-match ratings for completed matches ----------------------------
    ratings_created = 0
    completed_matches = [m for m in matches_created if m.status == "completed"]

    for match in completed_matches:
        from sqlalchemy import select as sa_select2
        player_rows = db.scalars(
            sa_select2(MatchPlayer).where(MatchPlayer.match_id == match.id)
        ).all()
        participant_ids = [mp.user_id for mp in player_rows if mp.attended]
        if len(participant_ids) < 2:
            continue

        # Each attended participant rates 1-2 others
        rated_set: set[tuple[int, int]] = set()
        for rater_id in participant_ids:
            others = [uid for uid in participant_ids if uid != rater_id]
            rnd.shuffle(others)
            for rated_id in others[: rnd.randint(1, 2)]:
                if (rater_id, rated_id) in rated_set:
                    continue
                rated_set.add((rater_id, rated_id))
                db.add(PickupRating(
                    match_id=match.id,
                    rater_id=rater_id,
                    rated_user_id=rated_id,
                    skill_score=rnd.randint(3, 5),
                    punctuality_score=rnd.randint(3, 5),
                    comment=rnd.choice([
                        "Great team player!", "Very punctual and skilled.",
                        "Excellent game!", "Fun to play with.",
                        "Looking forward to the next game.", None, None,
                    ]),
                ))
                ratings_created += 1

    db.flush()
    print(f"SportHub: seeded {ratings_created} post-match ratings.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--users", type=int, default=300, help="number of users (default 300)")
    parser.add_argument("--seed", type=int, default=42, help="random seed (reproducible data)")
    parser.add_argument("--reset", action="store_true", help="truncate seeded tables first")
    args = parser.parse_args()
    if args.users < 10:
        sys.exit("--users must be >= 10")

    rnd = random.Random(args.seed)
    Faker.seed(args.seed)
    try:
        fake = Faker("vi_VN")
    except Exception:  # locale missing in an old Faker
        fake = Faker()
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        if args.reset:
            db.execute(text(
                "TRUNCATE TABLE pickup_ratings, match_players, pickup_matches, "
                "tournament_matches, match_events, group_teams, tournament_groups, tournament_teams, "
                "tournaments, team_members, teams, "
                "chat_messages, chat_room_members, chat_rooms, notifications, "
                "player_availability, player_profiles, user_roles, users, sports "
                "RESTART IDENTITY CASCADE"
            ))
            db.commit()
        elif db.scalar(select(func.count(User.id))):
            sys.exit("Users already exist. Re-run with --reset to wipe and re-seed.")

        # ---- reference data ------------------------------------------------
        role_ids: dict[str, int] = {}
        for name in ROLE_NAMES:
            role = db.scalar(select(Role).where(Role.name == name))
            if role is None:
                role = Role(name=name, description=ROLE_DESCRIPTIONS[name])
                db.add(role)
                db.flush()
            role_ids[name] = role.id

        sports: list[Sport] = []
        for name, description, *_ in SPORTS:
            sport = db.scalar(select(Sport).where(Sport.slug == slugify(name)))
            if sport is None:
                sport = Sport(name=name, slug=slugify(name), description=description)
                db.add(sport)
            sports.append(sport)
        db.flush()
        sport_meta = {s.id: SPORTS[i] for i, s in enumerate(sports)}

        # ---- users ---------------------------------------------------------
        password_hash = hash_password(DEMO_PASSWORD)
        plan = build_role_plan(args.users, rnd)
        used_usernames = {a[1] for a in DEMO_ACCOUNTS}
        users: list[User] = []
        user_roles: dict[int, set[str]] = {}
        for index, roles in enumerate(plan):
            if index < len(DEMO_ACCOUNTS):
                email, username, full_name, _ = DEMO_ACCOUNTS[index]
                locked = False
            else:
                full_name = fake.name()
                base = slugify(full_name).replace("-", "")[:20] or "user"
                username = f"{base}{rnd.randint(10, 999)}"
                while username in used_usernames:
                    username = f"{base}{rnd.randint(10, 9999)}"
                used_usernames.add(username)
                email = f"{username}@{rnd.choice(['example.com', 'example.org', 'example.net'])}"
                locked = "admin" not in roles and rnd.random() < 0.03
            is_player = "player" in roles
            min_age, max_age = (16, 40) if is_player else (24, 58)
            created = now - timedelta(days=rnd.randint(1, 365), minutes=rnd.randint(0, 1439))
            users.append(User(
                email=email,
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                phone=fake.phone_number()[:30],
                date_of_birth=fake.date_of_birth(minimum_age=min_age, maximum_age=max_age),
                is_active=not locked,
                allow_scouting=is_player and rnd.random() < 0.6,
                last_login_at=(now - timedelta(hours=rnd.randint(1, 720))
                               if not locked and rnd.random() < 0.8 else None),
                created_at=created,
                updated_at=created,
            ))
        db.add_all(users)
        db.flush()
        for user, roles in zip(users, plan, strict=True):
            user_roles[user.id] = roles
            for role_name in roles:
                db.add(UserRole(user_id=user.id, role_id=role_ids[role_name]))

        # ---- profiles + weekly availability --------------------------------
        profile_count = slot_count = 0
        sport_weights = [s[2] for s in SPORTS]
        for user in users:
            if "player" not in user_roles[user.id]:
                continue
            city = weighted(rnd, CITIES)
            how_many = rnd.choices([1, 2, 3], weights=[55, 35, 10])[0]
            chosen: list[Sport] = []
            while len(chosen) < how_many:
                candidate = rnd.choices(sports, weights=sport_weights)[0]
                if candidate not in chosen:
                    chosen.append(candidate)
            for sport in chosen:
                _, _, _, positions, (mean_h, sd_h) = sport_meta[sport.id]
                height = int(min(205, max(145, rnd.gauss(mean_h, sd_h))))
                weight = round(rnd.uniform(19, 26) * (height / 100) ** 2)
                profile = PlayerProfile(
                    user_id=user.id,
                    sport_id=sport.id,
                    position=rnd.choice(positions),
                    skill_level=weighted(rnd, SKILLS),
                    preferred_side=weighted(rnd, SIDES),
                    height_cm=height,
                    weight_kg=weight,
                    city=city,
                    bio=rnd.choice(BIO_TEMPLATES).format(sport=sport.name.lower(), city=city),
                    is_visible=rnd.random() < 0.92,
                )
                db.add(profile)
                db.flush()
                profile_count += 1
                for day in rnd.sample(range(1, 8), rnd.randint(2, 4)):  # one window per day
                    start, end = rnd.choice(WEEKDAY_WINDOWS if day <= 5 else WEEKEND_WINDOWS)
                    db.add(PlayerAvailability(
                        player_profile_id=profile.id, day_of_week=day,
                        start_time=start, end_time=end,
                    ))
                    slot_count += 1

        # ---- notifications -------------------------------------------------
        for user in users:
            is_read = rnd.random() < 0.5
            db.add(Notification(
                user_id=user.id,
                type="welcome",
                title="Welcome to Sports Ecosystem",
                body=f"Hi {user.full_name}, your account is ready. Complete your profile to get started.",
                data={"deep_link": "/profile"},
                is_read=is_read,
                read_at=user.created_at + timedelta(hours=2) if is_read else None,
                created_at=user.created_at,
            ))

        # ---- a few direct chats ---------------------------------------------
        players = [u for u in users if "player" in user_roles[u.id] and u.is_active]
        pairs: set[tuple[int, int]] = set()
        room_count = min(20, len(players) // 2)
        while len(pairs) < room_count:
            a, b = rnd.sample(players, 2)
            pairs.add((min(a.id, b.id), max(a.id, b.id)))
        for a_id, b_id in sorted(pairs):
            started = now - timedelta(days=rnd.randint(1, 5), hours=rnd.randint(0, 20))
            room = ChatRoom(type="direct", created_by=a_id, created_at=started)
            db.add(room)
            db.flush()
            db.add_all([ChatRoomMember(room_id=room.id, user_id=a_id, joined_at=started),
                        ChatRoomMember(room_id=room.id, user_id=b_id, joined_at=started)])
            for i in range(rnd.randint(3, 6)):
                db.add(ChatMessage(
                    room_id=room.id,
                    sender_id=(a_id, b_id)[i % 2],
                    content=CHAT_LINES[i % len(CHAT_LINES)],
                    created_at=started + timedelta(minutes=5 * (i + 1)),
                ))

        db.commit()

        seed_courtbook(db, users, sports, rnd)
        db.commit()

        seed_sportarena(db, users, sports, rnd)
        db.commit()

        seed_matches(db, users, sports, rnd)
        db.commit()

        seed_sporthub(db, users, sports, rnd)
        db.commit()

        # ---- report ---------------------------------------------------------
        print(f"Seeded {len(users)} users, {len(sports)} sports, {profile_count} player profiles, "
              f"{slot_count} availability slots, {len(pairs)} chat rooms.")
        rows = db.execute(
            select(Role.name, func.count(UserRole.user_id))
            .join(UserRole, UserRole.role_id == Role.id).group_by(Role.name).order_by(Role.name)
        ).all()
        print("Users per role (multi-role users count once per role): "
              + ", ".join(f"{name}={count}" for name, count in rows))
        print(f"\nDemo logins (password for ALL seeded users: {DEMO_PASSWORD})")
        for email, _, _, roles in DEMO_ACCOUNTS:
            print(f"  {email:<24} {', '.join(sorted(roles))}")


if __name__ == "__main__":
    main()
