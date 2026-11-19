import copy
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from student_pilot import diagnostic, diagnostic_data, provisional, provisional_data, storage
from student_pilot.benchmark_eval import contracts, frames, generate, prepare, score
from student_pilot.common import binding, canonical_bytes, digest_json, load_json
from student_pilot.students import get_student, training_parameters
from tests import test_provisional as fixtures
from tests import test_benchmark_eval as benchmark_fixtures


LABEL = fixtures.LABEL


class ProvisionalPipelineTests(unittest.TestCase):
    setUp = fixtures.ProvisionalTests.setUp
    document = fixtures.ProvisionalTests.document
    candidates = fixtures.ProvisionalTests.candidates
    index = fixtures.ProvisionalTests.index
    baseline_function = fixtures.ProvisionalTests.baseline_function

    def prepare_pool(self, student="onethinker"):
        index, _ = self.candidates()
        marker = self.document("checkpoint.json", {"synthetic": True})
        base = {"revision": get_student(student)["snapshot"].name, "files": [binding(marker)], "weight_shards": []}
        patches = [patch.object(diagnostic_data, "checkpoint_bindings", return_value=base),
                   patch.object(storage, "code_provenance", side_effect=lambda config: {
                       "commit": "c" * 40, "dirty": False, "config_sha256": digest_json(config)}),
                   patch.object(storage, "SCRATCH_HOME", self.root),
                   patch.object(storage, "PUBLISH_HOME", self.root / "published"),
                   patch.object(storage.shutil, "disk_usage", return_value=SimpleNamespace(free=2**50))]
        for item in patches:
            item.start()
        self.addCleanup(lambda: [item.stop() for item in reversed(patches)])
        self.protocol_path = self.root / "protocol.json"
        self.training_path = self.root / "training.json"
        self.heldout_path = self.root / "heldout.json"
        provisional_data.prepare_protocol(index, self.protocol_path, LABEL, student)
        self.protocol = provisional_data.load_protocol(self.protocol_path, LABEL)

        def encode(processor, row):
            return {}, {"qid": row["qid"], "frame_count": 32, "assistant_tokens_including_eos": 10, "prompt_tokens": 20}

        with patch("student_pilot.batches.load_processor", return_value=object()), \
                patch.object(diagnostic_data, "target_tokens", return_value=10), \
                patch.object(diagnostic_data, "encode_training", side_effect=encode):
            provisional_data.prepare_training(self.protocol_path, self.training_path, LABEL)
        provisional_data.prepare_heldout(self.protocol_path, self.heldout_path, LABEL)
        return student

    def published_adapter(self, student="onethinker"):
        self.prepare_pool(student)
        source, _ = benchmark_fixtures.synthetic_adapter(self.root, student)
        config = provisional.tag({"student": student, "PROVISIONAL_DIVISION_SHA": self.protocol["PROVISIONAL_DIVISION_SHA"]}, LABEL)
        store = storage.RunArtifacts(self.root / "training_run", config, self.root)
        name = provisional.adapter_directory(LABEL)
        adapter = store.root / name
        adapter.mkdir()
        pins = {}
        for key, filename in (("config", "adapter_config.json"), ("weights", "adapter_model.safetensors")):
            storage.copy_new(source / filename, adapter / filename, binding(source / filename)["sha256"])
            pins[key] = binding(adapter / filename)
        store.write(f"{name}/provenance.json", {"adapter": pins})
        store.write("steps/0001.json", {"step": 1})
        result = {"schema": "completed-provisional-diagnostic-training-v1", "status": "TRAINED", "student": student,
                  "synthetic": True, "base": self.protocol["base"], "base_sha256": self.protocol["base_sha256"],
                  "base_restart": "fresh_load_of_original_snapshot_no_smoke_adapter", "protocol": binding(self.protocol_path),
                  "training_manifest": binding(self.training_path), "adapter": pins,
                  "adapter_parameters": training_parameters(student), "realized": {"optimizer_steps": 1}}
        store.write("training_result.json", result)
        store.write("run.json", result)
        store.write("input_manifest.json", {"rows": load_json(self.training_path)["rows"]})
        self.training_run = store.root
        self.publish = self.root / "published" / "student"
        storage.finalize(store.root, self.publish, self.root, provisional_diagnostic=LABEL)
        return self.publish / name, self.publish / "PUBLISHED.json"

    def test_provisional_manifests_bind_requested_division_and_keep_holdout_answer_free(self):
        self.prepare_pool()
        training = provisional_data.load_training(self.training_path, LABEL)
        heldout = provisional_data.load_heldout(self.heldout_path, LABEL)
        self.assertEqual((len(training["rows"]), len(heldout["rows"])), (18, 2))
        for path in (self.protocol_path, self.training_path, self.heldout_path):
            value = load_json(path)
            self.assertEqual(value["PROVISIONAL_DIVISION_SHA"], digest_json(self.protocol["division"]))
            self.assertEqual(value["result_status"], "diagnostic, provisional")
            self.assertNotIn("DIVISION_SHA", value)
        for row in heldout["rows"]:
            self.assertEqual(set(row), {"qid", "dataset", "scene", "category", "student_input"})
        with patch.object(provisional_data, "source_rows", side_effect=AssertionError("Inference must not read targets")):
            self.assertEqual(provisional_data.load_heldout(self.heldout_path, LABEL), heldout)
        altered = copy.deepcopy(training)
        altered["rows"].append(provisional_data.source_rows(self.protocol, LABEL)[0])
        path = self.document("changed_training.json", altered)
        with self.assertRaises(ValueError):
            provisional_data.load_training(path, LABEL)
        for loader, path in ((diagnostic_data.load_training, self.training_path), (diagnostic_data.load_heldout, self.heldout_path)):
            with self.assertRaises(ValueError):
                loader(path)

    def test_heldout_scores_use_provisional_denominator_and_tag_every_row(self):
        self.prepare_pool()
        manifest = provisional_data.load_heldout(self.heldout_path, LABEL)
        run = self.root / "heldout_run"
        header = provisional.tag({"schema": "provisional-student-generation-run-v1", "variant": "original",
                                 "protocol": binding(self.protocol_path), "evaluation_manifest": binding(self.heldout_path),
                                 "PROVISIONAL_DIVISION_SHA": self.protocol["PROVISIONAL_DIVISION_SHA"],
                                 "base_sha256": self.protocol["base_sha256"], "attempt_qids": manifest["heldout_qids"],
                                 "cohort_size": 2, "generation": diagnostic_data.GENERATION,
                                 "output_budget": 16384, "retry_plan": None}, LABEL)
        self.document("heldout_run/run.json", header)
        row = manifest["rows"][0]
        trace = provisional.tag({"qid": row["qid"], "variant": "original", "run_sha256": digest_json(header),
                                "input_sha256": digest_json(row["student_input"]), "budget": 16384, "status": "ok",
                                "budget_terminal": False, "generation": {"generated_token_ids": [42, 10], "generated_tokens": 2,
                                "eos_token_ids": [10], "finish_reason": "STOP", "raw_decoded_text": "<answer>2</answer>"}}, LABEL)
        self.document(f"heldout_run/traces/{row['qid']}.json", trace)
        result = provisional_data.score_run(run, self.root / "heldout_score.json", LABEL)
        self.assertEqual(result["cohort_size"], 2)
        self.assertEqual(result["exact_match"], 0.5)
        self.assertEqual(result["per_question_type"]["object_counting"]["count"], 2)
        self.assertTrue(all(item["provisional_diagnostic"] == LABEL for item in result["rows"]))
        with self.assertRaises(ValueError):
            provisional_data.score_run(run, self.root / "wrong-label-score.json", provisional.LABELS[1])

    def test_publication_carries_label_and_both_clean_receipt_directions_refuse(self):
        adapter, receipt_path = self.published_adapter()
        receipt = load_json(receipt_path)
        self.assertEqual(receipt["schema"], "student-publication-v1")
        self.assertEqual(receipt["provisional_diagnostic"], LABEL)
        self.assertIn(LABEL, adapter.name)
        self.assertEqual(Path(receipt["training_result"]["path"]), self.publish / "training_result.json")
        self.assertEqual(Path(receipt["protocol"]["path"]), self.publish / "protocol.json")
        self.assertEqual(binding(self.publish / "division.json")["sha256"], receipt["PROVISIONAL_DIVISION_SHA"])
        for path in (adapter / "provenance.json", self.publish / "SHA256_MANIFEST.json", self.publish / "publication_provenance.json"):
            provisional.require_mode(load_json(path), LABEL)
        pin = contracts.validate_adapter("distilled", "onethinker", adapter, receipt_path, contracts.DEFAULT_CONFIG,
                                         allow_synthetic=True, provisional_diagnostic=LABEL)
        self.assertEqual(pin["tensor_count"], 6)
        with self.assertRaises(ValueError):
            contracts.validate_adapter("distilled", "onethinker", adapter, receipt_path, contracts.DEFAULT_CONFIG, allow_synthetic=True)
        clean_adapter, clean_receipt = benchmark_fixtures.synthetic_adapter(self.root)
        with self.assertRaisesRegex(ValueError, "clean"):
            contracts.validate_adapter("distilled", "onethinker", clean_adapter, clean_receipt, contracts.DEFAULT_CONFIG,
                                       allow_synthetic=True, provisional_diagnostic=LABEL)
        config = provisional.tag({"PROVISIONAL_DIVISION_SHA": self.protocol["PROVISIONAL_DIVISION_SHA"]}, LABEL)
        store = storage.RunArtifacts(self.root / "cannot_emit_clean", config, self.root)
        with self.assertRaisesRegex(ValueError, "clean"):
            store.write("receipt.json", {"schema": "clean-student-training-v1"})
        self.assertFalse((store.root / "receipt.json").exists())
        with self.assertRaises(ValueError):
            storage.finalize(self.training_run, self.root / "published/unlabeled", self.root)

    def test_benchmark_publication_validation_never_reads_training_rows(self):
        from student_pilot import provisional_eval

        adapter, receipt = self.published_adapter()
        real_binding = provisional_eval.binding
        def answer_free_binding(path, expected=None):
            if Path(path).name == "input_manifest.json":
                raise AssertionError("Benchmark admission must not open published teacher targets")
            return real_binding(path, expected)
        with patch.object(provisional_eval, "binding", side_effect=answer_free_binding):
            contracts.validate_adapter("distilled", "onethinker", adapter, receipt, contracts.DEFAULT_CONFIG,
                                       allow_synthetic=True, provisional_diagnostic=LABEL)

    def test_heldout_adapter_admission_does_not_open_training_rows(self):
        self.published_adapter()
        result_path = self.training_run / "training_result.json"
        result = load_json(result_path)
        expected = {**result["adapter"], "training_result": binding(result_path)}
        targets = {self.training_path, self.training_run / "input_manifest.json", self.publish / "input_manifest.json",
                   self.root / "candidate_index.jsonl"}
        for entry in contracts.load_jsonl(self.root / "candidate_index.jsonl"):
            targets.update(Path(entry[key]) for key in ("row_path", "target_path"))
        targets = {path.resolve() for path in targets}
        changed = copy.deepcopy(result)
        changed["adapter"]["weights"]["sha256"] = "0" * 64
        bad_run = self.document("changed_adapter/training_result.json", changed).parent
        original_open = Path.open

        def answer_free_open(path, *args, **kwargs):
            if path.resolve() in targets:
                self.fail("Held-out adapter admission opened target-bearing training rows")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", answer_free_open):
            heldout = provisional_data.load_heldout(self.heldout_path, LABEL)
            self.assertEqual(len(heldout["rows"]), 2)
            admitted = diagnostic.adapter_binding(self.training_run, self.protocol_path, provisional_diagnostic=LABEL)
            self.assertEqual(admitted, expected)
            with self.assertRaisesRegex(ValueError, "[Hh]ash"):
                diagnostic.adapter_binding(bad_run, self.protocol_path, provisional_diagnostic=LABEL)

    def test_paper_attempt_authority_survives_artifact_root_change(self):
        class ModelBoundary(Exception):
            pass

        manifest_path = self.document("paper_manifest.json", {"fixture": "paper authority"})
        media = self.document("paper_media.json", {})
        audits = self.index([provisional.tag({"qid": "paper_fixture"}, LABEL)], "paper_audits.jsonl")
        manifest = {"benchmark": "vsibench_answerable500", "paper_cell": True,
                    "ordered_ids": ["paper_fixture"], "media": contracts.binding(media)}
        rows = [{"qid": "paper_fixture"}]
        model = {"snapshot": "unopened-fixture-model"}
        effective = {key: value for key, value in contracts.DECODING.items() if key != "seed"}
        effective["eos_token_id"] = 10
        protocol = contracts.protocol_identity(contracts.binding(manifest_path), model, None, contracts.DEFAULT_CONFIG, LABEL)
        preflight = self.document("paper_preflight.json", provisional.tag({
            "schema": "student-cpu-preflight-v1", "status": "CPU_READY", "synthetic": False,
            "manifest": contracts.binding(manifest_path), "model_name": "onethinker", "model": model,
            "config": contracts.DEFAULT_CONFIG, "checked_count": 1, "expected_count": 1, "failures": [],
            "runtime": contracts.runtime_bindings(LABEL), "versions": contracts.versions(), "variant": "base", "adapter": None,
            "protocol_sha256": protocol, "work_id": contracts.work_id(manifest["benchmark"], "onethinker", "base", protocol),
            "input_audits": contracts.binding(audits), "effective_generation_config": effective}, LABEL))
        shared_root = self.root / "shared_paper_authority"
        with ExitStack() as stack:
            stack.enter_context(patch.object(generate, "PROVISIONAL_ATTEMPT_ROOT", shared_root, create=True))
            stack.enter_context(patch.object(generate, "load_generation", return_value=(manifest, rows, contracts.DEFAULT_CONFIG)))
            stack.enter_context(patch.object(generate, "authenticate_lease", return_value={"fixture": True}))
            stack.enter_context(patch.object(contracts, "snapshot_binding", return_value=model))
            locks = stack.enter_context(patch.object(generate, "exclusive_lock", wraps=contracts.exclusive_lock))
            stack.enter_context(patch("transformers.set_seed"))
            processor = stack.enter_context(patch("transformers.AutoProcessor.from_pretrained", side_effect=ModelBoundary))

            def run(root_name, resume=False):
                root = self.root / root_name
                return generate.generate_run(manifest_path, "onethinker", "base", root / "run", root, preflight,
                    lease_path="fixture-supervisor", coord_root=provisional.COORD_ROOT, model_root="fixture-model-root",
                    resume=resume, provisional_diagnostic=LABEL)

            with self.assertRaises(ModelBoundary):
                run("first_root")
            authority = locks.call_args.args[0].parent
            authority_root = locks.call_args.args[1]
            header = load_json(self.root / "first_root/run/run.json")
            started = provisional.tag({"qid": "paper_fixture", "attempt_index": 1,
                                       "run_header_sha256": contracts.digest(header)}, LABEL)
            contracts.write_once(authority / "starts" / f"{contracts.safe_id('paper_fixture')}.json",
                                 started, authority_root, True)
            contracts.append_jsonl(self.root / "first_root/run/attempts.jsonl", started, self.root / "first_root", True)
            with self.assertRaisesRegex(ValueError, "exists"):
                run("first_root")
            for resume in (False, True):
                with self.subTest(resume=resume):
                    try:
                        with self.assertRaisesRegex(ValueError, "attempt authority"):
                            run("second_root", resume=resume)
                    except ModelBoundary:
                        self.fail("A new artifact root admitted a consumed provisional paper attempt")
            self.assertEqual(processor.call_count, 1)
            self.assertEqual(authority.parent, shared_root / "attempt_authorities")
            self.assertFalse((self.root / "second_root/run").exists())
            self.assertFalse((self.root / "first_root/attempt_authorities").exists())
            with contracts.exclusive_lock(authority / "cohort.lock", authority_root, True):
                with self.assertRaisesRegex(ValueError, "Another worker"):
                    run("contending_root")
            self.assertEqual(contracts.load_json(authority / "claim.json")["run_directory"],
                             str(self.root / "first_root/run"))

    def test_qwen35_publication_uses_the_matching_base_and_all_labels_are_explicit(self):
        adapter, receipt = self.published_adapter("qwen35")
        pin = contracts.validate_adapter("distilled", "qwen35", adapter, receipt, contracts.DEFAULT_CONFIG,
                                         allow_synthetic=True, provisional_diagnostic=LABEL)
        self.assertEqual(pin["tensor_count"], 6)
        with self.assertRaises(ValueError):
            contracts.validate_adapter("distilled", "onethinker", adapter, receipt, contracts.DEFAULT_CONFIG,
                                       allow_synthetic=True, provisional_diagnostic=LABEL)
        for label in provisional.LABELS:
            rows = provisional.load_provisional_candidates(self.root / "candidate_index.jsonl", label)
            self.assertTrue(all(row["provisional_diagnostic"] == label for row in rows))

    def test_clean_adapter_validation_is_byte_identical(self):
        adapter, receipt = benchmark_fixtures.synthetic_adapter(self.root)
        original = self.baseline_function(contracts, "validate_adapter")
        self.assertEqual(canonical_bytes(original("distilled", "onethinker", adapter, receipt, contracts.DEFAULT_CONFIG, True)),
                         canonical_bytes(contracts.validate_adapter("distilled", "onethinker", adapter, receipt, contracts.DEFAULT_CONFIG, True)))
        original_identity = self.baseline_function(contracts, "protocol_identity")
        arguments = ({"sha256": "a" * 64}, {"model": "fixture"}, None, contracts.DEFAULT_CONFIG)
        self.assertEqual(original_identity(*arguments), contracts.protocol_identity(*arguments))
        self.assertNotEqual(original_identity(*arguments), contracts.protocol_identity(*arguments, provisional_diagnostic=LABEL))

    def test_default_runtime_never_imports_provisional_implementation(self):
        program = '''import sys
def guard(event, args):
    if event == "open" and isinstance(args[0], str) and "/student_pilot/provisional" in args[0]:
        raise AssertionError("Clean runtime opened provisional implementation")
sys.addaudithook(guard)
from student_pilot import diagnostic, storage
from student_pilot.benchmark_eval import contracts, frames, generate
assert storage.tag({"unchanged": True}, None) == {"unchanged": True}
assert storage.provisional_flags(None) == {}
assert storage.adapter_directory(None) == "adapter"
assert diagnostic.execution_contract(None, None, None, "onethinker", "train")[0] is diagnostic.require_lease
assert contracts.provisional_flags(None) == {}
assert contracts.provisional_tag({"unchanged": True}, None) == {"unchanged": True}
assert contracts.validate_adapter("base", "onethinker", None, None, contracts.DEFAULT_CONFIG) is None
contracts.protocol_identity({"sha256": "a" * 64}, {}, None, contracts.DEFAULT_CONFIG)
assert not any(name.startswith("student_pilot.provisional") for name in sys.modules)
print("CLEAN_RUNTIME_ISOLATED")
'''
        result = subprocess.run([sys.executable, "-B", "-c", program], check=True, capture_output=True, text=True,
                                cwd=benchmark_fixtures.REPO, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES=""))
        self.assertIn("CLEAN_RUNTIME_ISOLATED", result.stdout)

    def test_cli_routes_explicit_flag_without_touching_default_diagnostic(self):
        common = ["--manifest", "train.json", "--protocol", "protocol.json", "--output", "run", "--lease", "lease.json"]
        with patch.object(diagnostic, "train", return_value={}) as train, redirect_stdout(io.StringIO()):
            diagnostic.main(["train", *common])
            self.assertNotIn("provisional_diagnostic", train.call_args.kwargs)
            diagnostic.main(["train", *common, "--scratch-root", "/scratch/jjyeung", "--provisional-diagnostic", LABEL])
            self.assertEqual(train.call_args.kwargs["provisional_diagnostic"], LABEL)
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
            diagnostic.main(["train", *common, "--scratch-root", "/scratch/jjyeung", "--provisional-diagnostic", "UNKNOWN"])

    def test_provisional_scope_refuses_unrequested_benchmarks_before_output(self):
        unsupported = ({"benchmark": "dsibench_all4", "paper_cell": False}, [], contracts.DEFAULT_CONFIG)
        with patch.object(frames, "load_generation", return_value=unsupported), self.assertRaisesRegex(ValueError, "scoped"):
            frames.cpu_check("unused", "onethinker", self.root / "preflight", self.root, synthetic=True,
                             provisional_diagnostic=LABEL)
        with patch.object(generate, "load_generation", return_value=unsupported), self.assertRaisesRegex(ValueError, "scoped"):
            generate.generate_run("unused", "onethinker", "base", self.root / "run", self.root, "unused",
                                  cpu_mock=True, provisional_diagnostic=LABEL)
        values = [provisional.tag({}, LABEL), {"schema": "student-scoring-manifest-v1", "benchmark": "dsibench_all4"}]
        with patch.object(score, "load_json", side_effect=values), self.assertRaisesRegex(ValueError, "scoped"):
            score.score_run(self.root / "unused", "unused", self.root / "score", self.root, provisional_diagnostic=LABEL)
        self.assertFalse((self.root / "preflight").exists())
        self.assertFalse((self.root / "run").exists())
        self.assertFalse((self.root / "score").exists())

    def test_generation_scores_and_tables_are_labeled_and_wrong_mode_refuses(self):
        adapter, receipt = self.published_adapter()
        fixture = prepare.materialize_fixtures(benchmark_fixtures.FIXTURES, self.root / "fixture", self.root)
        prepared = self.root / "prepared"
        prepare.prepare("vsibench_answerable500", benchmark_fixtures.CONFIG, prepared, self.root,
                        fixture / "vsibench", fixture / "videos", fixture / "vsibench/MEMBERSHIP_ANSWERABLE_500.json",
                        project_root=benchmark_fixtures.PROJECT, synthetic=True)
        manifest = prepared / "generation/manifest.json"
        outputs, scores = {}, {}
        for variant in ("base", "distilled"):
            preflight = self.root / f"preflight_{variant}"
            kwargs = {"adapter": adapter, "training_receipt": receipt} if variant == "distilled" else {}
            frames.cpu_check(manifest, "onethinker", preflight, self.root, synthetic=True, variant=variant,
                             provisional_diagnostic=LABEL, **kwargs)
            run = self.root / f"run_{variant}"
            result = generate.generate_run(manifest, "onethinker", variant, run, self.root, preflight / "preflight.json",
                                           cpu_mock=True, paired_base_run=outputs.get("base") if variant == "distilled" else None,
                                           provisional_diagnostic=LABEL, **kwargs)
            provisional.require_mode(result, LABEL)
            outputs[variant] = run
            for name in ("run.json", "completion.json"):
                provisional.require_mode(load_json(run / name), LABEL)
            for row in contracts.load_jsonl(run / "generations.jsonl") + contracts.load_jsonl(run / "attempts.jsonl"):
                provisional.require_mode(row, LABEL)
            for value in (None, provisional.LABELS[1]):
                with self.assertRaises(ValueError):
                    score.score_run(run, prepared / "scoring/manifest.json", self.root / "wrong_mode", self.root,
                                    provisional_diagnostic=value)
            scored = self.root / f"score_{variant}"
            report = score.score_run(run, prepared / "scoring/manifest.json", scored, self.root, provisional_diagnostic=LABEL)
            provisional.require_mode(report, LABEL)
            for row in contracts.load_jsonl(scored / "per_question_scores.jsonl"):
                provisional.require_mode(row, LABEL)
            self.assertIn(LABEL, (scored / "results.csv").read_text())
            self.assertIn("diagnostic, provisional", (scored / "results.csv").read_text())
            scores[variant] = scored / "scores.json"
        comparison = score.compare_scores(scores["base"], scores["distilled"], self.root / "comparison", self.root,
                                           provisional_diagnostic=LABEL)
        provisional.require_mode(comparison, LABEL)
        self.assertIn(LABEL, (self.root / "comparison/results.csv").read_text())
        with self.assertRaises(ValueError):
            score.compare_scores(scores["base"], scores["distilled"], self.root / "unlabeled-comparison", self.root)
        with self.assertRaises(ValueError):
            generate.generate_run(manifest, "onethinker", "base", self.root / "unlabeled-run", self.root,
                                  self.root / "preflight_base/preflight.json", cpu_mock=True)
        import torch
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == "__main__":
    unittest.main()
