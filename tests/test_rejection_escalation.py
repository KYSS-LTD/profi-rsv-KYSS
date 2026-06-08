import asyncio
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from app.services.task_decision_engine import TaskDecisionEngine


class _Fake:
    def __init__(self):
        self.calls = []

    def _escape(self, text):
        return text

    async def send_html_message(self, chat_id, html, reply_markup=None, message_thread_id=None):
        self.calls.append((chat_id, reply_markup))
        return {}


def _engine(manager):
    engine = TaskDecisionEngine.__new__(TaskDecisionEngine)
    engine.telegram = _Fake()
    engine.db = None
    engine._resolve_manager = lambda organization_id, department_id, team_id, employee: manager
    return engine


def _task():
    return SimpleNamespace(id="tid", employee_id=None, organization_id="o", department_id="d", team_id="t", title="X")


def test_rejection_escalation_offers_reassign_false_resend():
    manager = SimpleNamespace(telegram_id=900001, full_name="Boss")
    engine = _engine(manager)
    asyncio.run(engine._escalate_rejection_to_manager(_task(), "Нет времени"))
    assert engine.telegram.calls, "manager was not notified"
    chat_id, markup = engine.telegram.calls[-1]
    assert chat_id == 900001
    cbs = [b["callback_data"] for row in markup["inline_keyboard"] for b in row]
    assert any(c.startswith("mgr_reassign:") for c in cbs)
    assert any(c.startswith("mgr_reject_false:") for c in cbs)
    assert any(c.startswith("mgr_resend:") for c in cbs)


def test_rejection_escalation_silent_without_manager():
    engine = _engine(None)
    asyncio.run(engine._escalate_rejection_to_manager(_task(), None))
    assert not engine.telegram.calls
