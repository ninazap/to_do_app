from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class GoogleAuthRequest(BaseModel):
    """Схема для запроса авторизации"""
    user_id: str

class GoogleAuthResponse(BaseModel):
    """Схема ответа с URL для авторизации"""
    auth_url: str
    state: str

class GoogleCallbackRequest(BaseModel):
    """Схема для callback от Google"""
    code: str
    state: str

class ExportTaskRequest(BaseModel):
    """Схема для экспорта задачи"""
    task_ids: Optional[List[int]] = None
    user_id: str

class ExportStatusResponse(BaseModel):
    """Схема статуса экспорта"""
    status: str
    total_tasks: int
    exported_tasks: int
    failed_tasks: int
    error: Optional[str] = None
    details: Optional[List[Dict[str, Any]]] = None

class GoogleTask(BaseModel):
    """Схема задачи Google Tasks"""
    id: Optional[str] = None
    title: str
    notes: Optional[str] = None
    due: Optional[datetime] = None
    status: str = "needsAction"

class ExportRequest(BaseModel):
    user_id: str
    task_ids: Optional[List[int]] = None