from typing import List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .utils import authenticate_user, set_token
from ..dependencies.auth_dep import get_current_user, get_current_admin_user, check_refresh_token
from ..dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from exception import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from .dao import UsersDAO
from .schemas import SUserRegister, SUserAuth, EmailModel, SUserAddDB, SUserInfo

router = APIRouter()

@router.post("/register")
async def register_user(user_data: SUserRegister, session: AsyncSession = Depends(get_session_with_commit)) -> dict:
    user_dao = UsersDAO(session)
    existing_user = await user_dao.find_one_or_none(filtres=EmailModel(email=user_data.email))
    if existing_user:
        raise UserAlreadyExistsException
    
    user_data_dict = user_data.model_dump()
    user_data_dict.pop("confirm_password", None)
    
    await user_dao.add(values=SUserAddDB(**user_data_dict))
    
    return {"message": "User registered successfully"}

@router.post("/login")
async def auth_user(user_data: SUserAuth, response: Response, session: AsyncSession = Depends(get_session_without_commit)) -> dict:
    user_dao = UsersDAO(session)
    user = await user_dao.find_one_or_none(filters=EmailModel(email=user_data.email))
    
    if not (user and await authenticate_user(user=user, password=user_data.password)):
        raise IncorrectEmailOrPasswordException
    set_token(response, user.id)
    
    return {
        "Ok": True,
        "message": "User authenticated successfully"
    }


@router.post("logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {
        "message": "User logged out successfully"
    }

@router.get("/me")
async def get_me(user_data: User = Depends(get_current_user)) -> SUserInfo:
    return SUserInfo.model_validate(user_data)

@router.get("/all_users/")
async def get_all_users(session: AsyncSession = Depends(get_session_without_commit), 
                        user_data: User = Depends(get_current_admin_user)) -> List[SUserInfo]:
    return await UsersDAO(session).find_all()

@router.post("/refresh/")
async def process_refresh_token(response: Response, user: User = Depends(check_refresh_token)) -> dict:
    set_token(response, user_data.id)
    return {
        "message": "Token refreshed successfully"
    }