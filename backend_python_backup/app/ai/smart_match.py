"""AI Smart Match v1 – weighted cosine-similarity recommender.

Vectorizes candidate players across 6 normalized features:
  [sport_match, skill_level_proximity, area_match,
   availability_overlap_ratio, on_time_attendance_rate, avg_rating]

Returns top-N players with suitability % (0–100) and feature breakdown.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import time
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.pickup_match import FeatureBreakdown, PlayerRecommendation, SmartMatchResponse

# ---------------------------------------------------------------------------
# Feature weights (sum to 1.0 for interpretability)
# ---------------------------------------------------------------------------
WEIGHTS: list[float] = [
    0.30,  # sport_match              – hard must-have; zero kills cosine
    0.20,  # skill_level_proximity    – most critical for match quality
    0.15,  # area_match               – travel convenience
    0.15,  # availability_overlap_ratio – can they actually show up?
    0.10,  # on_time_attendance_rate  – reliability
    0.10,  # avg_rating               – social proof
]

SKILL_LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2, "pro": 3}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cosine_weighted(a: list[float], b: list[float], w: list[float]) -> float:
    """Weighted cosine similarity ∈ [0, 1]. Returns 0 on zero vectors."""
    dot = sum(w[i] * a[i] * b[i] for i in range(len(a)))
    mag_a = math.sqrt(sum(w[i] * a[i] ** 2 for i in range(len(a))))
    mag_b = math.sqrt(sum(w[i] * b[i] ** 2 for i in range(len(b))))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _skill_proximity(candidate_level: str, target_level: str) -> float:
    """1.0 = exact match; 0.5 = adjacent; 0.0 = three levels apart."""
    ci = SKILL_LEVEL_ORDER.get(candidate_level, 1)
    ti = SKILL_LEVEL_ORDER.get(target_level, 1)
    diff = abs(ci - ti)
    return max(0.0, 1.0 - diff * 0.33)


def _area_match(candidate_area: str, target_area: str) -> float:
    """1.0 if same city (case-insensitive substring); 0.0 otherwise."""
    if not candidate_area or not target_area:
        return 0.5  # unknown → neutral
    ca, ta = candidate_area.strip().lower(), target_area.strip().lower()
    return 1.0 if (ca in ta or ta in ca) else 0.0


def _availability_overlap(
    db: Session, player_profile_id: int, match_time: time, match_weekday: int
) -> float:
    """1.0 if the player has an availability window covering the match time, else 0.0."""
    from app.models.player import PlayerAvailability
    from sqlalchemy import select

    slots = db.scalars(
        select(PlayerAvailability).where(
            PlayerAvailability.player_profile_id == player_profile_id,
            PlayerAvailability.day_of_week == match_weekday,
        )
    ).all()
    for slot in slots:
        if slot.start_time <= match_time <= slot.end_time:
            return 1.0
    return 0.0 if slots else 0.5  # no data → neutral


# ---------------------------------------------------------------------------
# Target vector from match requirements
# ---------------------------------------------------------------------------

def _build_target_vector(match) -> list[float]:
    """Build a unit target vector that embodies the ideal candidate for `match`."""
    # sport_match = 1.0 (target always matches itself)
    # skill_level_proximity at exact level = 1.0
    # area = 1.0 (ideal player is in same area)
    # availability = 1.0 (ideal player is fully available)
    # on_time_rate = 1.0 (ideal player always attends)
    # avg_rating = 1.0 (normalized to max = 5)
    return [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]


# ---------------------------------------------------------------------------
# Main recommender
# ---------------------------------------------------------------------------

def recommend_players(
    db: Session,
    match_id: int,
    top_n: int = 10,
) -> SmartMatchResponse:
    """Return top-N player recommendations for a pickup match."""
    from sqlalchemy import select
    from app.models.pickup_match import MatchPlayer, PickupMatch
    from app.models.player import PlayerAvailability, PlayerProfile
    from app.models.user import User
    from app.services.pickup_match_service import get_user_avg_rating, get_user_on_time_rate

    match = db.get(PickupMatch, match_id)
    if match is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Pickup match not found")

    # Already-joined user IDs (exclude from recommendations)
    joined_ids: set[int] = {
        mp.user_id
        for mp in db.scalars(
            select(MatchPlayer).where(MatchPlayer.match_id == match_id)
        ).all()
    }

    # Candidate pool: players with a profile matching this sport (or any profile)
    candidate_profiles = db.scalars(
        select(PlayerProfile).where(
            PlayerProfile.sport_id == match.sport_id,
            PlayerProfile.is_visible == True,  # noqa: E712
        )
    ).all()

    target_vector = _build_target_vector(match)

    match_weekday = match.match_date.isoweekday()  # 1=Mon…7=Sun

    @dataclass
    class _Scored:
        user_id: int
        score: float
        breakdown: FeatureBreakdown
        profile: Any = field(repr=False)

    scored: list[_Scored] = []

    for profile in candidate_profiles:
        if profile.user_id in joined_ids:
            continue  # already in the match

        # Feature 1: sport_match
        f_sport = 1.0 if profile.sport_id == match.sport_id else 0.0

        # Feature 2: skill_level_proximity
        f_skill = _skill_proximity(profile.skill_level, match.skill_level)

        # Feature 3: area_match
        f_area = _area_match(profile.city or "", match.area)

        # Feature 4: availability_overlap_ratio
        f_avail = _availability_overlap(db, profile.id, match.time_slot, match_weekday)

        # Feature 5: on_time_attendance_rate
        f_ontime = get_user_on_time_rate(db, profile.user_id)

        # Feature 6: avg_rating (normalized from 1-5 → 0-1; 0.0 for no history)
        raw_rating = get_user_avg_rating(db, profile.user_id)
        f_rating = (raw_rating - 1.0) / 4.0 if raw_rating > 0 else 0.5  # 0 → neutral

        candidate_vector = [f_sport, f_skill, f_area, f_avail, f_ontime, f_rating]
        similarity = _cosine_weighted(candidate_vector, target_vector, WEIGHTS)

        scored.append(
            _Scored(
                user_id=profile.user_id,
                score=similarity,
                breakdown=FeatureBreakdown(
                    sport_match=round(f_sport, 4),
                    skill_level_proximity=round(f_skill, 4),
                    area_match=round(f_area, 4),
                    availability_overlap_ratio=round(f_avail, 4),
                    on_time_attendance_rate=round(f_ontime, 4),
                    avg_rating=round(f_rating, 4),
                ),
                profile=profile,
            )
        )

    # Sort descending by similarity
    scored.sort(key=lambda s: s.score, reverse=True)
    top = scored[:top_n]

    # Bulk-fetch users
    user_ids = [s.user_id for s in top]
    users_by_id: dict[int, User] = {}
    if user_ids:
        users = db.scalars(select(User).where(User.id.in_(user_ids))).all()
        users_by_id = {u.id: u for u in users}

    recommendations: list[PlayerRecommendation] = []
    for s in top:
        user = users_by_id.get(s.user_id)
        if user is None:
            continue
        recommendations.append(
            PlayerRecommendation(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                avatar_url=user.avatar_url,
                suitability_pct=round(s.score * 100, 2),
                feature_breakdown=s.breakdown,
            )
        )

    return SmartMatchResponse(match_id=match_id, recommendations=recommendations)
