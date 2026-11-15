"""Notification schemas."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    body: str | None = None
    data: dict[str, Any] | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class UnreadCount(BaseModel):
    unread: int


class MarkAllReadResult(BaseModel):
    updated: int
