"""Append-only JSONL event log. The log is the only evidence a verdict rests on."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


class EventLog:
    def __init__(self, path: str | Path, run_id: str) -> None:
        self.path = Path(path)
        self.run_id = run_id
        self._seq = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8", newline="\n")

    def write(self, kind: str, **fields: Any) -> None:
        self._seq += 1
        record = {
            "ts": datetime.now().astimezone().isoformat(timespec="milliseconds"),
            "run": self.run_id,
            "seq": self._seq,
            "kind": kind,
            **fields,
        }
        self._fh.write(json.dumps(record, ensure_ascii=True) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def read_events(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and "run" in event and "kind" in event:
                yield event
