from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "komandus",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_track_started=True,
    timezone="UTC",
    beat_schedule={
        "deadline-reminders-every-hour": {"task": "app.tasks.send_deadline_reminders", "schedule": 3600.0},
        "morning-digest-09utc": {"task": "app.tasks.send_morning_digest", "schedule": 86400.0},
        "evening-report-19utc": {"task": "app.tasks.send_evening_report", "schedule": 86400.0},
        "analytics-snapshots-nightly": {"task": "app.tasks.create_analytics_snapshots", "schedule": 86400.0},
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
