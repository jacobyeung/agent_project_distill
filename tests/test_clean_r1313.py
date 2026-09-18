import copy
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from clean_r1313_fixture import Fixture, document, response_for
from student_pilot import clean_conversion as converter
from student_pilot import clean_source
from student_pilot.common import digest_json


class SelectionTests(unittest.TestCase):
    def test_string_qids_keep_their_identity_and_lexical_order(self):
        self.assertEqual(clean_source.select_qids(["vsi590k_2", "vsi590k_10", "vsi590k_0001"], 2),
                         ["vsi590k_0001", "vsi590k_10"])

    def test_benchmark_and_duplicate_ids_are_rejected(self):
        for qids in (["3919"], ["vsi590k_01", "vsi590k_01"]):
            with self.assertRaises(ValueError):
                clean_source.select_qids(qids, 1)

    def test_invalid_selection_counts_are_rejected(self):
        for count in (0, -1, 2, True):
            with self.assertRaises(ValueError):
                clean_source.select_qids(["vsi590k_0001"], count)


class SourceTests(unittest.TestCase):
    def test_recovered_provider_failure_keeps_complete_attempt_census(self):
        fixture = Fixture(recovered_provider_error=True)
        snapshot = clean_source.load_snapshot(fixture.workspace, fixture.freeze()["path"])
        self.assertTrue(snapshot["rows"][0]["archive"]["complete"])
        self.assertTrue(snapshot["runnable"])

    def test_accepted_snapshot_binds_original_pixels_and_all_source_authorities(self):
        fixture = Fixture()
        snapshot = clean_source.load_snapshot(fixture.workspace, fixture.freeze()["path"])
        row = snapshot["rows"][0]
        self.assertTrue(snapshot["runnable"])
        self.assertTrue(row["membership_verified"])
        self.assertEqual(row["status"], "ready")
        self.assertEqual(len(row["media"]["frame_proofs"]), 32)
        self.assertTrue(all(p["exact_vsi_pixels"] for p in row["media"]["frame_proofs"]))
        self.assertEqual(set(row["authority"]), {"source_contract", "collection_config", "scene_receipt", "scene_registry"})
        self.assertEqual(set(row["sources"]), {"raw", "clean", "attempt"})
        self.assertTrue(row["archive"]["complete"])
        self.assertFalse(snapshot["benchmark_trained_diagnostic"])
        self.assertFalse(snapshot["training_eligible"])

    def test_wrong_scene_pixels_fail_even_when_all_recorded_frame_hashes_agree(self):
        fixture = Fixture(wrong_pixels=True)
        with self.assertRaisesRegex(ValueError, "Cross-scene frame mismatch"):
            fixture.freeze()

    def test_directory_scene_discrepancy_can_only_pass_with_pixel_proof(self):
        fixture = Fixture(frame_scene="different_scene")
        snapshot = clean_source.load_snapshot(fixture.workspace, fixture.freeze()["path"])
        media = snapshot["rows"][0]["media"]
        self.assertTrue(media["frame_path_discrepancy"])
        self.assertTrue(media["path_discrepancy_resolved_by_pixels"])
        self.assertEqual(len(media["frame_proofs"]), 32)

    def test_incorrect_frame_dimensions_fail(self):
        with self.assertRaisesRegex(ValueError, "dimensions"):
            Fixture(wrong_dimensions=True).freeze()

    def test_raw_source_hash_drift_is_rejected_after_freezing(self):
        fixture = Fixture()
        snapshot = fixture.freeze()
        with fixture.raw_paths[fixture.qids[0]].open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "Source-hash drift"):
            clean_source.load_snapshot(fixture.workspace, snapshot["path"])

    def test_source_rgb_hash_drift_is_rejected_after_freezing(self):
        fixture = Fixture()
        snapshot = fixture.freeze()
        frozen = clean_source.load_snapshot(fixture.workspace, snapshot["path"])
        path = Path(frozen["rows"][0]["media"]["bindings"]["frames"][0]["path"])
        with path.open("ab") as stream:
            stream.write(b"drift")
        with self.assertRaisesRegex(ValueError, "Source-hash drift"):
            clean_source.load_snapshot(fixture.workspace, snapshot["path"])

    def test_acceptance_authority_disagreement_is_rejected(self):
        def corrupt(accepted, decisions):
            decisions[0]["accepted"] = False
        with self.assertRaisesRegex(ValueError, "Acceptance-authority"):
            Fixture(acceptance_patch=corrupt).freeze()

    def test_successful_terminal_is_not_sufficient_acceptance_authority(self):
        def corrupt(accepted, decisions):
            accepted[0]["answer_correct"] = False
            decisions[0]["answer_correct"] = False
        with self.assertRaisesRegex(ValueError, "accepted-source authority"):
            Fixture(acceptance_patch=corrupt).freeze()

    def test_acceptance_does_not_override_foreign_terminal_identity(self):
        with self.assertRaisesRegex(ValueError, "terminal mismatch"):
            Fixture(terminal_patch=lambda terminal: terminal.update(question_id="vsi590k_999999")).freeze()

    def test_membership_projection_rejects_extra_fields(self):
        with self.assertRaisesRegex(ValueError, "Answer-free membership"):
            Fixture(source_patch=lambda rows: rows[0].update(unexpected_metadata=True)).freeze()

    def test_missing_membership_is_explicit_and_never_runnable(self):
        fixture = Fixture()
        frozen = fixture.freeze(allow_missing=True, membership=False)
        snapshot = clean_source.load_snapshot(fixture.workspace, frozen["path"], require_ready=False)
        self.assertFalse(snapshot["runnable"])
        self.assertEqual(snapshot["rows"][0]["status"], "requires_source_media")
        with self.assertRaisesRegex(ValueError, "requires_source_media"):
            clean_source.load_snapshot(fixture.workspace, frozen["path"])

    def test_missing_pixels_are_explicit_even_when_metadata_and_hashes_match(self):
        fixture = Fixture(frame_scene="different_scene")
        scene = clean_source.read_json(fixture.workspace, fixture.scene_pin["path"])
        mapping = fixture.save(fixture.root / "map.json", {"schema": "clean-vsi590k-source-map-v1", "files": {
                               scene["frames"][0]["path"]: str(fixture.root / "not_staged.png")}})
        frozen = clean_source.freeze(fixture.workspace, fixture.run_root, fixture.census, fixture.clean / "snapshot",
                                     fixture.membership, mapping["path"], allow_missing=True)
        snapshot = clean_source.load_snapshot(fixture.workspace, frozen["path"], require_ready=False)
        self.assertEqual(snapshot["rows"][0]["media"]["status"], "requires_source_media")
        self.assertFalse(snapshot["rows"][0]["media"]["pixels_verified"])
        self.assertTrue(snapshot["missing"])

    def test_raw_clean_native_final_disagreement_is_rejected(self):
        def corrupt(raw, clean, attempt):
            clean["trace"][-1]["content"][0]["text"] = "<ANSWER>B</ANSWER>"
            clean["trace"][-1]["raw_response"]["content"][0]["text"] = "<ANSWER>B</ANSWER>"
        with self.assertRaisesRegex(ValueError, "native-final"):
            Fixture(trace_patch=corrupt).freeze()

    def test_missing_source_usage_is_rejected(self):
        def corrupt(raw, clean, attempt):
            for entry in (raw, clean):
                entry["trace"][-1].pop("usage_metadata")
                entry["trace"][-1]["raw_response"].pop("usage_metadata")
        with self.assertRaisesRegex(ValueError, "Missing native source telemetry"):
            Fixture(trace_patch=corrupt).freeze()

    def test_source_output_cap_is_rejected(self):
        def corrupt(raw, clean, attempt):
            for entry in (raw, clean):
                entry["trace"][-1]["response_metadata"]["finish_reason"] = "MAX_TOKENS"
                entry["trace"][-1]["raw_response"]["response_metadata"]["finish_reason"] = "MAX_TOKENS"
        with self.assertRaisesRegex(ValueError, "Capped"):
            Fixture(trace_patch=corrupt).freeze()

    def test_foreign_source_scene_is_rejected(self):
        def corrupt(raw, clean, attempt):
            raw["scene_name"] = clean["scene_name"] = "scannetppv2__different_scene"
        with self.assertRaisesRegex(ValueError, "physical scene"):
            Fixture(trace_patch=corrupt).freeze()

    def test_outside_source_mapping_is_refused_before_any_external_open(self):
        fixture = Fixture()
        with self.assertRaisesRegex(ValueError, "outside"):
            clean_source.SourceStore(fixture.workspace, fixture.run_root, fixture.run_root,
                                    {"untrusted": "/data2/not-authorized-by-this-fixture.json"})

    def test_fps_timestamps_ordinals_frame_count_and_source_video_identity_fail_closed(self):
        from student_pilot.clean_media import validate_media
        fixture = Fixture()
        original = clean_source.read_json(fixture.workspace, fixture.scene_pin["path"])
        mutations = {
            "fps": lambda scene: scene["video"].update(fps=0),
            "timestamp": lambda scene: scene["frames"][1].update(timestamp_sec=987),
            "ordinal": lambda scene: scene["frames"][1].update(ordinal=0),
            "frame_count": lambda scene: scene["frames"].pop(),
            "video_scene": lambda scene: scene["video"].update(path="/not-opened/scannetppv2/other.mkv"),
            "physical_scene": lambda scene: scene.update(runtime_scene_id="scannetppv2__other"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                scene = copy.deepcopy(original)
                mutate(scene)
                receipt = {"student_inputs": {"frames": scene["frames"]}}
                store = clean_source.SourceStore(fixture.workspace, fixture.run_root, fixture.run_root)
                with self.assertRaises(ValueError):
                    validate_media(store, fixture.rows[0], receipt, scene)

    def test_unreceived_perceptual_evidence_cannot_satisfy_acceptance(self):
        def corrupt(accepted, decisions):
            for rows in (accepted, decisions):
                rows[0]["perceptual_evidence"][0]["tool_call_id"] = "not-a-source-call"
        with self.assertRaisesRegex(ValueError, "perceptual evidence"):
            Fixture(acceptance_patch=corrupt).freeze()

    def test_snapshot_content_cannot_drift_independently_of_bound_sources(self):
        fixture = Fixture()
        frozen = fixture.freeze()
        snapshot = clean_source.read_json(fixture.workspace, frozen["path"])
        snapshot["rows"][0]["media"]["frame_indices"][0] = 7
        changed = fixture.save(fixture.clean / "changed_snapshot.json", snapshot)
        with self.assertRaisesRegex(ValueError, "snapshot content drift"):
            clean_source.load_snapshot(fixture.workspace, changed["path"])


class ResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Fixture()
        cls.prepared = cls.fixture.prepare()
        cls.job, cls.snapshot = converter.load_job(cls.fixture.workspace, cls.prepared["job"]["path"])
        cls.context = clean_source.read_json(cls.fixture.workspace, cls.job["contexts"][0]["context"]["path"])

    def test_same_request_builder_prompt_model_and_budget(self):
        self.assertEqual(self.context["request"], converter.conversion.make_request(self.context["payload"]))
        self.assertEqual(self.context["request"]["config"]["max_output_tokens"], 32768)
        self.assertEqual(self.context["request"]["config"]["thinking_config"]["thinking_level"], "HIGH")
        self.assertTrue(converter.request_boundary(self.context["request"])["verified"])

    def test_complete_native_response_and_byte_identical_answer_are_supported(self):
        result = converter.validate_response(response_for(self.context["request"]), self.context["payload"])
        self.assertTrue(result["native_final_agreement"])
        self.assertTrue(result["target"].endswith("<answer>A</answer>"))
        self.assertFalse(result["training_eligible"])
        self.assertFalse(result["semantic_grounding_verified"])

    def test_answer_whitespace_is_preserved_not_normalized(self):
        payload = copy.deepcopy(self.context["payload"])
        payload["native_final_provenance"] = "<ANSWER> A \n</ANSWER>"
        result = converter.validate_response(response_for(converter.conversion.make_request(payload)), payload)
        self.assertEqual(result["answer"], " A \n")
        self.assertTrue(result["target"].endswith("<answer> A \n</answer>"))

    def test_changed_answer_is_rejected(self):
        value = document(self.context["payload"])
        value["answer"] = "B"
        with self.assertRaisesRegex(ValueError, "verbatim"):
            converter.conversion.validate_document(value, self.context["payload"])

    def test_missing_exposed_thoughts_are_rejected(self):
        response = response_for(self.context["request"])
        response.pop("thoughts")
        with self.assertRaisesRegex(ValueError, "thoughts"):
            converter.validate_response(response, self.context["payload"])

    def test_missing_usage_is_rejected(self):
        response = response_for(self.context["request"])
        response["usage"] = None
        with self.assertRaisesRegex(ValueError, "telemetry"):
            converter.validate_response(response, self.context["payload"])

    def test_native_cap_cannot_be_hidden_by_stop_in_flattened_metadata(self):
        response = response_for(self.context["request"])
        response["raw_response"][0]["candidates"][0]["finish_reason"] = "MAX_TOKENS"
        with self.assertRaisesRegex(ValueError, "Capped"):
            converter.validate_response(response, self.context["payload"])

    def test_missing_native_call_events_are_rejected(self):
        response = response_for(self.context["request"])
        response["events"] = []
        with self.assertRaisesRegex(ValueError, "call telemetry"):
            converter.validate_response(response, self.context["payload"])

    def test_response_text_must_agree_with_the_native_sdk_response(self):
        response = response_for(self.context["request"])
        response["content"] += " "
        with self.assertRaisesRegex(ValueError, "Native content"):
            converter.validate_response(response, self.context["payload"])

    def test_numeric_invention_and_invalid_spans_are_rejected(self):
        for mutation in ("number", "span"):
            value = document(self.context["payload"])
            if mutation == "number":
                value["explanation"][0]["claims"][0]["text"] += " The separation is 913 meters."
            else:
                value["explanation"][0]["claims"][0]["citations"][0]["quote"] += " not archived"
            with self.assertRaises(ValueError):
                converter.conversion.validate_document(value, self.context["payload"])

    def test_native_final_is_not_explanatory_evidence(self):
        value = document(self.context["payload"])
        value["explanation"][0]["claims"][0]["citations"][0]["evidence_id"] = "native-final"
        with self.assertRaises(ValueError):
            converter.conversion.validate_document(value, self.context["payload"])

    def test_accidental_label_scoring_or_correctness_keys_never_cross_request_boundary(self):
        for key in ("label", "ground_truth", "score", "is_correct", "answer_correct"):
            payload = copy.deepcopy(self.context["payload"])
            payload[key] = "OFFLINE_SELECTION_SENTINEL"
            with self.assertRaises(ValueError):
                converter.request_boundary(converter.conversion.make_request(payload))

    def test_selection_metadata_serialized_inside_evidence_text_is_rejected(self):
        payload = copy.deepcopy(self.context["payload"])
        item = payload["evidence"][0]
        item["text"] = '{"is_correct": true, "score": 1}'
        item["text_sha256"] = converter.hashlib.sha256(item["text"].encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "Serialized"):
            converter.request_boundary(converter.conversion.make_request(payload))

    def test_label_alias_values_are_rejected_in_copied_text_with_exact_locations(self):
        aliases = ("ground_truth_answer", "correct_answer", "gt_answer", "answer_label", "is_correct",
                   "correctness", "score", "evaluation_qid", "eval_qid", "label")
        for alias in aliases:
            for separator in ("_", "-", " "):
                for assignment in (": SENTINEL", "=SENTINEL", " is SENTINEL", "/SENTINEL"):
                    with self.subTest(alias=alias, separator=separator, assignment=assignment):
                        payload = copy.deepcopy(self.context["payload"])
                        item = payload["evidence"][3]
                        item["text"] = "Observation. " + alias.replace("_", separator).upper() + assignment
                        item["text_sha256"] = converter.hashlib.sha256(item["text"].encode()).hexdigest()
                        with self.assertRaisesRegex(ValueError, "label_alias_in_request") as caught:
                            converter.request_boundary(converter.conversion.make_request(payload))
                        self.assertEqual(caught.exception.evidence_id, item["id"])
                        self.assertEqual(caught.exception.offset, len("Observation. "))

    def test_label_alias_keys_are_rejected_recursively_before_schema_checks(self):
        for key in ("Ground Truth Answer", "CORRECT-ANSWER", "GT ANSWER", "Answer_Label", "IS-CORRECT",
                    "Correctness", "SCORE", "Evaluation Qid", "EVAL-QID", "Label"):
            with self.subTest(key=key):
                request = copy.deepcopy(self.context["request"])
                payload = json.loads(request["contents"][0]["parts"][0]["text"])
                item = payload["evidence"][3]
                item["metadata"] = [{key: "SENTINEL"}]
                request["contents"][0]["parts"][0]["text"] = json.dumps(payload)
                with self.assertRaisesRegex(ValueError, "label_alias_in_request") as caught:
                    converter.request_boundary(request)
                self.assertEqual(caught.exception.evidence_id, item["id"])
                self.assertEqual(caught.exception.offset, 0)
                self.assertIn("metadata", caught.exception.field_path)

    def test_all_allowlisted_source_string_channels_reject_alias_values(self):
        mutations = {
            "question": lambda p: p.update(question="correct answer: SENTINEL"),
            "option": lambda p: p["options"].append("EVAL QID=1506"),
            "native_final": lambda p: p.update(native_final_provenance="<ANSWER>answer-label: SENTINEL</ANSWER>"),
            "frame_metadata": lambda p: p["frame_metadata"].update(spatial_reference_policy="SCORE: 1"),
            "source_pointer": lambda p: p["evidence"][3].update(source_pointer="/trace/evaluation_qid/1506"),
            "tool_call_id": lambda p: p["evidence"][3].update(tool_call_id="LABEL: SENTINEL"),
        }
        for channel, mutate in mutations.items():
            with self.subTest(channel=channel):
                payload = copy.deepcopy(self.context["payload"])
                mutate(payload)
                with self.assertRaisesRegex(ValueError, "label_alias_in_request"):
                    converter.request_boundary(converter.conversion.make_request(payload))

    def test_mixed_separators_escaped_fields_and_unicode_offsets_are_rejected(self):
        for value in ('GrOuNd-_ TrUtH--AnSwEr: SENTINEL', r'\"correct_answer\": \"SENTINEL\"',
                      'label "SENTINEL"', 'correctness true', 'score 0.9'):
            with self.subTest(value=value):
                payload = copy.deepcopy(self.context["payload"])
                item = payload["evidence"][3]
                item["text"] = "π: " + value
                item["text_sha256"] = converter.hashlib.sha256(item["text"].encode()).hexdigest()
                with self.assertRaisesRegex(ValueError, "label_alias_in_request") as caught:
                    converter.request_boundary(converter.conversion.make_request(payload))
                self.assertEqual(caught.exception.evidence_id, item["id"])
                self.assertEqual(caught.exception.offset, 3 + value.index("correct_answer") if "correct_answer" in value else 3)
                self.assertEqual(caught.exception.offset_units, "unicode_code_points")

    def test_bare_mentions_and_non_alias_words_are_not_contamination(self):
        for text in ("Discuss the label and correctness without assigning either.",
                     "The scoreboard and ground_truth_answers are not field aliases.",
                     "The ground-truth-answer field is absent; no value is supplied.",
                     "The score-free geometric observation follows the reference direction."):
            with self.subTest(text=text):
                payload = copy.deepcopy(self.context["payload"])
                item = payload["evidence"][3]
                item["text"] = text
                item["text_sha256"] = converter.hashlib.sha256(text.encode()).hexdigest()
                self.assertTrue(converter.request_boundary(converter.conversion.make_request(payload))["verified"])

    def test_offline_label_paths_are_rejected_inside_evidence(self):
        payload = copy.deepcopy(self.context["payload"])
        item = payload["evidence"][3]
        item["text"] = "See offline_labels/v2/answers.json"
        item["text_sha256"] = converter.hashlib.sha256(item["text"].encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "label_alias_in_request") as caught:
            converter.request_boundary(converter.conversion.make_request(payload))
        self.assertEqual(caught.exception.evidence_id, item["id"])
        self.assertEqual(caught.exception.offset, 4)

    def test_contaminated_native_thought_argument_and_tool_result_cannot_prepare(self):
        for channel in ("thought", "argument", "tool_result"):
            with self.subTest(channel=channel):
                def contaminate(raw, clean, attempt):
                    for entry in (raw, clean):
                        if channel == "tool_result":
                            entry["trace"][1]["content"] = "Evaluation Qid: 1506"
                        else:
                            message = entry["trace"][0]
                            for native in (message, message["raw_response"]):
                                if channel == "thought":
                                    native["content"][0]["thinking"] = "Ground Truth Answer: SENTINEL"
                                else:
                                    native["tool_calls"][0]["args"]["execution_summary"] = "CORRECT-ANSWER: SENTINEL"
                fixture = Fixture(trace_patch=contaminate)
                with patch.object(converter, "native_transport", side_effect=AssertionError("provider reached")) as transport:
                    with self.assertRaisesRegex(ValueError, "label_alias_in_request"):
                        fixture.prepare()
                transport.assert_not_called()

    def test_top_level_trace_predictions_and_selection_fields_are_not_projected(self):
        source = self.snapshot["rows"][0]
        self.assertNotIn("IGNORED_PREDICTION", json.dumps(self.context["request"]))
        self.assertNotIn("acceptance_record_sha256", json.dumps(self.context["request"]))
        self.assertEqual(self.context["source_row_sha256"], digest_json(source))

    def test_diagnostic_job_loader_refuses_clean_job_before_loading_diagnostic_authorities(self):
        with patch.object(converter.conversion, "load_pool", side_effect=AssertionError("diagnostic authority access")):
            with self.assertRaisesRegex(ValueError, "contract changed"):
                converter.conversion.load_job(self.prepared["job"]["path"])


class AdmissionTests(unittest.TestCase):
    def run_fixture(self, qids=None, transport=None):
        fixture = Fixture(qids=qids)
        prepared = fixture.prepare()
        lease = fixture.lease(prepared["job"])
        output = fixture.clean / "runs/one"
        with patch.object(converter, "native_transport", side_effect=transport or (lambda request, telemetry: response_for(request))) as mock:
            converter.run(fixture.workspace, prepared["job"]["path"], lease["path"], output)
        self.assertEqual(mock.call_count, len(fixture.qids))
        return fixture, prepared, lease, output

    def test_only_individually_reviewed_passed_examples_enter_immutable_admission(self):
        fixture, _, _, output = self.run_fixture(["vsi590k_2", "vsi590k_10", "vsi590k_0001"])
        review = fixture.review(output, qids=["vsi590k_0001"])
        index = converter.admit(fixture.workspace, output, review["path"], fixture.clean / "admissions/one")
        manifest = converter.load_admitted(fixture.workspace, index["path"])
        self.assertEqual(manifest["accepted_count"], 1)
        self.assertEqual(manifest["unreviewed_qids"], ["vsi590k_10", "vsi590k_2"])
        self.assertTrue(manifest["clean_vsi590k_training"])
        self.assertFalse(manifest["benchmark_trained_diagnostic"])
        self.assertTrue(manifest["original_weights_required"])
        rows = converter.student_rows(fixture.workspace, index["path"], "OneThinker-8B", "original_weights")
        self.assertEqual(set(rows[0]), {"qid", "student_input", "target"})
        with self.assertRaisesRegex(ValueError, "original weights"):
            converter.student_rows(fixture.workspace, index["path"], "Qwen3.5-9B", "diagnostic_adapter")
        with self.assertRaisesRegex(ValueError, "actually accepted"):
            converter.conversion.load_accepted(Path(index["path"]).with_name("manifest.json"))

    def test_an_unsupported_independent_claim_verdict_blocks_admission(self):
        fixture, _, _, output = self.run_fixture()
        review = fixture.review(output, supported=False)
        with self.assertRaisesRegex(ValueError, "Every claim"):
            converter.admit(fixture.workspace, output, review["path"], fixture.clean / "admissions/unsupported")

    def test_converter_cannot_self_admit_an_independent_review(self):
        fixture, _, _, output = self.run_fixture()
        review = fixture.review(output, independent=False)
        with self.assertRaisesRegex(ValueError, "Independent claim"):
            converter.accepted_manifest(fixture.workspace, output, review["path"])

    def test_capped_native_outputs_are_archived_but_cannot_be_reviewed_into_training(self):
        def capped(request, telemetry):
            response = response_for(request)
            response["finish_reason"] = "MAX_TOKENS"
            return response
        fixture, _, _, output = self.run_fixture(transport=capped)
        record = clean_source.read_json(fixture.workspace, output / fixture.qids[0] / "decision.json")
        self.assertEqual(record["status"], "REJECTED")
        self.assertTrue(Path(record["provider"]["path"]).is_file())
        self.assertNotIn("candidate", record)
        review = fixture.review(output)
        with self.assertRaisesRegex(ValueError, "Unsupported, capped"):
            converter.accepted_manifest(fixture.workspace, output, review["path"])

    def test_missing_telemetry_stays_rejected_with_retained_request_and_response(self):
        def missing(request, telemetry):
            response = response_for(request)
            response.pop("thoughts")
            return response
        fixture, _, _, output = self.run_fixture(transport=missing)
        record = clean_source.read_json(fixture.workspace, output / fixture.qids[0] / "decision.json")
        self.assertEqual(record["status"], "REJECTED")
        for key in ("request", "provider", "started"):
            clean_source.verify_pin(fixture.workspace, record[key])

    def test_network_failure_is_archived_without_a_candidate_or_retry(self):
        fixture, _, _, output = self.run_fixture(transport=ConnectionError("synthetic"))
        record = clean_source.read_json(fixture.workspace, output / fixture.qids[0] / "decision.json")
        provider = clean_source.read_json(fixture.workspace, record["provider"]["path"])
        self.assertEqual(provider["error_type"], "ConnectionError")
        self.assertEqual(record["status"], "REJECTED")

    def test_once_consumed_job_cannot_be_replayed_into_another_run(self):
        fixture, prepared, lease, _ = self.run_fixture()
        with patch.object(converter, "native_transport", side_effect=AssertionError("must not call")) as mock:
            with self.assertRaises(FileExistsError):
                converter.run(fixture.workspace, prepared["job"]["path"], lease["path"], fixture.clean / "runs/two")
        mock.assert_not_called()

    def test_diagnostic_api_lease_is_refused(self):
        fixture = Fixture()
        prepared = fixture.prepare()
        lease = fixture.lease(prepared["job"])
        changed = clean_source.read_json(fixture.workspace, lease["path"])
        changed["schema"] = "student-conversion-api-lease-v1"
        foreign = fixture.save(fixture.clean / "leases/diagnostic.json", changed)
        with self.assertRaisesRegex(ValueError, "Clean API lease"):
            converter.require_api_lease(fixture.workspace, foreign["path"], prepared["job"]["path"], 1)

    def test_clean_api_lease_refuses_a_second_annotation_worker(self):
        fixture = Fixture()
        prepared = fixture.prepare()
        lease = fixture.lease(prepared["job"])
        changed = clean_source.read_json(fixture.workspace, lease["path"])
        changed.update(annotation_workers=2, concurrency_cap=2)
        foreign = fixture.save(fixture.clean / "leases/over-cap.json", changed)
        with self.assertRaisesRegex(ValueError, "Exactly one"):
            converter.require_api_lease(fixture.workspace, foreign["path"], prepared["job"]["path"], 1)

    def test_dry_run_never_authorizes_provider_calls(self):
        fixture = Fixture()
        prepared = fixture.prepare(dry_run=True)
        with patch.object(converter, "native_transport", side_effect=AssertionError("provider boundary reached")) as mock:
            with self.assertRaisesRegex(ValueError, "Dry-run"):
                converter.run(fixture.workspace, prepared["job"]["path"], fixture.clean / "not-created.json", fixture.clean / "runs/dry")
        mock.assert_not_called()

    def test_diagnostic_manifest_cannot_enter_clean_admission(self):
        fixture = Fixture()
        diagnostic = fixture.save(fixture.clean / "foreign/index.json", {"schema": "accepted-grounded-detailed-targets-v1", "rows": []})
        with self.assertRaisesRegex(ValueError, "Only clean-pool"):
            converter.load_admitted(fixture.workspace, diagnostic["path"])

    def test_outputs_outside_the_clean_namespace_are_refused(self):
        fixture = Fixture()
        with self.assertRaisesRegex(ValueError, "namespace"):
            clean_source.clean_path(fixture.workspace, fixture.root / "diagnostic/job.json")


class StagedSourceTests(unittest.TestCase):
    def test_strict_real_staged_inventory_includes_pilot_scene_path_discrepancy(self):
        staging = os.environ.get("R1313_STAGED_ROOT")
        if not staging:
            self.skipTest("requires_staged_r1313_fixture: set R1313_STAGED_ROOT to an authorized workspace copy")
        workspace = Path(os.environ["CLEAN_VSI590K_WORKSPACE"])
        staging = clean_source.local_path(workspace, staging)
        output = Path(os.environ["CLEAN_VSI590K_TEST_ROOT"]) / uuid4().hex / clean_source.POOL
        with self.assertRaises(clean_source.SnapshotIncomplete) as caught:
            clean_source.freeze(workspace, staging / "collector_gt_r1313", staging / "census_r1313/1789712349374075084",
                                output / "snapshot", strict=True)
        report = caught.exception.inventory
        pilot = next(row for row in report["frame_path_discrepancies"] if row["qid"] == "vsi590k_094586")
        self.assertEqual(pilot["physical_scene"], "scannetppv2__104acbf7d2")
        self.assertIn("scannetppv2__15b109bd584d", pilot["frames"][0]["source_path"])
        self.assertEqual(pilot["frames"][0]["sha256"], "5d97f7c03dc2b25a56ce8ed8811c2d9cd0ad41e4d2487c7c23460a282fb4aa60")
        self.assertTrue(any(item["source_path"] == pilot["frames"][0]["source_path"] and item["sha256"] == pilot["frames"][0]["sha256"]
                            for item in report["missing"]))
        self.assertFalse(report["runnable"])
        self.assertFalse((output / "snapshot/snapshot.json").exists())
        clean_source.write_json(workspace, output / "STRICT_STAGED_SOURCE_INVENTORY.json", report)

    def test_pinned_real_fixture_reports_requires_source_media_without_regrading(self):
        staging = os.environ.get("R1313_STAGED_ROOT")
        if not staging:
            self.skipTest("requires_staged_r1313_fixture: set R1313_STAGED_ROOT to the workspace copy")
        workspace = Path(os.environ["CLEAN_VSI590K_WORKSPACE"])
        staging = clean_source.local_path(workspace, staging)
        output = Path(os.environ["CLEAN_VSI590K_TEST_ROOT"]) / uuid4().hex / clean_source.POOL
        frozen = clean_source.freeze(workspace, staging / "collector_gt_r1313", staging / "census_r1313/1789712349374075084",
                                     output / "snapshot", allow_missing=True)
        snapshot = clean_source.load_snapshot(workspace, frozen["path"], require_ready=False)
        self.assertEqual(len(snapshot["accepted_qids"]), 14)
        self.assertFalse(snapshot["runnable"])
        real = snapshot["rows"][0]
        self.assertEqual(real["qid"], "vsi590k_094586")
        self.assertEqual(real["sources"]["raw"]["sha256"], "f29187785a7538729d439959603e20aa1fc462532ac94c5e83bd61c2a55066f5")
        self.assertEqual(real["status"], "requires_source_media")
        self.assertTrue(real["media"]["frame_path_discrepancy"])
        self.assertFalse(real["media"]["pixels_verified"])
        with patch.object(converter, "native_transport", side_effect=AssertionError("provider boundary reached")) as mock:
            result = converter.prepare(workspace, frozen["path"], output / "job", 14, dry_run=True)
        mock.assert_not_called()
        self.assertEqual(result["serialized_requests"], 1)
        check = clean_source.read_json(workspace, result["request_boundary"]["path"])
        self.assertEqual(len(check["unmaterialized_qids"]), 13)
        self.assertTrue(check["all_serialized_requests_checked"])
        self.assertEqual(check["provider_calls"], 0)


if __name__ == "__main__":
    unittest.main()
