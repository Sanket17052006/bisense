from __future__ import annotations

import os
import re
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from openai import OpenAI

from app.core.config import settings

load_dotenv()


class LLMNotConfigured(RuntimeError):
    """Raised when no LLM API key is configured.

    The agent graph treats this as the "offline mode" signal and falls back
    to the deterministic rule-based responder instead of a hard error.
    """


class LLMClient:
    """LLM adapter used by the BiSense agent pipeline.

    LangChain Core handles prompt construction and the runnable pipeline.
    The OpenAI SDK remains the low-level model transport so the existing
    LLMClient interface stays compatible with the rest of the application.
    """

    def __init__(self) -> None:
        self.api_key = settings.openai_api_key
        self.base_url = settings.llm_base_url or None
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout
        self.max_retries = settings.llm_max_retries
        self._client: OpenAI | None = None
        self._chain = self._build_chain()

    @property
    def client(self) -> OpenAI:
        """Create the OpenAI client lazily."""

        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )

        return self._client

    @staticmethod
    def _build_chain():
        """Build the reusable LangChain prompt and runnable chain."""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                ("human", "{user_message}"),
            ]
        )

        return prompt | RunnableLambda(
            lambda value: value.to_messages()
        )

    @staticmethod
    def _sanitize(content: str) -> str:
        """Strip control characters that break strict JSON/HTML clients.

        Language models occasionally emit DEL or other control bytes that
        FastAPI happily serialises raw (json.dumps(ensure_ascii=False)),
        producing JSON strict parsers reject. Only \t, \n and \r are kept.
        """
        return re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
            "",
            content,
        ).strip()

    def _call_model(self, messages: Any) -> str:
        """Send LangChain-rendered messages to the configured LLM."""

        if not self.api_key:
            raise LLMNotConfigured(
                "OPENAI_API_KEY is not configured."
            )

        openai_messages = []

        for message in messages:
            role = "user"

            if message.type == "system":
                role = "system"
            elif message.type == "human":
                role = "user"
            elif message.type == "ai":
                role = "assistant"

            openai_messages.append(
                {
                    "role": role,
                    "content": str(message.content),
                }
            )

        # Small models wired to tool-calling endpoints occasionally answer
        # with a tool call instead of text, which the plain SDK call rejects.
        # One retry absorbs that transient behavior.
        for attempt in range(2):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=0.2,
            )

            content = response.choices[0].message.content

            if content:
                return self._sanitize(content)

            if attempt == 0:
                continue

        raise RuntimeError(
            "LLM returned an empty response."
        )

    def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """Generate a response through the LangChain pipeline."""

        if not self.api_key:
            raise LLMNotConfigured(
                "OPENAI_API_KEY is not configured."
            )

        messages = self._chain.invoke(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
            }
        )

        return self._call_model(messages)