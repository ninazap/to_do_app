from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..dao.database import Base, str_uniq

class Role(Base):
    name: Mapped[str_uniq]
    users: Mapped[list["User"]] = relationship(back_populates="role")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"

class User(Base):
    phone_number: Mapped[str_uniq]
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str_uniq]
    password: Mapped[str]
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), default=1, server_default=text("1"))
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}"