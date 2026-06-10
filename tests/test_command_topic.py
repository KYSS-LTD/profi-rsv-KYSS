import asyncio

import pytest

pytest.importorskip("fastapi")

from app.telegram.commands import TelegramCommandRouter


class _Fake:
    def __init__(self):
        self.calls = []

    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None, message_thread_id=None):
        self.calls.append({"chat_id": chat_id, "message_thread_id": message_thread_id})
        return {}


def _router():
    router = TelegramCommandRouter.__new__(TelegramCommandRouter)
    router.telegram = _Fake()
    router._current_topic = None
    return router


def test_command_reply_keeps_topic_in_group():
    router = _router()
    router._current_topic = 77
    asyncio.run(router._send_message(-100123, "hi"))
    assert router.telegram.calls[-1]["message_thread_id"] == 77


def test_command_reply_no_topic_in_private():
    router = _router()
    router._current_topic = None
    asyncio.run(router._send_message(555, "hi"))
    assert router.telegram.calls[-1]["message_thread_id"] is None
