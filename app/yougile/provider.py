from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import httpx

from app.core.config import settings


class BoardProvider(ABC):
    @abstractmethod
    async def create_task(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    @abstractmethod
    async def update_task(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    @abstractmethod
    async def move_task(self, task_id: str, column_id: str) -> dict[str, Any]: ...
    @abstractmethod
    async def delete_task(self, task_id: str) -> dict[str, Any]: ...
    @abstractmethod
    async def get_task(self, task_id: str) -> dict[str, Any]: ...
    @abstractmethod
    async def sync(self) -> dict[str, Any]: ...


class YouGileProvider(BoardProvider):
    def __init__(self, api_token: str, base_url: str | None = None):
        self.api_token = api_token
        self.base_url = (base_url or settings.YOUGILE_API_BASE_URL).rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(method, f"{self.base_url}{path}", headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}

    async def verify(self) -> dict[str, Any]:
        return await self._request("GET", "/auth/companies")

    async def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/tasks", json=payload)

    async def update_task(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("PUT", f"/tasks/{task_id}", json=payload)

    async def move_task(self, task_id: str, column_id: str) -> dict[str, Any]:
        return await self.update_task(task_id, {"columnId": column_id})

    async def delete_task(self, task_id: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/tasks/{task_id}")

    async def get_task(self, task_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/tasks/{task_id}")

    async def sync(self) -> dict[str, Any]:
        projects = await self._request("GET", "/projects")
        users = await self._request("GET", "/users")
        return {"projects": projects, "users": users}
