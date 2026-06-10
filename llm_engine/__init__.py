"""LLM Pipeline для «Командус» — AI reasoning layer (text -> структура задач).

LLMPipelineService импортируется лениво, чтобы лёгкие модули (schemas, roster)
можно было использовать без установленных openai / langgraph.
"""

__all__ = ["LLMPipelineService"]


def __getattr__(name):
    if name == "LLMPipelineService":
        from llm_engine.service import LLMPipelineService

        return LLMPipelineService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
