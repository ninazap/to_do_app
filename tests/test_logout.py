import pytest
from fastapi.testclient import TestClient


def test_logout_success(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/auth/logout", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Успешный выход" in data["message"]


def test_logout_no_auth(client: TestClient):
    response = client.post("/auth/logout")
    assert response.status_code == 401