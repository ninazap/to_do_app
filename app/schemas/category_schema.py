from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    desc: Optional[str] = None

