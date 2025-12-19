FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Настраиваем Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы конфигурации Poetry
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости
RUN poetry install --no-root --no-interaction && rm -rf $POETRY_CACHE_DIR

# Копируем исходный код ОСНОВНОГО приложения
# У вас структура: app/, alembic/, tests/ и файлы на уровне
COPY . .


# Открываем порт
EXPOSE 8000

# Команда запуска (путь к main.py: app.main)
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
