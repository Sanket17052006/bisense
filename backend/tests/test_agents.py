from app.services.agents.agents import get_agent
from app.services.agents.pipeline import AgentPipeline
from app.services.agents.router import IntentRouter


class MockLLM:
    """Fake LLM used for local tests without API credits."""

    def generate(self, system_prompt: str, user_message: str) -> str:
        if "Classify the user's message" in system_prompt:
            return "standards"

        return "This is a mock BiSense response for local testing."


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