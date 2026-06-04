from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.models import Message
from app.schemas import TelegramWebhook
from app.tasks.tasks import process_callback_query_task, process_text_message_task, process_voice_message_task

router = APIRouter(tags=["Telegram"])


@router.post("/telegram/webhook")
@router.post("/webhooks/telegram")
def telegram_webhook(payload: TelegramWebhook, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if payload.message:
        msg = payload.message
        text = msg.get("text") or msg.get("caption")
        voice = msg.get("voice") or {}
        db_message = Message(
            telegram_update_id=payload.update_id,
            telegram_message_id=msg.get("message_id"),
            telegram_user_id=(msg.get("from") or {}).get("id"),
            chat_id=(msg.get("chat") or {}).get("id"),
            text=text,
            voice_file_id=voice.get("file_id"),
            raw_update=data,
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        if db_message.voice_file_id:
            process_voice_message_task.delay(db_message.id)
        elif db_message.text:
            process_text_message_task.delay(db_message.id)
    elif payload.callback_query:
        process_callback_query_task.delay(data)
    return {"status": "accepted"}
