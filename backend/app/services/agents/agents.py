from __future__ import annotations

from .llm import LLMClient
from .prompts import AGENT_PROMPTS, SYSTEM_PROMPT


class BaseAgent:
    """Base implementation shared by all BiSense domain agents."""

    def __init__(self, intent: str, llm: LLMClient | None = None) -> None:
        self.intent = intent
        self.llm = llm or LLMClient()

    def answer(
        self,
        message: str,
        context: str = "",
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate an answer using retrieval context and conversation history."""

        prompt = SYSTEM_PROMPT + "\n\n" + AGENT_PROMPTS[self.intent]

        if history:
            history_text = "\n".join(
                f"{item.get('role', 'user')}: {item.get('content', '')}"
                for item in history
                if item.get("content")
            )

            if history_text:
                prompt += (
                    "\n\nRecent conversation history:\n"
                    + history_text
                )

        if context:
            prompt += (
                "\n\nRetrieved information from the knowledge system:\n"
                + context
            )

        return self.llm.generate(
            system_prompt=prompt,
            user_message=message,
        )


class StandardsAgent(BaseAgent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("standards", llm)


class CertificationAgent(BaseAgent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("certification", llm)


class QCOAgent(BaseAgent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("qco", llm)


class LabAgent(BaseAgent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("lab", llm)


class HallmarkingAgent(BaseAgent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("hallmarking", llm)


class ConsumerAgent(BaseAgent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("consumer", llm)


class GeneralAgent(BaseAgent):
    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("general", llm)


AGENT_CLASSES = {
    "standards": StandardsAgent,
    "certification": CertificationAgent,
    "qco": QCOAgent,
    "lab": LabAgent,
    "hallmarking": HallmarkingAgent,
    "consumer": ConsumerAgent,
    "general": GeneralAgent,
}


def get_agent(intent: str, llm: LLMClient | None = None) -> BaseAgent:
    """Return the agent responsible for the requested intent."""

    agent_class = AGENT_CLASSES.get(intent, GeneralAgent)
    return agent_class(llm)