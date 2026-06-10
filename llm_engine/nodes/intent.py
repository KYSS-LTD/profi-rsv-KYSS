from dataclasses import dataclass

from llm_engine.prompt_manager import PromptManager
from llm_engine.provider import LLMProvider
from llm_engine.schemas import GraphState, IntentResult


@dataclass
class IntentClassifierNode:
    """Нода 1. LLM. Классифицирует намерение сообщения."""

    provider: LLMProvider
    prompts: PromptManager

    async def __call__(self, state: GraphState) -> dict:
        prompt = self.prompts.render(
            "intent_classify",
            text=state.text,
            sender=state.context.sender,
            chat_context=state.context.chat_context,
        )
        intent = await self.provider.structured(prompt, IntentResult)
        return {"intent": intent}
