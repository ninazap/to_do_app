import uuid

from datetime import datetime, timezone
from fastapi import Request, Depends
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dao import UsersDAO
from ..auth.models import User
from ..config import settings
from .dao_dep import get_session_without_commit
from ...exception import TokenNoFound, NoJwtException, TokenExpiredException, NoUserIdException, ForbiddenException, UserNotFoundException



def get_access_token(request: Request) -> str:
    """Извлекает access токен из cookies ИЛИ из заголовка"""
    # Сначала пробуем из cookies (как у вас работает логин)
    token = request.cookies.get("user_access_token")
    if token:
        return token
    
    # Затем пробуем из заголовка Authorization (для совместимости)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split("Bearer ")[1]
    
    # Если токена нет нигде
    raise TokenNoFound


def get_refresh_token(request: Request) -> str:
    token = request.cookies.get("user_refresh_token")
    if not token:
        raise TokenNoFound
    return token


async def check_refresh_token(token: str = Depends(get_refresh_token), session: AsyncSession = Depends(get_session_without_commit)) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_uuid_str = payload.get("sub")
        if not user_uuid_str:
            raise NoJwtException
        
        if payload.get("type") != "refresh":
            raise NoJwtException
        
        try:
            user_uuid = uuid.UUID(user_uuid_str)
        except ValueError:
            raise NoJwtException
        
        user = await UsersDAO(session).find_one_or_none_by_uuid(data_uuid=user_uuid)
        if not user:
            raise NoJwtException
        
        return user
    except JWTError:
        raise NoJwtException


async def get_current_user(token: str = Depends(get_access_token), session: AsyncSession = Depends(get_session_without_commit)) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
    except ExpiredSignatureError:
        raise TokenExpiredException
    except JWTError:
        raise NoJwtException
    
    if payload.get("type") != "access":
        raise NoJwtException
    
    expire: str = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise TokenExpiredException
    
    user_id: str = payload.get("sub")
    if not user_id:
        raise NoUserIdException
    
    user_uuid_str: str = payload.get("sub")  # Переименовали для ясности
    if not user_uuid_str:
        raise NoUserIdException
    
    try:
        user_uuid = uuid.UUID(user_uuid_str)
    except ValueError:
        raise NoJwtException
    
    user = await UsersDAO(session).find_one_or_none_by_uuid(data_uuid=user_uuid)
    if not user:
        raise UserNotFoundException
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if hasattr(current_user, 'role_id'):
        if current_user.role_id in [3, 4]:  # Роли администратора
            return current_user
    elif hasattr(current_user, 'role') and hasattr(current_user.role, 'id'):
        if current_user.role.id in [3, 4]:
            return current_user
    elif hasattr(current_user, 'is_superuser') and current_user.is_superuser:
        return current_user
    raise ForbiddenException