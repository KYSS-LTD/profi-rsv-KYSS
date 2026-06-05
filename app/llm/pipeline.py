from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.llm_service import LLMService
from app.tasks.services import V2TaskService


class LLMTaskPipeline:
    extraction_version = "v2.0"

    def __init__(self, db: Session, llm: LLMService | None = None):
        self.db = db
        self.llm = llm or LLMService()

    async def process_message(self, *, organization_id, employee_id, chat_id: int, message_id: int, text: str):
        result = await self.llm.extract_tasks(text)
        created = []
        for item in result.get("tasks", []):
            created.append(V2TaskService(self.db).create_from_llm(
                organization_id=organization_id,
                employee_id=employee_id,
                title=item["title"],
                description=item.get("source_excerpt"),
                source_chat_id=chat_id,
                source_message_id=message_id,
                confidence=float(item.get("confidence") or 0),
                llm_model=result.get("model", "heuristic"),
                extraction_version=self.extraction_version,
            ))
        return created
