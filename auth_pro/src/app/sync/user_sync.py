import asyncio
import os
import logging
import sys
from sqlalchemy import create_engine, text
from uuid import UUID

logger = logging.getLogger(__name__)

class AsyncUserSyncService:
    def __init__(self):
        self.todo_db_url = os.getenv("TODO_DB_URL")
                
        self.todo_engine = create_engine(
            self.todo_db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False  # Можно поставить True для отладки SQL
        )
    
    async def sync_user_to_todo_db(self, user_data: dict):
        try:
            success = await asyncio.to_thread(self._sync_user_sync, user_data)
            return success
        except Exception as e:
            return False
    
    def _sync_user_sync(self, user_data: dict) -> bool:
        try:
            email = user_data.get("email", "unknown")
                        
            with self.todo_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT email FROM users WHERE email = :email"),
                    {"email": email}
                )
                existing_user = result.fetchone()
                
                sync_data = {
                    "email": email,
                    "username": user_data.get("username") or email.split("@")[0],
                    "is_active": user_data.get("is_active", True),
                    "is_superuser": user_data.get("is_superuser", False),
                    "bio": user_data.get("bio", ""),
                    "theme": user_data.get("theme", "light"),
                    "uuid": user_data.get("uuid")  # Может быть None
                }
                
                if existing_user:
                    conn.execute(
                        text("""
                            UPDATE users 
                            SET username = :username,
                                is_active = :is_active,
                                is_superuser = :is_superuser,
                                bio = :bio,
                                theme = :theme,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE email = :email
                        """),
                        {k: v for k, v in sync_data.items() if k != "uuid"}
                    )
                else:
                    if sync_data["uuid"]:
                        try:
                            uuid_obj = UUID(sync_data["uuid"])
                            conn.execute(
                                text("""
                                    INSERT INTO users (
                                        uuid, username, email, is_active, 
                                        is_superuser, bio, theme
                                    ) VALUES (
                                        :uuid, :username, :email, :is_active,
                                        :is_superuser, :bio, :theme
                                    )
                                """),
                                sync_data
                            )
                        except ValueError:
                            # Если UUID невалидный, вставляем без него
                            conn.execute(
                                text("""
                                    INSERT INTO users (
                                        username, email, is_active, 
                                        is_superuser, bio, theme
                                    ) VALUES (
                                        :username, :email, :is_active,
                                        :is_superuser, :bio, :theme
                                    )
                                """),
                                {k: v for k, v in sync_data.items() if k != "uuid"}
                            )
                    else:
                        conn.execute(
                            text("""
                                INSERT INTO users (
                                    username, email, is_active, 
                                    is_superuser, bio, theme
                                ) VALUES (
                                    :username, :email, :is_active,
                                    :is_superuser, :bio, :theme
                                )
                            """),
                            {k: v for k, v in sync_data.items() if k != "uuid"}
                        )
                    
                
                conn.commit()
                return True
                
        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stderr)
            return False

# Глобальный экземпляр сервиса
async_user_sync_service = AsyncUserSyncService()