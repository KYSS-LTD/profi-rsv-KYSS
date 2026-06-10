from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.models import Message, Task, TaskCandidate

router = APIRouter(prefix="/task-candidates", tags=["Task candidates"])


@router.get("")
async def get_candidates(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(TaskCandidate).order_by(desc(TaskCandidate.created_at))
    if status:
        query = query.filter(TaskCandidate.status == status)
    return [serialize_candidate(db, candidate) for candidate in query.limit(200).all()]


@router.post("/{candidate_id}/confirm")
async def confirm_candidate(candidate_id: str, payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    candidate = get_db_candidate(db, candidate_id)
    if candidate.status != "pending":
        return {"task_id": None, "status": candidate.status}

    overrides = payload.get("overrides") or {}
    task = Task(
        candidate_id=candidate.id,
        title=overrides.get("title") or candidate.title,
        description=overrides.get("description") or candidate.source_excerpt or "Создано из AI-кандидата.",
        assignee=overrides.get("assignee_raw") or candidate.assignee_raw,
        assignee_id=overrides.get("assignee_id"),
        deadline=overrides.get("deadline") or candidate.deadline_raw,
        status="done" if candidate.action == "complete" else "todo",
        priority=overrides.get("priority") or "medium",
        source=get_candidate_source(db, candidate),
        confidence=candidate.confidence,
        created_by_ai=True,
    )
    candidate.status = "confirmed"
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"task_id": f"db_{task.id}", "external_kanban_id": None, "external_kanban_url": None, "status": "created"}


@router.post("/{candidate_id}/reject")
async def reject_candidate(candidate_id: str, payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    candidate = get_db_candidate(db, candidate_id)
    candidate.status = "rejected"
    db.commit()
    return {"status": "rejected", "candidate_id": str(candidate.id), "reason": payload.get("reason") or "other"}


def get_db_candidate(db: Session, candidate_id: str) -> TaskCandidate:
    raw_id = candidate_id.removeprefix("candidate_")
    if not raw_id.isdigit():
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate = db.query(TaskCandidate).filter(TaskCandidate.id == int(raw_id)).first()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


def get_candidate_source(db: Session, candidate: TaskCandidate) -> str:
    message = db.query(Message).filter(Message.id == candidate.message_id).first()
    return message.source if message else "telegram_text"


def serialize_candidate(db: Session, candidate: TaskCandidate) -> dict:
    source = get_candidate_source(db, candidate)
    missing_fields = []
    if not candidate.assignee_raw:
        missing_fields.append("assignee")
    if not candidate.deadline_raw:
        missing_fields.append("deadline")

    return {
        "id": str(candidate.id),
        "team_id": "team_1",
        "message_id": str(candidate.message_id),
        "title": candidate.title,
        "description": candidate.source_excerpt,
        "assignee_raw": candidate.assignee_raw,
        "deadline_raw": candidate.deadline_raw,
        "deadline": candidate.deadline_raw,
        "priority": "medium",
        "confidence": candidate.confidence,
        "status": candidate.status,
        "source": source,
        "missing_fields": missing_fields,
        "source_excerpt": candidate.source_excerpt,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
    }
