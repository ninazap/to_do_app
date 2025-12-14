from sqlalchemy.orm import Session
from app.models.user_google_token import UserGoogleToken
import uuid
import json
from datetime import datetime


def get_google_token(db: Session, user_id: str):
    """Получить Google токен пользователя"""
    try:
        user_uuid = uuid.UUID(user_id)
        return db.query(UserGoogleToken).filter(
            UserGoogleToken.user_id == user_uuid
        ).first()
    except ValueError:
        return None


def create_or_update_google_token(db: Session, user_id: str, token_data: dict):
    """Создать или обновить Google токен пользователя"""
    try:
        user_uuid = uuid.UUID(user_id)
        token_record = get_google_token(db, user_id)

        if token_record:
            token_record.token_data = json.dumps(token_data)
            token_record.updated_at = datetime.utcnow()
        else:
            token_record = UserGoogleToken(
                user_id=user_uuid,
                token_data=json.dumps(token_data)
            )
            db.add(token_record)

        db.commit()
        return token_record
    except Exception as e:
        db.rollback()
        raise e


def delete_google_token(db: Session, user_id: str) -> bool:
    """Удалить Google токен пользователя"""
    try:
        user_uuid = uuid.UUID(user_id)
        token = db.query(UserGoogleToken).filter(
            UserGoogleToken.user_id == user_uuid
        ).first()

        if token:
            db.delete(token)
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False


def get_user_by_google_token(db: Session, token_data: str):
    """Получить пользователя по Google токену"""
    return db.query(UserGoogleToken).filter(
        UserGoogleToken.token_data == token_data
    ).first()