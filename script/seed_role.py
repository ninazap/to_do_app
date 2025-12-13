import asyncio
import sys
import os

# Получаем абсолютный путь к корню проекта
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.app.dao.database import async_session_maker
from src.app.auth.dao import RoleDAO
from src.app.auth.schemas import RoleCreate


async def seed_roles():
    """Создать стандартные роли"""
    async with async_session_maker() as session:
        role_dao = RoleDAO(session)
        
        default_roles = [
            RoleCreate(id=1, name="user"),
            RoleCreate(id=2, name="moderator"),
            RoleCreate(id=3, name="admin"),
            RoleCreate(id=4, name="superadmin")
        ]
        
        for role_data in default_roles:
            # Проверяем существует ли роль
            existing_role = await role_dao.find_one_or_none_by_id(role_data.id)
            
            if not existing_role:
                try:
                    await role_dao.add(values=role_data)
                    print(f"✓ Created role: {role_data.name}")
                except Exception as e:
                    print(f"✗ Error creating role {role_data.name}: {e}")
            else:
                print(f"✓ Role already exists: {role_data.name}")
        
        await session.commit()
        


if __name__ == "__main__":
    asyncio.run(seed_roles())
