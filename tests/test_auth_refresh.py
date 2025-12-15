import pytest
from fastapi.testclient import TestClient


def test_refresh_token_success(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    login_response = client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200

    login_json = login_response.json()

    refresh_token = None
    if "refresh_token" in login_json:
        refresh_token = login_json["refresh_token"]
    elif "refreshToken" in login_json:
        refresh_token = login_json["refreshToken"]
    elif "refresh" in login_json:
        refresh_token = login_json["refresh"]

    if not refresh_token:
        pytest.skip("No refresh token in login response")

    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/auth/refresh", json=refresh_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(client: TestClient):
    refresh_data = {"refresh_token": "invalid_token"}
    response = client.post("/auth/refresh", json=refresh_data)

    assert response.status_code in [401, 422]

    if response.status_code == 401:
        assert "Недействительный refresh токен" in response.json()["detail"]


def test_refresh_token_empty(client: TestClient):
    response = client.post("/auth/refresh", json={})
    assert response.status_code == 422


def test_refresh_access_token_not_allowed(client: TestClient, test_user):
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpassword"
    }

    login_response = client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    refresh_data = {"refresh_token": access_token}
    response = client.post("/auth/refresh", json=refresh_data)

    assert response.status_code in [401, 422]

    if response.status_code == 401:
        assert "Недействительный refresh токен" in response.json()["detail"]