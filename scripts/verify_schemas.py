from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
required = {
    "case.schema.json",
    "suite.schema.json",
    "solution.schema.json",
    "decision.schema.json",
    "event.schema.json",
    "run-manifest.schema.json",
}
found = {path.name for path in SCHEMA_DIR.glob("*.json")}
if found != required:
    raise SystemExit(f"schema inventory mismatch: expected {sorted(required)}, found {sorted(found)}")
for path in sorted(SCHEMA_DIR.glob("*.json")):
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise SystemExit(f"wrong schema draft: {path.name}")
    if not value.get("$id") or not value.get("title") or value.get("type") != "object":
        raise SystemExit(f"incomplete schema metadata: {path.name}")
print(f"schemas passed: {len(found)}")
