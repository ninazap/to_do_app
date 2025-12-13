import uuid
from typing import Any

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import base


class Task(base.Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)

    priority = Column(Integer, default=0)
    due_date = Column(DateTime, nullable=True)

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
        return f""

    def to_dict(self) -> dict[str, Any]:
        return {}
