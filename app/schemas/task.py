from pydantic import BaseModel
from typing import Optional

class TaskBase(BaseModel):
    title: str
    description: str | None = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    user_id: Optional[str] = None  # Если делаете через API



class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_completed: bool | None = None


class TaskOut(TaskBase):
    id: int
    is_completed: bool

    class Config:
        orm_mode = True
