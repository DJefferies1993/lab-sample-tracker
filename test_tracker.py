"""Boundary and invalid-input checks for the sample tracker."""
import tempfile
import unittest
from pathlib import Path
from tracker import assess_samples, parse_time, read_samples


# SECTION 1 — Deadline behaviour
class DeadlineTests(unittest.TestCase):
    def test_pending_at_deadline_is_overdue(self):
        received = parse_time("2026-01-01T09:00:00Z")
        sample = {"sample_id": "A", "received": received, "completed": None}
        self.assertEqual(assess_samples([sample], parse_time("2026-01-01T10:00:00Z"), 60)[0]["status"], "OVERDUE")

    def test_completion_at_deadline_is_on_time(self):
        now = parse_time("2026-01-01T10:00:00Z")
        sample = {"sample_id": "A", "received": parse_time("2026-01-01T09:00:00Z"), "completed": now}
        self.assertEqual(assess_samples([sample], now, 60)[0]["status"], "COMPLETED")

    def test_demo_has_all_four_states(self):
        now = parse_time("2026-01-01T10:30:00Z")
        rows = assess_samples(read_samples("data/samples.csv", now), now, 60)
        self.assertEqual([row["status"] for row in rows], ["COMPLETED", "OVERDUE", "COMPLETED_LATE", "PENDING"])


# SECTION 2 — Rejected batches
class InputTests(unittest.TestCase):
    def check_invalid(self, body, message):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "samples.csv"
            path.write_text("sample_id,received_at,completed_at\n" + body, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, message):
                read_samples(path, parse_time("2026-01-01T12:00:00Z"))

    def test_duplicate_id(self):
        self.check_invalid("A,2026-01-01T09:00:00Z,\nA,2026-01-01T10:00:00Z,\n", "unique")

    def test_future_receipt(self):
        self.check_invalid("A,2026-01-02T09:00:00Z,\n", "future")

    def test_completion_before_receipt(self):
        self.check_invalid("A,2026-01-01T09:00:00Z,2026-01-01T08:00:00Z\n", "precede")

    def test_missing_timezone(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            parse_time("2026-01-01T09:00:00")

    def test_zero_deadline(self):
        with self.assertRaisesRegex(ValueError, "deadline"):
            assess_samples([], parse_time("2026-01-01T10:00:00Z"), 0)


if __name__ == "__main__":
    unittest.main()
