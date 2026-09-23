from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """State passed between the AI agent pipeline stages."""

    message: str

    intent: str = "general"
    agent: str | None = None
    confidence: float = 0.0

    answer: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)

    unsupported: bool = False
    disclaimer: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)