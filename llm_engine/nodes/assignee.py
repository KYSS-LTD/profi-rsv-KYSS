from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, create_model

from llm_engine.prompt_manager import PromptManager
from llm_engine.provider import LLMProvider
from llm_engine.schemas import GraphState


@lru_cache(maxsize=8)
def _build_resolutions_model(member_ids: tuple[str, ...]) -> type[BaseModel]:
    """Динамически собирает модель ответа с assignee_id, ограниченным ростером + 'unknown'.

    Strict structured output не даст LLM вернуть id вне этого набора.
    """
    assignee_id_type = Literal[member_ids + ("unknown",)]
    item = create_model(
        "AssigneeResolutionItem",
        task_index=(int, ...),
        assignee_id=(assignee_id_type, ...),
        confidence=(float, ...),
    )
    return create_model("AssigneeResolutions", items=(list[item], ...))


@dataclass
class AssigneeResolverNode:
    """Нода 4. LLM с выходом, ограниченным Literal[ростер]. Промахнуться в несуществующего нельзя."""

    provider: LLMProvider
    prompts: PromptManager

    async def __call__(self, state: GraphState) -> dict:
        members = state.context.team_members
        pending = [(i, t) for i, t in enumerate(state.tasks) if t.assignee_raw]
        if not pending or not members:
            return {"tasks": state.tasks}

        model = _build_resolutions_model(tuple(m.id for m in members))
        prompt = self.prompts.render(
            "assignee_resolve",
            members=members,
            items=[{"index": i, "assignee_raw": t.assignee_raw} for i, t in pending],
        )
        res = await self.provider.structured(prompt, model)

        by_index = {r.task_index: r for r in res.items}
        for i, t in pending:
            r = by_index.get(i)
            if r and r.assignee_id != "unknown":
                t.assignee_id = r.assignee_id
                t.assignee_confidence = round(r.confidence, 3)
        return {"tasks": state.tasks}
