from sqlalchemy.orm import Session
from app.models.models import Task

class TaskService:

    @staticmethod
    def get_all(db: Session):
        return db.query(Task).all()

    @staticmethod
    def create(db: Session, title: str, description: str | None):
        task = Task(
            title=title,
            description=description,
            status="todo",
            priority="medium"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task