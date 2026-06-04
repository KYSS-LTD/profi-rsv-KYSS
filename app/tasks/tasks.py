import asyncio

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.task_decision_engine import TaskDecisionEngine


@celery_app.task(name="app.tasks.process_text_message_task")
def process_text_message_task(message_id: int):
    db = SessionLocal()
    try:
        engine = TaskDecisionEngine(db)
        return asyncio.run(engine.process_text_message(message_id, source="telegram_text"))
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_voice_message_task")
def process_voice_message_task(message_id: int):
    db = SessionLocal()
    try:
        # Speech-to-text workers store the transcript on Message.text before reusing the same decision flow.
        engine = TaskDecisionEngine(db)
        return asyncio.run(engine.process_text_message(message_id, source="telegram_voice"))
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_callback_query_task")
def process_callback_query_task(payload: dict):
    db = SessionLocal()
    try:
        engine = TaskDecisionEngine(db)
        return asyncio.run(engine.process_update(payload))
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_telegram_message")
def process_telegram_message(payload: dict):
    db = SessionLocal()
    try:
        engine = TaskDecisionEngine(db)
        return asyncio.run(engine.process_update(payload))
    finally:
        db.close()
