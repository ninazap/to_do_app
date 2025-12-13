import re

from typing import Self, Optional
from pydantic import SecretStr, BaseModel, EmailStr, ConfigDict, Field, field_validator, model_validator, computed_field
from datetime import datetime
from uuid import UUID

from ..auth.utils import get_password_hash

class EmailModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr = Field(description="User email address")

class UserBase(EmailModel):
    phone_number: str = Field(description="User phone number, start with '+'")
    first_name: str = Field(min_length=3, max_length=50, description="User first name")
    last_name: str = Field(min_length=3, max_length=50, description="User last name")
    bio: str | None = Field(None, description="User biography")
    
    @field_validator("phone_number")
    def validate_phone_number(cls, value: str) -> str:
        pattern = r"^\+\d{10,15}$"
        if not re.match(pattern, value):
            raise ValueError("Phone number must start with '+' and contain 10 to 15 digits.")
        return value
    
    @computed_field
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"

class SUserRegister(UserBase):
    password: str = Field(min_length=8, max_length=50, description="User password")
    confirm_password: str = Field(min_length=8, max_length=50, description="Password confirmation")
    
    @model_validator(mode="after")
    def chek_passwords(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        self.password = get_password_hash(self.password)
        return self

class SUserAddDB(UserBase):
    password: str = Field(min_length=5, description="Hashed user password")

class SUserAuth(EmailModel):
    password: str = Field(min_length=8, max_length=50, description="User password")

class RoleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Role ID")
    name: str = Field(description="Role name")

class SUserInfo(UserBase):
    uuid: UUID = Field(description="User UUID")
    is_active: bool = Field(description="Is user active")
    is_superuser: bool = Field(description="Is user superuser")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    role: RoleModel = Field(description="User role")
    
    
    @computed_field
    def role_name(self) -> str:
        return self.role.name
    
    @computed_field
    def role_id(self) -> int:
        return self.role.id
    @computed_field
    def username(self) -> str:
        """Для совместимости с to_do системой"""
        return self.email.split('@')[0]

# Для обновления профиля
class SUserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    first_name: str | None = Field(None, min_length=3, max_length=50)
    last_name: str | None = Field(None, min_length=3, max_length=50)
    full_name: str | None = Field(None, max_length=100)
    bio: str | None = None
    phone_number: str | None = Field(None, pattern=r"^\+\d{10,15}$")


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Название роли")

class RoleCreate(RoleBase):
    id: int
    name: str

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="Название роли")

class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    users_count: Optional[int] = Field(None, description="Количество пользователей с этой ролью")

# Для связывания пользователя с ролью
class UserRoleUpdate(BaseModel):
    role_id: int = Field(..., description="ID новой роли пользователя")

class RoleFilter(BaseModel):
    """Модель для фильтрации ролей"""
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = Field(None, description="ID роли")
    name: Optional[str] = Field(None, description="Название роли")