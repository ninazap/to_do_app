from pwdlib import PasswordHash
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi.responses import Response
from app.config import settings
from app.auth.models import User


def create_tokens(data: dict) -> dict:
    now = datetime.now(timezone.utc)
    
    acсess_expire = now + timedelta(seconds=10)
    access_payload = data.copy()
    access_payload.update({"exp": int(acсess_expire.timestamp()), "type": "access"})
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    refresh_expire = now + timedelta(days=7)
    refresh_payload = data.copy()
    refresh_payload.update({"exp": int(refresh_expire.timestamp()), "type": "refresh"})
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        }

async def authenticate_user(user, password: str) -> User | None:
    if not user or verify_password(plain_password=password, hashed_password=user.password) is False:
        return None
    return user

def set_token(response: Response, user_id: int) -> None:
    new_tokens = create_tokens(data={"sub": str(user_id)})
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


pwd_context = PasswordHash.recommended()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)