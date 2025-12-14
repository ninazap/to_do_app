"""Эндпоинты аутентификации - полная версия со всеми требованиями."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from app.crud.user import (
    create_user,
    change_user_password,
    update_user,
    get_user,
)
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    UserChangePassword,
    UserUpdate,
)
from app.core.config import settings
from app.models.user import User

# Создаем роутер
router = APIRouter(prefix="/auth", tags=["auth"])


def create_refresh_token(data: dict) -> str:
    """Создает refresh токен (долгоживущий)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 7 дней для refresh токена
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Регистрация нового пользователя.

    - **username**: имя пользователя (уникальное)
    - **email**: email пользователя (уникальный)
    - **password**: пароль
    - **full_name**: полное имя (опционально)
    """
    try:
        user = create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Аутентификация пользователя.

    - **username_or_email**: имя пользователя ИЛИ email
    - **password**: пароль

    Возвращает access token и информацию о пользователе.
    """
    user = authenticate_user(db, login_data.username_or_email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя/email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создаем access token (короткоживущий)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.uuid),
            "username": user.username,
            "email": user.email,
            "type": "access"
        },
        expires_delta=access_token_expires
    )

    # Создаем refresh token (долгоживущий)
    refresh_token = create_refresh_token(
        data={
            "sub": str(user.uuid),
            "username": user.username,
            "email": user.email
        }
    )

    # Формируем ответ с информацией о пользователе
    user_response = UserResponse.from_orm(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,  # В реальном API лучше через httpOnly куки
        "user": user_response
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Обновление access токена с помощью refresh токена.

    - **refresh_token**: refresh токен, полученный при логине

    Возвращает новый access token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный refresh токен",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодируем refresh токен
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Проверяем, что это refresh токен
        if payload.get("type") != "refresh":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Получаем пользователя из БД
    user = get_user(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    # Создаем новый access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.uuid),
            "username": user.username,
            "email": user.email,
            "type": "access"
        },
        expires_delta=access_token_expires
    )

    # Создаем новый refresh token (ротация refresh токенов)
    new_refresh_token = create_refresh_token(
        data={
            "sub": str(user.uuid),
            "username": user.username,
            "email": user.email
        }
    )

    user_response = UserResponse.from_orm(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
        "user": user_response
    }


@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Смена пароля текущего пользователя.

    - **current_password**: текущий пароль
    - **new_password**: новый пароль

    Требует аутентификации.
    """
    try:
        user = change_user_password(db, str(current_user.uuid), password_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        return {
            "message": "Пароль успешно изменен",
            "user": {
                "uuid": str(user.uuid),
                "username": user.username,
                "email": user.email
            }
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_active_user)
):
    """
    Получение данных текущего пользователя.

    Требует аутентификации.
    Возвращает информацию о текущем пользователе.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Обновление данных текущего пользователя.

    - **full_name**: полное имя (опционально)
    - **bio**: информация о себе (опционально)
    - **theme**: тема интерфейса (light/dark)

    Требует аутентификации.
    """
    user = update_user(db, str(current_user.uuid), user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user


@router.post("/logout", response_model=dict)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Выход из системы.

    В JWT-аутентификации logout обычно клиентская операция.
    Сервер инвалидирует refresh токен (в реальном приложении).
    """
    return {
        "message": "Успешный выход из системы",
        "user": {
            "username": current_user.username,
            "email": current_user.email
        }
    }