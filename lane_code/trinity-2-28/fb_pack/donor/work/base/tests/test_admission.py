import copy
import unittest
from datetime import datetime, timedelta, timezone

from student_pilot.admission import native_final
from student_pilot.lease import check_lease


class SourceTests(unittest.TestCase):
    def fixture(self):
        return {"trace": [{
            "role": "ai", "provenance": "provider", "tool_calls": [],
            "content": [{"type": "thinking", "thinking": "Not a student input"}, {"type": "text", "text": "<ANSWER>fixture</ANSWER>"}],
            "raw_response": {"content": [{"type": "text", "text": "<ANSWER>fixture</ANSWER>"}]},
            "response_metadata": {"finish_reason": "STOP", "model_name": "gemini-3.1-pro-preview"},
        }]}

    def test_native_answer_ignores_predictions_and_thoughts(self):
        entry = self.fixture()
        entry["pred"] = "wrong"
        entry["results"] = {"pred": "wrong"}
        final = native_final(entry)
        self.assertEqual(final["target"], "<answer>fixture</answer>")
        self.assertEqual(final["native_final"], "<ANSWER>fixture</ANSWER>")

    def test_prediction_only_is_rejected(self):
        with self.assertRaises(ValueError):
            native_final({"pred": "fixture", "results": {"pred": "fixture"}})

    def test_incomplete_or_modified_native_response_is_rejected(self):
        for change in ("incomplete", "modified", "ambiguous"):
            entry = self.fixture()
            final = entry["trace"][0]
            if change == "incomplete":
                final["response_metadata"]["finish_reason"] = "MAX_TOKENS"
            elif change == "modified":
                final["raw_response"]["content"][0]["text"] = "different"
            else:
                final["content"] = "<ANSWER>fixture</ANSWER><ANSWER>other</ANSWER>"
                final["raw_response"]["content"] = final["content"]
            with self.assertRaises(ValueError):
                native_final(entry)


class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 18, tzinfo=timezone.utc)
        self.lease = {
            "host": "trinity-1-8", "gpu_index": 1, "owner": "test-only", "work_id": "test-only",
            "coordination_lease_evidence": "synthetic unit-test evidence, not launch authorization",
            "ownership_check_passed": True, "coordination_lease_passed": True, "vnice_wrapped": True,
            "ownership_checked_at": (self.now - timedelta(seconds=20)).isoformat(),
            "expires_at": (self.now + timedelta(seconds=600)).isoformat(),
        }

    def test_fresh_scoped_attestation(self):
        self.assertEqual(check_lease(self.lease, "trinity-1-8", "1", self.now), self.lease)

    def test_other_device_host_stale_or_missing_evidence_is_rejected(self):
        variants = [
            ({}, "trinity-1-13", "1"), ({}, "trinity-1-8", "0"),
            ({"ownership_check_passed": False}, "trinity-1-8", "1"),
            ({"vnice_wrapped": False}, "trinity-1-8", "1"),
            ({"ownership_checked_at": (self.now - timedelta(seconds=301)).isoformat()}, "trinity-1-8", "1"),
            ({"expires_at": self.now.isoformat()}, "trinity-1-8", "1"),
        ]
        for changes, host, visible in variants:
            lease = copy.deepcopy(self.lease)
            lease.update(changes)
            with self.assertRaises(ValueError):
                check_lease(lease, host, visible, self.now)


if __name__ == "__main__":
    unittest.main()
