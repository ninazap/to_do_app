"""Модуль безопасности: хеширование паролей, JWT токены."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import hashlib

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# Контекст для хеширования паролей
pwd_context = CryptContext(
    schemes=["bcrypt", "sha256_crypt"],
    deprecated="auto"
)

# OAuth2 схема для токенов
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля его хешу."""
    # Сначала пробуем стандартную проверку
    try:
        if pwd_context.verify(plain_password, hashed_password):
            return True
    except Exception:
        pass

    # Если не сработало, пробуем SHA256 (для существующих пользователей)
    if len(hashed_password) == 64 and all(c in '0123456789abcdef' for c in hashed_password):
        sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        if sha256_hash == hashed_password:
            return True

    return False


def get_password_hash(password: str) -> str:
    """Создает хеш пароля."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT токен (access token)."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Получает пользователя по email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Получает пользователя по имени пользователя."""
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
    """Аутентифицирует пользователя по username или email и паролю."""
    # Сначала пробуем найти по username
    user = get_user_by_username(db, username_or_email)

    # Если не нашли по username, пробуем по email
    if not user:
        user = get_user_by_email(db, username_or_email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    # Если хеш был SHA256 (64 hex символа), обновляем его на bcrypt
    if len(user.hashed_password) == 64 and all(c in '0123456789abcdef' for c in user.hashed_password):
        user.hashed_password = get_password_hash(password)
        db.commit()

    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Получает текущего пользователя из access токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Проверяем, что это access токен
        if payload.get("type") != "access":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Импортируем здесь, чтобы избежать циклического импорта
    from app.crud.user import get_user
    user = get_user(db, user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, активен ли текущий пользователь."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь неактивен"
        )
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, является ли текущий пользователь суперпользователем."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user