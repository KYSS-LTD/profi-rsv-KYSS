from langgraph.graph import END, StateGraph

from llm_engine.nodes import (
    ActionDecisionNode,
    AssigneeResolverNode,
    ConfidenceNode,
    DeadlineNormalizerNode,
    DeduplicationNode,
    IntentClassifierNode,
    TaskExtractorNode,
)
from llm_engine.prompt_manager import PromptManager
from llm_engine.provider import LLMProvider
from llm_engine.schemas import GraphState


class TaskExtractionPipeline:
    """LangGraph: intent -> (extract -> deadline -> assignee -> dedup -> confidence -> action) -> END."""

    def __init__(self, provider: LLMProvider, prompts: PromptManager):
        self.provider = provider
        self.prompts = prompts
        self._compiled = None

    def build(self):
        g = StateGraph(GraphState)
        g.add_node("intent", IntentClassifierNode(self.provider, self.prompts))
        g.add_node("extract", TaskExtractorNode(self.provider, self.prompts))
        g.add_node("deadline", DeadlineNormalizerNode())
        g.add_node("assignee", AssigneeResolverNode(self.provider, self.prompts))
        g.add_node("dedup", DeduplicationNode(self.provider, self.prompts))
        g.add_node("confidence", ConfidenceNode())
        g.add_node("action", ActionDecisionNode())

        g.set_entry_point("intent")
        g.add_conditional_edges("intent", self._after_intent, {"extract": "extract", "end": END})
        g.add_edge("extract", "deadline")
        g.add_edge("deadline", "assignee")
        g.add_edge("assignee", "dedup")
        g.add_edge("dedup", "confidence")
        g.add_edge("confidence", "action")
        g.add_edge("action", END)

        self._compiled = g.compile()
        return self._compiled

    @staticmethod
    def _after_intent(state: GraphState) -> str:
        return "extract" if state.intent and state.intent.has_action_item else "end"

    @property
    def compiled(self):
        if self._compiled is None:
            self.build()
        return self._compiled
