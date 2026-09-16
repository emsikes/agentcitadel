"""Approver behavior, with emphasis on the fail-closed paths."""

import pytest

from agentcitadel.guard.approval import AutoDeny, CLIApprover
from agentcitadel.protocols import Approver
from agentcitadel.types import ToolCall


@pytest.fixture
def call() -> ToolCall:
    return ToolCall(name="fs.write", arguments={"path": "/etc/hosts"})


def test_approvers_satisfy_protocol() -> None:
    assert isinstance(AutoDeny(), Approver)
    assert isinstance(CLIApprover(), Approver)


async def test_autodeny_refuses(call: ToolCall) -> None:
    assert await AutoDeny().request(call, "any reason") is False


@pytest.mark.parametrize("answer", ["y", "Y", "yes", "YES", " y "])
async def test_cli_accepts_explicit_yes(
    monkeypatch: pytest.MonkeyPatch, call: ToolCall, answer: str
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert await CLIApprover().request(call, "reason") is True


@pytest.mark.parametrize("answer", ["", "n", "N", "no", "sure", "yep", "\n"])
async def test_cli_denies_everything_else(
    monkeypatch: pytest.MonkeyPatch, call: ToolCall, answer: str
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert await CLIApprover().request(call, "reason") is False


async def test_cli_prompt_shows_arguments(
    monkeypatch: pytest.MonkeyPatch, call: ToolCall
) -> None:
    seen: list[str] = []

    def fake_input(prompt: str) -> str:
        seen.append(prompt)
        return "n"

    monkeypatch.setattr("builtins.input", fake_input)
    await CLIApprover().request(call, "write outside allowlist")

    assert "/etc/hosts" in seen[0]
    assert "write outside allowlist" in seen[0]
