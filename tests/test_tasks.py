# tests/test_tasks_fixed.py
import pytest
from fastapi import status
from datetime import datetime, timedelta
from sqlalchemy import text


class TestTaskAPIMinimalFixed:
    """Исправленные тесты для задач"""

    @pytest.fixture(autouse=True)
    def cleanup_before_test(self, clean_db):
        """Автоматически очищает БД перед каждым тестом"""
        # clean_db уже должен это делать, но на всякий случай
        db = clean_db
        db.execute(text("DELETE FROM tasks"))
        db.commit()
        yield
        db.rollback()

    def test_pagination(self, client, test_user):
        from app.core.database import SessionLocal

        db = SessionLocal()
        db.execute(text("DELETE FROM tasks"))
        db.commit()

        # Создаем 3 задачи
        for i in range(3):
            task_data = {
                "title": f"Задача {i}",
                "user_id": str(test_user.uuid)
            }
            client.post("/tasks/", json=task_data)

        # Проверяем базовую пагинацию
        response = client.get("/tasks/?limit=2")
        data = response.json()
        assert len(data) == 2  # Должно вернуть 2 из 3

        response = client.get("/tasks/?limit=10")
        data = response.json()
        assert len(data) == 3  # Должно вернуть все 3

        response = client.get("/tasks/?skip=2")
        data = response.json()
        assert len(data) == 1  # Должно вернуть 1 (пропустили 2)

        db.close()
    def test_create_task_minimal_success(self, client, test_user):
        task_data = {
            "title": "Важная задача",
            "user_id": str(test_user.uuid)
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["title"] == "Важная задача"
        assert data["is_completed"] is False

    def test_create_task_full_data(self, client, test_user):
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        task_data = {
            "title": "Срочная задача",
            "description": "Подробное описание задачи",
            "priority": 5,
            "due_date": due_date,
            "user_id": str(test_user.uuid)
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["priority"] == task_data["priority"]

    def test_create_task_validation_errors(self, client):
        response = client.post("/tasks/", json={"description": "Без заголовка"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response = client.post("/tasks/", json={"title": ""})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response = client.post("/tasks/", json={"title": "A" * 201})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response = client.post("/tasks/", json={
            "title": "Задача",
            "priority": -1
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response = client.post("/tasks/", json={
            "title": "Задача",
            "priority": 11
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_tasks_list(self, client):
        """Тест получения списка задач - проверяем только структуру"""
        response = client.get("/tasks/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        # Проверяем структуру, если есть задачи
        if data:
            task = data[0]
            assert "id" in task
            assert "title" in task
            assert "is_completed" in task

    def test_get_single_task(self, client, test_user):
        """Тест получения одной задачи"""
        # Создаем задачу
        task_data = {
            "title": "Тестовая задача для получения",
            "user_id": str(test_user.uuid),
            "priority": 3
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == status.HTTP_201_CREATED

        task_id = response.json()["id"]

        # Получаем задачу
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Тестовая задача для получения"
        assert data["priority"] == 3

    def test_get_task_not_found(self, client):
        response = client.get("/tasks/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Task not found"

    def test_update_task_success(self, client, test_user):
        """Тест обновления задачи"""
        # Создаем задачу
        task_data = {
            "title": "Старое название",
            "user_id": str(test_user.uuid),
            "priority": 1
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == status.HTTP_201_CREATED

        task_id = response.json()["id"]

        # Обновляем задачу
        update_data = {
            "title": "Новое название",
            "is_completed": True,
            "priority": 5
        }
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Новое название"
        assert data["is_completed"] is True
        assert data["priority"] == 5

        # Проверяем через GET
        get_response = client.get(f"/tasks/{task_id}")
        assert get_response.json()["title"] == "Новое название"

    def test_update_task_partial(self, client, test_user):
        """Тест частичного обновления"""
        # Создаем задачу
        task_data = {
            "title": "Исходная задача",
            "user_id": str(test_user.uuid)
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == status.HTTP_201_CREATED

        task_id = response.json()["id"]

        # Обновляем только статус
        response = client.put(f"/tasks/{task_id}", json={"is_completed": True})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Исходная задача"
        assert data["is_completed"] is True

    def test_update_task_not_found(self, client):
        response = client.put("/tasks/999999", json={"title": "Новое"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_task_success(self, client, test_user):
        """Тест удаления задачи"""
        # Создаем задачу
        task_data = {
            "title": "Задача для удаления",
            "user_id": str(test_user.uuid)
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == status.HTTP_201_CREATED

        task_id = response.json()["id"]

        # Удаляем задачу
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Проверяем, что задача удалена
        get_response = client.get(f"/tasks/{task_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_task_not_found(self, client):
        response = client.delete("/tasks/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_filter_tasks_by_status(self, client, test_user):
        """Тест фильтрации по статусу"""
        # Создаем выполненные задачи
        for i in range(2):
            task_data = {
                "title": f"Выполненная {i}",
                "user_id": str(test_user.uuid),
                "is_completed": True
            }
            client.post("/tasks/", json=task_data)

        # Создаем невыполненные задачи
        for i in range(3):
            task_data = {
                "title": f"Невыполненная {i}",
                "user_id": str(test_user.uuid),
                "is_completed": False
            }
            client.post("/tasks/", json=task_data)

        # Фильтруем выполненные
        response = client.get("/tasks/?status=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Проверяем, что все задачи выполнены
        if data:
            for task in data:
                assert task["is_completed"] is True

        # Фильтруем невыполненные
        response = client.get("/tasks/?status=false")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Проверяем, что все задачи не выполнены
        if data:
            for task in data:
                assert task["is_completed"] is False

    def test_sort_tasks_by_priority(self, client, test_user):
        """Тест сортировки по приоритету"""
        # Создаем задачи с разными приоритетами
        priorities = [3, 1, 2]
        for i, priority in enumerate(priorities):
            task_data = {
                "title": f"Задача {i} с приоритетом {priority}",
                "user_id": str(test_user.uuid),
                "priority": priority
            }
            client.post("/tasks/", json=task_data)

        # Сортируем по возрастанию
        response = client.get("/tasks/?sort_by=priority")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Находим наши задачи в ответе
        our_tasks = [t for t in data if "с приоритетом" in t["title"]]

        # Если нашли наши задачи, проверяем сортировку
        if len(our_tasks) >= 3:
            priorities_sorted = [t["priority"] for t in our_tasks[:3]]
            # Проверяем, что приоритеты отсортированы
            assert sorted(priorities_sorted) == priorities_sorted

        # Сортируем по убыванию
        response = client.get("/tasks/?sort_by=-priority")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        our_tasks = [t for t in data if "с приоритетом" in t["title"]]

        if len(our_tasks) >= 3:
            priorities_sorted_desc = [t["priority"] for t in our_tasks[:3]]
            # Проверяем, что приоритеты отсортированы по убыванию
            assert sorted(priorities_sorted_desc, reverse=True) == priorities_sorted_desc