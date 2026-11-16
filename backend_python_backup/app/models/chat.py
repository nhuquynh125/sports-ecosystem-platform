"""Chat rooms, membership and messages (ERD §3).

`chat_rooms.team_id` / `tournament_id` are plain bigint columns for now: the foreign keys
to `teams` / `tournaments` are added by the SportHub / SportArena migrations (Step 3).
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CHAT_ROOM_TYPES, MAX_CHAT_MESSAGE_LENGTH, MESSAGE_TYPES, in_check
from app.models.user import User


class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    __table_args__ = (
        CheckConstraint(in_check("type", CHAT_ROOM_TYPES), name="type"),
        CheckConstraint(
            "(type = 'direct' AND team_id IS NULL AND tournament_id IS NULL) OR "
            "(type = 'team' AND team_id IS NOT NULL AND tournament_id IS NULL) OR "
            "(type = 'tournament' AND tournament_id IS NOT NULL AND team_id IS NULL)",
            name="scope",
        ),
        UniqueConstraint("team_id", name="uq_chat_rooms_team_id"),
        UniqueConstraint("tournament_id", name="uq_chat_rooms_tournament_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str | None] = mapped_column(String(150))
    team_id: Mapped[int | None] = mapped_column(BigInteger)
    tournament_id: Mapped[int | None] = mapped_column(BigInteger)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    members: Mapped[list["ChatRoomMember"]] = relationship(
        back_populates="room", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin"
    )


class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"

    room_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_rooms.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    room: Mapped[ChatRoom] = relationship(back_populates="members")
    user: Mapped[User] = relationship(User, lazy="joined")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint(in_check("message_type", MESSAGE_TYPES), name="message_type"),
        CheckConstraint(
            f"char_length(content) BETWEEN 1 AND {MAX_CHAT_MESSAGE_LENGTH}", name="content_length"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    room_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False
    )
    # NULL for `system` messages and after a sender is removed.
    sender_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="text", server_default="text"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sender: Mapped[User | None] = relationship(User, lazy="joined")

    @property
    def sender_name(self) -> str | None:
        return self.sender.full_name if self.sender else None


Index("ix_chat_messages_room_created", ChatMessage.room_id, ChatMessage.created_at.desc())
