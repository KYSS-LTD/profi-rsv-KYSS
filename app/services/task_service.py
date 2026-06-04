from sqlalchemy.orm import Session

from app.models.models import Task


class TaskService:
    @staticmethod
    def get_all(db: Session):
        return db.query(Task).all()

    @staticmethod
    def create(db: Session, title: str, description: str | None, priority: str = "medium"):
        task = Task(title=title, description=description, status="todo", priority=priority, source="telegram_text")
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
