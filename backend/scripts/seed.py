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
from app.core.utils import slugify  # noqa: E402
from app.models import (  # noqa: E402
    ChatMessage,
    ChatRoom,
    ChatRoomMember,
    Notification,
    PlayerAvailability,
    PlayerProfile,
    Role,
    Sport,
    User,
    UserRole,
)
from app.models.enums import ROLE_NAMES  # noqa: E402

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
                "TRUNCATE TABLE chat_messages, chat_room_members, chat_rooms, notifications, "
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
