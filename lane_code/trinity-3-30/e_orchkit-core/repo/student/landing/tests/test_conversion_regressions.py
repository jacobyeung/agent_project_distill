import copy
import hashlib
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch
from uuid import uuid4

from student_pilot import admission, conversion
from student_pilot.common import binding, canonical_bytes, digest_json, load_json


def v1_validate_document(response, payload):
    return conversion.validate_document(response, payload, "v1")

def v1_validate_response(response, payload):
    return conversion.validate_response(response, payload, "v1")

def v1_response_decision(response, payload):
    return conversion.response_decision(response, payload, "v1")



class ServerError(Exception):
    def __init__(self, code=503, headers=None):
        super().__init__("Provider unavailable")
        self.code = code
        self.status = "UNAVAILABLE"
        self.response_json = {"error": {"code": code, "message": "Provider unavailable"},
                              "modelVersion": "served-fixture-model"}
        self.response = SimpleNamespace(status_code=code, text=json.dumps(self.response_json),
                                        headers=headers or {"Retry-After": "42", "x-request-id": "fixture-request"})


def immutable_fixture(path, value):
    path = Path(path)
    root = Path(os.environ["STUDENT_PILOT_TEST_OUTPUT"]).resolve()
    if not path.resolve().is_relative_to(root):
        raise ValueError("Fixture write escaped its output root")
    data = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Refusing to change immutable fixture")
        return path
    with path.open("xb") as stream:
        stream.write(data)
    return path


class ConverterFixture(unittest.TestCase):
    def setUp(self):
        self.output = Path(os.environ["STUDENT_PILOT_TEST_OUTPUT"]) / (self.id().split(".")[-1] + "_" + uuid4().hex)
        self.output.mkdir(parents=True)
        self.text = "The synthetic archived observation records the fixture clearly and supports the same conclusion without any additional measurements."
        self.payload = {"question": "Synthetic fixture question", "options": [],
                        "native_final_provenance": "<ANSWER>fixture</ANSWER>", "frame_metadata": {},
                        "evidence": [{"id": "e0001", "kind": "provider_thought_summary", "text": self.text}]}
        citation = {"evidence_id": "e0001", "start": 0, "end": len(self.text), "quote": self.text}
        self.document = {"status": "converted", "answer": "fixture",
                         "claims": [{"id": "c1", "text": self.text, "citations": [citation]},
                                    {"id": "c2", "text": self.text, "citations": [citation]}]}
        self.response = {"status": "ok", "finish_reason": "STOP", "provider_served_model": "fixture-model",
                         "raw_response": [{"content": "fixture"}],
                         "usage": {"prompt_token_count": 20, "candidates_token_count": 10, "total_token_count": 30},
                         "content": json.dumps(self.document)}
        request = conversion.make_request(self.payload, "v1")
        self.context = {"converter_version": "v1", "row": {"qid": "1", "sources": {}}, "payload": self.payload,
                        "request": request, "request_sha256": digest_json(request)}

    def collect(self, responses, **kwargs):
        with patch.object(conversion, "repo_output", side_effect=lambda path, **unused: Path(path)), \
                patch.object(conversion, "write_once", side_effect=immutable_fixture), \
                patch.object(conversion, "native_transport", side_effect=responses) as transport, \
                patch("time.sleep") as sleep:
            record = conversion.collect_one(self.context, self.output / "collected", **kwargs)
        return record, transport, sleep


