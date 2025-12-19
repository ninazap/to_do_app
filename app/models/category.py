
from typing import Any

from sqlalchemy import Column, String, Text

from models.base import Base, BaseModelMixin


class Category(Base, BaseModelMixin):
    __tablename__ = "category"

    name = Column(String, nullable=False, unique=True)
    desc = Column(Text)

    def __repr__(self) -> str:
        return f"uuid - {self.uuid}, name - {self.name} desc - {self.desc}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "desc": self.desc,
        }

