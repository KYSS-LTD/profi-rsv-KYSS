from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.models import Message, Task, TaskCandidate

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/team")
async def get_team_analytics(db: Session = Depends(get_db)):
    total_tasks = db.query(Task).count()
    ai_created_tasks = db.query(Task).filter(Task.created_by_ai.is_(True)).count()
    waiting_confirmation = db.query(TaskCandidate).filter(TaskCandidate.status.in_(("PENDING", "pending"))).count()
    rejected_suggestions = db.query(TaskCandidate).filter(TaskCandidate.status.in_(("REJECTED", "rejected"))).count()
    confirmed_candidates = db.query(TaskCandidate).filter(TaskCandidate.status.in_(("ACCEPTED", "approved", "confirmed"))).count()
    voice_messages_processed = db.query(Message).filter(Message.source == "telegram_voice").count()
    done_tasks = db.query(Task).filter(Task.status.in_(("DONE", "done"))).count()
    average_confidence = db.query(func.avg(TaskCandidate.confidence)).scalar() or 0

    return {
        "ai_created_tasks": ai_created_tasks,
        "auto_confirmed": confirmed_candidates,
        "waiting_confirmation": waiting_confirmation,
        "rejected_suggestions": rejected_suggestions,
        "voice_messages_processed": voice_messages_processed,
        "meetings_summarized": 0,
        "average_confidence": round(float(average_confidence), 2),
        "overdue_tasks": 0,
        "done_tasks": done_tasks,
        "team_velocity": {
            "done_this_week": done_tasks,
            "avg_lead_time_hours": 0,
            "overdue_percent": 0 if total_tasks == 0 else 0,
        },
        "ai_quality": {
            "average_confidence": round(float(average_confidence), 2),
            "auto_created": ai_created_tasks,
            "rejected_suggestions": rejected_suggestions,
        },
    }


@router.get("/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    rows = (
        db.query(Task.assignee, Task.assignee_id, func.count(Task.id))
        .filter(Task.status.in_(("DONE", "done")))
        .group_by(Task.assignee, Task.assignee_id)
        .all()
    )
    if not rows:
        return []

    return [
        {
            "user_id": assignee_id or f"user_{idx}",
            "name": assignee or assignee_id or "Не назначен",
            "xp": int(done_tasks) * 100,
            "level": "Active contributor" if done_tasks else "Starter",
            "done_tasks": int(done_tasks),
        }
        for idx, (assignee, assignee_id, done_tasks) in enumerate(rows, start=1)
    ]
