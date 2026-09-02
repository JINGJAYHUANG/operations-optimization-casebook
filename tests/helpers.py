from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "examples" / "synthetic-suite"
CASE_DIR = SUITE_ROOT / "cases"
SUITE = SUITE_ROOT / "casebook.json"
EXPECTED = SUITE_ROOT / "expected"
NEGATIVE = ROOT / "examples" / "negative-controls"
FIXED_TIME = "2026-09-02T00:00:00Z"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cases():
    suite = load(SUITE)
    return [load(SUITE_ROOT / relative) for relative in suite["cases"]]


def case_paths():
    suite = load(SUITE)
    return [SUITE_ROOT / relative for relative in suite["cases"]]


@contextmanager
def temporary_directory():
    with tempfile.TemporaryDirectory(prefix="opcase-test-") as temporary:
        yield Path(temporary)
