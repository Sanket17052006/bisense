from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .agents import get_agent
from .llm import LLMClient
from .rag import RAGService
from .router import IntentRouter


class GraphState(TypedDict, total=False):
    message: str
    history: list[dict[str, str]]

    intent: str
    confidence: float

    sources: list[dict]
    context: str

    answer: str
    unsupported: bool
    disclaimer: str | None
    metadata: dict


def classify_intent(
    state: GraphState,
    router: IntentRouter,
) -> GraphState:
    """Classify the user's message."""

    try:
        intent, confidence = router.classify(
            state["message"]
        )

        return {
            "intent": intent,
            "confidence": confidence,
        }

    except Exception as exc:
        return {
            "intent": "general",
            "confidence": 0.0,
            "unsupported": True,
            "metadata": {
                "intent_error": str(exc),
            },
        }


def retrieve_context(
    state: GraphState,
    rag: RAGService,
) -> GraphState:
    """Retrieve knowledge for the classified intent."""

    try:
        sources = rag.retrieve(
            query=state["message"],
            intent=state.get("intent"),
            limit=5,
        )

        return {
            "sources": sources,
            "context": rag.format_context(sources),
        }

    except Exception as exc:
        metadata = dict(state.get("metadata", {}))
        metadata["rag_error"] = str(exc)

        return {
            "sources": [],
            "context": "",
            "unsupported": True,
            "metadata": metadata,
        }


def generate_answer(
    state: GraphState,
    llm: LLMClient,
) -> GraphState:
    """Generate the final answer using the selected agent."""

    intent = state.get("intent", "general")
    agent = get_agent(intent, llm)

    try:
        answer = agent.answer(
            state["message"],
            context=state.get("context", ""),
            history=state.get("history", []),
        )

        return {
            "answer": answer,
        }

    except Exception as exc:
        metadata = dict(state.get("metadata", {}))
        metadata["error"] = str(exc)

        return {
            "answer": (
                "I’m unable to process your request right now. "
                "Please try again later."
            ),
            "unsupported": True,
            "disclaimer": (
                "The AI service could not process your request. "
                "Please try again later."
            ),
            "metadata": metadata,
        }


def build_agent_graph(
    llm: LLMClient,
    rag: RAGService,
) -> StateGraph:
    """Build the LangGraph workflow for the BiSense AI assistant."""

    router = IntentRouter(llm)

    graph = StateGraph(GraphState)

    graph.add_node(
        "classify_intent",
        lambda state: classify_intent(
            state,
            router,
        ),
    )

    graph.add_node(
        "retrieve_context",
        lambda state: retrieve_context(
            state,
            rag,
        ),
    )

    graph.add_node(
        "generate_answer",
        lambda state: generate_answer(
            state,
            llm,
        ),
    )

    graph.add_edge(
        START,
        "classify_intent",
    )

    graph.add_edge(
        "classify_intent",
        "retrieve_context",
    )

    graph.add_edge(
        "retrieve_context",
        "generate_answer",
    )

    graph.add_edge(
        "generate_answer",
        END,
    )

    return graph


def compile_agent_graph(
    llm: LLMClient,
    rag: RAGService,
):
    """Build and compile the BiSense LangGraph workflow."""

    return build_agent_graph(
        llm,
        rag,
    ).compile()