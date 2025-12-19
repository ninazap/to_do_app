
from typing import Any
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import base


class Task(base.Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)

    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("category.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    user_email = Column(
        String(100),
        ForeignKey("users.email", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    category = relationship("Category", lazy="joined")
    user = relationship("User", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}')>"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "is_completed": self.is_completed,
            "user_email": self.user_email,
            "category_id": str(self.category_id) if self.category_id else None
        }
