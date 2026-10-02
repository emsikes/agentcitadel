"""Audit chain integrity."""

from pathlib import Path

from agentcitadel.memory.audit import AuditLog, verify
from agentcitadel.storage.filesystem import FilesystemStorage


async def test_intact_chain_verifies(tmp_path: Path) -> None:
    storage = FilesystemStorage(tmp_path)
    log = AuditLog(storage)
    await log.record("write", "episodic", "turn 1")
    await log.record("read", "semantic", "query: ckd")

    assert verify(await storage.read("audit")) is None


async def test_modified_entry_is_detected(tmp_path: Path) -> None:
    storage = FilesystemStorage(tmp_path)
    log = AuditLog(storage)
    await log.record("write", "episodic", "turn 1")
    await log.record("read", "semantic", "query: ckd")

    entries = await storage.read("audit")
    entries[0]["detail"] = "turn 1 (altered)"

    assert verify(entries) == 1


async def test_deleted_entry_is_detected(tmp_path: Path) -> None:
    storage = FilesystemStorage(tmp_path)
    log = AuditLog(storage)
    await log.record("write", "episodic", "turn 1")
    await log.record("read", "semantic", "query: ckd")
    await log.record("write", "episodic", "turn 2")

    entries = await storage.read("audit")
    del entries[1]

    assert verify(entries) == 3
