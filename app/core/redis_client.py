import redis
from typing import Optional
from .config import settings

_redis_client: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    """Получает или создает Redis клиент"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Проверяем подключение
        try:
            _redis_client.ping()
            print("Redis connected successfully")
        except redis.ConnectionError as e:
            print(f"Redis connection error: {e}")
            raise
    return _redis_client