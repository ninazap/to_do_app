

from typing import List
from fastapi import APIRouter, Depends, Response, status, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timezone
from uuid import UUID

from .models import User
from .utils import authenticate_user, set_token, create_tokens, sync_user_to_todo_service
from ..dependencies.auth_dep import get_current_user, get_current_admin_user, check_refresh_token
from ..dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from src.exception import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from .dao import UsersDAO
from .schemas import SUserRegister, EmailModel, SUserAddDB, SUserInfo
from src.app.config import settings
from src.app.core.redis import redis_client

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register")
async def register_user(
    user_data: SUserRegister,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_with_commit),
    
) -> dict:
    
    user_dao = UsersDAO(session)
    existing_user = await user_dao.find_one_or_none(filters=EmailModel(email=user_data.email))
    if existing_user:
        raise UserAlreadyExistsException
    
    user_data_dict = user_data.model_dump()
    user_data_dict.pop("confirm_password", None)

    await user_dao.add(values=SUserAddDB(**user_data_dict))
    
    saved_user = await user_dao.find_one_or_none(filters=EmailModel(email=user_data.email))
    if saved_user:
            background_tasks.add_task(sync_user_to_todo_service, saved_user)

    return {
        "message": "User registered successfully",
        "email": user_data.email,
        "note": "User will be synced to todo service in background"
    }

@router.post("/login", response_model=dict)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session_without_commit),
    response: Response = None,
) -> dict:
    user_dao = UsersDAO(session)
    
    user = await user_dao.find_one_or_none(filters=EmailModel(email=form_data.username))
    
    if not user:
        raise IncorrectEmailOrPasswordException

    auth_user = await authenticate_user(user=user, password=form_data.password)
    
    if not auth_user:
        raise IncorrectEmailOrPasswordException
    
    tokens = create_tokens(data={"sub": str(user.uuid)})
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    try:
        payload = jwt.decode(
            access_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            now = datetime.now(timezone.utc).timestamp()
            expires_in = int(exp_timestamp - now)
            if expires_in > 0:
                redis_client.set_token(
                    token=access_token,
                    email=user.email,
                    expire_seconds=expires_in
                )
    except jwt.JWTError:
        pass
    
    try:
        refresh_payload = jwt.decode(
            refresh_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        refresh_exp_timestamp = refresh_payload.get("exp")
        if refresh_exp_timestamp:
            now = datetime.now(timezone.utc).timestamp()
            refresh_expires_in = int(refresh_exp_timestamp - now)
            if refresh_expires_in > 0:
                redis_client.set_session(
                    token=f"refresh:{refresh_token}",
                    user_data={"uuid": str(user.uuid), "email": user.email},
                    expire_seconds=refresh_expires_in
                )
    except jwt.JWTError:
        pass
    
    if response:
        set_token(response, user.uuid)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "uuid": str(user.uuid)
        }
    }

@router.post("/logout")
async def logout(response: Response, token: str = Depends(oauth2_scheme)) -> dict:
    redis_client.delete_token(token)
    if response:
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
    return {
        "message": "User logged out successfully"
    }

@router.get("/verify", response_model=dict)
async def verify_token(
    token: str = Depends(oauth2_scheme)
) -> dict:
    user_email = redis_client.get_token(token)
    if user_email:
        return {
            "email": user_email,
            "valid": True,
            "source": "redis"
        }
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        user_uuid_str = payload.get("sub")
        if not user_uuid_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        
        
        db = await anext(get_session_without_commit())
        user_dao = UsersDAO(db)
        
        user = await user_dao.find_one_or_none(uuid=UUID(user_uuid_str))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            now = datetime.now(timezone.utc).timestamp()
            expires_in = int(exp_timestamp - now)
            if expires_in > 0:
                redis_client.set_token(
                    token=token,
                    email=user.email,
                    expire_seconds=expires_in
                )
        
        return {
            "email": user.email,
            "uuid": str(user.uuid),
            "valid": True,
            "source": "jwt"
        }
        
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user UUID",
        )

@router.get("/me")
async def get_me(user_data: User = Depends(get_current_user)) -> SUserInfo:
    return SUserInfo.model_validate(user_data)

@router.get("/all_users/")
async def get_all_users(
    session: AsyncSession = Depends(get_session_without_commit), 
    user_data: User = Depends(get_current_admin_user)
) -> List[SUserInfo]:
    user_dao = UsersDAO(session)
    users = await user_dao.find_all()
    return [SUserInfo.model_validate(user) for user in users]

@router.post("/refresh/", response_model=dict)
async def process_refresh_token(
    response: Response, 
    user: User = Depends(check_refresh_token)
) -> dict:
    tokens = create_tokens(data={"sub": str(user.uuid)})
    access_token = tokens["access_token"]
    
    try:
        payload = jwt.decode(
            access_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            now = datetime.now(timezone.utc).timestamp()
            expires_in = int(exp_timestamp - now)
            if expires_in > 0:
                redis_client.set_token(
                    token=access_token,
                    email=user.email,
                    expire_seconds=expires_in
                )
    except jwt.JWTError:
        pass
    
    # Устанавливаем куки
    set_token(response, user.uuid)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Token refreshed successfully"
    }

@router.post("/admin/sync-to-todo/{email}")
async def admin_sync_user_to_todo(
    email: str,
    session: AsyncSession = Depends(get_session_without_commit),
    current_user: User = Depends(get_current_admin_user)
):
    user_dao = UsersDAO(session)
    user = await user_dao.find_one_or_none(filters=EmailModel(email=email))
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success, message = await sync_user_to_todo_service(user)
    
    return {
        "email": email,
        "success": success,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }