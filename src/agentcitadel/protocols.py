"""
Structural interfaces for pluggable components.

Core imports these: concrete implementations live behind optional extras.
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from agentcitadel.types import GuardResult, Message, ToolCall


@runtime_checkable
class Detector(Protocol):
    """
    Inspects content and returns a verdict.

    Implementations range from a regex scan to a transformer classifier.
    """

    name: str

    async def check(
        self, content: str, context: dict[str, str] | None = None
    ) -> GuardResult: ...


@runtime_checkable
class Approver(Protocol):
    """
    Decides whether a tool call the policy flagged as 'ask' may proceed.

    Implementations differ by deployment: a terminal prompt, a webook, or an unattended auto-deny.
    """

    async def request(self, call: ToolCall, reason: str) -> bool: ...


@runtime_checkable
class LLMProvider(Protocol):
    """
    Sends messages to a model and returns the reply.

    Adapters translate between 'Message' and each vendor's wire format.
    """

    model: str

    async def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[dict[str, object]] | None = None,
    ) -> Message: ...


@runtime_checkable
class VectorStore(Protocol):
    """
    Stores and retrieves embedded text by similarity.
    """

    async def add(
        self, texts: Sequence[str], metadata: Sequence[dict[str, str]] | None = None
    ) -> list[str]: ...

    async def search(self, query: str, k: int = 5) -> list[tuple[str, float]]: ...


@runtime_checkable
class Storage(Protocol):
    """
    Persists trace records and audit entries.
    """

    async def append(self, stream: str, record: dict[str, object]) -> None: ...

    async def read(
        self, stream: str, limit: int | None = None
    ) -> list[dict[str, object]]: ...
