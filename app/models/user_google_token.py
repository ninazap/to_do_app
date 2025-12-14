import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base


class UserGoogleToken(Base):
    __tablename__ = "user_google_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False, unique=True)

    # Google OAuth возвращает JSON с токенами. Будем хранить его как строку.
    token_data = Column(String, nullable=False)

    # Когда токен был обновлен
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = relationship("User", backref="google_token")

    def is_token_expired(self):
        """Проверяем, истек ли срок действия токена (примерно через 1 час)."""
        # Можно добавить логику проверки из token_data
        return datetime.utcnow() > self.updated_at + timedelta(hours=1)