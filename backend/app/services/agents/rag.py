from __future__ import annotations

from typing import Any


class RAGService:
    """
    Interface for the retrieval layer owned by Member 3.

    Member 2 does not implement document retrieval here.
    This class provides a clean seam for the agent pipeline.
    """

    def retrieve(
        self,
        query: str,
        intent: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant knowledge for the user's query.

        The Member 3 RAG implementation can replace or extend this method.
        Until then, return an empty result rather than inventing sources.
        """
        return []

    @staticmethod
    def format_context(sources: list[dict[str, Any]]) -> str:
        """Convert retrieved sources into context for an AI agent."""
        if not sources:
            return ""

        sections: list[str] = []

        for source in sources:
            title = source.get("title", "Untitled source")
            content = source.get("content", "")

            if content:
                sections.append(f"Source: {title}\n{content}")

        return "\n\n".join(sections)