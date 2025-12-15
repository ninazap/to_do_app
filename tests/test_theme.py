# tests/test_theme.py
import pytest
from fastapi import status
import uuid


class TestThemeAPI:
    """Тесты для API управления темами."""

    class TestThemeAPI:
        """Тесты для API управления темами."""

        def test_get_current_theme_success(self, client, test_user):
            """Тест получения текущей темы с существующим пользователем."""
            # Arrange
            user_id = str(test_user.uuid)

            # Act
            response = client.get(f"/theme/?user_id={user_id}")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["user_id"] == user_id
            assert data["username"] == test_user.username  # Используем имя из фикстуры
            assert data["theme"] == "light"

    def test_get_current_theme_user_not_found(self, client):
        """Тест получения темы для несуществующего пользователя."""
        # Arrange
        non_existent_user_id = str(uuid.uuid4())

        # Act
        response = client.get(f"/theme/?user_id={non_existent_user_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Пользователь не найден"

    def test_get_current_theme_invalid_uuid(self, client):
        """Тест получения темы с невалидным UUID."""
        # Arrange
        invalid_user_id = "not-a-valid-uuid"

        # Act
        response = client.get(f"/theme/?user_id={invalid_user_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Пользователь не найден"

    def test_update_theme_success(self, client, test_user):
        """Тест успешного обновления темы."""
        # Arrange
        user_id = str(test_user.uuid)
        new_theme = "dark"

        # Act
        response = client.put(
            f"/theme/?user_id={user_id}",
            json={"theme": new_theme}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["theme"] == new_theme
        assert data["user_id"] == user_id

        # Проверяем, что тема сохранилась в БД
        get_response = client.get(f"/theme/?user_id={user_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["theme"] == new_theme

    def test_update_theme_with_system_theme(self, client, test_user):
        """Тест обновления темы на 'system'."""
        # Arrange
        user_id = str(test_user.uuid)

        # Act
        response = client.put(
            f"/theme/?user_id={user_id}",
            json={"theme": "system"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["theme"] == "system"

    def test_update_theme_invalid_theme_value(self, client, test_user):
        """Тест обновления темы с невалидным значением."""
        # Arrange
        user_id = str(test_user.uuid)
        invalid_theme = "invalid_theme"

        # Act
        response = client.put(
            f"/theme/?user_id={user_id}",
            json={"theme": invalid_theme}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail = response.json()["detail"]
        assert any("theme" in str(err).lower() for err in error_detail)

    def test_update_theme_empty_json(self, client, test_user):
        """Тест обновления темы с пустым JSON."""
        # Arrange
        user_id = str(test_user.uuid)

        # Act
        response = client.put(
            f"/theme/?user_id={user_id}",
            json=None
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_theme_user_not_found(self, client):
        """Тест обновления темы для несуществующего пользователя."""
        # Arrange
        non_existent_user_id = str(uuid.uuid4())

        # Act
        response = client.put(
            f"/theme/?user_id={non_existent_user_id}",
            json={"theme": "dark"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Пользователь не найден"

    def test_update_theme_invalid_uuid_format(self, client):
        """Тест обновления темы с невалидным форматом UUID."""
        # Arrange
        invalid_user_id = "invalid-uuid-format"

        # Act
        response = client.put(
            f"/theme/?user_id={invalid_user_id}",
            json={"theme": "dark"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Пользователь не найден"

    def test_update_theme_with_default_user(self, client, db_session):
        """Тест обновления темы с использованием дефолтного пользователя."""
        # Arrange
        default_user_id = "11111111-1111-1111-1111-111111111111"
        new_theme = "dark"

        # Act
        response = client.put(
            "/theme/",  # Без параметра user_id, должен использоваться дефолтный
            json={"theme": new_theme}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == default_user_id
        assert data["theme"] == new_theme

        # Проверяем через GET
        get_response = client.get("/theme/")
        assert get_response.json()["theme"] == new_theme

    def test_list_users_endpoint(self, client, test_user, test_admin_user):
        """Тест эндпоинта list_users."""
        # Act
        response = client.get("/theme/users")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Проверяем, что получили список пользователей
        assert isinstance(data, list)

        # Проверяем структуру данных
        for user in data:
            assert "uuid" in user
            assert "username" in user
            assert "email" in user
            assert "theme" in user
            assert "full_name" in user

        # Проверяем, что наши тестовые пользователи есть в списке
        user_uuids = [user["uuid"] for user in data]
        assert str(test_user.uuid) in user_uuids
        assert str(test_admin_user.uuid) in user_uuids

        # Находим пользователей в списке и проверяем их данные
        test_user_data = next((u for u in data if u["uuid"] == str(test_user.uuid)), None)
        assert test_user_data is not None
        assert test_user_data["username"] == test_user.username
        assert test_user_data["theme"] == test_user.theme

    def test_theme_enum_validation(self, client, test_user):
        """Тест валидации значений темы через Pydantic."""
        # Arrange
        user_id = str(test_user.uuid)

        # Пробуем разные невалидные значения
        invalid_themes = [
            "LIGHT",  # должно быть lowercase
            "DARK",
            "SYSTEM",
            "blue",
            "red",
            "light-dark",
            123,  # число вместо строки
            True,  # булево значение
            "",  # пустая строка
            " "  # пробел
        ]

        for invalid_theme in invalid_themes:
            # Act
            response = client.put(
                f"/theme/?user_id={user_id}",
                json={"theme": invalid_theme}
            )

            # Assert
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, \
                f"Expected 422 for theme value: {invalid_theme}"

    def test_theme_persistence(self, client, db_session, test_user):
        """Тест персистентности данных темы в БД."""
        # Arrange
        user_id = str(test_user.uuid)

        # Act & Assert: Меняем тему несколько раз
        themes_to_test = ["light", "dark", "system", "light"]

        for expected_theme in themes_to_test:
            # Обновляем тему
            update_response = client.put(
                f"/theme/?user_id={user_id}",
                json={"theme": expected_theme}
            )
            assert update_response.status_code == status.HTTP_200_OK

            # Проверяем через GET
            get_response = client.get(f"/theme/?user_id={user_id}")
            assert get_response.status_code == status.HTTP_200_OK
            actual_theme = get_response.json()["theme"]
            assert actual_theme == expected_theme, \
                f"Expected theme {expected_theme}, got {actual_theme}"

    def test_concurrent_theme_updates(self, client, db_session, test_user):
        """Тест конкурентного обновления темы (симуляция)."""
        # Arrange
        user_id = str(test_user.uuid)

        # Act: Выполняем несколько запросов
        responses = []
        for theme in ["dark", "system"]:
            response = client.put(
                f"/theme/?user_id={user_id}",
                json={"theme": theme}
            )
            responses.append(response)

        # Assert: Последний запрос должен определить текущую тему
        assert responses[-1].status_code == status.HTTP_200_OK
        final_theme = responses[-1].json()["theme"]

        # Проверяем актуальное состояние
        get_response = client.get(f"/theme/?user_id={user_id}")
        assert get_response.json()["theme"] == final_theme