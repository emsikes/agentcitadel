"""
Declarative tool authorization policy.
"""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Action(str, Enum):
    """
    What the policy permits for a matching tool call.
    """

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class Rule(BaseModel):
    """
    One policy entry, matched against a tool call by name.
    """

    tool: str
    action: Action
    reason: str = ""


class Policy(BaseModel):
    """
    An ordered rule set with a failback for unmatched tools.
    """

    default: Action = Action.DENY
    rules: list[Rule] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_reachable(self) -> "Policy":
        """
        Reject duplicate patterns - a leter identical rule can never match.
        """
        seen: set[str] = set()
        for rule in self.rules:
            if rule.tool in seen:
                raise ValueError(
                    f"duplicate rule for {rule.tool!r}: the later one is unreachable"
                )
            seen.add(rule.tool)
        return self
