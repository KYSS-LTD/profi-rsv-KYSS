import asyncio
import logging

from app.audit.services import AuditService
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.task_decision_engine import TaskDecisionEngine
from app.telegram.service import TelegramDeliveryError

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.process_telegram_message",
    autoretry_for=(TelegramDeliveryError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_telegram_message(self, payload: dict):
    db = SessionLocal()
    try:
        engine = TaskDecisionEngine(db)
        return asyncio.run(engine.process_update(payload))
    except TelegramDeliveryError as exc:
        logger.exception("Telegram API error while processing update")
        AuditService(db).log(action="Telegram API Error", entity_type="TelegramUpdate", metadata={"error": str(exc), "update_id": payload.get("update_id")})
        raise
    finally:
        db.close()
