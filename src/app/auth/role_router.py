from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Role, User
from .schemas import RoleCreate, RoleUpdate, RoleResponse, UserRoleUpdate, RoleFilter
from .dao import RoleDAO, UsersDAO
from src.app.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from src.exception import ForbiddenException
from src.app.dependencies.auth_dep import get_current_admin_user

router = APIRouter()


@router.post("/create", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_session_with_commit),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать новую роль (только для администраторов)"""
    role_dao = RoleDAO(session)
    
    # Проверяем, существует ли роль с таким именем
    existing_role = await role_dao.find_by_name(role_data.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{role_data.name}' already exists"
        )
    id_role = await role_dao.find_by_id(role_data.id)
    if id_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{role_data.id}' already exists"
        )
    
    # Создаем новую роль
    new_role = await role_dao.add(values=role_data)
    
    # Получаем количество пользователей (0 для новой роли)
    new_role.users_count = 0
    
    return new_role


@router.get("/getrole", response_model=List[RoleResponse])
async def get_all_roles(
    session: AsyncSession = Depends(get_session_without_commit),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить все роли (только для администраторов)"""
    role_dao = RoleDAO(session)
    roles = await role_dao.get_all_with_counts()
    return roles


@router.get("/getbyid/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    session: AsyncSession = Depends(get_session_without_commit),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить роль по ID (только для администраторов)"""
    role_dao = RoleDAO(session)
    role = await role_dao.find_one_or_none_by_id(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Получаем количество пользователей
    role.users_count = await role_dao.get_users_count(role.id)
    
    return role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    session: AsyncSession = Depends(get_session_with_commit),
    current_user: User = Depends(get_current_admin_user)
):
    """Обновить роль (только для администраторов)"""
    role_dao = RoleDAO(session)
    
    # Проверяем существование роли
    role = await role_dao.find_one_or_none_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Проверяем новое имя на уникальность (если оно изменилось)
    if role_data.name and role_data.name != role.name:
        existing_role = await role_dao.find_by_name(role_data.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{role_data.name}' already exists"
            )
    
    # Обновляем роль
    updated_count = await role_dao.update_by_id(
        data_id=role_id,
        values=role_data,
    )
    
    if not updated_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Получаем обновленную роль
    role = await role_dao.find_one_or_none_by_id(role_id)
    role.users_count = await role_dao.get_users_count(role.id)
    
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    session: AsyncSession = Depends(get_session_with_commit),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить роль (только для администраторов)"""
    # Нельзя удалить системные роли (ID 1-4)
    if role_id in [1, 2, 3, 4]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles (ID 1-4)"
        )
    
    role_dao = RoleDAO(session)
    
    # Проверяем, есть ли пользователи с этой ролью
    users_count = await role_dao.get_users_count(role_id)
    if users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role with {users_count} users. Reassign users first."
        )
    
    # Удаляем роль
    deleted_count = await role_dao.delete_by_id(role_id)
    
    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )


@router.put("/users/{user_uuid}/role", response_model=dict)
async def update_user_role(
    user_uuid: str,
    role_data: UserRoleUpdate,
    session: AsyncSession = Depends(get_session_with_commit),
    current_user: User = Depends(get_current_admin_user)
):
    """Изменить роль пользователя (только для администраторов)"""
    users_dao = UsersDAO(session)
    role_dao = RoleDAO(session)
    
    # Проверяем существование пользователя
    user = await users_dao.find_one_or_none_by_uuid(user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with UUID {user_uuid} not found"
        )
    
    # Проверяем существование роли
    role = await role_dao.find_one_or_none_by_id(role_data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_data.role_id} not found"
        )
    
    # Нельзя изменить роль суперадмина если текущий пользователь не суперадмин
    if user.is_superuser and current_user.role_id != 4:  # 4 = superadmin
        raise ForbiddenException
    
    # Обновляем роль пользователя
    updated_user = await users_dao.update_user_role(user_uuid, role_data.role_id)
    
    return {
        "message": f"User role updated to '{role.name}'",
        "user_uuid": user_uuid,
        "new_role_id": role_data.role_id,
        "new_role_name": role.name
    }


@router.get("/default/setup", response_model=List[RoleResponse])
async def setup_default_roles(
    session: AsyncSession = Depends(get_session_with_commit),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать стандартные роли если их нет (только для администраторов)"""
    role_dao = RoleDAO(session)
    
    default_roles = [
        {"id": 1, "name": "user"},
        {"id": 2, "name": "moderator"},
        {"id": 3, "name": "admin"},
        {"id": 4, "name": "superadmin"}
    ]
    
    created_roles = []
    
    for role_data in default_roles:
        # Проверяем существует ли роль
        existing_role = await role_dao.find_one_or_none_by_id(role_data["id"])
        if not existing_role:
            # Создаем роль
            new_role = await role_dao.add(values=RoleCreate(**role_data))
            new_role.users_count = 0
            created_roles.append(new_role)
        else:
            # Обновляем существующую роль
            await role_dao.update(
                filters=RoleFilter(id=role_data["id"]),
                values=RoleUpdate(name=role_data["name"])
            )
            existing_role.users_count = await role_dao.get_users_count(existing_role.id)
            created_roles.append(existing_role)
    
    return created_roles