class AnswerEnvelopeTests(ConverterFixture):
    def test_normalizes_both_sides_without_nested_target_tags(self):
        for native in ("fixture", "<ANSWER>fixture</ANSWER>", " \n<AnSwEr>fixture</aNsWeR>\t"):
            for converted in ("fixture", "<ANSWER>fixture</ANSWER>", "\t<answer>fixture</answer>\n"):
                with self.subTest(native=native, converted=converted):
                    candidate = v1_validate_document({**self.document, "answer": converted},
                                                             {**self.payload, "native_final_provenance": native})
                    self.assertEqual(candidate["answer"], "fixture")
                    self.assertTrue(candidate["target"].endswith("<answer>fixture</answer>"))
                    self.assertEqual(candidate["target"].count("<answer>"), 1)
                    self.assertFalse(candidate["training_eligible"])
                    self.assertFalse(candidate["semantic_grounding_verified"])

    def test_body_whitespace_is_preserved_not_trimmed(self):
        body = " \nfixture\t "
        self.assertEqual(conversion.answer_body("\t<ANSWER>" + body + "</ANSWER>\n"), body)
        self.assertEqual(conversion.answer_body(body), body)
        candidate = v1_validate_document({**self.document, "answer": "<answer>" + body + "</answer>"},
                                                 {**self.payload, "native_final_provenance": body})
        self.assertEqual(candidate["answer"], body)

    def test_case_numeric_unicode_and_whitespace_mismatches_stay_rejected(self):
        for native, converted in (("fixture", "Fixture"), ("1", "1.0"), ("é", "e\u0301"),
                                  ("fixture", " fixture"), ("fixture", "fixture\n")):
            with self.subTest(native=native, converted=converted), self.assertRaisesRegex(ValueError, "verbatim"):
                v1_validate_document({**self.document, "answer": "<ANSWER>" + converted + "</ANSWER>"},
                                             {**self.payload, "native_final_provenance": "<answer>" + native + "</answer>"})

    def test_nested_sibling_malformed_empty_and_prose_wrappers_fail_closed(self):
        values = ("<ANSWER><ANSWER>fixture</ANSWER></ANSWER>", "<answer>fixture</answer><answer>fixture</answer>",
                  "<answer>fixture", "fixture</answer>", "<answer >fixture</answer>",
                  "prefix <answer>fixture</answer>", "<answer>fixture</answer> suffix", "<answer> </answer>", "", None, 1)
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                conversion.answer_body(value)

    def test_schema_and_prompt_require_bare_body_and_existing_claim_ids(self):
        answer = conversion.RESPONSE_SCHEMA["properties"]["answer"]
        self.assertIn("bare", answer["description"].lower())
        self.assertIn("<ANSWER>", answer["description"])
        self.assertIn("bare", conversion.SYSTEM.lower())
        pattern = conversion.RESPONSE_SCHEMA["properties"]["claims"]["items"]["properties"]["id"]["pattern"]
        self.assertRegex("c1", pattern)
        self.assertNotRegex("claim_1", pattern)

    def test_other_document_gates_remain_strict(self):
        documents = []
        for field, value in (("status", "insufficient_evidence"), ("claims", []), ("answer", "other")):
            documents.append({**self.document, field: value})
        for mutation in ("ids", "quote", "numeric", "artifact", "refusal"):
            value = copy.deepcopy(self.document)
            if mutation == "ids":
                value["claims"][0]["id"] = "claim_1"
            elif mutation == "quote":
                value["claims"][0]["citations"][0]["quote"] = "invented"
            elif mutation == "numeric":
                value["claims"][0]["text"] += " There are 23 units."
            elif mutation == "artifact":
                value["claims"][0]["text"] += " execute_python_code"
            else:
                value["claims"][0]["text"] = "I cannot assist with this fixture request."
            documents.append(value)
        for value in documents:
            with self.subTest(value=value), self.assertRaises(ValueError):
                v1_validate_document(value, self.payload)


