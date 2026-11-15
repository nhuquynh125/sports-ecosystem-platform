"""Import every model so that `Base.metadata` is complete (Alembic autogenerate relies on it)."""
from app.models.chat import ChatMessage, ChatRoom, ChatRoomMember
from app.models.notification import Notification
from app.models.player import PlayerAvailability, PlayerProfile
from app.models.sport import Sport
from app.models.user import Role, User, UserRole

__all__ = [
    "ChatMessage",
    "ChatRoom",
    "ChatRoomMember",
    "Notification",
    "PlayerAvailability",
    "PlayerProfile",
    "Role",
    "Sport",
    "User",
    "UserRole",
]
