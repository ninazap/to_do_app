FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root --no-interaction && rm -rf $POETRY_CACHE_DIR

# Копируем исходный код auth_pro (у него есть src/)
COPY src/ ./src/
COPY alembic.ini ./

EXPOSE 8001

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]