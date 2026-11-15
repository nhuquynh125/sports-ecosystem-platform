from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Page, PaginationParams, paginate
from app.schemas.notification import MarkAllReadResult, NotificationRead, UnreadCount
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=Page[NotificationRead], summary="My notifications (unread first)")
def list_notifications(
    user: CurrentUser,
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
    unread_only: Annotated[bool, Query()] = False,
):
    items, total = notification_service.list_notifications(db, user, params, unread_only)
    return paginate(items, total, params)


@router.get("/unread-count", response_model=UnreadCount, summary="Number of unread notifications")
def unread_count(user: CurrentUser, db: DbSession):
    return UnreadCount(unread=notification_service.unread_count(db, user))


@router.patch("/read-all", response_model=MarkAllReadResult, summary="Mark all as read")
def read_all(user: CurrentUser, db: DbSession):
    return MarkAllReadResult(updated=notification_service.mark_all_read(db, user))


@router.patch("/{notification_id}/read", response_model=NotificationRead, summary="Mark one as read")
def read_one(notification_id: int, user: CurrentUser, db: DbSession):
    return notification_service.mark_read(db, user, notification_id)
