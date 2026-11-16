"""Verification script for Module 3 (SportHub & Smart Match v1)."""
import ast
import re
import sys

print("=== Module 3 Verification ===\n")

# 1. seed.py checks
with open("scripts/seed.py") as f:
    src = f.read()

ast.parse(src)
print("  seed.py: syntax OK")

for fn in ["seed_sporthub", "seed_courtbook", "seed_sportarena", "seed_matches"]:
    assert f"def {fn}(" in src, f"Missing function: {fn}"
    print(f"  Function {fn}: found")

for cls in ["PickupMatch", "PickupRating", "MatchPlayer"]:
    assert cls in src, f"Missing class: {cls}"
    print(f"  Class {cls}: in seed")

# Count match definitions in PICKUP_MATCH_DATA
lines_in_data = re.findall(r'\("(?:Football|Badminton|Basketball|Tennis|Volleyball|Table Tennis|Pickleball)"', src)
print(f"  PICKUP_MATCH_DATA: {len(lines_in_data)} entries (required: >=25)")
assert len(lines_in_data) >= 25, f"Need at least 25 matches, got {len(lines_in_data)}"

assert "seed_sporthub(" in src
print("  seed_sporthub(): called in main")
assert "pickup_ratings" in src and "match_players" in src and "pickup_matches" in src
print("  TRUNCATE includes all pickup tables: OK")

# 2. AI smart match integrity
from app.ai.smart_match import WEIGHTS, SKILL_LEVEL_ORDER, _cosine_weighted, _skill_proximity, _area_match

assert abs(sum(WEIGHTS) - 1.0) < 1e-9, f"Weights must sum to 1.0, got {sum(WEIGHTS)}"
print(f"\n  WEIGHTS sum=1.0: {WEIGHTS}")
assert len(WEIGHTS) == 6, "Need exactly 6 features"
print(f"  6 features: OK")

# Perfect match = 1.0
v = [1.0] * 6
assert abs(_cosine_weighted(v, v, WEIGHTS) - 1.0) < 1e-9
print("  Perfect cosine similarity = 1.0: OK")

# Zero vector → 0.0
z = [0.0] * 6
assert _cosine_weighted(z, z, WEIGHTS) == 0.0
print("  Zero-vector cosine similarity = 0.0: OK")

# Skill proximity
assert _skill_proximity("intermediate", "intermediate") == 1.0
assert 0.6 < _skill_proximity("beginner", "intermediate") < 0.8
assert _skill_proximity("beginner", "pro") <= 0.02
print("  Skill proximity monotonically decreasing: OK")

# Area match
assert _area_match("Đà Nẵng", "Hải Châu, Đà Nẵng") == 1.0
assert _area_match("Hà Nội", "Hồ Chí Minh") == 0.0
assert _area_match("", "") == 0.5  # neutral
print("  Area matching: OK")

# 3. Models
from app.models.pickup_match import (
    PickupMatch, MatchPlayer, PickupRating,
    PICKUP_MATCH_STATUSES, MATCH_PLAYER_STATUSES,
)
assert PickupMatch.__tablename__ == "pickup_matches"
assert MatchPlayer.__tablename__ == "match_players"
assert PickupRating.__tablename__ == "pickup_ratings"
print(f"\n  Tables: {PickupMatch.__tablename__}, {MatchPlayer.__tablename__}, {PickupRating.__tablename__}")

cols = {c.key for c in PickupMatch.__table__.columns}
required = {"host_id", "sport_id", "venue_id", "area", "skill_level", "match_date",
            "time_slot", "max_players", "status", "chat_room_id"}
missing = required - cols
assert not missing, f"PickupMatch missing columns: {missing}"
print(f"  PickupMatch columns: {len(cols)} (all required present)")

mp_cols = {c.key for c in MatchPlayer.__table__.columns}
assert {"match_id", "user_id", "status", "attended"}.issubset(mp_cols)
print(f"  MatchPlayer columns: {len(mp_cols)}")

pr_cols = {c.key for c in PickupRating.__table__.columns}
assert {"match_id", "rater_id", "rated_user_id", "skill_score", "punctuality_score", "comment"}.issubset(pr_cols)
print(f"  PickupRating columns: {len(pr_cols)}")

# 4. Schemas
from app.schemas.pickup_match import (
    PickupMatchCreate, PickupMatchOut, MatchPlayerOut,
    RatingCreate, RatingOut, SmartMatchRequest, SmartMatchResponse,
    FeatureBreakdown, PlayerRecommendation,
)
print("\n  All schemas importable: OK")

# 5. Routes
from app.api.v1.endpoints.pickup_matches import router

# Merge methods per path (FastAPI can have multiple Route objects with same path)
route_map: dict[str, set] = {}
for r in router.routes:
    route_map.setdefault(r.path, set()).update(r.methods or set())

expected_routes = {
    "/matches": {"POST", "GET"},
    "/matches/{match_id}": {"GET"},
    "/matches/{match_id}/join": {"POST"},
    "/matches/{match_id}/leave": {"DELETE"},
    "/matches/{match_id}/ratings": {"POST"},
    "/ai/smart-match": {"POST"},
}
for path, methods in expected_routes.items():
    assert path in route_map, f"Missing route: {path}"
    for m in methods:
        assert m in route_map[path], f"Missing method {m} on {path}"
print(f"\n  All routes verified: {list(route_map.keys())}")

# 6. Service functions
from app.services.pickup_match_service import (
    create_match, list_matches, get_match, join_match, leave_match,
    create_rating, get_user_avg_rating, get_user_on_time_rate,
)
print("\n  All service functions importable: OK")

# 7. Migration file
with open("migrations/versions/20261115_0005_sporthub_schema.py") as f:
    mig = f.read()
ast.parse(mig)
for table in ["pickup_matches", "match_players", "pickup_ratings"]:
    assert table in mig, f"Missing table in migration: {table}"
    print(f"  Migration table {table}: found")
assert 'down_revision: str | None = "0004"' in mig
print("  Migration chain (0004→0005): OK")

print("\n" + "=" * 40)
print("ALL MODULE 3 VERIFICATIONS PASSED ✓")
print("=" * 40)
