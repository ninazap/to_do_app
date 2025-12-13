# app/schemas/theme.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class ThemeEnum(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

class ThemeBase(BaseModel):
    theme: ThemeEnum = Field(
        default=ThemeEnum.LIGHT,
        description="Тема интерфейса: light, dark или system"
    )

class ThemeUpdate(ThemeBase):
    pass

class ThemeResponse(ThemeBase):
    user_id: str = Field(..., description="UUID пользователя")
    username: str = Field(..., description="Имя пользователя")

    class Config:
        from_attributes = True