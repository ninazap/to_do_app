import pytest
from fastapi.testclient import TestClient


def test_get_current_user_success(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email


def test_get_current_user_no_token(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401


def test_update_current_user(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "full_name": "Updated Name",
        "theme": "dark"
    }

    response = client.put("/auth/me", json=update_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["theme"] == "dark"