from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import List, Optional

from models import User
from models.task import Task
from schemas.task import TaskCreate, TaskUpdate


def get_task(db: Session, task_id: int) -> Task | None:
    """Получить задачу по ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(db: Session) -> list[Task]:
    """Получить все задачи."""
    return db.query(Task).all()


def create_user_task(db: Session, task_data: TaskCreate, user_email: str) -> Task:
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        is_completed=task_data.is_completed if hasattr(task_data, 'is_completed') else False,
        user_email=user_email
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


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

# === НОВЫЕ функции с фильтрацией по пользователю ===

def delete_task(db: Session, task: Task) -> None:
    """Удалить задачу."""
    db.delete(task)
    db.commit()

def get_user_tasks(db: Session, user_email: str, skip: int = 0, limit: int = 100) -> List[Task]:
    """Получить задачи конкретного пользователя по email."""
    return db.query(Task).filter(
        Task.user_email == user_email
    ).offset(skip).limit(limit).all()

def get_user_task(db: Session, task_id: int, user_email: str) -> Optional[Task]:
    """Получить задачу пользователя по ID и email."""
    return db.query(Task).filter(
        and_(Task.id == task_id, Task.user_email == user_email)
    ).first()

def update_user_task(db: Session, task: Task, task_update: TaskUpdate) -> Task:
    """Обновить задачу пользователя."""
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

def delete_user_task(db: Session, task_id: int, user_email: str) -> bool:
    """Удалить задачу пользователя."""
    task = get_user_task(db, task_id, user_email)
    if not task:
        return False
    
    db.delete(task)
    db.commit()
    return True
