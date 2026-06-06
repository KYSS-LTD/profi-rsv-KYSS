from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.models import Employee, Organization, Task, TaskCandidate
from app.services.yougile_service import YouGileService

TASK_STATUSES = {"OPEN", "IN_PROGRESS", "DONE", "CANCELLED"}
LEGACY_STATUS_MAP = {"todo": "OPEN", "in_progress": "IN_PROGRESS", "done": "DONE", "cancelled": "CANCELLED"}


def normalize_task_status(status: str | None) -> str:
    if not status:
        return "OPEN"
    normalized = status.strip().upper()
    return LEGACY_STATUS_MAP.get(status.strip().lower(), normalized)


async def create_task_from_candidate(db: Session, candidate: TaskCandidate, creator: Employee | None = None) -> Task:
    assignee = db.query(Employee).filter(Employee.id == candidate.assignee_id).first() if candidate.assignee_id else None
    task = Task(
        organization_id=candidate.organization_id,
        candidate_id=candidate.id,
        title=candidate.title,
        description=candidate.description or candidate.source_excerpt or "Извлечено из Telegram-чата.",
        assignee_employee_id=assignee.id if assignee else None,
        assignee_id=str(assignee.id) if assignee else None,
        creator_id=creator.id if creator else None,
        assignee=assignee.full_name if assignee else candidate.assignee_raw,
        deadline=candidate.deadline or candidate.deadline_raw,
        due_date=candidate.deadline or candidate.deadline_raw,
        status="OPEN",
        priority="medium",
        source="telegram_text",
        confidence=candidate.confidence,
        created_by_ai=True,
    )
    candidate.status = "ACCEPTED"
    db.add(task)
    db.commit()
    db.refresh(task)

    organization = db.query(Organization).filter(Organization.id == task.organization_id).first() if task.organization_id else None
    result = await YouGileService().create_task(task, organization)
    if result.synced:
        task.yougile_task_id = result.external_id
        task.yougile_url = result.url
        db.commit()
        db.refresh(task)
    return task


async def sync_task_status_to_yougile(db: Session, task: Task) -> dict:
    organization = db.query(Organization).filter(Organization.id == task.organization_id).first() if task.organization_id else None
    result = await YouGileService().update_task_status(task, organization)
    return {"external_synced": result.synced, "external_error": result.error}
