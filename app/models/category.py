
from typing import Any

from sqlalchemy import Column, String, Text

from app.models.base import Base, BaseModelMixin


class Category(Base, BaseModelMixin):
    __tablename__ = "category"

    name = Column(String, nullable=False, unique=True)
    desc = Column(Text)

    # posts = relationship("Posts", back_populates="category")

    def __repr__(self) -> str:
        return f"uuid - {self.uuid}, name - {self.name} desc - {self.desc}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "desc": self.desc,
        }

