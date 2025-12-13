import asyncio
import subprocess
import sys

from pathlib import Path

from fastapi import APIRouter, Depends, status, HTTPException


from ..dependencies.auth_dep import get_current_admin_user
from ..dao.alembic_repos import revision, migrate, downgrade, get_history




# Админский роутер
admin_router = APIRouter(tags=["Alembic"], 
                        include_in_schema=True, 
                        dependencies=[Depends(get_current_admin_user)],
                        )

@admin_router.post("/migrate", summary="Применить миграции")
async def migrate_router():
    try:
        result = await asyncio.to_thread(migrate)
        return {
            "status": "success", 
            "message": result,
            "operation": "migrate"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )

@admin_router.post("/downgrade")
async def downgrade_router(revision_id: str = "-1", user=Depends(get_current_admin_user)):
    try:
        result = await asyncio.to_thread(downgrade, revision_id)
        return {
            "status": "success", 
            "message": result,
            "operation": "downgrade",
            "revision": revision_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Downgrade failed: {str(e)}"
        )

@admin_router.post("/revision", summary="Создать новую миграцию")
async def revision_router(message: str):
    """Создает новую миграцию с заданным сообщением"""
    if not message or len(message.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message must be at least 3 characters long"
        )
    
    try:
        result = await asyncio.to_thread(revision, message.strip())
        return {
            "status": "success", 
            "message": result,
            "operation": "revision",
            "revision_message": message
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revision creation failed: {str(e)}"
        )

@admin_router.get("/history", summary="История миграций")
async def history_router():
    """Показывает историю миграций"""
    result = await asyncio.to_thread(get_history)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration history: {result.get('error')}"
        )
    
    return {
        "status": "success",
        "data": result,
        "count": result.get("count", 0)
    }