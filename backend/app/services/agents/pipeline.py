from __future__ import annotations

from .graph import compile_agent_graph
from .llm import LLMClient
from .rag import RAGService
from .state import AgentState


class AgentPipeline:
    """Runs the BiSense AI workflow using LangGraph."""

    def __init__(
        self,
        llm: LLMClient | None = None,
        rag: RAGService | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.rag = rag or RAGService()
        self.graph = compile_agent_graph(
            self.llm,
            self.rag,
        )

    def run(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> AgentState:
        """Run the LangGraph workflow and convert its result to AgentState."""

        initial_state = {
            "message": message,
            "history": history or [],
        }

        try:
            result = self.graph.invoke(initial_state)
        except Exception as exc:
            return AgentState(
                message=message,
                intent="general",
                agent="general",
                confidence=0.0,
                answer=(
                    "I’m unable to process your request right now. "
                    "Please try again later."
                ),
                sources=[],
                unsupported=True,
                disclaimer=(
                    "The AI service could not process this request. "
                    "Please try again later."
                ),
                metadata={"graph_error": str(exc)},
            )

        intent = result.get("intent", "general")

        return AgentState(
            message=message,
            intent=intent,
            agent=intent,
            confidence=result.get("confidence", 0.0),
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            unsupported=result.get("unsupported", False),
            disclaimer=result.get("disclaimer"),
            metadata={
                **result.get("metadata", {}),
                "history": history or [],
            },
        )