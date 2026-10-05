from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: UUID,
        *,
        type: str = "info",
        title: str,
        body: str = "",
        link: str | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            link=link,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_for_user(self, user: User, limit: int = 50) -> list[Notification]:
        return list(
            self.db.scalars(
                select(Notification)
                .where(Notification.user_id == user.id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
            ).all()
        )

    def unread_count(self, user: User) -> int:
        return int(
            self.db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.user_id == user.id,
                    Notification.is_read.is_(False),
                )
            )
            or 0
        )

    def mark_all_read(self, user: User) -> None:
        self.db.execute(
            update(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        self.db.commit()
