"""Настройка подключения к базе данных."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from redis import Redis

from core.config import settings

# Создаем движок SQLAlchemy
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    echo=settings.DEBUG,  # Логирование SQL запросов в режиме отладки
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db():
    """Dependency для получения сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

redis_client: Redis = None

def get_redis() -> Redis:
    """Получаем Redis клиент"""
    global redis_client
    if redis_client is None:
        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    return redis_client
