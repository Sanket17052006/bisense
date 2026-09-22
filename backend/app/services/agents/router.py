from __future__ import annotations

from .llm import LLMClient
from .prompts import INTENT_ROUTER_PROMPT


VALID_INTENTS = {
    "standards",
    "certification",
    "qco",
    "lab",
    "hallmarking",
    "consumer",
    "general",
}


class IntentRouter:
    """Classifies a user message into one of the supported BiSense intents."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def classify(self, message: str) -> tuple[str, float]:
        result = self.llm.generate(
            system_prompt=INTENT_ROUTER_PROMPT,
            user_message=message,
        ).strip().lower()

        intent = result.split()[0] if result else "general"

        if intent not in VALID_INTENTS:
            intent = "general"

        # Confidence is intentionally conservative until a structured
        # classifier/RAG evaluation layer is added.
        confidence = 0.8 if intent != "general" else 0.6

        return intent, confidence