"""FilesystemStorage append and read."""

from pathlib import Path

from agentcitadel.storage.filesystem import FilesystemStorage


async def test_append_then_read(tmp_path: Path) -> None:
    s = FilesystemStorage(tmp_path)
    await s.append("run", {"step": 1})
    await s.append("run", {"step": 2})

    assert await s.read("run") == [{"step": 1}, {"step": 2}]
    assert await s.read("run", limit=1) == [{"step": 2}]


async def test_missing_stream_is_empty(tmp_path: Path) -> None:
    assert await FilesystemStorage(tmp_path).read("nothing") == []
