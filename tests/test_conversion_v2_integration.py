import copy
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from student_pilot import conversion, conversion_dry_run, conversion_v2
from student_pilot.common import REPO, binding, canonical_bytes, digest_json, load_json
from test_conversion_v2 import FIXTURE, synthetic_document, synthetic_payload


class DryRunTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ.get("STUDENT_CONVERTER_TEST_OUTPUT", REPO / ".tmp/conversion_v2_tests")) / uuid4().hex
        self.root.mkdir(parents=True)
        self.contexts = self.root / "contexts"
        self.contexts.mkdir()
        fixture = load_json(FIXTURE)
        request = conversion.make_request(fixture["payload"], "v1")
        request.pop("converter_version")
        context = {"row": {"qid": "3919", "native_answer_archive": {"native_final": fixture["payload"]["native_final_provenance"]}},
                   "payload": fixture["payload"], "request": request, "request_sha256": digest_json(request)}
        self.context_path = self.contexts / "3919.json"
        self.context_path.write_bytes(canonical_bytes(context))
        self.job = {"schema": "grounded-conversion-job-v1", "model": conversion.MODEL, "settings": conversion.SETTINGS,
                    "selected_qids": ["3919"], "contexts": [{"qid": "3919", "context": binding(self.context_path), "request_sha256": digest_json(request)}]}
        self.job_path = self.root / "job.json"
        self.job_path.write_bytes(canonical_bytes(self.job))

    def build(self):
        return conversion_dry_run.build_dry_run(self.job_path, self.contexts, self.root / "requests", self.root)

    def test_dry_run_uses_only_bound_local_contexts_without_provider_or_source_access(self):
        before = self.context_path.read_bytes()
        with patch.object(conversion, "native_transport", side_effect=AssertionError("Provider is forbidden")) as transport, patch.object(conversion, "load_pool", side_effect=AssertionError("External source access is forbidden")) as pool:
            receipt = self.build()
        transport.assert_not_called()
        pool.assert_not_called()
        self.assertEqual(receipt["provider_calls"], 0)
        self.assertFalse(receipt["launch_admitted"])
        self.assertFalse(receipt["training_eligible"])
        self.assertFalse(receipt["source_authorities_revalidated"])
        self.assertEqual(self.context_path.read_bytes(), before)
        record = receipt["requests"][0]
        for key in ("request", "rendered_prompt", "request_boundary"):
            self.assertEqual(binding(record[key]["path"]), record[key])
        self.assertTrue(load_json(record["request_boundary"]["path"])["passed"])
        self.assertIn(conversion_v2.SYSTEM, Path(record["rendered_prompt"]["path"]).read_text())
        self.assertEqual(load_json(self.root / "requests/RESPONSE_SCHEMA.json"), conversion_v2.RESPONSE_SCHEMA)

    def test_changed_context_hash_is_rejected_before_writing(self):
        self.context_path.write_bytes(self.context_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            self.build()
        self.assertFalse((self.root / "requests").exists())

    def test_external_archived_path_is_never_dereferenced(self):
        self.job["contexts"][0]["context"]["path"] = "/not-accessible/archived/3919.json"
        self.job_path.write_bytes(canonical_bytes(self.job))
        self.assertEqual(self.build()["selected_qids"], ["3919"])

    def test_existing_output_is_not_cleaned_or_overwritten(self):
        output = self.root / "requests"
        output.mkdir()
        marker = output / "keep.txt"
        marker.write_text("preserve me")
        with self.assertRaises(ValueError):
            self.build()
        self.assertEqual(marker.read_text(), "preserve me")

    def test_outside_workspace_is_refused_before_loading_inputs(self):
        with patch.object(conversion_dry_run, "load_json", side_effect=AssertionError("Must check scope first")), self.assertRaisesRegex(ValueError, "workspace"):
            conversion_dry_run.build_dry_run(self.root.parent / "outside.json", self.contexts, self.root / "requests", self.root)

    def test_boundary_checker_inspects_model_visible_json_not_only_envelope(self):
        request = conversion.make_request(synthetic_payload(), "v2")
        payload = json.loads(request["contents"][0]["parts"][0]["text"])
        payload["frame_metadata"]["score"] = 1
        request["contents"][0]["parts"][0]["text"] = canonical_bytes(payload).decode()
        with self.assertRaisesRegex(ValueError, "request_boundary"):
            conversion_dry_run.check_request_boundary(request)


class ReviewAndArchiveTests(unittest.TestCase):
    def collect(self, document, payload=None, version="v2"):
        payload = payload or synthetic_payload()
        request = conversion.make_request(payload, version)
        context = {"row": {"qid": "fixture", "sources": {}}, "payload": payload, "request": request,
                   "converter_version": version, "request_sha256": digest_json(request)}
        response = {"status": "ok", "finish_reason": "STOP", "provider_served_model": conversion.MODEL,
                    "raw_response": [{"fixture": "complete native archive"}], "thoughts": "Synthetic exposed thoughts.",
                    "events": [{"event": "fixture"}], "usage": {"prompt_token_count": 1, "candidates_token_count": 1, "total_token_count": 2},
                    "content": json.dumps(document)}
        saved = {}
        with patch.object(conversion, "repo_output", side_effect=Path), patch.object(conversion, "write_once", side_effect=lambda path, value: saved.update({Path(path).name: value})), patch.object(conversion, "binding", return_value={"fixture": True}), patch.object(conversion, "native_transport", return_value=response):
            decision = conversion.collect_one(context, Path("fixture-only"))
        return decision, saved, response

    def test_candidate_keeps_full_provider_archive_and_remains_unadmitted(self):
        decision, saved, response = self.collect(synthetic_document())
        self.assertEqual(saved["provider.json"], response)
        self.assertEqual(decision["status"], "AWAITING_INDEPENDENT_GROUNDED_REVIEW")
        self.assertEqual(decision["converter_version"], "v2")
        self.assertFalse(decision["training_eligible"])
        self.assertFalse(saved["candidate.json"]["training_eligible"])
        self.assertFalse(saved["candidate.json"]["semantic_grounding_verified"])

    def test_qualification_rejection_is_structured_in_decision(self):
        payload = synthetic_payload(synthetic_payload()["evidence"][0]["text"] + " There is a conflict about the box.")
        decision, saved, _ = self.collect(synthetic_document(), payload)
        self.assertEqual(decision["reason"], "qualification_omitted")
        self.assertEqual(decision["rejection_details"]["source_pointer"], "/trace/1/content")
        self.assertEqual(decision["rejection_details"]["evidence_id"], "e0000")
        self.assertNotIn("candidate.json", saved)

    def test_legacy_decisions_are_versioned_without_changing_legacy_validation(self):
        fixture = load_json(FIXTURE)
        decision, saved, response = self.collect(fixture["provider_document"], fixture["payload"], "v1")
        self.assertEqual(decision["converter_version"], "v1")
        self.assertEqual(saved["request.json"]["converter_version"], "v1")
        self.assertIn("Claim", decision["reason"])
        self.assertEqual(saved["provider.json"], response)

    def test_no_review_self_review_or_missing_claim_review_can_admit(self):
        candidate = conversion.validate_document(synthetic_document(), synthetic_payload(), "v2")
        item = {"qid": "fixture", "context": {"path": "fixture-context", "sha256": "fixture"}}
        context = {"row": {"qid": "fixture"}}
        record = {"status": "AWAITING_INDEPENDENT_GROUNDED_REVIEW", "candidate": {"path": "fixture-candidate"}}
        pin = {"path": "fixture-decision", "sha256": "fixture"}
        job = {"selected_qids": ["fixture"]}
        review = {"schema": "independent-grounded-review-v1", "reviewer": "synthetic-reviewer", "independent_of_converter": True,
                  "review_method": "agent_exact_evidence_review", "run": {"fixture": True},
                  "decisions": [{"qid": "fixture", "decision": pin, "verdict": "accept", "checks": {key: True for key in conversion.REVIEW_CHECKS}, "claim_verdicts": []}]}
        for changes in ({"independent_of_converter": False}, {"reviewer": ""}, {}):
            with self.subTest(changes=changes), patch.object(conversion, "verified_run", return_value=(job, [(item, context, record, pin)])), patch.object(conversion, "binding", return_value={"fixture": True}), patch.object(conversion, "load_json", side_effect=lambda path: candidate if path == "fixture-candidate" else {**review, **changes}), self.assertRaises(ValueError):
                conversion.accepted_manifest("fixture-run", "fixture-review")

    def test_version_disagreement_fails_before_provider(self):
        request = conversion.make_request(synthetic_payload(), "v2")
        with patch.object(conversion, "native_transport") as transport, self.assertRaisesRegex(ValueError, "versions disagree"):
            conversion.collect_one({"converter_version": "v1", "request": request}, "unused")
        transport.assert_not_called()

    def test_nfc_is_not_case_folding_or_compatibility_normalization(self):
        for source, quote in (("Box", "box"), ("\ufb01xture", "fixture")):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, "citation_not_found"):
                conversion_v2.resolve_citation({"evidence_id": "e0000", "quote": quote}, synthetic_payload(source))

    def test_byte_exact_answer_comparison_never_nfc_normalizes_answer(self):
        payload = synthetic_payload()
        payload["native_final_provenance"] = "<ANSWER>cafe\u0301</ANSWER>"
        document = synthetic_document()
        document["answer"] = "caf\u00e9"
        with self.assertRaisesRegex(ValueError, "agree verbatim"):
            conversion.validate_document(document, payload, "v2")


if __name__ == "__main__":
    unittest.main()
