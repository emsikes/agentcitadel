"""Append only JSONL storage, one file per stream."""

import json
from pathlib import Path


class FilesystemStorage:
    """
    Stores each stream as a JSONL file under a root directory.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    async def append(self, stream: str, record: dict[str, object]) -> None:
        # Append only, never writting in "w" mode so existing records can't be overwritten
        with (self.root / f"{stream}.jsonl").open("a") as f:
            f.write(json.dumps(record) + "\n")

    async def read(
        self, stream: str, limit: int | None = None
    ) -> list[dict[str, object]]:
        path = self.root / f"{stream}.jsonl"
        if not path.exists():
            return []
        records = [json.loads(line) for line in path.read_text().splitlines()]
        # Most recents records
        return records[-limit:] if limit else records
