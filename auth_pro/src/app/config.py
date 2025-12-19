from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

HERE = Path(__file__).resolve().parent
ENV_PATH = HERE / ".env"


class Settings(BaseSettings):
    # База данных - используем переменные из docker-compose
    DB_HOST: str = Field(default="auth_db")  # ← Имя сервиса в docker-compose
    DB_PORT: int = Field(default=5432)       # ← Внутренний порт PostgreSQL
    DB_USER: str = Field(default="auth_user")
    DB_PASS: str = Field(default="auth_password")
    DB_NAME: str = Field(default="auth_db")
    
    TODO_SERVICE_URL: str = Field(default="http://todo_app:8000")
    AUTH_SERVICE_URL: str = Field(default="http://auth_app:8001")

    # Redis - общий для сервисов
    REDIS_HOST: str = Field(default="redis")  # ← Имя сервиса Redis
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = 0
    # JWT
    SECRET_KEY: str = Field(default="dev_secret_key_change_in_production")
    ALGORITHM: str = Field(default="HS256")
    
    
    @property
    def DB_URL(self):
        """URL для подключения к БД"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def REDIS_URL(self):
        """URL для подключения к Redis"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Разрешает дополнительные переменные


settings = Settings()
database_url = settings.DB_URL
redis_url = settings.REDIS_URL
