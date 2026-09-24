"""Anthropic provider adapter."""

from collections.abc import Sequence
from typing import Any

import httpx

from agentcitadel.config import Settings
from agentcitadel.types import Message, ToolCall

API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider:
    """Translate Message objects to and from the Anthropic Messages API."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        api_key: str | None = None,
        max_tokens: int = 4096,
    ) -> None:
        self.model = model
        self.api_key = api_key or Settings().anthropic_api_key
        self.max_tokens = max_tokens

    async def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[dict[str, Any]] | None = None,
    ) -> Message:
        system = next((m.content for m in messages if m.role == "system"), None)
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": _to_anthropic([m for m in messages if m.role != "system"]),
        }
        if system:
            body["system"] = system
        if tools:
            body["tools"] = list(tools)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                API_URL,
                json=body,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
        response.raise_for_status()

        return _from_anthropic(response.json())


def _to_anthropic(messages: Sequence[Message]) -> list[dict[str, Any]]:
    """Convert Message objects to Anthropic content-block format."""
    out: list[dict[str, Any]] = []
    for m in messages:
        if m.role == "tool":
            content: Any = [
                {
                    "type": "tool_result",
                    "tool_use_id": m.tool_call_id,
                    "content": m.content,
                }
            ]
            out.append({"role": "user", "content": content})
        elif m.tool_calls:
            blocks: list[dict[str, Any]] = [
                {"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments}
                for c in m.tool_calls
            ]
            if m.content:
                blocks.insert(0, {"type": "text", "text": m.content})
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": m.role, "content": m.content})
    return out


def _from_anthropic(payload: dict[str, Any]) -> Message:
    """Convert an Anthropic response into a Message."""
    text = ""
    calls: list[ToolCall] = []
    for block in payload.get("content", []):
        if block["type"] == "text":
            text += block["text"]
        elif block["type"] == "tool_use":
            calls.append(
                ToolCall(id=block["id"], name=block["name"], arguments=block["input"])
            )
    return Message(role="assistant", content=text, tool_calls=calls)
