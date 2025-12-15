import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_register_valid(client: TestClient, clean_db: Session):
    # Генерируем уникальные данные для каждого теста
    unique_id = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"newuser_{unique_id}",
        "email": f"newuser_{unique_id}@example.com",
        "password": "password123",
        "full_name": "New User"
    }

    response = client.post("/auth/register", json=user_data)

    print(f"\n=== DEBUG REGISTER ===")
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.text}")

    if response.status_code == 400:
        error_detail = response.json().get("detail", "No detail")
        print(f"Error detail: {error_detail}")

        # Проверяем БД
        from app.crud.user import get_user_by_username
        user_in_db = get_user_by_username(clean_db, user_data["username"])
        print(f"User in DB: {user_in_db}")

    print("=== END DEBUG ===")

    assert response.status_code == 201

    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "uuid" in data
    assert "hashed_password" not in data

    from app.crud.user import get_user_by_username
    db_user = get_user_by_username(clean_db, user_data["username"])
    assert db_user is not None
    assert db_user.email == user_data["email"]


def test_register_duplicate_username(client: TestClient, test_user):
    user_data = {
        "username": test_user.username,
        "email": "different@example.com",
        "password": "password123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "уже существует" in data["detail"]


def test_register_duplicate_email(client: TestClient, test_user):
    user_data = {
        "username": "differentuser",
        "email": test_user.email,
        "password": "password123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "уже существует" in data["detail"]


def test_register_invalid_email(client: TestClient):
    user_data = {
        "username": "testuser123",
        "email": "invalid-email",
        "password": "password123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_register_short_password(client: TestClient):
    user_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_register_short_username(client: TestClient):
    user_data = {
        "username": "ab",
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_register_invalid_username_special_chars(client: TestClient):
    user_data = {
        "username": "test@user",
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_register_missing_required_fields(client: TestClient):
    response = client.post("/auth/register", json={"username": "test"})
    assert response.status_code == 422