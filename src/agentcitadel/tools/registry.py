"""Tool lookup and execution."""

import time
from typing import Any

from agentcitadel.tools.base import Tool
from agentcitadel.types import ToolCall, ToolResult


class ToolRegistry:
    """
    Holds tools by name and runs them.

    Tool function exception should not kill the overall agent loop.
    The model gets the error as tool content, and can adapt (e.g. file not found).
    """

    def __init__(self, tools: list[Tool]) -> None:
        self.tools = {tool.name: tool for tool in tools}

    async def run(self, call: ToolCall) -> ToolResult:
        tool = self.tools.get(call.name)
        if tool is None:
            return ToolResult(
                call_id=call.id,
                ok=False,
                content=f"unkown tool {call.name!r}",
                error="not_found",
            )

        started = time.perf_counter()
        try:
            content = await tool.fn(**call.arguments)
            ok, error = True, None
        except Exception as exc:  # noqa: BLE001 - tool code is arbitrary; failures become results
            content, ok, error = f"{type(exc).__name__}: {exc}", False, str(exc)

        duration = (time.perf_counter() - started) * 1000
        return ToolResult(
            call_id=call.id, ok=ok, content=content, error=error, duration_ms=duration
        )

    def schemas(self) -> list[dict[str, Any]]:
        """Tool definitions in the shape providers expect."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in self.tools.values()
        ]
