# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import Base, get_db
from app.core.config import Settings


# Переопределяем настройки для тестов
class TestSettings(Settings):
    """Настройки для тестовой среды."""

    # Используем тестовую базу данных
    POSTGRES_DB: str = "todo_test_db"

    @property
    def database_url(self) -> str:
        """Возвращает URL для тестовой базы данных."""
        # Используем отдельную тестовую БД
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


test_settings = TestSettings()

# Создаем тестовый движок БД
TEST_DATABASE_URL = test_settings.database_url

# Проверяем существование тестовой БД
engine = create_engine(TEST_DATABASE_URL)

# Создаем фабрику сессий для тестов
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Переопределенная зависимость для тестов."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Переопределяем зависимость get_db в приложении
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Настройка тестовой базы данных перед всеми тестами."""
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)

    yield

    # Очищаем после всех тестов
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Фикстура для тестовой сессии БД."""
    # Создаем новую сессию
    session = TestingSessionLocal()

    # Начинаем транзакцию
    session.begin()

    try:
        yield session
    finally:
        # Откатываем транзакцию и закрываем сессию
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def clean_db(db_session):
    """Очищает все данные из таблиц перед тестом."""
    # Получаем все таблицы в правильном порядке для очистки
    tables = list(reversed(Base.metadata.sorted_tables))

    # Очищаем таблицы с отключенными foreign key constraints
    db_session.execute(text("SET session_replication_role = 'replica';"))

    for table in tables:
        db_session.execute(table.delete())

    db_session.execute(text("SET session_replication_role = 'origin';"))
    db_session.commit()

    yield db_session


@pytest.fixture(scope="function")
def client(clean_db):
    """Фикстура для тестового клиента."""
    # Используем clean_db сессию
    app.dependency_overrides[get_db] = lambda: clean_db

    with TestClient(app) as test_client:
        yield test_client

    # Очищаем зависимости после теста
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(clean_db):
    """Фикстура для создания тестового пользователя."""
    from app.models.user import User
    import uuid
    import hashlib

    # Генерируем уникальные данные для каждого теста
    user_uuid = uuid.uuid4()
    username = f"testuser_{user_uuid.hex[:8]}"
    email = f"test_{user_uuid.hex[:8]}@example.com"

    # Создаем хеш пароля
    password_hash = hashlib.sha256(b"testpassword").hexdigest()

    test_user = User(
        uuid=user_uuid,
        username=username,
        email=email,
        hashed_password=password_hash,
        full_name="Test User",
        theme="light",
        is_active=True,
        is_superuser=False
    )

    clean_db.add(test_user)
    clean_db.commit()
    clean_db.refresh(test_user)

    return test_user


@pytest.fixture(scope="function")
def default_user(clean_db):
    """Фикстура для создания дефолтного пользователя (admin)."""
    from app.models.user import User
    import uuid
    import hashlib

    default_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")

    # Проверяем, не существует ли уже пользователь с таким UUID
    existing_user = clean_db.query(User).filter(User.uuid == default_uuid).first()
    if existing_user:
        clean_db.delete(existing_user)
        clean_db.commit()

    # Создаем нового
    password_hash = hashlib.sha256(b"adminpassword").hexdigest()

    default_user = User(
        uuid=default_uuid,
        username="admin",
        email="admin@example.com",
        hashed_password=password_hash,
        full_name="Default Admin",
        theme="light",
        is_active=True,
        is_superuser=True
    )

    clean_db.add(default_user)
    clean_db.commit()
    clean_db.refresh(default_user)

    return default_user


@pytest.fixture(scope="function")
def test_admin_user(clean_db):
    """Фикстура для создания тестового администратора."""
    from app.models.user import User
    import uuid
    import hashlib

    # Генерируем уникальный UUID для администратора
    admin_uuid = uuid.uuid4()
    username = f"admin_{admin_uuid.hex[:8]}"
    email = f"admin_{admin_uuid.hex[:8]}@example.com"

    # Создаем хеш пароля
    password_hash = hashlib.sha256(b"adminpassword").hexdigest()

    admin_user = User(
        uuid=admin_uuid,
        username=username,
        email=email,
        hashed_password=password_hash,
        full_name="Test Administrator",
        theme="light",
        is_active=True,
        is_superuser=True
    )

    clean_db.add(admin_user)
    clean_db.commit()
    clean_db.refresh(admin_user)

    return admin_user