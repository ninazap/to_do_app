# app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship  # Добавьте этот импорт
from .base import Base

class User(Base):
    __tablename__ = "users"

    uuid = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    is_active = Column(
        Boolean,
        default=True
    )
    is_superuser = Column(
        Boolean,
        default=False
    )
    bio = Column(
        Text,
        nullable=True
    )
    theme = Column(
        String(20),
        default="light",
        nullable=False
    )
    created_at = Column(
        TIMESTAMP, 
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.now(), 
        onupdate=func.now()
    )

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """Преобразует в словарь (без чувствительных данных)"""
        return {
            "uuid": str(self.uuid),
            "email": self.email,
            "username": self.username,
            "theme": self.theme,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
