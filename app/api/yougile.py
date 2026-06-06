from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db
from app.models.models import Organization, Task
from app.services.yougile_service import YouGileService

router = APIRouter(prefix="/yougile", tags=["YouGile"])


@router.get("/health")
async def yougile_health():
    result = await YouGileService().check_token()
    return {"enabled": YouGileService().enabled, "token_works": result.synced, "error": result.error}


@router.post("/webhook")
async def yougile_webhook(payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    external_id = str(data.get("taskId") or data.get("id") or data.get("task_id") or "")
    if not external_id:
        return {"status": "ignored", "reason": "missing_task_id"}

    task = db.query(Task).filter(Task.yougile_task_id == external_id).first()
    if task is None:
        return {"status": "ignored", "reason": "task_not_found"}

    status = data.get("status") or _status_by_column(data.get("columnId") or data.get("column_id"), task.organization_id, db)
    if not status:
        return {"status": "ignored", "reason": "missing_status"}

    task.status = str(status).upper()
    db.commit()
    db.refresh(task)
    return {"status": "updated", "task_id": f"db_{task.id}", "new_status": task.status}


def _status_by_column(column_id: str | None, organization_id: int | None, db: Session) -> str | None:
    if not column_id:
        return None
    organization = db.query(Organization).filter(Organization.id == organization_id).first() if organization_id else None
    mapping = {
        (organization.yougile_default_column_id if organization else None) or settings.YOUGILE_DEFAULT_COLUMN_ID: "OPEN",
        (organization.yougile_in_progress_column_id if organization else None) or settings.YOUGILE_IN_PROGRESS_COLUMN_ID: "IN_PROGRESS",
        (organization.yougile_done_column_id if organization else None) or settings.YOUGILE_DONE_COLUMN_ID: "DONE",
        (organization.yougile_cancelled_column_id if organization else None) or settings.YOUGILE_CANCELLED_COLUMN_ID: "CANCELLED",
    }
    return mapping.get(column_id)
