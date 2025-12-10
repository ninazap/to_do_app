from fastapi import APIRouter, Depends, HTTPException
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
def list_tasks(db: Session = Depends(get_db)):
    """Получение списка всех задач."""
    return get_tasks(db)

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
