"""Tool registry executin paths."""

from agentcitadel.tools.base import Tool
from agentcitadel.tools.registry import ToolRegistry
from agentcitadel.types import ToolCall


async def echo(text: str) -> str:
    return text.upper()


async def boom() -> str:
    raise ValueError("nope")


REGISTRY = ToolRegistry(
    [
        Tool(name="echo", description="echo", parameters={"type": "object"}, fn=echo),
        Tool(name="boom", description="fails", parameters={"type": "object"}, fn=boom),
    ]
)


async def test_success() -> None:
    result = await REGISTRY.run(ToolCall(name="echo", arguments={"text": "hi"}))
    assert result.ok and result.content == "HI"


async def test_exception_is_captured_not_raised() -> None:
    result = await REGISTRY.run(ToolCall(name="boom", arguments={}))
    assert not result.ok
    assert "nope" in result.content


async def test_unkown_tool() -> None:
    result = await REGISTRY.run(ToolCall(name="undefined", arguments={}))
    assert not result.ok and result.error == "not_found"
