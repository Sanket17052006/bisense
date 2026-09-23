from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMClient:
    """Small wrapper around the OpenAI chat completion API."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL") or None
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("LLM returned an empty response.")

        return content.strip()