import os
from unittest import mock

from app.api.routes.chat import _coerce_sources
from app.schemas.schemas import SourceOut
from app.services.agents.agents import get_agent
from app.services.agents.llm import LLMClient
from app.services.agents.pipeline import AgentPipeline
from app.services.agents.rag import RAGService
from app.services.agents.router import IntentRouter


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


class FakeRAG(RAGService):
    """Fake retrieval layer returning mixed-quality results."""

    def retrieve(self, query: str, intent: str | None = None, limit: int = 5):
        return [
            {"id": "s1", "title": "IS 1234", "content": "Full text about IS 1234."},
            {"id": "s2", "title": "IS 5678", "is_number": "5678"},
            {"id": "s3", "content": "Missing a title and id."},
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
    pipeline = AgentPipeline(llm=MockLLM(), rag=FakeRAG())
    state = pipeline.run("What is IS 1234?")

    outputs = _coerce_sources(state.sources)

    assert all(isinstance(item, SourceOut) for item in outputs)
    assert [item.id for item in outputs] == ["s1", "s2"]
    assert outputs[0].title == "IS 1234"


def test_coerce_sources_drops_invalid_entries():
    outputs = _coerce_sources(["not-a-dict", {"title": "no id"}])

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
            raise AssertionError("expected RuntimeError for missing API key")