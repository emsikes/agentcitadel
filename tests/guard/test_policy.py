"""Policy matching, evaluation order, and lint warnings."""

import pytest
from pydantic import ValidationError

from agentcitadel.guard.policy.engine import evaluate, lint, matches
from agentcitadel.guard.policy.schema import Action, Policy, Rule


def test_glob_matches_prefix() -> None:
    assert matches("fs.*", "fs.read")
    assert matches("*", "anything")
    assert matches("fs.read", "fs.read")


def test_dot_is_literal_not_wildcard() -> None:
    assert not matches("fs.read", "fsXread")


def test_matching_is_case_sensitive() -> None:
    assert not matches("fs.read", "FS.READ")


def test_first_matching_rule_wins() -> None:
    policy = Policy(
        rules=[
            Rule(tool="fs.read", action=Action.ALLOW),
            Rule(tool="fs.*", action=Action.ASK),
        ]
    )
    assert evaluate(policy, "fs.read")[0] is Action.ALLOW
    assert evaluate(policy, "fs.write")[0] is Action.ASK


def test_unmatched_tool_hits_default_deny() -> None:
    action, reason = evaluate(Policy(), "anything")
    assert action is Action.DENY
    assert "anything" in reason


def test_author_reason_survives_evaluation() -> None:
    policy = Policy(rules=[Rule(tool="fs.*", action=Action.ASK, reason="needs review")])
    assert evaluate(policy, "fs.write")[1] == "needs review"


def test_duplicate_rule_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unreachable"):
        Policy(
            rules=[
                Rule(tool="fs.*", action=Action.ALLOW),
                Rule(tool="fs.*", action=Action.DENY),
            ]
        )


def test_lint_flags_shadowed_rule() -> None:
    policy = Policy(
        rules=[
            Rule(tool="fs.*", action=Action.ASK),
            Rule(tool="fs.read", action=Action.ALLOW),
        ]
    )
    assert "shadowed" in lint(policy)[0]


def test_lint_is_quiet_on_correct_ordering() -> None:
    policy = Policy(
        rules=[
            Rule(tool="fs.read", action=Action.ALLOW),
            Rule(tool="fs.*", action=Action.ASK),
        ]
    )
    assert lint(policy) == []


def test_lint_flags_permissive_wildcard() -> None:
    assert lint(Policy(rules=[Rule(tool="*", action=Action.ALLOW)]))