class ProviderFailureTests(ConverterFixture):
    def test_full_error_is_archived_before_classification(self):
        original = conversion.validate_response

        def validate(response, payload, converter_version="v1"):
            self.assertEqual(load_json(self.output / "collected/attempts/001/provider.json"), response)
            return original(response, payload, converter_version)

        with patch.object(conversion, "validate_response", side_effect=validate):
            record, transport, sleep = self.collect([ServerError()], max_attempts=1)
        archive = load_json(self.output / "collected/provider.json")
        self.assertEqual(record["status"], "INFRA_REQUEUE")
        self.assertEqual(archive["status_code"], 503)
        self.assertEqual(archive["response_body"], ServerError().response.text)
        self.assertEqual(archive["response_json"], ServerError().response_json)
        self.assertEqual(archive["response_headers"]["x-request-id"], "fixture-request")
        self.assertEqual(archive["retry_after"], "42")
        self.assertEqual(archive["requested_model"], self.context["request"]["model"])
        self.assertEqual(archive["provider_served_model"], "served-fixture-model")
        self.assertIsInstance(archive["elapsed_ms"], int)
        self.assertGreaterEqual(archive["elapsed_ms"], 0)
        self.assertEqual(archive["error_message"], "Provider unavailable")
        self.assertEqual(archive["error_type"], "ServerError")
        self.assertEqual(transport.call_count, 1)
        sleep.assert_not_called()

    def test_unknown_http_metadata_remains_explicitly_null(self):
        archive = conversion.error_response(TimeoutError("fixture timeout"), self.context["request"], 12)
        for field in ("status_code", "response_body", "response_json", "retry_after", "provider_served_model"):
            self.assertIsNone(archive[field])
        self.assertEqual(archive["response_headers"], {})
        self.assertEqual(archive["elapsed_ms"], 12)
        self.assertEqual(archive["requested_model"], conversion.MODEL)

    def test_response_credentials_are_redacted_without_losing_diagnostics(self):
        error = ServerError(headers={"Retry-After": "30", "Authorization": "Bearer fixture-secret",
                                     "Set-Cookie": "fixture-secret", "x-request-id": "safe"})
        archive = conversion.error_response(error, self.context["request"], 1)
        self.assertNotIn("fixture-secret", json.dumps(archive))
        self.assertEqual(archive["response_headers"]["x-request-id"], "safe")
        self.assertEqual(archive["status_code"], 503)

    def test_all_server_codes_and_transport_timeouts_are_infrastructure(self):
        for code in (500, 502, 503, 504, 599):
            with self.subTest(code=code):
                response = conversion.error_response(ServerError(code), self.context["request"], 1)
                with self.assertRaises(conversion.InfrastructureFailure):
                    v1_validate_response(response, self.payload)
        for error in (ConnectionError(), TimeoutError(), ConnectionResetError(),
                      type("ReadTimeout", (Exception,), {})(), type("ConnectError", (Exception,), {})()):
            with self.subTest(error=type(error).__name__):
                response = conversion.error_response(error, self.context["request"], 1)
                with self.assertRaises(conversion.InfrastructureFailure):
                    v1_validate_response(response, self.payload)

    def test_legacy_server_error_is_infra_without_inventing_http_status(self):
        response = {"status": "error", "error_type": "ServerError", "raw_response": [], "usage": None, "finish_reason": None}
        decision, candidate = v1_response_decision(response, self.payload)
        self.assertEqual(decision["status"], "INFRA_REQUEUE")
        self.assertIn("unavailable", decision["reason"].lower())
        self.assertNotIn("503", decision["reason"])
        self.assertIsNone(candidate)
        self.assertNotIn("status_code", response)

    def test_refusal_cutoff_and_nontransient_errors_stay_terminal(self):
        variants = [{**self.response, "finish_reason": reason} for reason in ("MAX_TOKENS", "SAFETY", "RECITATION")]
        variants += [{**self.response, "status": "refused"},
                     {**self.response, "content": json.dumps({**self.document, "status": "insufficient_evidence"})},
                     {"status": "error", "status_code": 400, "error_type": "ClientError"},
                     {"status": "error", "status_code": 401, "error_type": "ServerError"},
                     {"status": "error", "status_code": 503, "finish_reason": "MAX_TOKENS"}]
        for index, response in enumerate(variants):
            with self.subTest(index=index):
                decision, candidate = v1_response_decision(response, self.payload)
                self.assertEqual(decision["status"], "REJECTED")
                self.assertIsNone(candidate)

    def test_three_attempts_have_distinct_immutable_archives_and_bounded_backoff(self):
        gate = Mock()
        record, transport, sleep = self.collect([TimeoutError("first"), TimeoutError("second"), TimeoutError("third")],
                                              before_attempt=gate)
        self.assertEqual(transport.call_count, 3)
        self.assertEqual(gate.call_count, 3)
        self.assertEqual(sleep.call_args_list, [call(30), call(120)])
        self.assertEqual(record["status"], "INFRA_REQUEUE")
        self.assertEqual(record["attempt_count"], 3)
        self.assertTrue(record["retry_exhausted"])
        self.assertEqual(record["retry_after_seconds"], 300)
        self.assertEqual(len(record["attempts"]), 3)
        self.assertEqual([load_json(self.output / f"collected/attempts/{i:03d}/provider.json")["error_message"]
                          for i in range(1, 4)], ["first", "second", "third"])
        for pin in record["attempts"]:
            self.assertEqual(binding(pin["path"]), pin)
        before = {str(path): path.read_bytes() for path in (self.output / "collected").rglob("*.json")}
        with self.assertRaises(ValueError):
            self.collect([self.response])
        self.assertEqual(before, {str(path): path.read_bytes() for path in (self.output / "collected").rglob("*.json")})

    def test_success_stops_retries_but_keeps_failure_attempt(self):
        record, transport, sleep = self.collect([TimeoutError(), self.response])
        self.assertEqual(record["status"], "AWAITING_INDEPENDENT_GROUNDED_REVIEW")
        self.assertEqual(transport.call_count, 2)
        self.assertEqual(sleep.call_args_list, [call(30)])
        self.assertEqual(record["attempt_count"], 2)
        self.assertEqual(load_json(self.output / "collected/attempts/001/decision.json")["status"], "INFRA_REQUEUE")
        self.assertFalse(load_json(record["candidate"]["path"])["training_eligible"])

    def test_merit_rejection_makes_one_attempt(self):
        record, transport, sleep = self.collect([{**self.response, "finish_reason": "MAX_TOKENS"}])
        self.assertEqual(record["status"], "REJECTED")
        self.assertEqual(transport.call_count, 1)
        sleep.assert_not_called()

    def test_invalid_attempt_limits_fail_before_transport(self):
        for maximum in (0, 4, -1, True, 1.5):
            with self.subTest(maximum=maximum), self.assertRaises(ValueError):
                self.collect([self.response], max_attempts=maximum)

    def test_retry_after_is_honored_or_deferred_without_a_long_automatic_sleep(self):
        record, transport, sleep = self.collect([ServerError(headers={"Retry-After": "301"})])
        self.assertEqual(record["status"], "INFRA_REQUEUE")
        self.assertTrue(record["retry_deferred"])
        self.assertEqual(record["retry_after_seconds"], 301)
        self.assertEqual(transport.call_count, 1)
        sleep.assert_not_called()
        now = datetime(2026, 9, 18, tzinfo=timezone.utc)
        self.assertEqual(conversion.retry_delay_seconds({"retry_after": "Fri, 18 Sep 2026 00:02:00 GMT"}, 1, now), 120)
        self.assertEqual(conversion.retry_delay_seconds({"retry_after": "nonsense"}, 1, now), 30)
        self.assertEqual(conversion.retry_delay_seconds({"retry_after": "42"}, 1, now), 42)

    def test_expired_retry_lease_stops_before_another_provider_call(self):
        gate = Mock(side_effect=[None, ValueError("expired fixture lease")])
        with self.assertRaisesRegex(ValueError, "expired fixture lease"):
            self.collect([TimeoutError()], before_attempt=gate)
        self.assertTrue((self.output / "collected/attempts/001/provider.json").is_file())
        self.assertTrue((self.output / "collected/attempts/001/decision.json").is_file())
        self.assertFalse((self.output / "collected/attempts/002/started.json").exists())


