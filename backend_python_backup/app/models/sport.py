"""Sports catalogue (ERD §3)."""
from sqlalchemy import Boolean, Identity, SmallInteger, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Sport(Base):
    __tablename__ = "sports"
    __table_args__ = (
        UniqueConstraint("name", name="uq_sports_name"),
        UniqueConstraint("slug", name="uq_sports_slug"),
    )

    id: Mapped[int] = mapped_column(SmallInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    icon_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
