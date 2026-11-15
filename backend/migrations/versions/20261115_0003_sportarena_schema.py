"""sportarena schema: teams, team_members, tournaments, tournament_teams, groups

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-15

Tables (ERD §5):
  teams              – team catalogue
  team_members       – many-to-many user ↔ team with role (captain/member)
  tournaments        – tournament catalogue
  tournament_teams   – team registration with approval workflow
  tournament_groups  – named groups within a tournament
  group_teams        – team-to-group assignment

All constraint names follow the README naming convention (ix_/uq_/ck_/fk_/pk_)
and are spelled out explicitly with op.f() so Alembic can generate correct
downgrade DROP statements.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TEAM_MEMBER_ROLES = "('captain', 'member')"
_TOURNAMENT_STATUSES = (
    "('draft', 'open', 'registration_closed', 'ongoing', 'completed', 'cancelled')"
)
_TOURNAMENT_FORMATS = (
    "('round_robin', 'single_elimination', 'double_elimination', 'group_stage')"
)
_REGISTRATION_STATUSES = "('pending', 'approved', 'rejected')"


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
    # ------------------------------------------------------------------ teams
    op.create_table(
        "teams",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(110), nullable=False),
        sa.Column("sport_id", sa.SmallInteger(), nullable=False),
        sa.Column("captain_id", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        _ts(),
        _updated_at(),
        sa.ForeignKeyConstraint(
            ["sport_id"], ["sports.id"],
            name=op.f("fk_teams_sport_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["captain_id"], ["users.id"],
            name=op.f("fk_teams_captain_id"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teams")),
        sa.UniqueConstraint("slug", name=op.f("uq_teams_slug")),
    )
    op.create_index("ix_teams_sport_id", "teams", ["sport_id"])
    op.create_index("ix_teams_captain_id", "teams", ["captain_id"])

    # --------------------------------------------------------------- team_members
    op.create_table(
        "team_members",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"],
            name=op.f("fk_team_members_team_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_team_members_user_id"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_team_members")),
        sa.UniqueConstraint("team_id", "user_id", name=op.f("uq_team_members_team_id_user_id")),
        sa.CheckConstraint(
            f"role IN {_TEAM_MEMBER_ROLES}", name=op.f("ck_team_members_role")
        ),
    )
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"])
    op.create_index("ix_team_members_user_id", "team_members", ["user_id"])

    # ------------------------------------------------------------- tournaments
    op.create_table(
        "tournaments",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("organizer_id", sa.BigInteger(), nullable=False),
        sa.Column("sport_id", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("format", sa.String(30), nullable=False, server_default="group_stage"),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("max_teams", sa.SmallInteger(), nullable=True),
        sa.Column("prize_pool", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("registration_deadline", sa.Date(), nullable=True),
        sa.Column("rules", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default=sa.true(), nullable=False),
        _ts(),
        _updated_at(),
        sa.ForeignKeyConstraint(
            ["organizer_id"], ["users.id"],
            name=op.f("fk_tournaments_organizer_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["sport_id"], ["sports.id"],
            name=op.f("fk_tournaments_sport_id"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tournaments")),
        sa.CheckConstraint(
            f"status IN {_TOURNAMENT_STATUSES}", name=op.f("ck_tournaments_status")
        ),
        sa.CheckConstraint(
            f"format IN {_TOURNAMENT_FORMATS}", name=op.f("ck_tournaments_format")
        ),
        sa.CheckConstraint(
            "max_teams IS NULL OR max_teams >= 2", name=op.f("ck_tournaments_max_teams")
        ),
        sa.CheckConstraint(
            "registration_deadline IS NULL OR registration_deadline <= start_date",
            name=op.f("ck_tournaments_reg_deadline"),
        ),
    )
    op.create_index("ix_tournaments_sport_id", "tournaments", ["sport_id"])
    op.create_index("ix_tournaments_organizer_id", "tournaments", ["organizer_id"])
    op.create_index("ix_tournaments_status", "tournaments", ["status"])

    # --------------------------------------------------------- tournament_teams
    op.create_table(
        "tournament_teams",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("tournament_id", sa.BigInteger(), nullable=False),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "registration_status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column("registered_by", sa.BigInteger(), nullable=False),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(255), nullable=True),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"], ["tournaments.id"],
            name=op.f("fk_tournament_teams_tournament_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"], ["teams.id"],
            name=op.f("fk_tournament_teams_team_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["registered_by"], ["users.id"],
            name=op.f("fk_tournament_teams_registered_by"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"], ["users.id"],
            name=op.f("fk_tournament_teams_reviewed_by"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tournament_teams")),
        sa.UniqueConstraint(
            "tournament_id", "team_id",
            name=op.f("uq_tournament_teams_tournament_id_team_id"),
        ),
        sa.CheckConstraint(
            f"registration_status IN {_REGISTRATION_STATUSES}",
            name=op.f("ck_tournament_teams_status"),
        ),
    )
    op.create_index("ix_tournament_teams_tournament_id", "tournament_teams", ["tournament_id"])
    op.create_index("ix_tournament_teams_team_id", "tournament_teams", ["team_id"])
    op.create_index(
        "ix_tournament_teams_status", "tournament_teams", ["registration_status"]
    )

    # ------------------------------------------------------- tournament_groups
    op.create_table(
        "tournament_groups",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("tournament_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"], ["tournaments.id"],
            name=op.f("fk_tournament_groups_tournament_id"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tournament_groups")),
        sa.UniqueConstraint(
            "tournament_id", "name",
            name=op.f("uq_tournament_groups_tournament_id_name"),
        ),
    )
    op.create_index(
        "ix_tournament_groups_tournament_id", "tournament_groups", ["tournament_id"]
    )

    # ---------------------------------------------------------------- group_teams
    op.create_table(
        "group_teams",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("tournament_id", sa.BigInteger(), nullable=False),
        sa.Column("tournament_team_id", sa.BigInteger(), nullable=False),
        sa.Column("seeding", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"], ["tournament_groups.id"],
            name=op.f("fk_group_teams_group_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"], ["tournaments.id"],
            name=op.f("fk_group_teams_tournament_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tournament_team_id"], ["tournament_teams.id"],
            name=op.f("fk_group_teams_tournament_team_id"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group_teams")),
        sa.UniqueConstraint(
            "group_id", "tournament_team_id",
            name=op.f("uq_group_teams_group_id_tournament_team_id"),
        ),
        sa.UniqueConstraint(
            "tournament_id", "tournament_team_id",
            name=op.f("uq_group_teams_tournament_id_tournament_team_id"),
        ),
    )
    op.create_index("ix_group_teams_group_id", "group_teams", ["group_id"])
    op.create_index("ix_group_teams_tournament_id", "group_teams", ["tournament_id"])


def downgrade() -> None:
    op.drop_table("group_teams")
    op.drop_table("tournament_groups")
    op.drop_table("tournament_teams")
    op.drop_table("tournaments")
    op.drop_table("team_members")
    op.drop_table("teams")
