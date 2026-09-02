from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .canonical import canonical_dumps, sha256_json


class DeterministicClock:
    def __init__(self, base: datetime) -> None:
        if base.tzinfo is None:
            raise ValueError("clock base must be timezone-aware")
        self.base = base.astimezone(timezone.utc)
        self.index = 0

    def next(self) -> str:
        value = self.base + timedelta(microseconds=self.index)
        self.index += 1
        return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass
class EventLog:
    path: Path
    run_id: str
    clock: DeterministicClock
    sequence: int = 0
    previous_hash: str = "0" * 64

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "seq": self.sequence,
            "ts": self.clock.next(),
            "run_id": self.run_id,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": self.previous_hash,
        }
        event_hash = sha256_json(body)
        event = {**body, "event_hash": event_hash}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_dumps(event) + "\n")
        self.sequence += 1
        self.previous_hash = event_hash
        return event


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"event {number} must be an object")
            events.append(value)
    return events


def verify_event_log(path: Path, expected_run_id: str | None = None) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    try:
        events = load_events(path)
    except (OSError, ValueError) as exc:
        return False, [str(exc)], {"event_count": 0}
    previous = "0" * 64
    for index, event in enumerate(events):
        if event.get("seq") != index:
            errors.append(f"event {index} has non-contiguous sequence")
        if event.get("previous_hash") != previous:
            errors.append(f"event {index} previous_hash mismatch")
        if expected_run_id is not None and event.get("run_id") != expected_run_id:
            errors.append(f"event {index} run_id mismatch")
        body = dict(event)
        recorded = body.pop("event_hash", None)
        calculated = sha256_json(body)
        if recorded != calculated:
            errors.append(f"event {index} hash mismatch")
        previous = recorded if isinstance(recorded, str) else ""
    return not errors, errors, {"event_count": len(events), "final_event_hash": previous if events else "0" * 64}
