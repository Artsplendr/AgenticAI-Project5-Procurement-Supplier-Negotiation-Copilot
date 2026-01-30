from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from owpa.schemas.deal_state import DealState


def ensure_parent_dir(file_path: str | Path) -> None:
    Path(file_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


class JsonlDealStateStore:
    """
    Append-only JSONL store for DealState snapshots.
    Each line: {"deal_id": "...", "state": {...}}.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        ensure_parent_dir(self.path)

    def append(self, state: DealState) -> None:
        record = {"deal_id": state.deal_id, "state": state.model_dump(mode="json")}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def iter_records(self) -> Iterable[dict]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)

    def load_latest(self, deal_id: str) -> Optional[DealState]:
        """
        Returns the most recent snapshot for deal_id, or None if not found.
        """
        latest = None
        for rec in self.iter_records():
            if rec.get("deal_id") == deal_id:
                latest = rec.get("state")
        if latest is None:
            return None
        return DealState.model_validate(latest)
