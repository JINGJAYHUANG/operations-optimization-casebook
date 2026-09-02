from __future__ import annotations

import sys
import unittest
from pathlib import Path

MINIMUM_TESTS = 350
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

suite = unittest.defaultTestLoader.discover(
    start_dir=str(ROOT / "tests"),
    pattern="test*.py",
    top_level_dir=str(ROOT),
)
count = suite.countTestCases()
print(f"discovered tests: {count}")
if count < MINIMUM_TESTS:
    raise SystemExit(f"test floor failed: expected at least {MINIMUM_TESTS}, found {count}")
