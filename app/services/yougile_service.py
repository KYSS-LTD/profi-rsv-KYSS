from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.models.models import Organization, Task

logger = logging.getLogger(__name__)

STATUS_TO_COLUMN_ATTR = {
    "OPEN": "yougile_default_column_id",
    "IN_PROGRESS": "yougile_in_progress_column_id",
    "DONE": "yougile_done_column_id",
    "CANCELLED": "yougile_cancelled_column_id",
}


@dataclass
class YouGileResult:
    synced: bool
    external_id: str | None = None
    url: str | None = None
    error: str | None = None


class YouGileService:
    def __init__(self):
        self.base_url = settings.YOUGILE_BASE_URL.rstrip("/")
        self.token = settings.YOUGILE_API_TOKEN

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    async def check_token(self) -> YouGileResult:
        if not self.enabled:
            return YouGileResult(False, error="YOUGILE_API_TOKEN is not configured")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/projects", headers=self._headers(), timeout=10.0)
            if response.is_success:
                return YouGileResult(True)
            return YouGileResult(False, error=f"YouGile returned {response.status_code}: {response.text[:300]}")
        except Exception as exc:
            logger.exception("YouGile token check failed")
            return YouGileResult(False, error=str(exc))

    async def create_task(self, task: Task, organization: Organization | None) -> YouGileResult:
        if not self.enabled:
            return YouGileResult(False, error="YOUGILE_API_TOKEN is not configured")
        project_id = (organization and organization.yougile_project_id) or settings.YOUGILE_PROJECT_ID
        column_id = self._column_id(organization, task.status)
        if not project_id or not column_id:
            return YouGileResult(False, error="YOUGILE_PROJECT_ID and YOUGILE_DEFAULT_COLUMN_ID are required")

        payload = {
            "title": task.title,
            "description": task.description or "",
            "projectId": project_id,
            "columnId": column_id,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/tasks", json=payload, headers=self._headers(), timeout=10.0)
            if not response.is_success:
                return YouGileResult(False, error=f"YouGile returned {response.status_code}: {response.text[:300]}")
            data = response.json() if response.content else {}
            external_id = str(data.get("id") or data.get("taskId") or "") or None
            return YouGileResult(True, external_id=external_id, url=self._task_url(external_id))
        except Exception as exc:
            logger.exception("YouGile task creation failed")
            return YouGileResult(False, error=str(exc))

    async def update_task_status(self, task: Task, organization: Organization | None) -> YouGileResult:
        if not self.enabled:
            return YouGileResult(False, error="YOUGILE_API_TOKEN is not configured")
        if not task.yougile_task_id:
            return YouGileResult(False, error="Task has no yougile_task_id")
        column_id = self._column_id(organization, task.status)
        if not column_id:
            return YouGileResult(False, error=f"No YouGile column configured for status {task.status}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/tasks/{task.yougile_task_id}",
                    json={"columnId": column_id},
                    headers=self._headers(),
                    timeout=10.0,
                )
            if response.is_success:
                return YouGileResult(True, external_id=task.yougile_task_id, url=task.yougile_url)
            return YouGileResult(False, error=f"YouGile returned {response.status_code}: {response.text[:300]}")
        except Exception as exc:
            logger.exception("YouGile status sync failed")
            return YouGileResult(False, error=str(exc))

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def _column_id(self, organization: Organization | None, status: str) -> str:
        attr = STATUS_TO_COLUMN_ATTR.get(status, "yougile_default_column_id")
        organization_value = getattr(organization, attr, None) if organization else None
        settings_name = {
            "yougile_default_column_id": "YOUGILE_DEFAULT_COLUMN_ID",
            "yougile_in_progress_column_id": "YOUGILE_IN_PROGRESS_COLUMN_ID",
            "yougile_done_column_id": "YOUGILE_DONE_COLUMN_ID",
            "yougile_cancelled_column_id": "YOUGILE_CANCELLED_COLUMN_ID",
        }[attr]
        return organization_value or getattr(settings, settings_name) or settings.YOUGILE_DEFAULT_COLUMN_ID

    def _task_url(self, external_id: str | None) -> str | None:
        if not external_id:
            return None
        return f"{self.base_url.removesuffix('/api-v2')}/task/{external_id}"
