"""NotificationService (ARCH §11): persist notifications; other modules call `notify`."""
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Notification, User
from app.schemas.common import PaginationParams


def notify(
    db: Session,
    user_id: int,
    type_: str,
    title: str,
    body: str | None = None,
    data: dict[str, Any] | None = None,
) -> Notification:
    """Queue a notification inside the CALLER's transaction (the caller commits).

    A failed notification must never be a reason to fail the business operation, so callers
    that cannot tolerate that should call this after their own commit.
    """
    notification = Notification(user_id=user_id, type=type_, title=title, body=body, data=data)
    db.add(notification)
    return notification


def list_notifications(
    db: Session, user: User, params: PaginationParams, unread_only: bool = False
) -> tuple[list[Notification], int]:
    filters = [Notification.user_id == user.id]
    if unread_only:
        filters.append(Notification.is_read.is_(False))
    total = db.scalar(select(func.count(Notification.id)).where(*filters)) or 0
    items = db.scalars(
        select(Notification)
        .where(*filters)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc(), Notification.id.desc())
        .limit(params.page_size)
        .offset(params.offset)
    ).all()
    return list(items), total


def unread_count(db: Session, user: User) -> int:
    return (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id, Notification.is_read.is_(False)
            )
        )
        or 0
    )


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    if notification is None:
        raise NotFoundError("Notification not found")
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = func.now()
        db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user: User) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read.is_(False))
        .values(is_read=True, read_at=func.now())
    )
    db.commit()
    return result.rowcount or 0
