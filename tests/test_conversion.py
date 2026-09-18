import unittest
from unittest.mock import patch
from uuid import uuid4

from student_pilot import conversion
from student_pilot.common import REPO, load_json


class ConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = conversion.load_pool(conversion.DEFAULT_AUDIT)
        cls.qids = conversion.first_three(cls.pool)
        cls.contexts = [conversion.prepare_packet(cls.pool["packets"][qid]) for qid in cls.qids]
        cls.context = cls.contexts[0]
        cls.payload = cls.context["payload"]

    def test_first_three_are_fixed_training_and_category_diverse(self):
        self.assertEqual(self.qids, conversion.first_three(self.pool))
        self.assertEqual(len(self.qids), 3)
        self.assertEqual(len({self.pool["identities"][qid]["question_type"] for qid in self.qids}), 3)
        split = load_json(conversion.SPLIT_PATH)
        self.assertTrue(set(self.qids) <= set(split["train_candidate_qids"]))
        self.assertFalse(set(self.qids) & set(split["heldout_qids"]))

    def test_payload_is_an_allowlisted_projection_not_an_audit_record(self):
        self.assertEqual(set(self.payload), {"question", "options", "native_final_provenance", "frame_metadata", "evidence"})
        self.assertTrue(self.payload["question"] == self.context["row"]["student_input"]["question"])
        self.assertTrue(self.payload["options"] == self.context["row"]["student_input"]["options"])
        self.assertNotIn("native-final", {item["id"] for item in self.payload["evidence"]})
        self.assertTrue(self.payload["evidence"])

    def test_prepared_first_three_job_revalidates_without_network(self):
        output = REPO / ".tmp" / ("conversion_job_fixture_" + uuid4().hex)
        conversion.prepare(conversion.DEFAULT_AUDIT, output)
        job = conversion.load_job(output / "job.json")
        self.assertEqual(job["selected_qids"], self.qids)
        self.assertEqual(job["paid_calls_maximum"], 9)
        self.assertEqual(job["retry_policy"], conversion.RETRY_POLICY)
        self.assertFalse(job["training_eligible"])

    def test_citations_bind_exact_unicode_spans(self):
        item = self.payload["evidence"][0]
        end = min(120, len(item["text"]))
        citation = {"evidence_id": item["id"], "start": 0, "end": end, "quote": item["text"][:end]}
        conversion.check_citations([citation], self.payload)
        with self.assertRaises(ValueError):
            conversion.check_citations([{**citation, "end": end + 1}], self.payload)
        with self.assertRaises(ValueError):
            conversion.check_citations([{**citation, "evidence_id": "native-final"}], self.payload)

    def test_native_answer_alone_is_not_a_detailed_target(self):
        with self.assertRaises(ValueError):
            conversion.validate_document({"status": "converted", "claims": [], "answer": conversion.answer_body(self.payload["native_final_provenance"])}, self.payload)

    def test_cutoff_is_rejected_even_before_content_parsing(self):
        with self.assertRaises(ValueError):
            conversion.validate_response({"status": "ok", "finish_reason": "MAX_TOKENS"}, self.payload)

    def test_network_failure_is_archived_without_admitting_a_target(self):
        output = REPO / ".tmp" / ("conversion_fixture_" + uuid4().hex)
        output.mkdir(parents=True)
        with patch.object(conversion, "native_transport", side_effect=ConnectionError), patch("time.sleep"):
            record = conversion.collect_one(self.context, output)
        self.assertEqual(record["status"], "INFRA_REQUEUE")
        self.assertEqual(record["attempt_count"], 3)
        self.assertFalse(record["training_eligible"])
        self.assertEqual(load_json(output / "provider.json")["error_type"], "ConnectionError")
        self.assertNotIn("target", record)


if __name__ == "__main__":
    unittest.main()
