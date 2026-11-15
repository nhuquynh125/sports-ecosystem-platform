"""match schema: tournament_matches, match_events

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-15

Tables (ERD §6):
  tournament_matches  – individual matches within a tournament/group
  match_events        – in-match events (goals, cards, assists)

All constraint names follow the README naming convention (ix_/uq_/ck_/fk_/pk_)
and are spelled out explicitly with op.f() so Alembic can generate correct
downgrade DROP statements.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MATCH_STATUSES = "('scheduled', 'ongoing', 'completed', 'cancelled', 'postponed')"
_MATCH_EVENT_TYPES = "('goal', 'assist', 'yellow_card', 'red_card', 'own_goal')"


def _ts() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def _updated_at() -> sa.Column:
    return sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def upgrade() -> None:
    # ---------------------------------------------------- tournament_matches
    op.create_table(
        "tournament_matches",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("tournament_id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=True),
        sa.Column("home_team_id", sa.BigInteger(), nullable=False),
        sa.Column("away_team_id", sa.BigInteger(), nullable=False),
        sa.Column("court_id", sa.BigInteger(), nullable=True),
        sa.Column("match_date", sa.Date(), nullable=True),
        sa.Column("time_slot", sa.Time(), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="scheduled"
        ),
        _ts(),
        _updated_at(),
        sa.ForeignKeyConstraint(
            ["tournament_id"], ["tournaments.id"],
            name=op.f("fk_tournament_matches_tournament_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["tournament_groups.id"],
            name=op.f("fk_tournament_matches_group_id"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["home_team_id"], ["teams.id"],
            name=op.f("fk_tournament_matches_home_team_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["away_team_id"], ["teams.id"],
            name=op.f("fk_tournament_matches_away_team_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["court_id"], ["courts.id"],
            name=op.f("fk_tournament_matches_court_id"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tournament_matches")),
        sa.CheckConstraint(
            f"status IN {_MATCH_STATUSES}", name=op.f("ck_tournament_matches_status")
        ),
    )

    # Standard lookup indexes
    op.create_index(
        "ix_tournament_matches_tournament_id", "tournament_matches", ["tournament_id"]
    )
    op.create_index(
        "ix_tournament_matches_group_id", "tournament_matches", ["group_id"]
    )
    op.create_index(
        "ix_tournament_matches_match_date", "tournament_matches", ["match_date"]
    )
    op.create_index(
        "ix_tournament_matches_status", "tournament_matches", ["status"]
    )

    # Partial unique index: no two matches may share court+date+slot when all three are set
    op.create_index(
        "uq_tournament_matches_court_date_slot",
        "tournament_matches",
        ["court_id", "match_date", "time_slot"],
        unique=True,
        postgresql_where=sa.text(
            "court_id IS NOT NULL AND match_date IS NOT NULL AND time_slot IS NOT NULL"
        ),
    )

    # ----------------------------------------------------------- match_events
    op.create_table(
        "match_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("match_id", sa.BigInteger(), nullable=False),
        sa.Column("player_id", sa.BigInteger(), nullable=True),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("minute", sa.SmallInteger(), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        _ts(),
        sa.ForeignKeyConstraint(
            ["match_id"], ["tournament_matches.id"],
            name=op.f("fk_match_events_match_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"], ["users.id"],
            name=op.f("fk_match_events_player_id"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"],
            name=op.f("fk_match_events_team_id"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_events")),
        sa.CheckConstraint(
            f"event_type IN {_MATCH_EVENT_TYPES}", name=op.f("ck_match_events_event_type")
        ),
    )

    op.create_index("ix_match_events_match_id", "match_events", ["match_id"])
    op.create_index("ix_match_events_player_id", "match_events", ["player_id"])


def downgrade() -> None:
    op.drop_table("match_events")
    op.drop_index(
        "uq_tournament_matches_court_date_slot", table_name="tournament_matches"
    )
    op.drop_table("tournament_matches")
