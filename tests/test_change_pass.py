import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_change_password_success(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    password_data = {
        "current_password": "testpassword",
        "new_password": "newpassword123"
    }

    response = client.post("/auth/change-password", json=password_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "Пароль успешно изменен" in data["message"]

    new_login_data = {
        "username_or_email": test_user.username,
        "password": "newpassword123"
    }

    new_login_response = client.post("/auth/login", json=new_login_data)
    assert new_login_response.status_code == 200


def test_change_password_wrong_current(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123"
    }

    response = client.post("/auth/change-password", json=password_data, headers=headers)
    assert response.status_code == 400
    assert "Неверный текущий пароль" in response.json()["detail"]


def test_change_password_no_auth(client: TestClient):
    password_data = {
        "current_password": "oldpass",
        "new_password": "newpass"
    }

    response = client.post("/auth/change-password", json=password_data)
    assert response.status_code == 401


def test_change_password_short_new_password(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    password_data = {
        "current_password": "testpassword",
        "new_password": "123"  # 3 символа - должно вызвать 422 ошибку
    }

    response = client.post("/auth/change-password", json=password_data, headers=headers)

    # Отладочный вывод
    print(f"\n=== DEBUG SHORT PASSWORD ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("=== END DEBUG ===\n")

    assert response.status_code == 422

    response = client.post("/auth/change-password", json=password_data, headers=headers)
    assert response.status_code == 422