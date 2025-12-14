from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
import json
import logging

from app.core.database import get_db
from app.services.google_tasks_service import GoogleTasksService
from app.schemas.google_tasks import (
    GoogleAuthResponse,
    GoogleCallbackRequest,
    ExportTaskRequest,
    ExportStatusResponse
)
from app.crud.task import get_tasks_by_user
from app.crud.google_token import delete_google_token

router = APIRouter(prefix="/tasks/external-tasks/google", tags=["google-export"])
google_service = GoogleTasksService()
logger = logging.getLogger(__name__)


@router.get("/auth", response_model=GoogleAuthResponse)
async def get_google_auth_url(
        user_id: str = Query(..., description="ID пользователя"),
        db: Session = Depends(get_db)
) -> GoogleAuthResponse:
    """
    Получить URL для авторизации пользователя в Google
    """
    try:
        auth_url, state = google_service.get_authorization_url(user_id)
        return GoogleAuthResponse(auth_url=auth_url, state=state)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth configuration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating auth URL: {str(e)}"
        )


@router.get("/auth/callback")
async def google_auth_callback(
        code: str = Query(...),
        state: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    Callback endpoint для обработки ответа от Google OAuth
    """
    try:
        # Декодируем state
        try:
            state_data = json.loads(state)
            user_id = state_data.get('user_id')
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state format"
            )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID not found in state"
            )

        logger.info(f"Processing OAuth callback for user {user_id}")

        # Сохраняем токены
        success = google_service.save_credentials_from_code(db, code, user_id)

        if success:
            # Тестируем подключение
            connection_test = google_service.test_connection(db, user_id)

            if connection_test.get("connected"):
                return {
                    "status": "success",
                    "message": "Successfully connected to Google Tasks",
                    "details": connection_test
                }
            else:
                return {
                    "status": "warning",
                    "message": "Credentials saved but connection test failed",
                    "details": connection_test
                }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save credentials. Please try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/export", response_model=ExportStatusResponse)
async def export_tasks_to_google(
        request: ExportTaskRequest,
        db: Session = Depends(get_db)
) -> ExportStatusResponse:
    """
    Экспортировать задачи пользователя в Google Tasks
    """
    try:
        # Получаем задачи пользователя
        all_tasks = get_tasks_by_user(db, request.user_id)

        if not all_tasks:
            return ExportStatusResponse(
                status="completed",
                total_tasks=0,
                exported_tasks=0,
                failed_tasks=0,
                error="No tasks found for user",
                details=[]
            )

        # Фильтруем задачи если указаны IDs
        if request.task_ids:
            tasks = [task for task in all_tasks if task.id in request.task_ids]
            if not tasks:
                return ExportStatusResponse(
                    status="completed",
                    total_tasks=0,
                    exported_tasks=0,
                    failed_tasks=0,
                    error=f"No tasks found with specified IDs",
                    details=[]
                )
        else:
            tasks = all_tasks

        logger.info(f"Exporting {len(tasks)} tasks for user {request.user_id}")

        # Экспортируем задачи
        results = google_service.export_user_tasks(db, request.user_id, tasks)

        # Определяем статус
        if results.get('error') and results['success'] == 0:
            status_val = "failed"
        elif results['failed'] > 0:
            status_val = "partial"
        else:
            status_val = "completed"

        return ExportStatusResponse(
            status=status_val,
            total_tasks=results['total'],
            exported_tasks=results['success'],
            failed_tasks=results['failed'],
            error=results.get('error'),
            details=results.get('exported_tasks', [])
        )

    except Exception as e:
        logger.error(f"Error exporting tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting tasks: {str(e)}"
        )


@router.get("/status")
async def get_export_status(
        user_id: str = Query(..., description="ID пользователя"),
        db: Session = Depends(get_db)
):
    """
    Получить статус подключения к Google Tasks
    """
    try:
        connection_status = google_service.test_connection(db, user_id)
        return connection_status
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking status: {str(e)}"
        )


@router.delete("/disconnect")
async def disconnect_google(
        user_id: str = Query(..., description="ID пользователя"),
        db: Session = Depends(get_db)
):
    """
    Отключить аккаунт Google
    """
    try:
        success = delete_google_token(db, user_id)

        if success:
            return {
                "status": "success",
                "message": "Google account disconnected successfully"
            }
        else:
            return {
                "status": "error",
                "message": "No Google connection found for this user"
            }

    except Exception as e:
        logger.error(f"Error disconnecting Google: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disconnecting: {str(e)}"
        )


@router.get("/tasks")
async def get_google_tasks(
        user_id: str = Query(..., description="ID пользователя"),
        max_results: int = Query(10, description="Maximum number of tasks to return"),
        db: Session = Depends(get_db)
):
    """
    Получить задачи из Google Tasks
    """
    try:
        service = google_service.get_tasks_service(db, user_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication required. Please connect your Google account first."
            )

        # Получаем задачи из default tasklist
        tasks_result = service.tasks().list(
            tasklist='@default',
            maxResults=max_results,
            showCompleted=True,
            showHidden=True
        ).execute()

        tasks = tasks_result.get('items', [])

        return {
            "status": "success",
            "total_tasks": len(tasks),
            "tasks": tasks
        }

    except HttpError as e:
        logger.error(f"Google API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting Google tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tasks: {str(e)}"
        )


@router.post("/sync-from-google")
async def sync_from_google(
        user_id: str = Query(..., description="ID пользователя"),
        tasklist_id: str = Query('@default', description="ID списка задач в Google"),
        db: Session = Depends(get_db)
):
    """
    Полная синхронизация задач между Google Tasks и локальной БД

    Что делает:
    1. Скачивает все задачи из Google Tasks
    2. Создает локальные задачи для новых задач из Google
    3. Обновляет существующие задачи (статус, название, описание)
    4. Удаляет локальные задачи, которых нет в Google
    """
    try:
        logger.info(f"Manual sync requested for user {user_id}, tasklist: {tasklist_id}")

        result = google_service.sync_tasks_from_google(db, user_id, tasklist_id)

        return result

    except Exception as e:
        logger.error(f"Error in sync endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )

@router.post("/sync-to-google")
async def sync_to_google(
        user_id: str = Query(..., description="ID пользователя"),
        tasklist_id: str = Query("@default", description="ID списка задач Google"),
        db: Session = Depends(get_db)
):
    """Синхронизация локальных изменений в Google Tasks"""
    try:
        google_service = GoogleTasksService()
        result = google_service.sync_local_to_google(db, user_id, tasklist_id)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"Error syncing to Google: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-google-tasks")
async def clear_google_tasks(
        user_id: str = Query(..., description="ID пользователя"),
        tasklist_id: str = Query('@default', description="ID списка задач в Google"),
        confirm: bool = Query(False, description="Подтверждение удаления всех задач"),
        db: Session = Depends(get_db)
):
    """
    УДАЛИТЬ ВСЕ задачи из Google Tasks (ОПАСНО!)

    Предупреждение: Эта операция удаляет ВСЕ задачи из указанного списка Google Tasks.
    Используйте только для очистки или тестирования.
    """
    try:
        if not confirm:
            return {
                "status": "warning",
                "message": "Для удаления всех задач необходимо установить параметр confirm=true",
                "details": {
                    "tasklist_id": tasklist_id,
                    "user_id": user_id,
                    "tasks_count": "unknown (not fetched without confirmation)"
                }
            }

        logger.warning(f"USER {user_id} REQUESTED FULL GOOGLE TASKS CLEARANCE! Tasklist: {tasklist_id}")

        # Получаем сервис
        service = google_service.get_tasks_service(db, user_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication required"
            )

        # Сначала получаем все задачи для отчета
        tasks_result = service.tasks().list(
            tasklist=tasklist_id,
            showCompleted=True,
            showHidden=True,
            maxResults=1000
        ).execute()

        all_tasks = tasks_result.get('items', [])

        if not all_tasks:
            return {
                "status": "success",
                "message": "No tasks found in Google Tasks",
                "details": {
                    "tasklist_id": tasklist_id,
                    "deleted_count": 0,
                    "failed_count": 0
                }
            }

        logger.info(f"Found {len(all_tasks)} tasks to delete from Google Tasks")

        # Удаляем задачи
        deleted_count = 0
        failed_tasks = []

        for task in all_tasks:
            try:
                task_id = task.get('id')
                task_title = task.get('title', 'Untitled')

                if task_id:
                    service.tasks().delete(
                        tasklist=tasklist_id,
                        task=task_id
                    ).execute()

                    deleted_count += 1
                    logger.info(f"Deleted Google task: {task_title} (ID: {task_id})")

            except Exception as e:
                failed_tasks.append({
                    "task_id": task.get('id'),
                    "title": task.get('title', 'Unknown'),
                    "error": str(e)
                })
                logger.error(f"Failed to delete task {task.get('id')}: {e}")

        # Также очищаем google_task_id в локальной БД для удаленных задач
        try:
            from app.models.task import Task
            tasks_to_clear = db.query(Task).filter(
                Task.user_id == uuid.UUID(user_id),
                Task.google_task_id.isnot(None)
            ).all()

            cleared_count = 0
            for task in tasks_to_clear:
                task.google_task_id = None
                task.google_tasklist_id = None
                cleared_count += 1

            db.commit()
            logger.info(f"Cleared google_task_id for {cleared_count} local tasks")
        except Exception as e:
            logger.error(f"Error clearing local task references: {e}")
            # Продолжаем, так как основная операция в Google выполнена

        result = {
            "status": "success" if len(failed_tasks) == 0 else "partial",
            "message": f"Deleted {deleted_count} tasks from Google Tasks" +
                       (f", {len(failed_tasks)} failed" if failed_tasks else ""),
            "details": {
                "tasklist_id": tasklist_id,
                "total_found": len(all_tasks),
                "deleted_count": deleted_count,
                "failed_count": len(failed_tasks),
                "failed_tasks": failed_tasks[:10],  # Ограничиваем вывод
                "local_references_cleared": cleared_count if 'cleared_count' in locals() else "not attempted"
            }
        }

        # Логируем серьезное действие
        logger.warning(f"GOOGLE TASKS CLEARED for user {user_id}: {deleted_count} tasks deleted")

        return result

    except HttpError as e:
        logger.error(f"Google API error in clear_google_tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in clear_google_tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing Google tasks: {str(e)}"
        )