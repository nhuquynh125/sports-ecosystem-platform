"""In-process registry of open WebSocket connections, grouped by chat room.

Limitation (documented in backend/README.md): connections live in this process only. Running
several API instances needs a shared broker (Redis pub/sub / Postgres LISTEN-NOTIFY) behind
`broadcast`; the rest of the code would not change.
"""
import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[int, set[WebSocket]] = defaultdict(set)

    def connect(self, room_id: int, websocket: WebSocket) -> None:
        """Register an already-accepted socket."""
        self._rooms[room_id].add(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        sockets = self._rooms.get(room_id)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            self._rooms.pop(room_id, None)

    def connection_count(self, room_id: int) -> int:
        return len(self._rooms.get(room_id, ()))

    async def broadcast(self, room_id: int, payload: dict[str, Any]) -> None:
        sockets = list(self._rooms.get(room_id, ()))
        if not sockets:
            return
        results = await asyncio.gather(
            *(socket.send_json(payload) for socket in sockets), return_exceptions=True
        )
        for socket, result in zip(sockets, results, strict=True):
            if isinstance(result, Exception):  # dead connection: drop it
                self.disconnect(room_id, socket)


manager = ConnectionManager()
