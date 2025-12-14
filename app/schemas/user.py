"""Схемы Pydantic для пользователей и аутентификации."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid


class UserBase(BaseModel):
    """Базовая схема пользователя."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Схема для создания пользователя (регистрация)."""
    password: str


class UserLogin(BaseModel):
    """Схема для входа пользователя."""
    username_or_email: str
    password: str


class UserChangePassword(BaseModel):
    """Схема для смены пароля."""
    current_password: str
    new_password: str


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