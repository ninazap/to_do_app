from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import require_active_user
from schemas.task import TaskCreate, TaskUpdate, TaskOut


from crud.task import (
    get_user_tasks,  
    get_user_task,       
    create_user_task,    
    update_user_task,     
    delete_user_task,          
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskOut])
async def list_user_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    tasks = get_user_tasks(
        db, 
        user_email=current_user["email"], 
        skip=skip, 
        limit=limit
    )
    return tasks

@router.get("/{task_id}", response_model=TaskOut)
async def retrieve_user_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    task = get_user_task(db, task_id, current_user["email"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/", response_model=TaskOut, status_code=201)
async def create_new_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    return create_user_task(
        db, 
        payload, 
        current_user["email"]
    )

@router.put("/{task_id}", response_model=TaskOut)
async def update_existing_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    task = get_user_task(db, task_id, current_user["email"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return update_user_task(db, task, payload)

@router.delete("/{task_id}", status_code=204)
async def remove_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    success = delete_user_task(db, task_id, current_user["email"])
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
