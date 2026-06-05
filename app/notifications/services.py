from __future__ import annotations

import httpx
from app.core.config import settings
from app.monitoring.metrics import increment


class TelegramNotificationService:
    async def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> dict:
        if not settings.BOT_TOKEN:
            raise RuntimeError("BOT_TOKEN is not configured")
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception:
            increment("telegram_send_errors_total")
            raise
