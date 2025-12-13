import uuid

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional


from ..dao.base import BaseDAO
from .models import User, Role

class UsersDAO(BaseDAO):
    model = User
    
    async def find_one_or_none_by_uuid(self, data_uuid: uuid.UUID) -> Optional[User]:
        """Найти пользователя по UUID"""
        return await self.find_one_or_none_by_field(field_name="uuid", value=data_uuid)
    
    async def find_one_or_none_by_email(self, email: str) -> Optional[User]:
        """Найти пользователя по email"""
        return await self.find_one_or_none_by_field(field_name="email", value=email)
    
    async def find_one_or_none_by_field(self, field_name: str, value) -> Optional[User]:
        """Универсальный метод поиска по любому полю"""
        try:
            query = select(self.model).where(getattr(self.model, field_name) == value)
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            # Логирование ошибки
            raise
    
    async def update_user_role(self, user_uuid: str, role_id: int) -> Optional[User]:
        """Обновить роль пользователя по UUID"""
        try:
            # Находим пользователя по UUID
            user_uuid_obj = uuid.UUID(user_uuid)
            user = await self.find_one_or_none_by_uuid(user_uuid_obj)
            
            if not user:
                return None
            
            # Обновляем роль
            user.role_id = role_id
            await self._session.flush()
            return user
        except Exception as e:
            raise e

class RoleDAO(BaseDAO):
    model = Role
    
    async def find_by_name(self, name: str) -> Optional[Role]:
        """Найти роль по имени"""
        try:
            query = select(self.model).where(self.model.name == name)
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise e
        
    async def find_by_id(self, id: int) -> Optional[Role]:
        """Найти роль по id"""
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise e
    
    async def get_users_count(self, role_id: int) -> int:
        """Получить количество пользователей с этой ролью"""
        try:
            query = select(func.count(User.uuid)).where(User.role_id == role_id)
            result = await self._session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            raise e
    
    async def get_all_with_counts(self) -> List[Role]:
        """Получить все роли с количеством пользователей"""
        try:
            # Используем подзапрос для подсчета пользователей
            
            
            subquery = (
                select(
                    User.role_id,
                    func.count(User.uuid).label('users_count')
                )
                .group_by(User.role_id)
                .subquery()
            )
            
            query = (
                select(
                    Role,
                    func.coalesce(subquery.c.users_count, 0).label('users_count')
                )
                .outerjoin(subquery, Role.id == subquery.c.role_id)
            )
            
            result = await self.session.execute(query)
            roles_with_counts = []
            for role, users_count in result.all():
                role.users_count = users_count
                roles_with_counts.append(role)
            
            return roles_with_counts
        except Exception as e:
            # Если не получается с JOIN, делаем простой запрос
            roles = await self.find_all()
            for role in roles:
                role.users_count = await self.get_users_count(role.id)
            return roles
    
    async def create_from_dict(self, role_dict: dict):
        """Создать роль из словаря"""
        try:
            new_role = self.model(**role_dict)
            self.session.add(new_role)
            await self.session.flush()
            return new_role
        except Exception as e:
            raise