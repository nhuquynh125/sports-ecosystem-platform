"""WebSocket chat endpoint: ``/api/v1/ws/chat/{room_id}``.

Protocol
--------
Connect : ``ws://host/api/v1/ws/chat/{room_id}?token=<access_token>``
          (browsers cannot set headers on a WebSocket; non-browser clients may instead send
          ``Authorization: Bearer <token>``).
Client -> server : ``{"content": "hello"}``  (or ``{"type": "ping"}``)
Server -> room   : ``{"type": "message", "data": {id, room_id, sender_id, sender_name,
                    content, message_type, created_at}}``
Server -> sender : ``{"type": "error", "detail": "..."}`` for invalid frames (socket stays open)
Close codes      : 4401 not authenticated / token expired, 4403 forbidden (not a member or
                   account disabled), 4404 room not found.

Every message is persisted to ``chat_messages`` BEFORE it is broadcast.
"""
import json
import logging
import time

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models import ChatRoom, User
from app.models.enums import MAX_CHAT_MESSAGE_LENGTH
from app.services import chat_service
from app.services.ws_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


class _Reject(Exception):
    def __init__(self, code: int, reason: str):
        self.code = code
        self.reason = reason
        super().__init__(reason)


def _token_from(websocket: WebSocket, query_token: str | None) -> str | None:
    if query_token:
        return query_token
    header = websocket.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    return value.strip() if scheme.lower() == "bearer" and value.strip() else None


def _authorize(token: str | None, room_id: int) -> tuple[int, str, float]:
    """Blocking (runs in a worker thread). Returns (user_id, full_name, token_exp)."""
    if not token:
        raise _Reject(4401, "Not authenticated")
    try:
        claims = decode_access_token(token)
        user_id = int(claims["sub"])
        expires_at = float(claims["exp"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise _Reject(4401, "Could not validate credentials") from None

    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            raise _Reject(4401, "Could not validate credentials")
        if not user.is_active:
            raise _Reject(4403, "Account is disabled")
        if db.get(ChatRoom, room_id) is None:
            raise _Reject(4404, "Chat room not found")
        if not chat_service.is_member(db, room_id, user_id):
            raise _Reject(4403, "You are not a member of this chat room")
        return user.id, user.full_name, expires_at


def _persist(room_id: int, user_id: int, sender_name: str, content: str) -> dict:
    """Blocking: save one message and build the broadcast payload."""
    with SessionLocal() as db:
        try:
            message = chat_service.create_message(db, room_id, user_id, content)
        except Exception as exc:
            if getattr(exc, "status_code", None) == 403:  # removed from the room meanwhile
                raise _Reject(4403, "You are not a member of this chat room") from None
            raise
        return chat_service.message_payload(message, sender_name)


@router.websocket("/ws/chat/{room_id}")
async def chat_socket(
    websocket: WebSocket, room_id: int, token: str | None = Query(default=None)
) -> None:
    await websocket.accept()
    try:
        user_id, sender_name, expires_at = await run_in_threadpool(
            _authorize, _token_from(websocket, token), room_id
        )
    except _Reject as rejection:
        await websocket.close(code=rejection.code, reason=rejection.reason)
        return

    manager.connect(room_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()

            if time.time() >= expires_at:  # access token lifetime also bounds the socket
                await websocket.close(code=4401, reason="Token expired")
                return

            try:
                frame = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue
            if not isinstance(frame, dict):
                await websocket.send_json({"type": "error", "detail": "Expected a JSON object"})
                continue

            if frame.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            content = frame.get("content")
            if not isinstance(content, str) or not content.strip():
                await websocket.send_json(
                    {"type": "error", "detail": "Message content is required"}
                )
                continue
            content = content.strip()
            if len(content) > MAX_CHAT_MESSAGE_LENGTH:
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": f"Message is too long (max {MAX_CHAT_MESSAGE_LENGTH} characters)",
                    }
                )
                continue

            try:
                payload = await run_in_threadpool(
                    _persist, room_id, user_id, sender_name, content
                )
            except _Reject as rejection:
                await websocket.close(code=rejection.code, reason=rejection.reason)
                return
            except Exception:
                logger.exception("Could not persist chat message (room=%s)", room_id)
                await websocket.send_json(
                    {"type": "error", "detail": "Could not save the message"}
                )
                continue

            await manager.broadcast(room_id, {"type": "message", "data": payload})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(room_id, websocket)
