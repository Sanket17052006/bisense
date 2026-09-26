from __future__ import annotations

from typing import Any

try:
    from app.rag.pipeline.retrieval_pipeline import retrieve as rag_retrieve
except ImportError:
    rag_retrieve = None


class RAGService:
    """
    RAG Service that wraps the complete RAG pipeline.
    """

    def __init__(self):
        self._retrieve_fn = rag_retrieve

    def retrieve(
        self,
        query: str,
        intent: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant knowledge for the user's query.
        """
        if self._retrieve_fn is None:
            return []

        try:
            # Don't filter by doc_type - let hybrid search handle relevance
            # The intent-based filtering was causing issues because intent names
            # don't match the actual doc_type values in the index.
            doc_type = None

            results = self._retrieve_fn(query, top_k=limit, doc_type=doc_type)
            return results
        except Exception as e:
            print(f"[RAGService] Retrieval error: {e}")
            return []

    @staticmethod
    def format_context(sources: list[dict[str, Any]]) -> str:
        """Convert retrieved sources into context for an AI agent."""
        if not sources:
            return ""

        sections: list[str] = []

        for source in sources:
            title = source.get("title") or source.get("source", "Untitled source")
            content = source.get("content") or source.get("text", "")

            if content:
                sections.append(f"Source: {title}\n{content}")

        return "\n\n".join(sections)