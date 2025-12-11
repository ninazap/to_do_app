from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def get_task(db: Session, task_id: int) -> Task | None:
    """Получить задачу по ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(db: Session) -> list[Task]:
    """Получить все задачи."""
    return db.query(Task).all()


def create_task(db: Session, data: TaskCreate) -> Task:
    """Создать или обновить задачу."""
    task = Task(
        title=data.title,
        description=data.description,
        user_id=data.user_id,
        category_id=data.category_id
    )
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
