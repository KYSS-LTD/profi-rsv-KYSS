from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.dependencies import get_current_employee, get_db
from app.models.models import Employee, Message, TaskCandidate
from app.services.task_service import create_task_from_candidate

router = APIRouter(prefix="/task-candidates", tags=["Task candidates"])


@router.get("")
async def get_candidates(
    status: str | None = None,
    current: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    query = db.query(TaskCandidate).filter(TaskCandidate.organization_id == current.organization_id).order_by(desc(TaskCandidate.created_at))
    if current.role == "EMPLOYEE":
        query = query.filter(TaskCandidate.assignee_id == current.id)
    if status:
        query = query.filter(TaskCandidate.status == status.upper())
    return [serialize_candidate(db, candidate) for candidate in query.limit(200).all()]


@router.post("/{candidate_id}/confirm")
async def confirm_candidate(
    candidate_id: str,
    payload: dict = Body(default_factory=dict),
    current: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    candidate = get_db_candidate(db, candidate_id, current)
    if candidate.status not in {"PENDING", "pending"}:
        return {"task_id": None, "status": candidate.status}

    overrides = payload.get("overrides") or {}
    if overrides.get("title"):
        candidate.title = overrides["title"]
    if overrides.get("description"):
        candidate.description = overrides["description"]
    if overrides.get("deadline"):
        candidate.deadline = overrides["deadline"]
        candidate.deadline_raw = overrides["deadline"]
    task = await create_task_from_candidate(db, candidate, current)
    return {"task_id": f"db_{task.id}", "external_kanban_id": task.yougile_task_id, "external_kanban_url": task.yougile_url, "status": "created"}


@router.post("/{candidate_id}/reject")
async def reject_candidate(
    candidate_id: str,
    payload: dict = Body(default_factory=dict),
    current: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    candidate = get_db_candidate(db, candidate_id, current)
    candidate.status = "REJECTED"
    candidate.rejection_reason = payload.get("reason") or "other"
    db.commit()
    return {"status": "REJECTED", "candidate_id": str(candidate.id), "reason": candidate.rejection_reason}


def get_db_candidate(db: Session, candidate_id: str, current: Employee) -> TaskCandidate:
    raw_id = candidate_id.removeprefix("candidate_")
    if not raw_id.isdigit():
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate = db.query(TaskCandidate).filter(TaskCandidate.id == int(raw_id), TaskCandidate.organization_id == current.organization_id).first()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current.role == "EMPLOYEE" and candidate.assignee_id != current.id:
        raise HTTPException(status_code=403, detail="Employees can process only own candidates")
    return candidate


def get_candidate_source(db: Session, candidate: TaskCandidate) -> str:
    message = db.query(Message).filter(Message.id == candidate.message_id).first()
    return message.source if message else "telegram_text"


def serialize_candidate(db: Session, candidate: TaskCandidate) -> dict:
    return {
        "id": f"candidate_{candidate.id}",
        "db_id": candidate.id,
        "organization_id": candidate.organization_id,
        "message_id": candidate.message_id,
        "chat_id": candidate.chat_id,
        "source_message_id": candidate.source_message_id,
        "source_chat_id": candidate.source_chat_id,
        "title": candidate.title,
        "description": candidate.description,
        "assignee_raw": candidate.assignee_raw,
        "assignee_id": candidate.assignee_id,
        "deadline_raw": candidate.deadline_raw,
        "deadline": candidate.deadline,
        "confidence": candidate.confidence,
        "status": candidate.status,
        "action": candidate.action,
        "source": get_candidate_source(db, candidate),
        "source_excerpt": candidate.source_excerpt,
        "llm_block": candidate.llm_block,
        "rejection_reason": candidate.rejection_reason,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
    }
