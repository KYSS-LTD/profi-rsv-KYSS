import asyncio
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.task_decision_engine import TaskDecisionEngine

@celery_app.task(name="app.tasks.process_telegram_message")
def process_telegram_message(payload: dict):
    db = SessionLocal()
    try:
        engine = TaskDecisionEngine(db)
        asyncio.run(engine.process_update(payload))
    finally:
        db.close()