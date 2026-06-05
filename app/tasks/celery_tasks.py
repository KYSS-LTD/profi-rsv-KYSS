from __future__ import annotations

from datetime import date

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.models import AnalyticsSnapshot
from app.analytics.services import AnalyticsService
from app.models.models import Organization


RETRY_KWARGS = {"autoretry_for": (Exception,), "retry_backoff": True, "retry_jitter": True, "max_retries": 5}


@celery_app.task(name="app.tasks.sync_task_to_yougile", **RETRY_KWARGS)
def sync_task_to_yougile(task_id: str):
    return {"queued": True, "task_id": task_id}


@celery_app.task(name="app.tasks.send_deadline_reminders", **RETRY_KWARGS)
def send_deadline_reminders():
    return {"queued": True}


@celery_app.task(name="app.tasks.send_morning_digest", **RETRY_KWARGS)
def send_morning_digest():
    return {"queued": True}


@celery_app.task(name="app.tasks.send_evening_report", **RETRY_KWARGS)
def send_evening_report():
    return {"queued": True}


@celery_app.task(name="app.tasks.create_analytics_snapshots", **RETRY_KWARGS)
def create_analytics_snapshots():
    db = SessionLocal()
    try:
        for org in db.query(Organization).filter(Organization.is_active.is_(True)).all():
            class UserCtx:
                organization_id = org.id
            payload = AnalyticsService(db).dashboard(UserCtx())
            db.add(AnalyticsSnapshot(organization_id=org.id, snapshot_date=date.today(), kind="dashboard", payload=payload))
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()
