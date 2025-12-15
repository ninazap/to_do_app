"""Схемы Pydantic для пользователей и аутентификации."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import uuid


class UserBase(BaseModel):
    """Базовая схема пользователя."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Схема для создания пользователя (регистрация)."""
    password: str = Field(..., min_length=6)

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Имя пользователя должно быть не менее 3 символов')
        if not v.replace('_', '').isalnum():
            raise ValueError('Имя пользователя должно содержать только буквы, цифры и подчеркивания')
        return v


class UserLogin(BaseModel):
    """Схема для входа пользователя."""
    username_or_email: str
    password: str


class UserChangePassword(BaseModel):
    """Схема для смены пароля."""
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Схема для обновления данных пользователя."""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    theme: Optional[str] = "light"


class UserResponse(UserBase):
    """Схема ответа с данными пользователя."""
    uuid: uuid.UUID
    is_active: bool
    is_superuser: bool
    theme: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Схема ответа с токеном."""
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None  # Добавим информацию о пользователе


class RefreshToken(BaseModel):
    """Схема для обновления токена."""
    refresh_token: str