from __future__ import annotations

from app.telegram.commands import TelegramCommandRouter


class TelegramCallbackRouter:
    def __init__(self, engine):
        self.engine = engine
        self.commands = TelegramCommandRouter(engine.db, engine.telegram)

    async def dispatch(self, callback: dict):
        data = callback.get("data", "")
        if data.startswith("menu:"):
            return await self._menu(callback, data.split(":", 1)[1])
        return await self.engine._handle_task_callback(callback)

    async def _menu(self, callback: dict, action: str):
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        callback_id = callback["id"]
        from_user = callback.get("from") or {}
        fake_msg = {"chat": {"id": chat_id, "type": "private"}, "from": from_user}
        mapping = {"tasks": "/tasks", "today": "/today", "stats": "/stats", "help": "/help", "login": "/login"}
        if action in mapping:
            await self.engine.telegram.answer_callback_query(callback_id)
            return await self.commands._employee_command(fake_msg, mapping[action])
        await self.engine.telegram.answer_callback_query(callback_id, "Раздел скоро появится")
        return {"status": "menu", "action": action}
