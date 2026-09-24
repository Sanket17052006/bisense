import os
import uuid
from unittest import mock

from app.api.routes.chat import _coerce_sources
from app.schemas.schemas import SourceOut
from app.services.agents.agents import get_agent
from app.services.agents.llm import LLMClient
from app.services.agents.pipeline import AgentPipeline
from app.services.agents.prompts import SYSTEM_PROMPT
from app.services.agents.rag import RAGService
from app.services.agents.router import IntentRouter


def _email(tag):
    return f"{tag}-{uuid.uuid4().hex[:8]}@example.com"


class MockLLM:
    """Fake LLM used for local tests without API credits."""

    def generate(self, system_prompt: str, user_message: str) -> str:
        if "Classify the user's message" in system_prompt:
            return "standards"

        return "This is a mock BiSense response for local testing."


class RaisingLLM:
    """Fake LLM that simulates an API outage."""

    def generate(self, system_prompt: str, user_message: str) -> str:
        raise RuntimeError("LLM API is down")


class RecordingLLM:
    """Fake LLM that records prompts for pipeline behavior tests."""

    def __init__(self):
        self.calls = []

    def generate(self, system_prompt: str, user_message: str) -> str:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
            }
        )

        if "Classify the user's message" in system_prompt:
            return "standards"

        return "Recorded mock BiSense response."


class InvalidIntentLLM:
    """Fake LLM that returns an unsupported intent."""

    def generate(self, system_prompt: str, user_message: str) -> str:
        if "Classify the user's message" in system_prompt:
            return "unsupported_intent"

        return "Fallback response."


class RaisingRAG(RAGService):
    """Fake retrieval layer that simulates a retrieval failure."""

    def retrieve(
        self,
        query: str,
        intent: str | None = None,
        limit: int = 5,
    ):
        raise RuntimeError("RAG service is unavailable")


class FakeRAG(RAGService):
    """Fake retrieval layer returning mixed-quality results."""

    def retrieve(
        self,
        query: str,
        intent: str | None = None,
        limit: int = 5,
    ):
        return [
            {
                "id": "s1",
                "title": "IS 1234",
                "content": "Full text about IS 1234.",
            },
            {
                "id": "s2",
                "title": "IS 5678",
                "is_number": "5678",
            },
            {
                "id": "s3",
                "content": "Missing a title and id.",
            },
        ]


def test_intent_router():
    llm = MockLLM()
    router = IntentRouter(llm)

    intent, confidence = router.classify(
        "What is a BIS standard?"
    )

    assert intent == "standards"
    assert confidence > 0


def test_agent_selection():
    llm = MockLLM()

    agent = get_agent("standards", llm)

    assert agent.intent == "standards"


def test_full_agent_pipeline():
    llm = MockLLM()
    pipeline = AgentPipeline(llm=llm)

    state = pipeline.run("What is a BIS standard?")

    assert state.intent == "standards"
    assert state.agent == "standards"
    assert state.answer
    assert state.unsupported is False


def test_pipeline_graceful_fallback_on_llm_failure():
    pipeline = AgentPipeline(llm=RaisingLLM())
    state = pipeline.run("What is a BIS standard?")

    assert state.unsupported is True
    assert state.answer
    assert state.disclaimer
    assert "intent_error" in state.metadata


def test_sources_coerced_to_response_model():
    pipeline = AgentPipeline(
        llm=MockLLM(),
        rag=FakeRAG(),
    )
    state = pipeline.run("What is IS 1234?")

    outputs = _coerce_sources(state.sources)

    assert all(isinstance(item, SourceOut) for item in outputs)
    assert [item.id for item in outputs] == ["s1", "s2"]
    assert outputs[0].title == "IS 1234"


def test_coerce_sources_drops_invalid_entries():
    outputs = _coerce_sources(
        [
            "not-a-dict",
            {"title": "no id"},
        ]
    )

    assert outputs == []


def test_llm_client_constructs_without_key_but_raises_on_generate():
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OPENAI_API_KEY", None)

        llm = LLMClient()
        assert llm.api_key is None

        try:
            llm.generate("system", "hi")
        except RuntimeError as exc:
            assert "OPENAI_API_KEY" in str(exc)
        else:
            raise AssertionError(
                "expected RuntimeError for missing API key"
            )


def test_llm_sanitizes_control_characters():
    assert LLMClient._sanitize("a\x7fb\tc\nd") == "ab\tc\nd"
    assert LLMClient._sanitize("\x0bsolar\x0c") == "solar"


