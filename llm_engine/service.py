import os
from datetime import datetime
from zoneinfo import ZoneInfo

from llm_engine.graph import TaskExtractionPipeline
from llm_engine.prompt_manager import PromptManager
from llm_engine.provider import LLMProvider
from llm_engine.roster import default_team
from llm_engine.schemas import ExtractionContext, GraphState, TaskExtractionResult


class LLMPipelineService:

    def __init__(self, model: str | None = None, mode: str | None = None):
        mode = mode or os.getenv("LLM_PROVIDER", "api")
        model = model or os.getenv("LLM_MODEL", "deepseek/deepseek-v4-flash")
        self.provider = LLMProvider(mode=mode, model=model)
        self.prompts = PromptManager()
        self.pipeline = TaskExtractionPipeline(self.provider, self.prompts)

    async def extract_tasks(self, text: str, context: dict | ExtractionContext | None = None) -> dict:
        ctx = self._build_context(context)
        state = GraphState(text=text, context=ctx)
        out = await self.pipeline.compiled.ainvoke(state)

        # ainvoke может вернуть dict или сам объект состояния — поддержим оба
        get = out.get if isinstance(out, dict) else lambda k, d=None: getattr(out, k, d)
        intent = get("intent")
        tasks = get("tasks", []) or []
        result = TaskExtractionResult(
            has_task=bool(tasks),
            source_type=ctx.source_type,
            tasks=tasks,
            raw_reasoning_summary=(intent.message_type.value if intent else None),
        )
        return result.model_dump(mode="json")

    @staticmethod
    def _build_context(context) -> ExtractionContext:
        if isinstance(context, ExtractionContext):
            return context
        data = dict(context or {})
        tz = data.get("timezone", "Europe/Moscow")
        if not data.get("now"):
            data["now"] = datetime.now(ZoneInfo(tz))
        if not data.get("team_members"):
            data["team_members"] = default_team()  # ЗАГЛУШКА: пока backend не передаёт реальных
        return ExtractionContext(**data)
