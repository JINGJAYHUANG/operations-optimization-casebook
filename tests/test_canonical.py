from __future__ import annotations

import unittest
from datetime import datetime, timezone

from opcase.canonical import canonical_dumps, safe_relative_path, sha256_json, write_json, load_json
from opcase.events import DeterministicClock, EventLog, load_events, verify_event_log
from tests.helpers import temporary_directory


class CanonicalAndEventTests(unittest.TestCase):
    def test_canonical_key_order(self):
        self.assertEqual(canonical_dumps({"b": 1, "a": 2}), '{"a":2,"b":1}')

    def test_canonical_unicode(self):
        self.assertIn("优化", canonical_dumps({"value": "优化"}))

    def test_canonical_rejects_nan(self):
        with self.assertRaises(ValueError):
            canonical_dumps({"value": float("nan")})

    def test_hash_mapping_order(self):
        self.assertEqual(sha256_json({"a": 1, "b": 2}), sha256_json({"b": 2, "a": 1}))

    def test_write_and_load_json(self):
        with temporary_directory() as temp:
            path = temp / "value.json"
            write_json(path, {"b": 1, "a": 2})
            self.assertEqual(load_json(path), {"a": 2, "b": 1})
            self.assertTrue(path.read_text().endswith("\n"))

    def test_safe_path(self):
        self.assertEqual(safe_relative_path("a/b.json"), "a/b.json")

    def test_path_backslash_normalized(self):
        self.assertEqual(safe_relative_path("a\\b.json"), "a/b.json")

    def test_path_absolute_rejected(self):
        with self.assertRaises(ValueError):
            safe_relative_path("/etc/passwd")

    def test_path_parent_rejected(self):
        with self.assertRaises(ValueError):
            safe_relative_path("a/../b")

    def test_clock_requires_timezone(self):
        with self.assertRaises(ValueError):
            DeterministicClock(datetime(2026, 1, 1))

    def test_event_log_valid(self):
        with temporary_directory() as temp:
            path = temp / "events.jsonl"
            log = EventLog(path, "run-1", DeterministicClock(datetime(2026, 1, 1, tzinfo=timezone.utc)))
            log.append("start", {"a": 1})
            log.append("end", {"b": 2})
            passed, errors, details = verify_event_log(path, "run-1")
            self.assertTrue(passed, errors)
            self.assertEqual(details["event_count"], 2)

    def test_event_tamper_detected(self):
        with temporary_directory() as temp:
            path = temp / "events.jsonl"
            log = EventLog(path, "run-1", DeterministicClock(datetime(2026, 1, 1, tzinfo=timezone.utc)))
            log.append("start", {"a": 1})
            events = load_events(path)
            events[0]["payload"]["a"] = 2
            path.write_text(__import__("json").dumps(events[0]) + "\n")
            self.assertFalse(verify_event_log(path)[0])

    def test_event_reorder_detected(self):
        with temporary_directory() as temp:
            path = temp / "events.jsonl"
            log = EventLog(path, "run-1", DeterministicClock(datetime(2026, 1, 1, tzinfo=timezone.utc)))
            log.append("one", {})
            log.append("two", {})
            events = load_events(path)
            path.write_text("\n".join(__import__("json").dumps(item) for item in reversed(events)) + "\n")
            self.assertFalse(verify_event_log(path)[0])

    def test_event_run_id_mismatch(self):
        with temporary_directory() as temp:
            path = temp / "events.jsonl"
            log = EventLog(path, "run-1", DeterministicClock(datetime(2026, 1, 1, tzinfo=timezone.utc)))
            log.append("one", {})
            self.assertFalse(verify_event_log(path, "wrong")[0])
