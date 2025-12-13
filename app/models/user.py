# app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
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
    hashed_password = Column(
        String(255),
        nullable=False
    )
    full_name = Column(
        String(100),
        nullable=True
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
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    tasks = relationship("Task", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"