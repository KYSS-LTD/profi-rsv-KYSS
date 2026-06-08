import asyncio
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from app.services.task_decision_engine import TaskDecisionEngine, match_employee_by_name
from app.telegram.service import TelegramService


def _run(coro):
    return asyncio.run(coro)


# --- message_thread_id (topic) propagation -----------------------------------

def test_send_message_includes_message_thread_id():
    service = TelegramService(token="dummy")
    captured = {}

    async def fake_request(method, payload=None):
        captured["payload"] = payload
        return {"ok": True, "result": {}}

    service._request = fake_request

    _run(service.send_message(123, "hi", message_thread_id=42))
    assert captured["payload"]["message_thread_id"] == 42

    captured.clear()
    _run(service.send_message(123, "hi"))
    assert "message_thread_id" not in captured["payload"]


def test_send_group_message_passes_thread_id():
    service = TelegramService(token="dummy")
    captured = {}

    async def fake_request(method, payload=None):
        if method == "sendMessage":
            captured["payload"] = payload
        return {"ok": True, "result": {}}

    async def fake_member(chat_id, user_id):
        return {"result": {"status": "administrator"}}

    service._request = fake_request
    service.get_chat_member = fake_member

    _run(service.send_group_message(-100123, "task", message_thread_id=7))
    assert captured["payload"]["message_thread_id"] == 7


# --- assignee name matching (pure) -------------------------------------------

def _emp(name, team=None, dept=None):
    return SimpleNamespace(full_name=name, team_id=team, department_id=dept, id=name)


def test_match_exact_and_first_name_token():
    emps = [_emp("Иван Петров"), _emp("Мария Сидорова")]
    assert match_employee_by_name("Иван Петров", emps).full_name == "Иван Петров"
    assert match_employee_by_name("Иван", emps).full_name == "Иван Петров"


def test_match_ambiguous_returns_none():
    emps = [_emp("Иван Петров", team="t1"), _emp("Иван Сидоров", team="t1")]
    assert match_employee_by_name("Иван", emps, team_id="t1") is None


def test_match_scope_tiebreak_team_then_department():
    a = _emp("Иван Петров", team="t1", dept="d1")
    b = _emp("Иван Сидоров", dept="d2")
    assert match_employee_by_name("Иван", [a, b], team_id="t1") is a

    c = _emp("Олег Кузнецов", dept="d1")
    d = _emp("Олег Орлов")
    assert match_employee_by_name("Олег", [c, d], department_id="d1") is c


def test_match_no_match_and_empty():
    emps = [_emp("Иван Петров")]
    assert match_employee_by_name("Сергей", emps) is None
    assert match_employee_by_name(None, emps) is None
    assert match_employee_by_name("   ", emps) is None


# --- routing precedence in _dispatch_detected_task ---------------------------

class _FakeTelegram:
    def __init__(self):
        self.calls = []

    async def send_task_confirmation(self, employee, task):
        self.calls.append(("employee", getattr(employee, "id", None)))
        return {}

    async def send_manager_task_confirmation(self, manager, task, employee_hint=None):
        self.calls.append(("manager", getattr(manager, "id", None), employee_hint))
        return {}

    async def send_group_message(self, chat_id, text, reply_markup=None, message_thread_id=None):
        self.calls.append(("group", chat_id, message_thread_id))
        return {}


def _engine(telegram, manager=None):
    engine = TaskDecisionEngine.__new__(TaskDecisionEngine)
    engine.telegram = telegram
    engine.db = None
    engine._resolve_manager = lambda organization_id, department_id, team_id, employee: manager
    return engine


def _task(confidence=0.9, title="T"):
    return SimpleNamespace(id="task-uuid", title=title, due_at=None, llm_confidence=confidence)


def test_dispatch_to_employee_when_resolved_and_high_confidence():
    fake = _FakeTelegram()
    engine = _engine(fake)
    employee = SimpleNamespace(id="e1", full_name="Иван", telegram_id=555)
    result = _run(engine._dispatch_detected_task(_task(0.9), employee, "org", "d", "t", -100, 12))
    assert result["routed_to"] == "employee"
    assert fake.calls[0][0] == "employee"


def test_dispatch_to_manager_when_low_confidence():
    fake = _FakeTelegram()
    manager = SimpleNamespace(id="m1", full_name="Менеджер", telegram_id=777)
    engine = _engine(fake, manager=manager)
    employee = SimpleNamespace(id="e1", full_name="Иван", telegram_id=555)
    result = _run(engine._dispatch_detected_task(_task(0.5), employee, "org", "d", "t", -100, 12))
    assert result["routed_to"] == "manager"
    assert fake.calls[0][0] == "manager"


def test_dispatch_to_manager_when_no_assignee():
    fake = _FakeTelegram()
    manager = SimpleNamespace(id="m1", full_name="Менеджер", telegram_id=777)
    engine = _engine(fake, manager=manager)
    result = _run(engine._dispatch_detected_task(_task(0.95), None, "org", "d", "t", -100, 12))
    assert result["routed_to"] == "manager"


def test_dispatch_group_fallback_keeps_topic():
    fake = _FakeTelegram()
    engine = _engine(fake, manager=None)
    result = _run(engine._dispatch_detected_task(_task(0.95), None, "org", "d", "t", -100, 34))
    assert result["routed_to"] == "group"
    assert fake.calls[0] == ("group", -100, 34)
