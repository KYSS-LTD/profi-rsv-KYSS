from dataclasses import dataclass

from llm_engine.schemas import ActionRecommendation, DedupRelation, GraphState


@dataclass
class ActionDecisionNode:
    """Нода 7. Рекомендация действия по порогам."""

    auto: float = 0.85
    confirm_floor: float = 0.55

    async def __call__(self, state: GraphState) -> dict:
        for t in state.tasks:
            if t.dedup_relation != DedupRelation.none:
                # duplicate -> прикрепить к существующей; update -> применить детали (P1)
                t.action = ActionRecommendation.update_existing
            elif t.confidence >= self.auto:
                t.action = ActionRecommendation.auto_create
            elif t.confidence >= self.confirm_floor:
                t.action = ActionRecommendation.confirm
            else:
                t.action = ActionRecommendation.skip
            t.needs_confirmation = t.action in (
                ActionRecommendation.confirm,
                ActionRecommendation.update_existing,
            )
        return {"tasks": state.tasks}
