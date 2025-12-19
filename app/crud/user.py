import uuid

from typing import Optional

from sqlalchemy.orm import Session
from models.user import User
from schemas.theme import ThemeUpdate


def get_user(db: Session, user_id: str):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return None

    return db.query(User).filter(User.uuid == user_uuid).first()

def update_user_theme(db: Session, user_id: str, theme_update: ThemeUpdate):
    user = get_user(db, user_id)
    if not user:
        return None

    user.theme = theme_update.theme
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Найти пользователя по email"""
    return db.query(User).filter(User.email == email).first()

def get_or_create_user_by_email(db: Session, email: str) -> User:
    """Получить или создать пользователя по email"""
    user = get_user_by_email(db, email)
    if not user:
        # Создаем нового пользователя
        user = User(
            uuid=uuid4(),
            email=email,
            username=email.split('@')[0],
            hashed_password="",  # Пустой пароль для пользователей из auth сервиса
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user