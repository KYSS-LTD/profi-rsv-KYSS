from dataclasses import dataclass

from llm_engine.schemas import GraphState


@dataclass
class ConfidenceNode:
    """Нода 6. Взвешенная итоговая уверенность."""

    async def __call__(self, state: GraphState) -> dict:
        intent_conf = state.intent.confidence if state.intent else 0.5
        src_quality = state.context.source_quality
        for t in state.tasks:
            deadline_conf = 1.0 if t.deadline else 0.6  # нет срока — нейтрально, не штраф
            t.confidence = round(
                intent_conf * 0.30
                + t.extraction_confidence * 0.30
                + t.assignee_confidence * 0.20
                + deadline_conf * 0.10
                + src_quality * 0.10,
                3,
            )
        return {"tasks": state.tasks}
