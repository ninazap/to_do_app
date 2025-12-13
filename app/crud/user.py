# app/crud/user.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.theme import ThemeUpdate
import uuid

def get_user(db: Session, user_id: str):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return None

    return db.query(User).filter(User.uuid == user_uuid).first()

def update_user_theme(db: Session, user_id: str, theme_update: ThemeUpdate):
    user = get_user(db, user_id)
    if not user:
        return None

    user.theme = theme_update.theme
    db.commit()
    db.refresh(user)
    return user