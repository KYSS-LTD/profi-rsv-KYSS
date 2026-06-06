from sqlalchemy.orm import Session

from app.models.models import Task


class KanbanAdapter:
    """
    Внутренний Kanban адаптер. Выполняет роль честного fallback-решения
    для управления доской задач, если внешняя интеграция отсутствует.
    """

    def __init__(self, db: Session):
        self.db = db

    def add_task(
        self,
        title: str,
        description: str | None = None,
        candidate_id: int | None = None,
        assignee: str | None = None,
        deadline: str | None = None,
        source: str = "telegram_text",
        confidence: float | None = None,
        status: str = "todo",
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            candidate_id=candidate_id,
            assignee=assignee,
            deadline=deadline,
            source=source,
            confidence=confidence,
            created_by_ai=candidate_id is not None,
            status=("OPEN" if status == "todo" else status.upper()),
            priority="medium",
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task_status(self, task_id: int, status: str) -> Task | None:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            self.db.commit()
            self.db.refresh(task)
        return task

    def get_all_tasks(self):
        return self.db.query(Task).all()
