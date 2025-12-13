from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def get_task(db: Session, task_id: int) -> Task | None:
    """Получить задачу по ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: bool | None = None,
    category_id: str | None = None,
    sort_by: str | None = None
) -> list[Task]:
    """
    Получить список задач с пагинацией, фильтрацией и сортировкой.
    
    Параметры:
    - skip: сколько задач пропустить (для пагинации)
    - limit: максимальное количество задач
    - status: фильтр по статусу (True = выполненные, False = невыполненные)
    - category_id: фильтр по категории
    - sort_by: сортировка ('priority', '-priority', 'due_date', '-due_date')
    """
    query = db.query(Task)
    
    if status is not None:
        query = query.filter(Task.is_completed == status)
    
    if category_id:
        query = query.filter(Task.category_id == category_id)
    
    if sort_by:
        if sort_by == 'priority':
            query = query.order_by(asc(Task.priority))
        elif sort_by == '-priority':
            query = query.order_by(desc(Task.priority))
        elif sort_by == 'due_date':
            query = query.order_by(asc(Task.due_date))
        elif sort_by == '-due_date':
            query = query.order_by(desc(Task.due_date))
    
    return query.offset(skip).limit(limit).all()


def create_task(db: Session, data: TaskCreate) -> Task:
    """Создать или обновить задачу."""
    task = Task(
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date
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
    if data.priority is not None:
        task.priority = data.priority
    if data.due_date is not None:
        task.due_date = data.due_date
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    """Удалить задачу."""
    db.delete(task)
    db.commit()
