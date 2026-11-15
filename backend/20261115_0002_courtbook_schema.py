"""courtbook schema: venues, courts, bookings

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-15

Tables (ERD §4): venues, courts, bookings.

Double-booking guard: a UNIQUE index on (court_id, booking_date, time_slot) restricted to rows
that occupy the slot (status IN ('confirmed', 'completed')). Cancelled rows keep the history but
free the slot. All names follow the README convention and are spelled out with op.f().

Deliberately NOT here yet: venue approval workflow, payments, reviews, court_closures, and the
`pending` / `expired` booking statuses (they arrive with the payment-hold flow).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
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
    # ----------------------------------------------------------------- venues
    op.create_table(
        "venues",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("open_time", sa.Time(), nullable=False),
        sa.Column("close_time", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        _created_at(),
        _updated_at(),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name=op.f("fk_venues_owner_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_venues")),
        sa.CheckConstraint("close_time > open_time", name=op.f("ck_venues_time_order")),
        sa.CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90", name=op.f("ck_venues_latitude")
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180", name=op.f("ck_venues_longitude")
        ),
    )
    op.create_index("ix_venues_owner_id", "venues", ["owner_id"])
    op.create_index("ix_venues_city_district", "venues", ["city", "district"])

    # ----------------------------------------------------------------- courts
    op.create_table(
        "courts",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("venue_id", sa.BigInteger(), nullable=False),
        sa.Column("sport_id", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("surface_type", sa.String(20), nullable=True),
        sa.Column("capacity", sa.SmallInteger(), nullable=True),
        sa.Column("hourly_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        _created_at(),
        _updated_at(),
        sa.ForeignKeyConstraint(
            ["venue_id"], ["venues.id"], name=op.f("fk_courts_venue_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["sport_id"], ["sports.id"], name=op.f("fk_courts_sport_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_courts")),
        sa.UniqueConstraint("venue_id", "name", name=op.f("uq_courts_venue_id_name")),
        sa.CheckConstraint("hourly_price >= 0", name=op.f("ck_courts_hourly_price")),
        sa.CheckConstraint("capacity IS NULL OR capacity > 0", name=op.f("ck_courts_capacity")),
        sa.CheckConstraint(
            "surface_type IS NULL OR surface_type IN "
            "('grass', 'turf', 'wood', 'hard', 'clay', 'synthetic')",
            name=op.f("ck_courts_surface_type"),
        ),
    )
    op.create_index("ix_courts_venue_id", "courts", ["venue_id"])
    op.create_index("ix_courts_sport_id", "courts", ["sport_id"])

    # --------------------------------------------------------------- bookings
    op.create_table(
        "bookings",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("booking_code", sa.String(20), nullable=False),
        sa.Column("court_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("time_slot", sa.Time(), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), server_default="confirmed", nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.String(255), nullable=True),
        _created_at(),
        _updated_at(),
        sa.ForeignKeyConstraint(
            ["court_id"], ["courts.id"], name=op.f("fk_bookings_court_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_bookings_user_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bookings")),
        sa.UniqueConstraint("booking_code", name=op.f("uq_bookings_booking_code")),
        sa.CheckConstraint(
            "status IN ('confirmed', 'cancelled', 'completed')", name=op.f("ck_bookings_status")
        ),
        sa.CheckConstraint("total_price >= 0", name=op.f("ck_bookings_total_price")),
    )
    op.create_index(
        "uq_bookings_court_id_booking_date_time_slot",
        "bookings",
        ["court_id", "booking_date", "time_slot"],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed', 'completed')"),
    )
    op.create_index("ix_bookings_user_id_booking_date", "bookings", ["user_id", "booking_date"])
    op.create_index("ix_bookings_court_id_booking_date", "bookings", ["court_id", "booking_date"])


def downgrade() -> None:
    op.drop_table("bookings")  # its indexes go with it
    op.drop_table("courts")
    op.drop_table("venues")
