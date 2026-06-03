from fastapi import APIRouter
from app.schemas import TelegramWebhook
from app.tasks.tasks import process_telegram_message

router = APIRouter(
    prefix="/telegram",
    tags=["Telegram"],
)

@router.post("/webhook")
async def telegram_webhook(
    payload: TelegramWebhook,
):
    process_telegram_message.delay(payload.model_dump())
    return {
        "status": "accepted"
    }