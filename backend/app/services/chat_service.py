"""ChatService (ARCH §3.2): rooms, membership and messages.

`create_room`, `add_member` and `remove_member` do NOT commit: other modules (SportHub teams,
SportArena tournaments) call them inside their own transaction (e.g. "approve registration +
add team to tournament chat").
"""
from collections.abc import Iterable
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, aliased

from app.core.exceptions import BusinessRuleError, NotFoundError, PermissionDenied
from app.models import ChatMessage, ChatRoom, ChatRoomMember, User
from app.models.enums import ROLE_ADMIN
from app.schemas.common import PaginationParams


# ---------------------------------------------------------------- membership
def is_member(db: Session, room_id: int, user_id: int) -> bool:
    return db.get(ChatRoomMember, (room_id, user_id)) is not None


def create_room(
    db: Session,
    *,
    room_type: str,
    created_by: int | None = None,
    name: str | None = None,
    team_id: int | None = None,
    tournament_id: int | None = None,
    member_ids: Iterable[int] = (),
) -> ChatRoom:
    room = ChatRoom(
        type=room_type,
        name=name,
        team_id=team_id,
        tournament_id=tournament_id,
        created_by=created_by,
    )
    db.add(room)
    db.flush()
    for user_id in dict.fromkeys(member_ids):  # de-duplicate, keep order
        db.add(ChatRoomMember(room_id=room.id, user_id=user_id))
    db.flush()
    return room


def add_member(db: Session, room_id: int, user_id: int) -> None:
    if not is_member(db, room_id, user_id):
        db.add(ChatRoomMember(room_id=room_id, user_id=user_id))
        db.flush()


def remove_member(db: Session, room_id: int, user_id: int) -> None:
    member = db.get(ChatRoomMember, (room_id, user_id))
    if member is not None:
        db.delete(member)
        db.flush()


# --------------------------------------------------------------------- rooms
def get_or_create_direct_room(db: Session, user: User, other_user_id: int) -> tuple[ChatRoom, bool]:
    """Return ``(room, created)`` for the 1:1 room between two users."""
    if other_user_id == user.id:
        raise BusinessRuleError("You cannot start a chat with yourself")
    other = db.get(User, other_user_id)
    if other is None or not other.is_active:
        raise NotFoundError("User not found")

    # Serialise concurrent "open chat" clicks for the same pair (released at commit).
    low, high = sorted((user.id, other_user_id))
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": f"direct-room:{low}:{high}"}
    )
    mine = aliased(ChatRoomMember)
    theirs = aliased(ChatRoomMember)
    existing = db.scalars(
        select(ChatRoom)
        .join(mine, mine.room_id == ChatRoom.id)
        .join(theirs, theirs.room_id == ChatRoom.id)
        .where(ChatRoom.type == "direct", mine.user_id == user.id, theirs.user_id == other_user_id)
        .limit(1)
    ).first()
    if existing is not None:
        db.commit()
        return existing, False

    room = create_room(
        db, room_type="direct", created_by=user.id, member_ids=[user.id, other_user_id]
    )
    db.commit()
    db.refresh(room)
    return room, True


def list_rooms(db: Session, user: User) -> list[ChatRoom]:
    return list(
        db.scalars(
            select(ChatRoom)
            .join(ChatRoomMember, ChatRoomMember.room_id == ChatRoom.id)
            .where(ChatRoomMember.user_id == user.id)
            .order_by(ChatRoom.created_at.desc(), ChatRoom.id.desc())
        ).all()
    )


def get_room_for_viewer(db: Session, room_id: int, user: User, allow_admin: bool = False) -> ChatRoom:
    room = db.get(ChatRoom, room_id)
    if room is None:
        raise NotFoundError("Chat room not found")
    if is_member(db, room_id, user.id):
        return room
    if allow_admin and ROLE_ADMIN in user.role_names:  # moderation (FR-SH-10)
        return room
    raise PermissionDenied("You are not a member of this chat room")


# ------------------------------------------------------------------ messages
def list_messages(
    db: Session, room_id: int, params: PaginationParams
) -> tuple[list[ChatMessage], int]:
    """Newest first; the client reverses for display."""
    filters = [ChatMessage.room_id == room_id, ChatMessage.deleted_at.is_(None)]
    total = db.scalar(select(func.count(ChatMessage.id)).where(*filters)) or 0
    items = db.scalars(
        select(ChatMessage)
        .where(*filters)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(params.page_size)
        .offset(params.offset)
    ).all()
    return list(items), total


def create_message(
    db: Session, room_id: int, sender_id: int, content: str, message_type: str = "text"
) -> ChatMessage:
    """Persist and commit one message. Membership is checked here, not just at connect time."""
    if not is_member(db, room_id, sender_id):
        raise PermissionDenied("You are not a member of this chat room")
    message = ChatMessage(
        room_id=room_id, sender_id=sender_id, content=content, message_type=message_type
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def message_payload(message: ChatMessage, sender_name: str | None) -> dict[str, Any]:
    """JSON-safe dict broadcast over the WebSocket (timestamps ISO-8601 UTC)."""
    return {
        "id": message.id,
        "room_id": message.room_id,
        "sender_id": message.sender_id,
        "sender_name": sender_name,
        "content": message.content,
        "message_type": message.message_type,
        "created_at": message.created_at.isoformat(),
    }
