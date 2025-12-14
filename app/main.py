"""Главный файл приложения."""
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
import logging

from app.api.task import router as task_router
from app.api.theme import router as theme_router
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.google_export import router as google_export_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# Включаем роутеры
app.include_router(task_router)
app.include_router(theme_router)
app.include_router(google_export_router)

logger.info("Application started")

def check_database_connection():
    """Проверяет подключение к базе данных."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False


@app.get("/")
async def root():
    """Корневой endpoint."""
    db_connected = check_database_connection()

    # Проверяем Google OAuth настройки
    google_configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)

    return {
        "message": "Welcome to To-Do App",
        "status": "running",
        "database": "connected" if db_connected else "disconnected",
        "google_oauth": "configured" if google_configured else "not configured",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_connected = check_database_connection()

    return {
        "status": "healthy" if db_connected else "unhealthy",
        "database": "connected" if db_connected else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }