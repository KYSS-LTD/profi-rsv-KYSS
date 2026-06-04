from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.models import TaskCandidate
from app.services.task_decision_engine import TaskDecisionEngine

router = APIRouter(prefix="/task-candidates", tags=["Task candidates"])


def serialize_candidate(candidate: TaskCandidate) -> dict:
    return {
        "id": str(candidate.id),
        "team_id": candidate.team_id,
        "message_id": str(candidate.message_id) if candidate.message_id else None,
        "meeting_id": str(candidate.meeting_id) if candidate.meeting_id else None,
        "title": candidate.title,
        "description": candidate.description,
        "assignee_id": str(candidate.assignee_id) if candidate.assignee_id else None,
        "assignee_raw": candidate.assignee_raw,
        "deadline": candidate.deadline,
        "deadline_raw": candidate.deadline_raw,
        "priority": candidate.priority,
        "confidence": candidate.confidence,
        "status": candidate.status,
        "source": candidate.source,
        "missing_fields": candidate.missing_fields or [],
        "reason": candidate.reason,
        "source_excerpt": candidate.source_excerpt,
        "source_message_url": candidate.source_message_url,
        "created_at": candidate.created_at,
        "updated_at": candidate.updated_at,
    }


@router.get("")
def get_candidates(status: str | None = None, db: Session = Depends(get_db)):
    stmt = select(TaskCandidate).order_by(TaskCandidate.created_at.desc())
    if status:
        stmt = stmt.where(TaskCandidate.status == status)
    return [serialize_candidate(candidate) for candidate in db.execute(stmt).scalars().all()]


@router.post("/{candidate_id}/reject")
def reject_candidate(candidate_id: int, payload: dict | None = None, db: Session = Depends(get_db)):
    engine = TaskDecisionEngine(db)
    try:
        candidate = engine.reject_candidate(candidate_id, reason=(payload or {}).get("reason") or "other")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": candidate.status, "candidate_id": str(candidate.id)}
