"""Hash-chained audit log for memory access."""

import hashlib
import json
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from agentcitadel.protocols import Storage


class AuditEntry(BaseModel):
    """One recorded memory access, chained to the entry before it."""

    seq: int
    op: str
    store: str
    detail: str
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    prev_hash: str
    hash: str = ""


def _compute_hash(entry: AuditEntry) -> str:
    """Hash on entry's contents plus the previous hash."""
    payload = json.dumps(
        {
            "seq": entry.seq,
            "op": entry.op,
            "store": entry.store,
            "detail": entry.detail,
            "at": entry.at.isoformat(),
            "prev_hash": entry.prev_hash,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class AuditLog:
    """Append-only chain of memory access entries."""

    def __init__(self, storage: Storage, stream: str = "audit") -> None:
        self.storage = storage
        self.stream = stream
        self._seq = 0
        self._last_hash = "genesis"

    async def record(self, op: str, store: str, detail: str) -> AuditEntry:
        """Append one entry, chained to the previous."""
        self._seq += 1
        entry = AuditEntry(
            seq=self._seq, op=op, store=store, detail=detail, prev_hash=self._last_hash
        )
        entry.hash = _compute_hash(entry)
        self._last_hash = entry.hash
        await self.storage.append(self.stream, entry.model_dump(mode="json"))
        return entry


def verify(entries: list[dict[str, object]]) -> int | None:
    """Check the chain.  Returns the seq of the first broken entry, or None if intact."""
    prev = "genesis"
    for raw in entries:
        entry = AuditEntry.model_validate(raw)
        if entry.prev_hash != prev or _compute_hash(entry) != entry.hash:
            return entry.seq
        prev = entry.hash
    return None
