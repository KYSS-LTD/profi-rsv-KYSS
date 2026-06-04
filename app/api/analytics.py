from fastapi import APIRouter, Depends
from sqlalchemy import avg, func, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.models import Meeting, Message, Task, TaskCandidate

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/team")
def get_team_analytics(db: Session = Depends(get_db)):
    total_ai_tasks = db.scalar(select(func.count()).select_from(Task).where(Task.created_by_ai.is_(True))) or 0
    auto_confirmed = db.scalar(select(func.count()).select_from(TaskCandidate).where(TaskCandidate.status == "confirmed", TaskCandidate.confidence >= 0.85)) or 0
    waiting = db.scalar(select(func.count()).select_from(TaskCandidate).where(TaskCandidate.status == "pending")) or 0
    rejected = db.scalar(select(func.count()).select_from(TaskCandidate).where(TaskCandidate.status == "rejected")) or 0
    avg_conf = db.scalar(select(avg(TaskCandidate.confidence))) or 0
    done_tasks = db.scalar(select(func.count()).select_from(Task).where(Task.status == "done")) or 0
    overdue = db.scalar(select(func.count()).select_from(Task).where(Task.status.notin_(["done", "cancelled"]), Task.deadline < func.now())) or 0
    voice_messages = db.scalar(select(func.count()).select_from(Message).where(Message.voice_file_id.is_not(None))) or 0
    meetings = db.scalar(select(func.count()).select_from(Meeting)) or 0
    return {
        "ai_created_tasks": total_ai_tasks,
        "auto_confirmed": auto_confirmed,
        "waiting_confirmation": waiting,
        "rejected_suggestions": rejected,
        "voice_messages_processed": voice_messages,
        "meetings_summarized": meetings,
        "average_confidence": round(float(avg_conf), 2),
        "overdue_tasks": overdue,
        "done_tasks": done_tasks,
        "team_velocity": {"done_this_week": done_tasks, "avg_lead_time_hours": 0, "overdue_percent": 0},
        "ai_quality": {"average_confidence": round(float(avg_conf), 2), "auto_created": auto_confirmed, "rejected_suggestions": rejected},
    }


@router.get("/leaderboard")
def get_leaderboard():
    return []
