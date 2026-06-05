from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.models import Message, TaskCandidate
from app.schemas import TelegramWebhook
from app.services.task_decision_engine import TaskDecisionEngine
from app.tasks.tasks import process_telegram_message

router = APIRouter(
    prefix="/telegram",
    tags=["Telegram"],
)


@router.post("/webhook")
async def telegram_webhook(payload: TelegramWebhook, db: Session = Depends(get_db)):
    update = payload.model_dump()
    try:
        process_telegram_message.delay(update)
        return {"status": "accepted", "mode": "celery"}
    except Exception:
        result = await TaskDecisionEngine(db).process_update(update)
        return {"status": "accepted", "mode": "inline", "result": result}


@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: int, limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(desc(Message.telegram_message_id))
        .limit(limit)
        .all()
    )
    return [serialize_message(message) for message in reversed(rows)]


@router.post("/chats/{chat_id}/analyze")
async def analyze_chat(chat_id: int, db: Session = Depends(get_db)):
    candidates = await TaskDecisionEngine(db).process_chat_context(chat_id)
    return {"created_candidates": [serialize_candidate(candidate) for candidate in candidates]}


@router.get("/candidates")
async def get_db_candidates(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(TaskCandidate).order_by(desc(TaskCandidate.created_at))
    if status:
        query = query.filter(TaskCandidate.status == status)
    return [serialize_candidate(candidate) for candidate in query.limit(200).all()]


def serialize_message(message: Message) -> dict:
    return {
        "id": message.id,
        "telegram_message_id": message.telegram_message_id,
        "telegram_user_id": message.telegram_user_id,
        "chat_id": message.chat_id,
        "sender_name": message.sender_name,
        "username": message.username,
        "text": message.text,
        "source": message.source,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def serialize_candidate(candidate: TaskCandidate) -> dict:
    return {
        "id": candidate.id,
        "message_id": candidate.message_id,
        "chat_id": candidate.chat_id,
        "title": candidate.title,
        "assignee_raw": candidate.assignee_raw,
        "deadline_raw": candidate.deadline_raw,
        "confidence": candidate.confidence,
        "status": candidate.status,
        "action": candidate.action,
        "source_excerpt": candidate.source_excerpt,
        "llm_block": candidate.llm_block,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
    }
