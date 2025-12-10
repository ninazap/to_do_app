from uuid import UUID

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict



# Базовые схемы
class TaskBase(BaseModel):
    media_id: UUID = None
    desc: Optional[str] = None
    category_id: UUID | None = None