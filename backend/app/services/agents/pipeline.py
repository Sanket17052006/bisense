from __future__ import annotations

from .agents import get_agent
from .llm import LLMClient
from .rag import RAGService
from .router import IntentRouter
from .state import AgentState


class AgentPipeline:
    """Runs the complete BiSense AI agent pipeline."""

    def __init__(
        self,
        llm: LLMClient | None = None,
        rag: RAGService | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.rag = rag or RAGService()
        self.router = IntentRouter(self.llm)

    def run(self, message: str) -> AgentState:
        state = AgentState(message=message)

        # 1. Classify the user's intent.
        intent, confidence = self.router.classify(message)

        state.intent = intent
        state.agent = intent
        state.confidence = confidence

        # 2. Retrieve relevant information.
        sources = self.rag.retrieve(
            query=message,
            intent=intent,
            limit=5,
        )

        state.sources = sources

        # 3. Convert retrieved information into agent context.
        context = self.rag.format_context(sources)

        # 4. Select the specialized agent.
        agent = get_agent(intent, self.llm)

        # 5. Generate the answer.
        try:
            state.answer = agent.answer(
                message,
                context=context,
            )
        except Exception as exc:
            state.unsupported = True
            state.disclaimer = (
                "The AI service could not process this request. "
                "Please try again later."
            )
            state.metadata["error"] = str(exc)
            state.answer = (
                "I’m unable to process your request right now. "
                "Please try again later."
            )

        return state