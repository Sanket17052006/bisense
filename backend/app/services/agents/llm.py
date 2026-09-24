from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from openai import OpenAI

load_dotenv()


class LLMClient:
    """LLM adapter used by the BiSense agent pipeline.

    LangChain Core handles prompt construction and the runnable pipeline.
    The OpenAI SDK remains the low-level model transport so the existing
    LLMClient interface stays compatible with the rest of the application.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL") or None
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._client: OpenAI | None = None
        self._chain = self._build_chain()

    @property
    def client(self) -> OpenAI:
        """Create the OpenAI client lazily."""

        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
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
            lambda messages: messages
        )

    def _call_model(self, messages: Any) -> str:
        """Send LangChain-rendered messages to the configured LLM."""

        if not self.api_key:
            raise RuntimeError(
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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=0.2,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "LLM returned an empty response."
            )

        return content.strip()

    def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """Generate a response through the LangChain pipeline."""

        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        messages = self._chain.invoke(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
            }
        )

        return self._call_model(messages)