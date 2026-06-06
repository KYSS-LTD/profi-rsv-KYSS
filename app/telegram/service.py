from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.models.models import Employee, KomandusTask
from app.monitoring.metrics import increment

logger = logging.getLogger(__name__)


class TelegramDeliveryError(RuntimeError):
    pass


@dataclass
class TelegramService:
    token: str | None = None
    api_base_url: str = "https://api.telegram.org"

    @property
    def bot_token(self) -> str:
        token = self.token or settings.BOT_TOKEN
        if not token:
            raise TelegramDeliveryError("BOT_TOKEN is not configured. Telegram delivery is disabled until a real bot token is provided.")
        return token

    async def _request(self, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.api_base_url}/bot{self.bot_token}/{method}"
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(url, json=payload or {})
                    data = response.json()
                    response.raise_for_status()
                if not data.get("ok"):
                    raise TelegramDeliveryError(f"Telegram API {method} failed: {data.get('description', 'unknown error')}")
                return data
            except httpx.HTTPStatusError as exc:
                detail = self._extract_error(exc.response)
                last_error = TelegramDeliveryError(f"Telegram API {method} failed: {detail}")
            except TelegramDeliveryError as exc:
                last_error = exc
            except Exception as exc:
                last_error = TelegramDeliveryError(f"Telegram API {method} failed: {exc}")
            increment("telegram_send_errors_total")
            logger.warning("Telegram API %s failed on attempt %s/3: %s", method, attempt + 1, last_error)
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
        raise last_error or TelegramDeliveryError(f"Telegram API {method} failed")

    def _extract_error(self, response: httpx.Response) -> str:
        try:
            data = response.json()
            return data.get("description") or response.text
        except Exception:
            return response.text

    async def send_message(self, chat_id: int | str, text: str, reply_markup: dict[str, Any] | None = None, parse_mode: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        safe_markup = self._sanitize_reply_markup(reply_markup)
        if safe_markup:
            payload["reply_markup"] = safe_markup
        return await self._request("sendMessage", payload)

    async def send_html_message(self, chat_id: int | str, html: str, reply_markup: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.send_message(chat_id, html, reply_markup=reply_markup, parse_mode="HTML")

    async def send_group_message(self, chat_id: int | str, text: str, reply_markup: dict[str, Any] | None = None) -> dict[str, Any]:
        bot_member = await self.get_chat_member(chat_id, "@self")
        status = bot_member.get("result", {}).get("status")
        if status not in {"administrator", "creator", "member"}:
            raise TelegramDeliveryError("Bot is not a member of this chat or has no permission to post messages.")
        return await self.send_message(chat_id, text, reply_markup=reply_markup)

    async def send_task_confirmation(self, employee: Employee, task: KomandusTask) -> dict[str, Any]:
        if not employee.telegram_id:
            raise TelegramDeliveryError(f"Employee {employee.id} has no telegram_user_id. Ask them to send /start to the bot.")
        text = (
            "<b>Найдена задача:</b>\n\n"
            f"<b>Название:</b> {self._escape(task.title)}\n"
            f"<b>Срок:</b> {task.due_at.isoformat() if task.due_at else '—'}\n"
            f"<b>Исполнитель:</b> {self._escape(employee.full_name)}\n"
            f"<b>Описание:</b> {self._escape(task.description or '—')}"
        )
        markup = {"inline_keyboard": [[{"text": "✅ Принять", "callback_data": f"task_accept:{task.id}"}, {"text": "❌ Отклонить", "callback_data": f"task_reject:{task.id}"}]]}
        return await self.send_html_message(employee.telegram_id, text, reply_markup=markup)

    async def send_activation_link(self, employee: Employee, activation_url: str | None) -> dict[str, Any]:
        if not employee.telegram_id:
            raise TelegramDeliveryError(f"Employee {employee.id} has no telegram_user_id. Cannot send direct message until /start is completed.")
        if not activation_url or not self.is_allowed_button_url(activation_url):
            logger.error("APP_PUBLIC_URL is missing or invalid; sending Telegram activation fallback without button for employee %s", employee.id)
            return await self.send_message(employee.telegram_id, "Ваш аккаунт создан.\n\nДля активации обратитесь к администратору.")
        first_name = employee.telegram_first_name or (employee.full_name.split()[0] if employee.full_name else "")
        text = f"Здравствуйте, {first_name}.\n\nВаш аккаунт в Командус готов. Задайте пароль самостоятельно по защищённой ссылке активации."
        markup = {"inline_keyboard": [[{"text": "🔗 Активировать Командус", "url": activation_url}]]}
        return await self.send_message(employee.telegram_id, text, reply_markup=markup)

    async def send_magic_login(self, employee: Employee, magic_url: str | None) -> dict[str, Any]:
        return await self.send_activation_link(employee, magic_url)

    async def send_login_credentials(self, employee: Employee, frontend_url: str | None = None) -> dict[str, Any]:
        return await self.send_activation_link(employee, frontend_url)

    async def send_reminder(self, employee: Employee, task: KomandusTask, reminder_label: str) -> dict[str, Any]:
        if not employee.telegram_id:
            raise TelegramDeliveryError(f"Employee {employee.id} has no telegram_user_id.")
        return await self.send_message(employee.telegram_id, f"Напоминание {reminder_label}: {task.title}")

    async def send_manager_notification(self, manager_chat_id: int | str, text: str) -> dict[str, Any]:
        return await self.send_message(manager_chat_id, f"Уведомление менеджеру:\n{text}")


    async def get_chat(self, chat_id: int | str) -> dict[str, Any]:
        return await self._request("getChat", {"chat_id": chat_id})

    async def get_chat_member(self, chat_id: int | str, user_id: int | str) -> dict[str, Any]:
        if user_id == "@self":
            me = await self._request("getMe")
            user_id = me.get("result", {}).get("id")
            if not user_id:
                raise TelegramDeliveryError("Cannot resolve bot user id via getMe.")
        return await self._request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def get_chat_member_count(self, chat_id: int | str) -> int | None:
        data = await self._request("getChatMemberCount", {"chat_id": chat_id})
        return data.get("result")

    async def get_user_profile(self, user_id: int) -> dict[str, Any]:
        return await self._request("getUserProfilePhotos", {"user_id": user_id, "limit": 1})

    async def answer_callback_query(self, callback_query_id: str, text: str | None = None, show_alert: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text
        return await self._request("answerCallbackQuery", payload)

    async def edit_message_text(self, chat_id: int | str, message_id: int, text: str, reply_markup: dict[str, Any] | None = None, parse_mode: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "message_id": message_id, "text": text}
        safe_markup = self._sanitize_reply_markup(reply_markup)
        if safe_markup:
            payload["reply_markup"] = safe_markup
        if parse_mode:
            payload["parse_mode"] = parse_mode
        return await self._request("editMessageText", payload)

    async def set_webhook(self, url: str, secret_token: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"url": url, "allowed_updates": ["message", "callback_query", "chat_member", "my_chat_member"]}
        if secret_token:
            payload["secret_token"] = secret_token
        return await self._request("setWebhook", payload)

    def is_allowed_button_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            return False
        public_url = settings.public_app_url
        if not public_url:
            return False
        public = urlparse(public_url)
        return parsed.netloc.lower() == public.netloc.lower()

    def _sanitize_reply_markup(self, reply_markup: dict[str, Any] | None) -> dict[str, Any] | None:
        if not reply_markup:
            return reply_markup
        keyboard = reply_markup.get("inline_keyboard")
        if not isinstance(keyboard, list):
            return reply_markup
        sanitized_rows = []
        for row in keyboard:
            sanitized_row = []
            for button in row:
                if isinstance(button, dict) and "url" in button and not self.is_allowed_button_url(str(button["url"])):
                    logger.error("Dropping invalid Telegram inline button URL: %s", button.get("url"))
                    continue
                sanitized_row.append(button)
            if sanitized_row:
                sanitized_rows.append(sanitized_row)
        return {**reply_markup, "inline_keyboard": sanitized_rows} if sanitized_rows else None

    def http_exception(self, exc: TelegramDeliveryError) -> HTTPException:
        return HTTPException(status_code=502, detail=str(exc))

    def _escape(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
