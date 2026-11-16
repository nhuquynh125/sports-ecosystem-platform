from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import CurrentUser, DbSession
from app.schemas.chat import ChatMessageRead, ChatRoomRead, DirectRoomCreate
from app.schemas.common import Page, PaginationParams, paginate
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/rooms", response_model=list[ChatRoomRead], summary="Rooms I belong to")
def my_rooms(user: CurrentUser, db: DbSession):
    return chat_service.list_rooms(db, user)


@router.post(
    "/rooms",
    response_model=ChatRoomRead,
    status_code=201,
    summary="Open (or create) a direct 1:1 room",
)
def open_direct_room(
    payload: DirectRoomCreate, user: CurrentUser, db: DbSession, response: Response
):
    """Idempotent: returns 201 when the room was created, 200 when it already existed.
    Team and tournament rooms are created by their own modules."""
    room, created = chat_service.get_or_create_direct_room(db, user, payload.user_id)
    response.status_code = 201 if created else 200
    return room


@router.get("/rooms/{room_id}", response_model=ChatRoomRead, summary="Room details")
def get_room(room_id: int, user: CurrentUser, db: DbSession):
    return chat_service.get_room_for_viewer(db, room_id, user, allow_admin=True)


@router.get(
    "/rooms/{room_id}/messages",
    response_model=Page[ChatMessageRead],
    summary="Message history (newest first)",
)
def room_messages(
    room_id: int,
    user: CurrentUser,
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
):
    """Send messages over the WebSocket `/api/v1/ws/chat/{room_id}`."""
    chat_service.get_room_for_viewer(db, room_id, user, allow_admin=True)
    items, total = chat_service.list_messages(db, room_id, params)
    return paginate(items, total, params)
