import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base, Employee, Organization, Task, TelegramSource
from app.services.task_decision_engine import TaskDecisionEngine


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_telegram_start_connects_employee_by_username():
    db = make_db()
    org = Organization(name="Komandus")
    db.add(org)
    db.flush()
    employee = Employee(
        organization_id=org.id,
        full_name="Иван Петров",
        email="ivan@example.com",
        role="EMPLOYEE",
        telegram_username="ivan_petrov",
    )
    db.add(employee)
    db.commit()

    result = asyncio.run(
        TaskDecisionEngine(db).process_update(
            {
                "message": {
                    "message_id": 1,
                    "text": "/start",
                    "chat": {"id": 100, "type": "private"},
                    "from": {"id": 777, "username": "ivan_petrov", "first_name": "Иван", "last_name": "Петров"},
                }
            }
        )
    )

    db.refresh(employee)
    assert result["status"] == "connected"
    assert employee.telegram_user_id == 777
    assert employee.telegram_connected is True


def test_unregistered_chat_is_ignored_before_message_analysis():
    db = make_db()
    result = asyncio.run(
        TaskDecisionEngine(db).process_update(
            {
                "message": {
                    "message_id": 1,
                    "text": "Иван, подготовь демо до завтра",
                    "chat": {"id": -1001, "type": "supergroup", "title": "Work"},
                    "from": {"id": 777, "username": "manager"},
                }
            }
        )
    )

    assert result == {"status": "ignored", "reason": "unregistered_chat"}


def test_accepting_candidate_creates_open_task_in_same_organization():
    db = make_db()
    org = Organization(name="Komandus")
    db.add(org)
    db.flush()
    manager = Employee(
        organization_id=org.id,
        full_name="Мария Manager",
        email="manager@example.com",
        role="MANAGER",
        telegram_username="manager",
        telegram_user_id=500,
        telegram_connected=True,
    )
    assignee = Employee(
        organization_id=org.id,
        full_name="Иван Петров",
        email="ivan@example.com",
        role="EMPLOYEE",
        telegram_username="ivan_petrov",
        telegram_user_id=777,
        telegram_connected=True,
    )
    db.add_all([manager, assignee])
    db.flush()
    db.add(TelegramSource(organization_id=org.id, chat_id=-1001, chat_title="Work", is_active=True))
    db.commit()

    engine = TaskDecisionEngine(db)
    asyncio.run(
        engine.process_update(
            {
                "message": {
                    "message_id": 10,
                    "text": "Иван, подготовь демо до завтра",
                    "chat": {"id": -1001, "type": "supergroup", "title": "Work"},
                    "from": {"id": 500, "username": "manager", "first_name": "Мария"},
                }
            }
        )
    )
    # The fallback extractor is conservative and assigns 55% confidence, so the
    # candidate goes to the manager but can still be accepted through callback.
    from app.models.models import TaskCandidate

    candidate = db.query(TaskCandidate).first()
    assert candidate.organization_id == org.id
    assert candidate.status == "PENDING"

    result = asyncio.run(
        engine.process_update(
            {
                "callback_query": {
                    "id": "cb1",
                    "data": f"candidate_accept_{candidate.id}",
                    "from": {"id": 777},
                    "message": {"message_id": 11, "chat": {"id": 777, "type": "private"}},
                }
            }
        )
    )

    task = db.query(Task).first()
    assert result["status"] == "accepted"
    assert task.organization_id == org.id
    assert task.status == "OPEN"
    assert task.assignee_employee_id == assignee.id
