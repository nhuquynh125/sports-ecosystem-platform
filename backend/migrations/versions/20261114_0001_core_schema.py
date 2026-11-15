"""core schema: identity, sports, player profiles, notifications, chat

Revision ID: 0001
Revises:
Create Date: 2026-11-14

Tables (ERD §3): roles, users, user_roles, sports, player_profiles, player_availability,
notifications, chat_rooms, chat_room_members, chat_messages.

Deliberately NOT here yet:
  * refresh_tokens        - Step 2 issues access tokens only.
  * FKs chat_rooms.team_id -> teams.id and chat_rooms.tournament_id -> tournaments.id - those
    tables arrive with SportHub / SportArena, whose migrations add the constraints.
All constraint / index names follow the README convention and are spelled out with op.f().
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def _updated_at() -> sa.Column:
    return sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def upgrade() -> None:
    # Normally created by docker/postgres/init/01-extensions.sql; repeated so that a database
    # that was not initialised through Docker works too.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # ------------------------------------------------------------------ roles
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.SmallInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.String(30), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("name", name=op.f("uq_roles_name")),
    )
    op.bulk_insert(
        roles,
        [
            {"name": "admin", "description": "Operates the platform: users, roles, approvals, catalogue"},
            {"name": "player", "description": "Books courts, keeps a profile, joins teams and matches"},
            {"name": "venue_owner", "description": "Owns venues and courts, manages bookings"},
            {"name": "organizer", "description": "Creates tournaments and reviews registrations"},
            {"name": "coach", "description": "Uses statistics and AI scouting, manages watchlists"},
        ],
    )

    # ------------------------------------------------------------------ users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("username", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("allow_scouting", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.SmallInteger(), nullable=False),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("assigned_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_roles_user_id"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_user_roles_role_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"], ["users.id"], name=op.f("fk_user_roles_assigned_by"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name=op.f("pk_user_roles")),
    )

    # ----------------------------------------------------------------- sports
    op.create_table(
        "sports",
        sa.Column("id", sa.SmallInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sports")),
        sa.UniqueConstraint("name", name=op.f("uq_sports_name")),
        sa.UniqueConstraint("slug", name=op.f("uq_sports_slug")),
    )

    # -------------------------------------------------------- player profiles
    op.create_table(
        "player_profiles",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("sport_id", sa.SmallInteger(), nullable=False),
        sa.Column("position", sa.String(50), nullable=True),
        sa.Column("skill_level", sa.String(20), server_default="beginner", nullable=False),
        sa.Column("preferred_side", sa.String(10), nullable=True),
        sa.Column("height_cm", sa.SmallInteger(), nullable=True),
        sa.Column("weight_kg", sa.SmallInteger(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_visible", sa.Boolean(), server_default=sa.true(), nullable=False),
        _created_at(),
        _updated_at(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_player_profiles_user_id"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["sport_id"], ["sports.id"], name=op.f("fk_player_profiles_sport_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_player_profiles")),
        sa.UniqueConstraint("user_id", "sport_id", name=op.f("uq_player_profiles_user_id_sport_id")),
        sa.CheckConstraint(
            "skill_level IN ('beginner', 'intermediate', 'advanced', 'pro')",
            name=op.f("ck_player_profiles_skill_level"),
        ),
        sa.CheckConstraint(
            "preferred_side IS NULL OR preferred_side IN ('left', 'right', 'both')",
            name=op.f("ck_player_profiles_preferred_side"),
        ),
        sa.CheckConstraint(
            "height_cm IS NULL OR height_cm > 0", name=op.f("ck_player_profiles_height_cm")
        ),
        sa.CheckConstraint(
            "weight_kg IS NULL OR weight_kg > 0", name=op.f("ck_player_profiles_weight_kg")
        ),
    )
    op.create_index(
        "ix_player_profiles_sport_city_level",
        "player_profiles",
        ["sport_id", "city", "skill_level"],
    )

    op.create_table(
        "player_availability",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("player_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["player_profile_id"],
            ["player_profiles.id"],
            name=op.f("fk_player_availability_player_profile_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_player_availability")),
        sa.CheckConstraint(
            "day_of_week BETWEEN 1 AND 7", name=op.f("ck_player_availability_day_of_week")
        ),
        sa.CheckConstraint(
            "end_time > start_time", name=op.f("ck_player_availability_time_order")
        ),
    )
    op.create_index(
        "ix_player_availability_profile_day",
        "player_availability",
        ["player_profile_id", "day_of_week"],
    )

    # ---------------------------------------------------------- notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_notifications_user_id"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id", "is_read", sa.text("created_at DESC")],
    )

    # ------------------------------------------------------------------- chat
    op.create_table(
        "chat_rooms",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(150), nullable=True),
        sa.Column("team_id", sa.BigInteger(), nullable=True),
        sa.Column("tournament_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_chat_rooms_created_by"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_rooms")),
        sa.UniqueConstraint("team_id", name=op.f("uq_chat_rooms_team_id")),
        sa.UniqueConstraint("tournament_id", name=op.f("uq_chat_rooms_tournament_id")),
        sa.CheckConstraint(
            "type IN ('direct', 'team', 'tournament')", name=op.f("ck_chat_rooms_type")
        ),
        sa.CheckConstraint(
            "(type = 'direct' AND team_id IS NULL AND tournament_id IS NULL) OR "
            "(type = 'team' AND team_id IS NOT NULL AND tournament_id IS NULL) OR "
            "(type = 'tournament' AND tournament_id IS NOT NULL AND team_id IS NULL)",
            name=op.f("ck_chat_rooms_scope"),
        ),
    )

    op.create_table(
        "chat_room_members",
        sa.Column("room_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["room_id"], ["chat_rooms.id"], name=op.f("fk_chat_room_members_room_id"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_chat_room_members_user_id"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("room_id", "user_id", name=op.f("pk_chat_room_members")),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("room_id", sa.BigInteger(), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(20), server_default="text", nullable=False),
        _created_at(),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["room_id"], ["chat_rooms.id"], name=op.f("fk_chat_messages_room_id"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"], ["users.id"], name=op.f("fk_chat_messages_sender_id"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
        sa.CheckConstraint(
            "message_type IN ('text', 'image', 'system')", name=op.f("ck_chat_messages_message_type")
        ),
        sa.CheckConstraint(
            "char_length(content) BETWEEN 1 AND 2000", name=op.f("ck_chat_messages_content_length")
        ),
    )
    op.create_index(
        "ix_chat_messages_room_created", "chat_messages", ["room_id", sa.text("created_at DESC")]
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_room_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_table("chat_room_members")
    op.drop_table("chat_rooms")
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_player_availability_profile_day", table_name="player_availability")
    op.drop_table("player_availability")
    op.drop_index("ix_player_profiles_sport_city_level", table_name="player_profiles")
    op.drop_table("player_profiles")
    op.drop_table("sports")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
    # Extensions are shared with other modules; they are intentionally left installed.