class RequestBoundaryTests(ConverterFixture):
    def test_request_projection_cannot_reach_labels_scoring_or_correctness(self):
        content = [{"type": "thinking", "thinking": self.text}]
        message = {"provenance": "provider", "content": content, "tool_calls": [], "response_metadata": {},
                   "raw_response": {"content": content, "tool_calls": [], "response_metadata": {}}}
        raw = {"trace": [message], "ground_truth": "FORBIDDEN_LABEL", "is_correct": True, "results": {"score": "FORBIDDEN_SCORE"}}
        row = {"qid": "1", "sources": {}, "source_video": {}, "video_timing": {},
               "student_input": {"question": self.payload["question"], "options": [], "frame_indices": list(range(32)),
                                 "timestamps": list(range(32)), "fps": 1, "total_num_frames": 32},
               "native_answer_archive": {"native_final": "<ANSWER>fixture</ANSWER>", "message_index": 0}}
        packet = {"qid": "1", "sources": {}, "source_video": {}, "video_timing": {}, "student_input": row["student_input"],
                  "rendering": self.text, "numeric_tool_evidence": [],
                  "spans": [{"pointer": "/trace/0/content/0/thinking", "start": 0, "end": len(self.text),
                             "sha256": hashlib.sha256(self.text.encode()).hexdigest(), "message_index": 0,
                             "kind": "provider_thought_summary"}]}
        with patch.object(conversion, "source_candidate", return_value=(row, {}, {}, raw)), \
                patch.object(admission, "resolve_answer_key", side_effect=AssertionError("label access")), \
                patch.object(admission, "load_scorer", side_effect=AssertionError("scorer access")), \
                patch.object(conversion, "load_json", side_effect=AssertionError("unexpected file read")):
            first = conversion.prepare_packet(packet, "v1")["request"]
            row.update(ground_truth="FORBIDDEN_LABEL", is_correct=False, score="FORBIDDEN_SCORE")
            packet.update(ground_truth="FORBIDDEN_LABEL", offline={"fully_correct": False})
            second = conversion.prepare_packet(packet, "v1")["request"]
        self.assertEqual(first, second)
        self.assertNotIn("FORBIDDEN", json.dumps(second))
        payload = json.loads(second["contents"][0]["parts"][0]["text"])
        self.assertEqual(set(payload), {"question", "options", "native_final_provenance", "frame_metadata", "evidence"})


