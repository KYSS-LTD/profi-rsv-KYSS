from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.access_scope import AccessScopeService
from app.common.enums import TaskStatus
from app.models.models import KomandusTask, User


class AIAssistantService:
    """Operational AI assistant with deterministic DB-backed fallback."""

    def __init__(self, db: Session):
        self.db = db

    async def answer(self, user: User, question: str) -> dict:
        # Production hook: call external LLM here. The fallback below is always
        # safe and never exposes provider failures to Telegram/frontend users.
        return self.fallback_answer(user, question)

    def fallback_answer(self, user: User, question: str) -> dict:
        tasks = AccessScopeService(self.db).get_visible_tasks(user).all()
        total = len(tasks)
        overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
        in_work = sum(1 for task in tasks if task.status in {TaskStatus.ACCEPTED.value, TaskStatus.TO_DO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.REVIEW.value})
        completed = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
        lower = question.lower()
        if "сегодня" in lower:
            today_tasks = [task for task in tasks if task.due_at and task.due_at.date().isoformat()]
            answer = f"В вашей зоне видимости {len(today_tasks)} задач с дедлайнами. В работе: {in_work}."
        elif "риск" in lower or "проср" in lower:
            answer = f"Главный риск сейчас — {overdue} просроченных задач из {total}."
        else:
            answer = f"В доступной вам области {total} задач: {completed} завершено, {in_work} в работе, {overdue} просрочено."
        return {"answer": answer, "facts": [f"Всего задач: {total}", f"В работе: {in_work}", f"Завершено: {completed}", f"Просрочено: {overdue}"]}
