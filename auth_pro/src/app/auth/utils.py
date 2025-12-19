
from pwdlib import PasswordHash
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi.responses import Response
from loguru import logger
from uuid import UUID

from src.app.config import settings
from src.app.auth.models import User
from src.app.sync.user_sync import async_user_sync_service

pwd_context = PasswordHash.recommended()


def create_tokens(data: dict):
    now = datetime.now(timezone.utc)
    
    access_expire = now + timedelta(seconds=1800)
    access_payload = data.copy()
    access_payload.update({"exp": int(access_expire.timestamp()), "type": "access"})
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    refresh_expire = now + timedelta(days=7)
    refresh_payload = data.copy()
    refresh_payload.update({"exp": int(refresh_expire.timestamp()), "type": "refresh"})
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        }

async def authenticate_user(user: User | None, password: str) -> User | None:
    if not user:
        return None
    if not user.password:
        return None
    
    try:
        if verify_password(password, user.password):
            return user
    except Exception:
        logger.error(f"Error verifying password for user {user.email}")
    
    return None

def set_token(response: Response, user_uuid: UUID) -> None:
    new_tokens = create_tokens(data={"sub": str(user_uuid)})
    access_token = new_tokens.get("access_token")
    refresh_token = new_tokens.get("refresh_token") 
    
    response.set_cookie(
        key="user_access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    
    response.set_cookie(
        key="user_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def sync_user_to_todo_service(user):
    try:
        user_data = {
            "uuid": str(user.uuid),
            "email": user.email,
            "username": getattr(user, "username", "") or user.email.split("@")[0],
            "is_active": user.is_active,
            "is_superuser": getattr(user, "is_superuser", False),
            "bio": getattr(user, "bio", ""),
            "theme": getattr(user, "theme", "light")
        }

        success = await async_user_sync_service.sync_user_to_todo_db(user_data)

        if success:
            return True, "Synced successfully"

        return False, "Sync failed"

    except Exception as e:
        return False, f"Unexpected error: {e}"
