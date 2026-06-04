from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Task, TaskStatusHistory

logger = logging.getLogger(__name__)


@dataclass
class KanbanCardRef:
    provider: str
    external_id: str | None = None
    external_url: str | None = None


class InternalKanbanAdapter:
    def __init__(self, db: Session):
        self.db = db

    def create_card(self, task: Task) -> KanbanCardRef:
        task.kanban_provider = "internal"
        self.db.commit()
        self.db.refresh(task)
        return KanbanCardRef(provider="internal")

    def update_card_status(self, task: Task, status: str, source: str = "sync") -> KanbanCardRef:
        old_status = task.status
        task.status = status
        task.status_changed_count = (task.status_changed_count or 0) + (0 if old_status == status else 1)
        self.db.add(TaskStatusHistory(task_id=task.id, old_status=old_status, new_status=status, source=source))
        self.db.commit()
        self.db.refresh(task)
        return KanbanCardRef(provider="internal", external_id=task.external_kanban_id, external_url=task.external_kanban_url)


class YouGileAdapter:
    def create_card(self, task: Task) -> KanbanCardRef:
        if not settings.YOUGILE_API_KEY or not settings.YOUGILE_COLUMN_ID:
            raise RuntimeError("YouGile credentials are not configured")
        payload = {
            "title": task.title,
            "columnId": settings.YOUGILE_COLUMN_ID,
            "description": task.description or "",
        }
        headers = {"Authorization": f"Bearer {settings.YOUGILE_API_KEY}"}
        with httpx.Client(timeout=5.0) as client:
            response = client.post(f"{settings.YOUGILE_API_URL.rstrip('/')}/tasks", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        card_id = str(data.get("id") or data.get("taskId") or "")
        return KanbanCardRef(provider="external", external_id=card_id or None, external_url=data.get("url"))


class TrelloAdapter:
    def create_card(self, task: Task) -> KanbanCardRef:
        if not settings.TRELLO_API_KEY or not settings.TRELLO_TOKEN or not settings.TRELLO_LIST_ID:
            raise RuntimeError("Trello credentials are not configured")
        params = {"key": settings.TRELLO_API_KEY, "token": settings.TRELLO_TOKEN, "idList": settings.TRELLO_LIST_ID}
        payload = {"name": task.title, "desc": task.description or ""}
        with httpx.Client(timeout=5.0) as client:
            response = client.post(f"{settings.TRELLO_API_URL.rstrip('/')}/cards", params=params, data=payload)
            response.raise_for_status()
            data = response.json()
        return KanbanCardRef(provider="external", external_id=data.get("id"), external_url=data.get("url"))


class ResilientKanbanAdapter:
    def __init__(self, db: Session):
        self.db = db
        self.internal = InternalKanbanAdapter(db)

    def create_card(self, task: Task) -> KanbanCardRef:
        provider = settings.KANBAN_PROVIDER.lower().strip()
        if provider in {"yougile", "external"}:
            external = YouGileAdapter()
        elif provider == "trello":
            external = TrelloAdapter()
        else:
            return self.internal.create_card(task)

        try:
            ref = external.create_card(task)
            task.kanban_provider = ref.provider
            task.external_kanban_id = ref.external_id
            task.external_kanban_url = ref.external_url
            self.db.commit()
            self.db.refresh(task)
            return ref
        except Exception as exc:
            logger.warning("External Kanban failed; falling back to internal board: %s", exc)
            return self.internal.create_card(task)

    def update_card_status(self, task: Task, status: str, source: str = "sync") -> KanbanCardRef:
        # Status updates are persisted locally first so demos remain live even when a provider is unavailable.
        return self.internal.update_card_status(task, status, source=source)


KanbanAdapter = ResilientKanbanAdapter
