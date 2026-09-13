from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    """
    What a detector concluded about a piece of content.

    FLAG means suspicious but not conclusive.  Content proceeds, signal is recorded.
    """

    ALLOW = "allow"
    BLOCK = "block"
    FLAG = "flag"


class GuardResult(BaseModel):
    """
    A single detector's findings, carrying its own provenance.

    'score' is None when a detector as no confidence measures - not 0.0.
    """

    verdict: Verdict
    detector: str
    reason: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """
    A request to invoke a tool.

    'id' is initialized here, not taken from the provider, so replayed and live
    calls share on schema.  'arguments' is validated by the registry.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    arguments: dict[str, Any]
    called_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolResult(BaseModel):
    """
    Outcome of a single tool invocation, paired to its ToolCall by id.

    Always carries `content` — on failure, a description the agent can
    feed back to the model. Callers branch on `ok`, not on `error`.
    """

    call_id: str
    ok: bool
    content: str
    error: str | None = None
    duration_ms: float | None = None


class Message(BaseModel):
    """
    A single turn in a conversation.

    Provider-neutral - adapters in 'llm/' translate to and from venfor formats
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None
