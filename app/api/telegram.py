from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.dependencies import get_current_employee, get_db, require_manager
from app.models.models import Employee, Message, TaskCandidate, TelegramSource
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


@router.get("/sources")
async def list_sources(current: Employee = Depends(get_current_employee), db: Session = Depends(get_db)):
    return [serialize_source(source) for source in db.query(TelegramSource).filter(TelegramSource.organization_id == current.organization_id).all()]


@router.post("/sources", status_code=201)
async def create_source(payload: dict = Body(default_factory=dict), current: Employee = Depends(require_manager), db: Session = Depends(get_db)):
    chat_id = payload.get("chat_id")
    if chat_id is None:
        raise HTTPException(status_code=422, detail="chat_id is required")
    source = db.query(TelegramSource).filter(TelegramSource.chat_id == int(chat_id)).first()
    if source and source.organization_id != current.organization_id:
        raise HTTPException(status_code=409, detail="Chat is already registered in another organization")
    if source is None:
        source = TelegramSource(chat_id=int(chat_id), organization_id=current.organization_id)
        db.add(source)
    source.chat_title = payload.get("chat_title")
    source.department_id = payload.get("department_id")
    source.is_active = bool(payload.get("is_active", True))
    db.commit()
    db.refresh(source)
    return serialize_source(source)


def serialize_source(source: TelegramSource) -> dict:
    return {
        "id": source.id,
        "organization_id": source.organization_id,
        "chat_id": source.chat_id,
        "chat_title": source.chat_title,
        "department_id": source.department_id,
        "is_active": source.is_active,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }


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
        "source_excerpt": candidate.source_excerpt,
        "llm_block": candidate.llm_block,
        "rejection_reason": candidate.rejection_reason,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
    }
