"""
Policy evaluation: match a tool call against an ordered rule set.
"""

from fnmatch import fnmatchcase

from agentcitadel.guard.policy.schema import Action, Policy


def matches(pattern: str, tool: str) -> bool:
    """
    Whether a rule pattern matches a tool name.

    Glob semantics: 'fs.*' matches 'fs.read', '*' matches everything.
    """
    return fnmatchcase(tool, pattern)


def evaluate(policy: Policy, tool: str) -> tuple[Action, str]:
    """
    Resolve a tool name against the policy.  First matching rule wins.

    Returns the action and the reason to record or show a human.
    """
    for rule in policy.rules:
        if matches(rule.tool, tool):
            return rule.action, rule.reason or f"matched rule {rule.tool}"
    return policy.default, f"no rule matched {tool}: policy default"


def lint(policy: Policy) -> list[str]:
    """
    Report rules that are probably mistakes but not provably invalid.

    Shadowing is a warning, not an error.  A security tool that refuses to
    start over a stylistic complaint gets replaced with one that doesn't.
    """
    warnings: list[str] = []

    for i, rule in enumerate(policy.rules):
        for earlier in policy.rules[:i]:
            if matches(earlier.tool, rule.tool):
                warnings.append(
                    f"rule {rule.tool!r} is shadowed by earlier rule {earlier.tool!r}"
                )
                break

        if rule.tool == "*" and rule.action is Action.ALLOW:
            warnings.append("rule '*' with action allow permits every tool")

    return warnings
