"""Главный файл приложения."""
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from app.api.task import router as task_router
from app.api.theme import router as theme_router
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal

# Создаем таблицы при запуске (для разработки)
# В продакшене лучше использовать миграции Alembic
# try:
#     Base.metadata.create_all(bind=engine)
# except Exception as e:
#     print(f"Warning: Could not create tables: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)
app.include_router(task_router)
app.include_router(theme_router)

def check_database_connection():
    """Проверяет подключение к базе данных."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


@app.get("/")
async def root():
    """Корневой endpoint."""
    db_connected = check_database_connection()
    return {
        "message": "Welcome to To-Do App",
        "status": "running",
        "database": "connected" if db_connected else "disconnected",
        "database_url": settings.database_url.split("@")[1] if "@" in settings.database_url else "hidden"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения."""
    db_connected = check_database_connection()
    if not db_connected:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {
        "status": "healthy",
        "database": "connected"
    }


@app.get("/db/test")
async def test_database():
    """Тестовый endpoint для проверки подключения к БД."""
    try:
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT version(), current_database(), current_user"))
            row = result.fetchone()
            return {
                "status": "success",
                "message": "Database connection successful",
                "database_info": {
                    "version": row[0],
                    "database": row[1],
                    "user": row[2]
                }
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )
