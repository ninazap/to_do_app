import re
from typing import Self
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, model_validator, computed_field

from ..auth.utils import get_password_hash

class EmailModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr = Field(description="User email address")

class UserBase(EmailModel):
    phone_number: str = Field(description="User phone number, start with '+'")
    first_name: str = Field(min_length=3, max_length=50, description="User first name")
    last_name: str = Field(min_length=3, max_length=50, description="User last name")
    
    @field_validator("phone_number")
    def validate_phone_number(cls, value: str) -> str:
        pattern = r"^\+\d{10,15}$"
        if not re.match(pattern, value):
            raise ValueError("Phone number must start with '+' and contain 10 to 15 digits.")
        return value

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
    id: int = Field(description="User ID")
    role: RoleModel = Field(exclude=True, description="User role")
    
    @computed_field
    def role_name(self) -> str:
        return self.role.name
    
    @computed_field
    def role_id(self) -> int:
        return self.role.id