from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower(), User.is_active.is_(True)).first()

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()

    def count(self) -> int:
        return self.db.query(func.count(User.id)).scalar() or 0

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