class RedecisionTests(ConverterFixture):
    def make_run(self, provider_sha=None):
        run = self.output / "run"
        immutable_fixture(run / "run.json", {"schema": "grounded-conversion-run-v1", "job": {"path": "/never/read/job.json", "sha256": "0" * 64}})
        directory = run / "1"
        immutable_fixture(directory / "request.json", self.context["request"])
        immutable_fixture(directory / "provider.json", self.response)
        immutable_fixture(directory / "started.json", {"request_sha256": self.context["request_sha256"], "started_at": "2026-09-18T00:00:00+00:00"})
        provider_pin = binding(directory / "provider.json")
        if provider_sha is not None:
            provider_pin["sha256"] = provider_sha
        immutable_fixture(directory / "decision.json", {"qid": "1", "request": binding(directory / "request.json"),
                          "request_sha256": self.context["request_sha256"], "provider": provider_pin,
                          "sources": {}, "status": "REJECTED", "training_eligible": False})
        return run

    def test_idempotent_sidecars_do_not_call_provider_or_load_external_authorities(self):
        from student_pilot.redecision import redecide
        run = self.make_run()
        originals = {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in run.rglob("*.json")}
        output = self.output / "summary.json"
        with patch.object(conversion, "native_transport", side_effect=AssertionError("network forbidden")), \
                patch.object(conversion, "load_job", side_effect=AssertionError("external authority forbidden")):
            first = redecide(run, output)
            sidecars = {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in run.rglob("*.json")}
            second = redecide(run, output)
        self.assertEqual(first, second)
        self.assertEqual(sidecars, {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in run.rglob("*.json")})
        for path, content in originals.items():
            self.assertEqual((Path(path).read_bytes(), Path(path).stat().st_mtime_ns), content)
        self.assertEqual(first["counts"], {"AWAITING_INDEPENDENT_GROUNDED_REVIEW": 1})
        self.assertEqual(first["provider_calls"], 0)
        self.assertFalse(first["training_eligible"])
        self.assertFalse(first["source_authorities_revalidated"])

    def test_changed_archive_fails_closed_and_does_not_create_sidecar(self):
        from student_pilot.redecision import redecide
        run = self.make_run(provider_sha="0" * 64)
        actual = conversion.response_decision
        with patch.object(conversion, "response_decision", wraps=actual) as decide, self.assertRaisesRegex(ValueError, "Hash mismatch"):
            redecide(run, self.output / "summary.json")
        decide.assert_not_called()
        self.assertEqual(sorted(path.name for path in (run / "1").iterdir()),
                         ["decision.json", "provider.json", "request.json", "started.json"])

    def test_sidecar_conflict_refuses_all_writes(self):
        from student_pilot.redecision import redecide
        run = self.make_run()
        conflict = run / "1/decision.redecision.envelope-infra-v1.json"
        immutable_fixture(conflict, {"different": True})
        before = conflict.read_bytes()
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            redecide(run, self.output / "summary.json")
        self.assertEqual(conflict.read_bytes(), before)
        self.assertFalse((run / "1/candidate.redecision.envelope-infra-v1.json").exists())
        self.assertFalse((self.output / "summary.json").exists())

    def test_real_3919_envelope_passes_but_unchanged_claim_identity_gate_rejects(self):
        run = Path(os.environ["STUDENT_PILOT_ARCHIVED_RUN"])
        response = load_json(run / "3919/provider.json")
        request = load_json(run / "3919/request.json")
        payload = json.loads(request["contents"][0]["parts"][0]["text"])
        document = json.loads(response["content"])
        self.assertEqual(conversion.answer_body(document["answer"]), conversion.answer_body(payload["native_final_provenance"]))
        self.assertEqual([claim["id"] for claim in document["claims"]], ["claim_1", "claim_2"])
        with self.assertRaisesRegex(ValueError, "Claim identity"):
            v1_validate_response(response, payload)


