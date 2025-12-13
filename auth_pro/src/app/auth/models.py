import uuid

from sqlalchemy import text, ForeignKey, UUID, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from ..dao.database import Base, str_uniq

class Role(Base):
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str_uniq]
    users: Mapped[list["User"]] = relationship(back_populates="role")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"

class User(Base):
    __tablename__ = 'users'
    
    #Основные поля
    uuid = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str_uniq]
    first_name: Mapped[str]
    last_name: Mapped[str]
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str_uniq]
    password: Mapped[str]
    
    #Статус и права
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    #Доп. поля
    bio: Mapped [str | None] = mapped_column(Text, nullable=True)
    
    #Связь с ролью
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), default=1, server_default=text("1"))
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")
    
    @property
    def username(self) -> str:
        """Для совместимости с to_do системой"""
        return self.email.split("@")[0] # или phone_number, или что-то другое
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.uuid}"