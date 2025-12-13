# To-Do Application

Приложение для управления задачами с использованием FastAPI, PostgreSQL и Docker.

## Требования

- Docker и Docker Compose
- Poetry (опционально, для локальной разработки)

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd to_do_app-1
```

### 2. Настройка переменных окружения (опционально)

Создайте файл `.env` в корне проекта (можно скопировать из `.env.example`):

```env
POSTGRES_USER=todo_user
POSTGRES_PASSWORD=todo_password
POSTGRES_DB=todo_db
POSTGRES_PORT=5432
APP_PORT=8000
```

### 3. Запуск с Docker Compose

```bash
docker-compose up --build
```

Это команда:
- Соберет образы для приложения и базы данных
- Запустит PostgreSQL контейнер
- Запустит Python контейнер с приложением
- Настроит сеть между контейнерами

### 4. Доступ к приложению

- API: http://localhost:8000
- Документация API: http://localhost:8000/docs
- Альтернативная документация: http://localhost:8000/redoc

### 5. Подключение к базе данных

Для подключения к PostgreSQL извне контейнера:

```bash
# Хост: localhost
# Порт: 5432 (или значение из .env)
# Пользователь: todo_user (или значение из .env)
# Пароль: todo_password (или значение из .env)
# База данных: todo_db (или значение из .env)
```

## Разработка

### Локальная разработка с Poetry

1. Установите Poetry: https://python-poetry.org/docs/#installation

2. Установите зависимости:

```bash
poetry install
```

3. Активируйте виртуальное окружение:

```bash
poetry shell
```

4. Запустите только базу данных:

```bash
docker-compose up db
```

5. Запустите приложение локально:

```bash
poetry run uvicorn app.main:app --reload
```

### Работа с миграциями Alembic

```bash
# Создание миграции
docker-compose exec app poetry run alembic revision --autogenerate -m "description"

# Применение миграций
docker-compose exec app poetry run alembic upgrade head
```

## Структура проекта

```
to_do_app-1/
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Конфигурация и подключение к БД
│   ├── crud/         # CRUD операции
│   ├── models/       # SQLAlchemy модели
│   ├── schemas/      # Pydantic схемы
│   ├── services/     # Бизнес-логика
│   └── main.py       # Точка входа приложения
├── tests/            # Тесты
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml    # Конфигурация Poetry
└── README.md
```

## Полезные команды

```bash
# Остановка контейнеров
docker-compose down

# Остановка с удалением volumes (удалит данные БД!)
docker-compose down -v

# Просмотр логов
docker-compose logs -f app
docker-compose logs -f db

# Выполнение команд в контейнере
docker-compose exec app poetry run python -m pytest
docker-compose exec app bash

# Пересборка образов
docker-compose build --no-cache
```

## Переменные окружения

Все переменные окружения имеют значения по умолчанию и могут быть переопределены через файл `.env` или переменные окружения системы.

- `POSTGRES_USER` - пользователь PostgreSQL (по умолчанию: `todo_user`)
- `POSTGRES_PASSWORD` - пароль PostgreSQL (по умолчанию: `todo_password`)
- `POSTGRES_DB` - имя базы данных (по умолчанию: `todo_db`)
- `POSTGRES_PORT` - порт PostgreSQL (по умолчанию: `5432`)
- `APP_PORT` - порт приложения (по умолчанию: `8000`)

