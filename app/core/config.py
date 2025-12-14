"""Конфигурация приложения."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Database settings
    POSTGRES_USER: str = "todo_user"
    POSTGRES_PASSWORD: str = "todo_password"
    POSTGRES_DB: str = "todo_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    
    # Database URL (может быть переопределен через переменную окружения)
    DATABASE_URL: Optional[str] = None
    
    # Application settings
    APP_NAME: str = "To-Do App"
    DEBUG: bool = True
    APP_PORT: int = 8000

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/tasks/external-tasks/google/auth/callback"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def database_url(self) -> str:
        """Возвращает URL для подключения к базе данных."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

