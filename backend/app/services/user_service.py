from sqlalchemy.orm import Session
from app.db.models import User
from app.models.schemas import UserCreate
from app.services.password_service import PasswordService
from typing import Optional

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, user: UserCreate) -> User:
        hashed_password = PasswordService.get_password_hash(user.password)
        db_user = User(
            email=user.email,
            name=user.name,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not PasswordService.verify_password(password, user.hashed_password):
            return None
        return user