def test_llm_chain_renders_openai_compatible_messages():
    """The LangChain chain must produce a message list, not a ChatPromptValue.

    Regression test: the previous chain passed a ChatPromptValue straight
    through, so _call_model crashed on every real LLM request
    ('tuple' object has no attribute 'type').
    """
    llm = LLMClient()
    messages = llm._chain.invoke(
        {
            "system_prompt": "You are a bot.",
            "user_message": "Hello",
        }
    )
    roles = [getattr(message, "type", None) for message in messages]
    assert roles == ["system", "human"]
    assert isinstance(list(messages)[0].content, str)


def test_pipeline_rule_based_fallback_without_llm_key():
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OPENAI_API_KEY", None)

        pipeline = AgentPipeline()
        state = pipeline.run("What is a BIS standard?")

        assert state.answer
        assert state.unsupported is False
        assert state.metadata.get("mode") == "rule-based"


def test_chat_route_rejects_other_users_conversation():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        # Create User A
        owner_email = _email("conversation-owner")
        owner_register = client.post(
            "/api/auth/register",
            json={
                "name": "Conversation Owner",
                "email": owner_email,
                "password": "S3cure!pass",
            },
        )

        assert owner_register.status_code == 201, owner_register.text
        owner_token = owner_register.json()["access_token"]

        # Create User A's conversation
        owner_response = client.post(
            "/api/chat",
            headers={
                "Authorization": f"Bearer {owner_token}"
            },
            json={
                "message": "Create my conversation"
            },
        )

        assert owner_response.status_code == 200, owner_response.text

        conversation_id = owner_response.json()["conversation_id"]

        # Create User B
        other_email = _email("conversation-other")
        other_register = client.post(
            "/api/auth/register",
            json={
                "name": "Other User",
                "email": other_email,
                "password": "S3cure!pass",
            },
        )

        assert other_register.status_code == 201, other_register.text
        other_token = other_register.json()["access_token"]

        # User B tries to access User A's conversation
        response = client.post(
            "/api/chat",
            headers={
                "Authorization": f"Bearer {other_token}"
            },
            json={
                "message": (
                    "Try to access another user's conversation"
                ),
                "conversation_id": conversation_id,
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Conversation not found"


def test_pipeline_passes_conversation_history_to_agent():
    llm = RecordingLLM()
    pipeline = AgentPipeline(llm=llm)

    history = [
        {
            "role": "user",
            "content": "What is BIS?",
        },
        {
            "role": "assistant",
            "content": "BIS is the Bureau of Indian Standards.",
        },
    ]

    state = pipeline.run(
        "Tell me more about it.",
        history=history,
    )

    assert state.answer
    assert len(llm.calls) == 2

    answer_call = llm.calls[1]

    assert "Recent conversation history:" in (
        answer_call["system_prompt"]
    )
    assert "What is BIS?" in answer_call["system_prompt"]
    assert (
        "BIS is the Bureau of Indian Standards."
        in answer_call["system_prompt"]
    )
    assert answer_call["user_message"] == "Tell me more about it."


def test_pipeline_preserves_rag_failure_metadata():
    pipeline = AgentPipeline(
        llm=MockLLM(),
        rag=RaisingRAG(),
    )

    state = pipeline.run(
        "What is a BIS standard?"
    )

    assert state.answer
    assert state.unsupported is True
    assert "rag_error" in state.metadata
    assert state.sources == []


def test_invalid_router_intent_falls_back_to_general():
    router = IntentRouter(InvalidIntentLLM())

    intent, confidence = router.classify(
        "This is an unrelated question."
    )

    assert intent == "general"
    assert confidence == 0.6


def test_multilingual_response_rules_are_present():
    assert (
        "Reply in the same language used by the user"
        in SYSTEM_PROMPT
    )
    assert (
        "If the user explicitly asks for a different language"
        in SYSTEM_PROMPT
    )
    assert "English, Hindi, Hinglish" in SYSTEM_PROMPT


def test_all_supported_intents_have_agents():
    supported_intents = {
        "standards",
        "certification",
        "qco",
        "lab",
        "hallmarking",
        "consumer",
        "general",
    }

    for intent in supported_intents:
        agent = get_agent(
            intent,
            MockLLM(),
        )

        assert agent.intent == intent


def test_rag_context_is_passed_to_agent():
    llm = RecordingLLM()
    pipeline = AgentPipeline(
        llm=llm,
        rag=FakeRAG(),
    )

    state = pipeline.run(
        "What is IS 1234?"
    )

    assert state.answer

    answer_call = llm.calls[1]

    assert (
        "Retrieved information from the knowledge system:"
        in answer_call["system_prompt"]
    )
    assert "IS 1234" in answer_call["system_prompt"]
    assert "Full text about IS 1234." in (
        answer_call["system_prompt"]
    )