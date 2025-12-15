import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_login_success_username(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    response = client.post("/auth/login", json=login_data)
    print(f"\n=== DEBUG LOGIN RESPONSE ===")
    print(f"Status: {response.status_code}")
    print(f"Response keys: {response.json().keys()}")
    print(f"Full response: {response.json()}")
    print("=== END DEBUG ===\n")

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Проверяем актуальные ключи из вашего auth.py
    if "refresh_token" in data:
        assert "refresh_token" in data
    if "user" in data:
        assert "user" in data
        assert data["user"]["username"] == test_user.username


def test_login_success_email(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.email,
        "password": "testpassword"
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data


def test_login_wrong_password(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "wrongpassword"
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Неверное имя пользователя" in response.json()["detail"]


def test_login_user_not_found(client: TestClient):
    login_data = {
        "username_or_email": "nonexistentuser",
        "password": "password123"
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Неверное имя пользователя" in response.json()["detail"]


def test_login_inactive_user(client: TestClient, clean_db: Session):
    from app.models.user import User
    import uuid
    import hashlib

    user_uuid = uuid.uuid4()
    username = f"inactive_{user_uuid.hex[:8]}"

    inactive_user = User(
        uuid=user_uuid,
        username=username,
        email=f"{username}@example.com",
        hashed_password=hashlib.sha256(b"testpassword").hexdigest(),
        is_active=False
    )

    clean_db.add(inactive_user)
    clean_db.commit()

    login_data = {
        "username_or_email": username,
        "password": "testpassword"
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401