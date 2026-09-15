"""
Ordered evaluation of detectors over a single piece of content.
"""

import asyncio

from agentcitadel.protocols import Detector
from agentcitadel.types import GuardResult, Verdict


class GuardPipeline:
    """
    Runs detectors concurrently and resolves their verdicts.

    BLOCK from any detector takes precedence.  Results are returned in detector order.
    not completion order, so traces are reproducable.
    """

    def __init__(self, detectors: list[Detector]) -> None:
        self.detectors = detectors

    async def run(
        self, content: str, context: dict[str, str] | None = None
    ) -> list[GuardResult]:
        """
        Evaluate all detectors against 'content'.

        Every detector runs to completion even after one blocks, so the trace
        records what each concluded.
        """
        return await asyncio.gather(
            *(d.check(content, context) for d in self.detectors)
        )


def resolve(results: list[GuardResult]) -> Verdict:
    """
    Collapse detector findings into one verdict, BLOCK takes precedence, then FLAG.
    """
    verdicts = {r.verdict for r in results}
    if Verdict.BLOCK in verdicts:
        return Verdict.BLOCK
    if Verdict.FLAG in verdicts:
        return Verdict.FLAG
    return Verdict.ALLOW
