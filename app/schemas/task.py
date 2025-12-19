from pydantic import BaseModel, ConfigDict
from uuid import UUID

class TaskBase(BaseModel):
    title: str
    description: str | None = None
    is_completed: bool = False


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_completed: bool | None = None


class TaskOut(TaskBase):
    id: int
    user_email: str
    category_id: UUID | None = None
    
    model_config = ConfigDict(from_attributes=True)
