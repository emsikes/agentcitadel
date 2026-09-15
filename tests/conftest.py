"""Shared fixtures.

The fakes here let every test exercise the real code paths without a network
call or an API key.
"""

from collections.abc import Sequence

import pytest

from agentcitadel.types import GuardResult, Message, ToolCall, Verdict


class FakeProvider:
    """LLMProvider that replays a scripted list of assistant turns."""

    model = "fake-1"

    def __init__(self, replies: list[Message]) -> None:
        self.replies = list(replies)
        self.calls: list[Sequence[Message]] = []

    async def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[dict[str, object]] | None = None,
    ) -> Message:
        self.calls.append(list(messages))
        if not self.replies:
            raise AssertionError("FakeProvider ran out of scripted replies")
        return self.replies.pop(0)


class FakeDetector:
    """Detector that returns a fixed verdict and records what it saw."""

    def __init__(self, name: str = "fake", verdict: Verdict = Verdict.ALLOW) -> None:
        self.name = name
        self.verdict = verdict
        self.seen: list[str] = []

    async def check(
        self, content: str, context: dict[str, str] | None = None
    ) -> GuardResult:
        self.seen.append(content)
        return GuardResult(
            verdict=self.verdict,
            detector=self.name,
            reason=f"fake detector configured to {self.verdict.value}",
        )


@pytest.fixture
def allow_detector() -> FakeDetector:
    return FakeDetector(name="allow", verdict=Verdict.ALLOW)


@pytest.fixture
def block_detector() -> FakeDetector:
    return FakeDetector(name="block", verdict=Verdict.BLOCK)


@pytest.fixture
def text_reply() -> Message:
    return Message(role="assistant", content="ok")


@pytest.fixture
def tool_reply() -> Message:
    call = ToolCall(name="read_file", arguments={"path": "/tmp/x"})
    return Message(role="assistant", content="", tool_calls=[call])
