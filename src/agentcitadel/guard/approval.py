"""Approver implementation for policy rules that resolves to 'ask'."""

import asyncio

import httpx

from agentcitadel.types import ToolCall


class AutoDeny:
    """Refuses every request.  The correct default for unattended runs."""

    async def request(self, call: ToolCall, reason: str) -> bool:
        return False


class CLIApprover:
    """Prompts on the terminal.  Blocking input runs in a worker thread."""

    async def request(self, call: ToolCall, reason: str) -> bool:
        prompt = f"\nApprove {call.name}({call.arguments})?\n {reason}\n [y/N]"
        answer = await asyncio.to_thread(input, prompt)
        return answer.strip().lower() in {"y", "yes"}


class WebhookApprover:
    """
    Posts the request to an external endpoint and awaits its verdict.

    Fails closed: a timeout, a non-200, or a malformed body all deny.
    """

    def __init__(self, url: str, timeout: float = 300.0) -> None:
        self.url = url
        self.timeout = timeout

    async def request(self, call: ToolCall, reason: str) -> bool:
        payload = {
            "call_id": call.id,
            "tool": call.name,
            "arguments": call.arguments,
            "reason": reason,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.url, json=payload)
            response.raise_for_status()
            return response.json().get("approved") is True
        except (httpx.HTTPError, ValueError):
            return False