class RetryAdmissionTests(ConverterFixture):
    def job_and_lease(self, maximum=3):
        context_path = self.output / "context.json"
        immutable_fixture(context_path, self.context)
        job = {"schema": "grounded-conversion-job-v1", "model": conversion.MODEL, "settings": conversion.SETTINGS,
               "phase": "first3", "selected_qids": ["1"], "contexts": [{"qid": "1", "context": binding(context_path)}],
               "paid_calls_maximum": 3, "retry_policy": conversion.RETRY_POLICY,
               "bindings": {}, "audited_packets": {}, "audited_pool_qids": ["1"]}
        job_path = self.output / "job.json"
        immutable_fixture(job_path, job)
        supervisor = immutable_fixture(self.output / "supervisor.json", {"fixture_only": True})
        now = datetime.now(timezone.utc)
        lease = {"schema": "student-conversion-api-lease-v1", "job": binding(job_path),
                 "coordination_lease_passed": True, "collector_handshake_passed": True, "no_other_paid_calls": True,
                 "annotation_workers": 1, "concurrency_cap": 1, "model": conversion.MODEL, "max_calls": maximum,
                 "owner": "offline-fixture", "work_id": "offline-fixture", "coordination_lease_evidence": "fixture-only",
                 "collector_handshake_evidence": "fixture-only", "supervisor_status": binding(supervisor),
                 "admitted_at": now.isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat()}
        lease_path = immutable_fixture(self.output / "lease.json", lease)
        return job, job_path, lease_path

    def test_run_rechecks_real_lease_each_attempt_and_never_counts_infra_as_merit(self):
        job, job_path, lease_path = self.job_and_lease()
        output = self.output / "run"
        with patch.object(conversion, "REPO", self.output), \
                patch.object(conversion, "ARTIFACTS", self.output / "artifacts"), \
                patch.object(conversion, "load_job", return_value=job), \
                patch.object(conversion, "runtime_bindings", return_value=[]), \
                patch.object(conversion, "write_once", side_effect=immutable_fixture), \
                patch.object(conversion, "require_api_lease", wraps=conversion.require_api_lease) as lease, \
                patch.object(conversion, "native_transport", side_effect=TimeoutError("fixture timeout")) as transport, \
                patch("time.sleep"):
            result = conversion.run(job_path, output, lease_path)
            self.assertEqual(lease.call_count, 4)
            self.assertTrue(all(item.args[2] == 3 for item in lease.call_args_list))
            self.assertEqual(transport.call_count, 3)
            self.assertEqual(result["deterministic_candidates"], 0)
            summary = load_json(output / "summary.json")
            self.assertEqual(summary["provider_attempts"], 3)
            self.assertEqual(summary["counts"], {"INFRA_REQUEUE": 1})
            review = load_json(output / "review_bundle.json")["review_template"]
            self.assertEqual(review["decisions"][0]["verdict"], "requeue")
            review.update(reviewer="offline-fixture-only", independent_of_converter=True, rollout_allowed=True)
            review_path = immutable_fixture(self.output / "review.json", review)
            manifest = conversion.accepted_manifest(output, review_path)
            self.assertEqual(manifest["rejected_qids"], [])
            self.assertEqual(manifest["infra_requeue_qids"], ["1"])
            self.assertEqual(manifest["accepted_count"], 0)
            self.assertFalse(manifest["rollout_allowed"])
            for verdict in ("accept", "reject"):
                review["decisions"][0]["verdict"] = verdict
                invalid = immutable_fixture(self.output / (verdict + ".json"), review)
                with self.assertRaisesRegex(ValueError, "infrastructure failures"):
                    conversion.accepted_manifest(output, invalid)

    def test_old_lease_budget_refuses_before_any_transport(self):
        job, job_path, lease_path = self.job_and_lease(maximum=1)
        with patch.object(conversion, "load_job", return_value=job), \
                patch.object(conversion, "native_transport") as transport, self.assertRaisesRegex(ValueError, "bounded call count"):
            conversion.run(job_path, self.output / "run", lease_path)
        transport.assert_not_called()
        self.assertFalse((self.output / "run").exists())

    def test_old_job_requires_reviewed_retry_budget_before_source_access(self):
        job, _, _ = self.job_and_lease()
        for index, updates in enumerate(({"paid_calls_maximum": 1}, {"retry_policy": None})):
            path = immutable_fixture(self.output / f"old_job_{index}.json", {**job, **updates})
            with patch.object(conversion, "load_pool") as pool, self.assertRaisesRegex(ValueError, "independently review"):
                conversion.load_job(path)
            pool.assert_not_called()


if __name__ == "__main__":
    unittest.main()
