from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Legacy health", description="Legacy health endpoint for frontend compatibility.")
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "environment": settings.APP_ENV}


@router.get("/health/live", summary="Liveness probe", description="Return process liveness without checking dependencies.")
async def live():
    return {"status": "live", "service": settings.APP_NAME}


@router.get("/health/ready", summary="Readiness probe", description="Check PostgreSQL connectivity and report integration configuration readiness for Redis, Celery, Telegram, and YouGile.")
async def ready():
    checks = {"postgres": False, "redis": bool(settings.REDIS_URL), "celery": bool(settings.CELERY_BROKER_URL), "telegram": bool(settings.BOT_TOKEN), "yougile": bool(settings.YOUGILE_API_BASE_URL)}
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["postgres"] = True
    finally:
        db.close()
    status = "ready" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
