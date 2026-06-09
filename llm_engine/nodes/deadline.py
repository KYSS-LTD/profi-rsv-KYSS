from dataclasses import dataclass

from llm_engine.schemas import GraphState


@dataclass
class DeadlineNormalizerNode:
    """Нода 3. Тонкая страховка: дату в прошлом не доверяем."""

    async def __call__(self, state: GraphState) -> dict:
        for t in state.tasks:
            if t.deadline and t.deadline < state.context.now:
                t.deadline = None
        return {"tasks": state.tasks}
