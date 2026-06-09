from dataclasses import dataclass

from llm_engine.prompt_manager import PromptManager
from llm_engine.provider import LLMProvider
from llm_engine.schemas import ExtractedTask, ExtractedTaskList, GraphState

RU_WEEKDAYS = [
    "понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье",
]


@dataclass
class TaskExtractorNode:
    """Нода 2. LLM. Извлекает задачи и сразу пишет deadline в ISO."""

    provider: LLMProvider
    prompts: PromptManager

    async def __call__(self, state: GraphState) -> dict:
        now = state.context.now
        prompt = self.prompts.render(
            "task_extract",
            text=state.text,
            sender=state.context.sender,
            now_iso=now.isoformat(),
            weekday_ru=RU_WEEKDAYS[now.weekday()],
            chat_context=state.context.chat_context,
        )
        result = await self.provider.structured(prompt, ExtractedTaskList)
        tasks = [ExtractedTask(**t.model_dump()) for t in result.tasks]
        return {"tasks": tasks}
