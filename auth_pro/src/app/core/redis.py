import redis
import json
from typing import Optional, Dict, Any
from src.app.config import settings

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def set_session(self, token: str, user_data: dict, expire_seconds: int = 1800) -> bool:
        """Сохраняет сессию пользователя в Redis."""
        key = f"token:{token}"
        return self.client.setex(key, expire_seconds, json.dumps(user_data))
    
    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Получает данные сессии из Redis."""
        key = f"token:{token}"
        data = self.client.get(key)
        return json.loads(data) if data else None
    
    def delete_session(self, token: str) -> int:
        """Удаляет сессию из Redis (при логауте)."""
        key = f"token:{token}"
        return self.client.delete(key)
    
    def set_token(self, token: str, email: str, expire_seconds: int = 1800) -> bool:
        """Сохраняет токен -> email в Redis для быстрой проверки."""
        key = f"token:{token}"
        return self.client.setex(key, expire_seconds, email)
    
    def get_token(self, token: str) -> Optional[str]:
        """Получает email по токену."""
        key = f"token:{token}"
        return self.client.get(key)
    
    def delete_token(self, token: str) -> int:
        """Удаляет токен из Redis."""
        key = f"token:{token}"
        return self.client.delete(key)

# Создаем глобальный экземпляр
redis_client = RedisClient()