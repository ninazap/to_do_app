from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional
import uuid

def get_task(db: Session, task_id: int) -> Task | None:
    """Получить задачу по ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(db: Session) -> list[Task]:
    """Получить все задачи."""
    return db.query(Task).all()


def create_task(db: Session, data: TaskCreate) -> Task:
    """Создать или обновить задачу."""
    task = Task(title=data.title, description=data.description, user_id=data.user_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    """Обновить задачу заданными полями."""
    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.is_completed is not None:
        task.is_completed = data.is_completed
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    """Удалить задачу."""
    db.delete(task)
    db.commit()

def get_tasks_by_user(db: Session, user_id: str):
    try:
        import uuid
        user_uuid = uuid.UUID(user_id)
        return db.query(Task).filter(
            Task.user_id == user_uuid
        ).all()
    except ValueError:
        return []

def get_tasks_by_ids(db: Session, task_ids: List[int], user_id: str):
    """Получить задачи по ID для конкретного пользователя"""
    try:
        user_uuid = uuid.UUID(user_id)
        return db.query(Task).filter(
            Task.id.in_(task_ids),
            Task.user_id == user_uuid
        ).all()
    except (ValueError, AttributeError):
        return []