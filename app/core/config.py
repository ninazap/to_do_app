# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Основная БД
    POSTGRES_USER: str = Field(default="todo_user")
    POSTGRES_PASSWORD: str = Field(default="todo_password")
    POSTGRES_DB: str = Field(default="todo_db")
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_PORT: int = Field(default=5432)
    
    # Redis (для будущего использования)
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = 0
    REDIS_TOKEN_TTL: int = 1800  # 30 минут

    # Сервис авторизации
    AUTH_SERVICE_URL: str = Field(default="http://auth_app:8001")
    TODO_SERVICE_URL: str = Field(default="http://app:8000")
    
    # Настройки приложения
    APP_NAME: str = Field(default="To-Do App")
    DEBUG: bool = Field(default=False)
    
    
    @property
    def database_url(self):
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
