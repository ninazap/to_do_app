import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import base


class Task(base.Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    due_date = Column(DateTime, nullable=True)
    # Новые поля для синхронизации с Google Tasks
    google_task_id = Column(String, nullable=True, index=True)
    # ID задачи в Google Tasks API

    google_tasklist_id = Column(String, nullable=True, default="@default")
    # ID списка задач в Google (по умолчанию "@default")

    synced_with_google_at = Column(DateTime, nullable=True)
    # Когда последний раз синхронизировали с Google

    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("category.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    category = relationship("Category", lazy="joined")
    user = relationship("User", back_populates="tasks")

    def __repr__(self) -> str:
        google_info = f" [Google: {self.google_task_id[:10]}...]" if self.google_task_id else ""
        return f"Task(id={self.id}, title='{self.title[:20]}...', completed={self.is_completed}{google_info})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "is_completed": self.is_completed,
            "google_task_id": self.google_task_id,
            "google_tasklist_id": self.google_tasklist_id,
            "synced_with_google_at": self.synced_with_google_at.isoformat() if self.synced_with_google_at else None,
            "category_id": str(self.category_id) if self.category_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "category": self.category.to_dict() if self.category else None,
        }

    def update_from_google_task(self, google_task: dict) -> bool:
        """
        Обновить задачу на основе данных из Google Tasks
        Возвращает True, если были изменения
        """
        changed = False

        # Обновляем статус выполнения
        google_status = google_task.get('status')
        is_completed_in_google = google_status == 'completed'

        if self.is_completed != is_completed_in_google:
            self.is_completed = is_completed_in_google
            changed = True

        # Обновляем заголовок, если изменился
        google_title = google_task.get('title', '')
        if google_title and self.title != google_title:
            self.title = google_title
            changed = True

        # Обновляем описание
        google_notes = google_task.get('notes', '')
        if google_notes is not None and self.description != google_notes:
            self.description = google_notes
            changed = True

        if changed:
            self.synced_with_google_at = datetime.utcnow()

        return changed