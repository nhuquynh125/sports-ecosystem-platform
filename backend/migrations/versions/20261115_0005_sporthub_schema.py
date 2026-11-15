"""sporthub schema: pickup_matches, match_players, pickup_ratings

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-15

Tables (ERD §7 – Module 3: SportHub & Smart Match v1):
  pickup_matches  – casual open-invitation matches posted by a host
  match_players   – participants who join a pickup match
  pickup_ratings  – post-match peer ratings (skill + punctuality)

All constraint names follow the README naming convention (ix_/uq_/ck_/fk_/pk_).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SKILL_LEVELS = "('beginner', 'intermediate', 'advanced', 'pro')"
_PICKUP_STATUSES = "('open', 'full', 'ongoing', 'completed', 'cancelled')"
_PLAYER_STATUSES = "('joined', 'left', 'removed')"


def _ts(col: str = "created_at") -> sa.Column:
    return sa.Column(
        col,
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def upgrade() -> None:
    # ---------------------------------------------------- pickup_matches
    op.create_table(
        "pickup_matches",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("host_id", sa.BigInteger(), nullable=False),
        sa.Column("sport_id", sa.SmallInteger(), nullable=False),
        sa.Column("venue_id", sa.BigInteger(), nullable=True),
        sa.Column("area", sa.String(150), nullable=False),
        sa.Column(
            "skill_level", sa.String(20), nullable=False, server_default="intermediate"
        ),
        sa.Column("match_date", sa.Date(), nullable=False),
        sa.Column("time_slot", sa.Time(), nullable=False),
        sa.Column("max_players", sa.SmallInteger(), nullable=False, server_default="10"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("chat_room_id", sa.BigInteger(), nullable=True),
        _ts("created_at"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["host_id"], ["users.id"],
            name=op.f("fk_pickup_matches_host_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sport_id"], ["sports.id"],
            name=op.f("fk_pickup_matches_sport_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["venue_id"], ["venues.id"],
            name=op.f("fk_pickup_matches_venue_id"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["chat_room_id"], ["chat_rooms.id"],
            name=op.f("fk_pickup_matches_chat_room_id"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pickup_matches")),
        sa.CheckConstraint(
            f"skill_level IN {_SKILL_LEVELS}", name=op.f("ck_pickup_matches_skill_level")
        ),
        sa.CheckConstraint(
            f"status IN {_PICKUP_STATUSES}", name=op.f("ck_pickup_matches_status")
        ),
        sa.CheckConstraint("max_players >= 2", name=op.f("ck_pickup_matches_max_players_min")),
    )
    op.create_index("ix_pickup_matches_host_id", "pickup_matches", ["host_id"])
    op.create_index("ix_pickup_matches_sport_id", "pickup_matches", ["sport_id"])
    op.create_index("ix_pickup_matches_match_date", "pickup_matches", ["match_date"])
    op.create_index("ix_pickup_matches_status", "pickup_matches", ["status"])
    op.create_index("ix_pickup_matches_area", "pickup_matches", ["area"])

    # ---------------------------------------------------- match_players
    op.create_table(
        "match_players",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("match_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="joined"),
        sa.Column("attended", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        _ts("joined_at"),
        sa.ForeignKeyConstraint(
            ["match_id"], ["pickup_matches.id"],
            name=op.f("fk_match_players_match_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_match_players_user_id"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_players")),
        sa.UniqueConstraint(
            "match_id", "user_id", name=op.f("uq_match_players_match_id_user_id")
        ),
        sa.CheckConstraint(
            f"status IN {_PLAYER_STATUSES}", name=op.f("ck_match_players_status")
        ),
    )
    op.create_index("ix_match_players_match_id", "match_players", ["match_id"])
    op.create_index("ix_match_players_user_id", "match_players", ["user_id"])

    # ---------------------------------------------------- pickup_ratings
    op.create_table(
        "pickup_ratings",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("match_id", sa.BigInteger(), nullable=False),
        sa.Column("rater_id", sa.BigInteger(), nullable=False),
        sa.Column("rated_user_id", sa.BigInteger(), nullable=False),
        sa.Column("skill_score", sa.SmallInteger(), nullable=False),
        sa.Column("punctuality_score", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        _ts("created_at"),
        sa.ForeignKeyConstraint(
            ["match_id"], ["pickup_matches.id"],
            name=op.f("fk_pickup_ratings_match_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["rater_id"], ["users.id"],
            name=op.f("fk_pickup_ratings_rater_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["rated_user_id"], ["users.id"],
            name=op.f("fk_pickup_ratings_rated_user_id"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pickup_ratings")),
        sa.UniqueConstraint(
            "match_id", "rater_id", "rated_user_id",
            name=op.f("uq_pickup_ratings_match_rater_rated"),
        ),
        sa.CheckConstraint(
            "skill_score BETWEEN 1 AND 5", name=op.f("ck_pickup_ratings_skill_score")
        ),
        sa.CheckConstraint(
            "punctuality_score BETWEEN 1 AND 5",
            name=op.f("ck_pickup_ratings_punctuality_score"),
        ),
        sa.CheckConstraint(
            "rater_id != rated_user_id", name=op.f("ck_pickup_ratings_no_self_rating")
        ),
    )
    op.create_index("ix_pickup_ratings_match_id", "pickup_ratings", ["match_id"])
    op.create_index("ix_pickup_ratings_rater_id", "pickup_ratings", ["rater_id"])
    op.create_index("ix_pickup_ratings_rated_user_id", "pickup_ratings", ["rated_user_id"])


def downgrade() -> None:
    op.drop_table("pickup_ratings")
    op.drop_table("match_players")
    op.drop_index("ix_pickup_matches_area", table_name="pickup_matches")
    op.drop_index("ix_pickup_matches_status", table_name="pickup_matches")
    op.drop_index("ix_pickup_matches_match_date", table_name="pickup_matches")
    op.drop_index("ix_pickup_matches_sport_id", table_name="pickup_matches")
    op.drop_index("ix_pickup_matches_host_id", table_name="pickup_matches")
    op.drop_table("pickup_matches")
