# app/api/theme.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.theme import ThemeUpdate, ThemeResponse
from app.crud.user import get_user, update_user_theme
from app.models.user import User

router = APIRouter(prefix="/theme", tags=["theme"])

# Правильные UUID из миграции fa8fcaf9ff48_create_fake_users_data.py
DEFAULT_USER_ID = "11111111-1111-1111-1111-111111111111"

@router.get("/users", response_model=List[dict])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "uuid": str(user.uuid),
            "username": user.username,
            "email": user.email,
            "theme": user.theme,
            "full_name": user.full_name
        }
        for user in users
    ]

@router.get("/", response_model=ThemeResponse)
def get_current_theme(
        user_id: str = Query(
            default=DEFAULT_USER_ID,
            description="UUID пользователя"
        ),
        db: Session = Depends(get_db)
):

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return ThemeResponse(
        user_id=str(user.uuid),
        username=user.username,
        theme=user.theme
    )


@router.put("/", response_model=ThemeResponse)
def update_theme(
        theme_update: ThemeUpdate,
        user_id: str = Query(
            default=DEFAULT_USER_ID,
            description="UUID пользователя"
        ),
        db: Session = Depends(get_db)
):

    user = update_user_theme(db, user_id, theme_update.theme)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return ThemeResponse(
        user_id=str(user.uuid),
        username=user.username,
        theme=user.theme
    )