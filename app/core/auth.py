import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
from typing import Optional, Dict, Any
import logging
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .redis_client import get_redis
from services.user_service import UserService

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.AUTH_SERVICE_URL}/auth/login",
    auto_error=False
)



class AuthService:
    def __init__(self):
        self.base_url = settings.AUTH_SERVICE_URL.rstrip('/')
    
    async def verify_token_remote(self, token: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Auth service returned {response.status_code}")
                    return None
            except httpx.RequestError as e:
                logger.error(f"Auth service request error: {e}")
                return None
    
    async def get_user_info_remote(self, token: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"Auth service returned {response.status_code} for /auth/me")
                return None
            except httpx.RequestError as e:
                logger.error(f"Error getting user info: {e}")
                return None
    
    async def get_current_user_email(self, token: str) -> Optional[str]:
        redis_client = get_redis()
        
        # 1. Проверяем в Redis (быстрая проверка)
        redis_key = f"token:{token}"
        user_email = redis_client.get(redis_key)
        if user_email:
            logger.debug(f"Token found in Redis for email: {user_email}")
            return user_email
        
        # 2. Если нет в Redis, проверяем через auth service
        token_data = await self.verify_token_remote(token)
        if token_data and token_data.get("valid"):
            email = token_data.get("email")
            if email:
                # Сохраняем в Redis для будущих запросов
                redis_client.setex(redis_key, settings.REDIS_TOKEN_TTL, email)
                logger.debug(f"Token verified via auth service for email: {email}")
                return email
        
        return None

auth_service = AuthService()

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_email = await auth_service.get_current_user_email(token)
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_info = await auth_service.get_user_info_remote(token)
    
    if user_info:
        user_data = {
            "email": user_email,
            "uuid": user_info.get("uuid"),
            "username": user_info.get("username", user_email.split('@')[0]),
            "is_active": user_info.get("is_active", True),
            "theme": user_info.get("theme", "light"),
            "created_at": user_info.get("created_at")
        }
        
        user = UserService.get_or_create_lightweight_user(db, user_data)
        
        return {
            "email": user.email,
            "uuid": str(user.uuid) if user.uuid else None,
            "username": user.username,
            "theme": user.theme,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    user_data = {
        "email": user_email,
        "username": user_email.split('@')[0],
        "is_active": True,
        "theme": "light"
    }
    
    user = UserService.get_or_create_lightweight_user(db, user_data)
    
    return {
        "email": user.email,
        "username": user.username,
        "theme": user.theme,
        "is_active": user.is_active
    }

async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    
    user_email = await auth_service.get_current_user_email(token)
    if not user_email:
        return None
    
    user = UserService.get_user_by_email(db, user_email)
    if user:
        return {
            "email": user.email,
            "uuid": str(user.uuid) if user.uuid else None,
            "username": user.username,
            "theme": user.theme,
            "is_active": user.is_active
        }
    
    return {"email": user_email}

async def require_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    return current_user