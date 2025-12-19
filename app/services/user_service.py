from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
import logging
from datetime import datetime

from models.user import User

logger = logging.getLogger(__name__)

class UserService:
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_uuid(db: Session, user_uuid: UUID) -> Optional[User]:
        return db.query(User).filter(User.uuid == user_uuid).first()
    
    @staticmethod
    def get_or_create_lightweight_user(
        db: Session, 
        user_data: Dict[str, Any]
    ) -> User:
        try:
            email = user_data["email"]
            user = UserService.get_user_by_email(db, email)
            
            if user:
                update_fields = ["username", "is_active", "theme"]
                for field in update_fields:
                    if field in user_data and user_data[field] is not None:
                        setattr(user, field, user_data[field])
                
                logger.debug(f"Обновлен пользователь: {email}")
            else:
                user = User(
                    uuid=UUID(user_data["uuid"]) if user_data.get("uuid") else None,
                    email=email,
                    username=user_data.get("username", email.split('@')[0]),
                    is_active=user_data.get("is_active", True),
                    theme=user_data.get("theme", "light"),
                    created_at=user_data.get("created_at", datetime.utcnow())
                )
                db.add(user)
                logger.debug(f"Создан пользователь: {email}")
            
            db.commit()
            db.refresh(user)
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка создания/обновления пользователя {user_data.get('email')}: {e}")
            raise
    
    @staticmethod
    def update_user_profile(
        db: Session, 
        email: str, 
        profile_data: Dict[str, Any]
    ) -> Optional[User]:
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        
        # Разрешаем обновлять только безопасные поля
        allowed_fields = ["username", "theme"]
        
        for field, value in profile_data.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def deactivate_user(db: Session, email: str) -> bool:
        user = UserService.get_user_by_email(db, email)
        if not user:
            return False
        
        user.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def get_all_active_users(db: Session, skip: int = 0, limit: int = 100):
        return db.query(User).filter(
            User.is_active == True
        ).offset(skip).limit(limit).all()