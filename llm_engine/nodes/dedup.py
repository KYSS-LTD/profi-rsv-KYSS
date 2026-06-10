from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, create_model

from llm_engine.prompt_manager import PromptManager
from llm_engine.provider import LLMProvider
from llm_engine.schemas import DedupRelation, GraphState


@lru_cache(maxsize=16)
def _build_dedup_model(existing_ids: tuple[str, ...]) -> type[BaseModel]:
    """Модель вердикта дедупа: existing_task_id ограничен задачами сотрудника + 'none'."""
    target = Literal[existing_ids + ("none",)]
    item = create_model(
        "DedupVerdict",
        task_index=(int, ...),
        relation=(DedupRelation, ...),
        existing_task_id=(target, ...),
        confidence=(float, ...),
    )
    return create_model("DedupVerdicts", items=(list[item], ...))


@dataclass
class DeduplicationNode:
    """Нода 5. LLM-дедуп по исполнителю: новая задача vs открытые задачи того же сотрудника."""

    provider: LLMProvider
    prompts: PromptManager

    async def __call__(self, state: GraphState) -> dict:
        # группируем новые задачи по исполнителю; без assignee_id дедуп пропускаем
        groups: dict[str, list] = {}
        for i, t in enumerate(state.tasks):
            if t.assignee_id:
                groups.setdefault(t.assignee_id, []).append((i, t))

        for assignee_id, items in groups.items():
            existing = [o for o in state.context.open_tasks if o.assignee_id == assignee_id]
            if not existing:
                continue

            model = _build_dedup_model(tuple(o.id for o in existing))
            prompt = self.prompts.render(
                "dedup",
                existing=existing,
                items=[{"index": i, "title": t.title, "deadline": t.deadline} for i, t in items],
            )
            res = await self.provider.structured(prompt, model)

            by_index = {v.task_index: v for v in res.items}
            for i, t in items:
                v = by_index.get(i)
                if v and v.relation != DedupRelation.none and v.existing_task_id != "none":
                    t.dedup_relation = v.relation
                    t.is_duplicate = v.relation == DedupRelation.duplicate
                    t.existing_task_id = v.existing_task_id
                    t.duplicate_confidence = round(v.confidence, 3)
        return {"tasks": state.tasks}
