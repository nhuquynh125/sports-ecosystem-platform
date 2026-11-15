"""Chat schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.user import UserPublic


class DirectRoomCreate(BaseModel):
    user_id: int


class ChatRoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    name: str | None = None
    team_id: int | None = None
    tournament_id: int | None = None
    created_by: int | None = None
    created_at: datetime
    members: list[UserPublic] = []

    @field_validator("members", mode="before")
    @classmethod
    def _member_users(cls, value):
        return [getattr(member, "user", member) for member in value]


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    sender_id: int | None = None
    sender_name: str | None = None
    content: str
    message_type: str
    created_at: datetime
    edited_at: datetime | None = None
