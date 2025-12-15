# app/schemas/task.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
import uuid


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: int = Field(0, ge=0, le=10)
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    user_id: Optional[str] = None
    category_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=10)
    due_date: Optional[datetime] = None


class TaskOut(TaskBase):
    id: int
    is_completed: bool
    category_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)