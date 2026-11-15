"""Import every model so that `Base.metadata` is complete (Alembic autogenerate relies on it)."""
from app.models.booking import Booking
from app.models.chat import ChatMessage, ChatRoom, ChatRoomMember
from app.models.notification import Notification
from app.models.player import PlayerAvailability, PlayerProfile
from app.models.sport import Sport
from app.models.team import Team, TeamMember
from app.models.tournament import GroupTeam, Tournament, TournamentGroup, TournamentTeam
from app.models.user import Role, User, UserRole
from app.models.venue import Court, Venue

__all__ = [
    "Booking",
    "ChatMessage",
    "ChatRoom",
    "ChatRoomMember",
    "Court",
    "GroupTeam",
    "Notification",
    "PlayerAvailability",
    "PlayerProfile",
    "Role",
    "Sport",
    "Team",
    "TeamMember",
    "Tournament",
    "TournamentGroup",
    "TournamentTeam",
    "User",
    "UserRole",
    "Venue",
]
