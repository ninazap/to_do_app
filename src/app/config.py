import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

HERE = Path(__file__).resolve().parent
ENV_PATH = HERE / ".env"


class Settings(BaseSettings):
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5438
    DB_USER: str = "user"
    DB_PASS: str = "password"
    DB_NAME: str = "postgres"
    
    SECRET_KEY: str = Field(default_factory=lambda: os.environ.get("SECRET_KEY", "dev_secret_key_for_local"))
    ALGORITHM: str = "HS256"
    
    @property
    def DB_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }    


settings = Settings()
database_url = settings.DB_URL