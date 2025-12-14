# app/crud/user.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserChangePassword
from app.core.security import get_password_hash, verify_password, get_user_by_email, get_user_by_username
import uuid


def get_user(db: Session, user_id: str) -> User | None:
    """Получает пользователя по ID."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return None
    return db.query(User).filter(User.uuid == user_uuid).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """Создает нового пользователя."""
    # Проверяем, существует ли пользователь с таким email или username
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise ValueError("Пользователь с таким email уже существует")

    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise ValueError("Пользователь с таким именем уже существует")

    # Создаем пользователя
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        bio=getattr(user_data, 'bio', None)  # Если bio есть в схеме
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Не удалось создать пользователя")


def update_user(db: Session, user_id: str, user_data: UserUpdate) -> User | None:
    """Обновляет данные пользователя."""
    user = get_user(db, user_id)
    if not user:
        return None

    # Обновляем только переданные поля
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def change_user_password(db: Session, user_id: str, password_data: UserChangePassword) -> User | None:
    """Изменяет пароль пользователя."""
    user = get_user(db, user_id)
    if not user:
        return None

    # Проверяем текущий пароль
    if not verify_password(password_data.current_password, user.hashed_password):
        raise ValueError("Неверный текущий пароль")

    # Устанавливаем новый пароль
    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    db.refresh(user)
    return user


def update_user_theme(db: Session, user_id: str, theme: str) -> User | None:
    """Обновляет тему пользователя."""
    user = get_user(db, user_id)
    if not user:
        return None

    user.theme = theme
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: str) -> User | None:
    """Деактивирует пользователя."""
    user = get_user(db, user_id)
    if not user:
        return None

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


def activate_user(db: Session, user_id: str) -> User | None:
    """Активирует пользователя."""
    user = get_user(db, user_id)
    if not user:
        return None

    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    """Получает всех пользователей."""
    return db.query(User).offset(skip).limit(limit).all()