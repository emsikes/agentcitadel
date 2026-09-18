"""Pattern-based detection.  Core dependency-free baseline."""

import re

from agentcitadel.types import GuardResult, Verdict


class RegexDetector:
    """
    Flags content matching any configured patterns.

    Ships in core with no ML dependencies.  A bare install will still
    have a working guard.  Patterns are compiled once at construction.
    """

    def __init__(
        self,
        patterns: dict[str, str],
        name: str = "regex",
        verdict: Verdict = Verdict.BLOCK,
    ) -> None:
        self.name = name
        self.verdict = verdict
        self.patterns = {
            label: re.compile(pattern, re.IGNORECASE)
            for label, pattern in patterns.items()
        }

    async def check(
        self, content: str, context: dict[str, str] | None = None
    ) -> GuardResult:
        for label, pattern in self.patterns.items():
            if pattern.search(content):
                return GuardResult(
                    verdict=self.verdict, detector=self.name, reason=f"matches {label}"
                )
        return GuardResult(verdict=Verdict.ALLOW, detector=self.name, reason="no match")
