from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.crud.task import (
    get_task,
    get_tasks,
    create_task,
    update_task,
    delete_task
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=list[TaskOut])
def list_tasks(
    skip: int = Query(0, ge=0, description="Количество пропускаемых задач"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество задач"),
    status: bool | None = Query(None, description="Фильтр по статусу: true - выполненные, false - невыполненные"),
    category_id: str | None = Query(None, description="Фильтр по ID категории"),
    sort_by: str | None = Query(None, description="Сортировка: priority, -priority, due_date, -due_date"),
    db: Session = Depends(get_db)
):
    """
    Получение списка задач с поддержкой:
    - Пагинации (skip, limit)
    - Фильтрации по статусу и категории
    - Сортировки по приоритету и сроку выполнения
    """
    return get_tasks(db, skip=skip, limit=limit, status=status, category_id=category_id, sort_by=sort_by)


@router.get("/{task_id}", response_model=TaskOut)
def retrieve_task(task_id: int, db: Session = Depends(get_db)):
    """Получить конкретную задачу."""
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task

@router.post("/", response_model=TaskOut, status_code=201)
def create_new_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Создать новую задачу."""
    return create_task(db, payload)

@router.put("/{task_id}", response_model=TaskOut)
def update_existing_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Обновить существующую задачу."""
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return update_task(db, task, payload)

@router.delete("/{task_id}", status_code=204)
def remove_task(task_id: int, db: Session = Depends(get_db)):
    """Удалить задачу."""
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    delete_task(db, task)
