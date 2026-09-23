"""Tool definition and execution."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Tool:
    """A callable the agent may invoke, with a JSON Schema for its arguments."""

    name: str
    description: str
    parameters: dict[str, Any]
    fn: Callable[..., Awaitable[str]]
