"""SQLAlchemy engine, session factory and declarative base."""
from collections.abc import Iterator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Naming convention = README "Database Naming": ix_/uq_/ck_/fk_ (+ pk_).
# `ck` needs an explicit name on every CheckConstraint (the "rule" part of the name).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Fetch server-generated values (now(), identity) in the same round trip.
    __mapper_args__ = {"eager_defaults": True}


engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,
    echo=settings.SQL_ECHO,
    # Always talk UTC to PostgreSQL so timestamptz values come back in UTC (README: Time).
    connect_args={"options": "-c timezone=utc"},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed (rolls back if uncommitted)."""
    with SessionLocal() as db:
        yield db
