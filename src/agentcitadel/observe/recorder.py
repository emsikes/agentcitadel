"""Writes spans to storage.  The single writer of trace data."""

from agentcitadel.protocols import Storage
from agentcitadel.types import Span


class Recorder:
    """Persists spans, one stream per run."""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    async def record(self, span: Span) -> None:
        await self.storage.append(span.run_id, span.model_dump(mode="json"))
