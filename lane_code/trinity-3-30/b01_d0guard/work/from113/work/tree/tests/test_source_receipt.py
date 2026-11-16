import copy
import json
import unittest
from unittest.mock import patch

from student_pilot import provisional, provisional_data, storage
from student_pilot.common import binding, digest_json, load_json
from tests import test_provisional as fixtures
from tests import test_provisional_pipeline as pipeline


LABEL = fixtures.LABEL


class SourceReceiptTests(unittest.TestCase):
    setUp = fixtures.ProvisionalTests.setUp
    document = fixtures.ProvisionalTests.document
    candidates = fixtures.ProvisionalTests.candidates
    index = fixtures.ProvisionalTests.index
    prepare_pool = pipeline.ProvisionalPipelineTests.prepare_pool

    def sealed(self):
        self.prepare_pool()
        self.full = provisional_data.load_training(self.training_path, LABEL)
        self.receipt_path = provisional_data.source_receipt_path(self.training_path)
        result = provisional_data.seal_source(self.training_path, self.receipt_path, LABEL)
        self.assertEqual(result["receipt"], binding(self.receipt_path))
        return load_json(self.receipt_path)

    def forge(self, manifest):
        """Rewrite the manifest and a receipt that matches its new bytes, as an attacker with write access could."""
        self.training_path.write_text(json.dumps(manifest, indent=2) + "\n")
        protocol = provisional_data.load_protocol(manifest["protocol"]["path"], LABEL)
        receipt = provisional.tag(provisional_data._source_receipt(binding(self.training_path), manifest, protocol), LABEL)
        receipt["provenance"] = {"commit": "c" * 40, "dirty": False, "config_sha256": digest_json(receipt)}
        self.receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    def no_payload_reads(self):
        return [patch.object(provisional_data, "source_rows", side_effect=AssertionError("payloads re-read")),
                patch.object(provisional_data, "load_provisional_candidates", side_effect=AssertionError("payloads re-read"))]

    def test_receipt_admits_the_same_manifest_without_rereading_payloads(self):
        receipt = self.sealed()
        self.assertEqual(receipt["schema"], provisional_data.SOURCE_RECEIPT_SCHEMA)
        self.assertEqual(receipt["manifest"], binding(self.training_path))
        self.assertEqual(receipt["protocol"], binding(self.protocol_path))
        self.assertEqual(receipt["candidate_census_sha256"], digest_json(self.protocol["candidate_census"]))
        patches = self.no_payload_reads()
        for item in patches:
            item.start()
        try:
            self.assertEqual(provisional_data.load_training(self.training_path, LABEL), self.full)
        finally:
            for item in reversed(patches):
                item.stop()

    def test_without_receipt_or_when_disabled_the_full_admission_runs(self):
        self.prepare_pool()
        with patch.object(provisional_data, "source_rows", wraps=provisional_data.source_rows) as spy:
            provisional_data.load_training(self.training_path, LABEL)
        self.assertEqual(spy.call_count, 1)
        provisional_data.seal_source(self.training_path, provisional_data.source_receipt_path(self.training_path), LABEL)
        with patch.object(provisional_data, "source_rows", wraps=provisional_data.source_rows) as spy:
            provisional_data.load_training(self.training_path, LABEL, use_receipt=False)
        self.assertEqual(spy.call_count, 1)

    def test_any_manifest_byte_change_invalidates_the_receipt(self):
        self.sealed()
        text = self.training_path.read_text()
        self.training_path.write_text(text + " ")
        with self.assertRaisesRegex(ValueError, "Source receipt does not match"):
            provisional_data.load_training(self.training_path, LABEL)

    def test_forged_receipt_cannot_admit_a_changed_row(self):
        self.sealed()
        manifest = copy.deepcopy(self.full)
        manifest["rows"][0] = {**manifest["rows"][0], "target": "forged answer"}
        self.forge(manifest)
        with self.assertRaisesRegex(ValueError, "rows, or input audit counts changed"):
            provisional_data.load_training(self.training_path, LABEL)

    def test_forged_receipt_cannot_admit_a_missing_or_foreign_row(self):
        self.sealed()
        missing = copy.deepcopy(self.full)
        missing["rows"].pop()
        missing["input_audits"].pop()
        self.forge(missing)
        with self.assertRaises(ValueError):
            provisional_data.load_training(self.training_path, LABEL)
        foreign = copy.deepcopy(self.full)
        heldout = set(self.protocol["division"]["heldout_qids"])
        row = next(row for row in provisional_data.source_rows(self.protocol, LABEL) if row["qid"] in heldout)
        foreign["rows"][0] = row
        foreign["input_audits"][0] = {**foreign["input_audits"][0], "qid": row["qid"]}
        self.forge(foreign)
        with self.assertRaises(ValueError):
            provisional_data.load_training(self.training_path, LABEL)

    def tokenizer_patches(self, tokens):
        from student_pilot import diagnostic_data

        def encode(processor, row):
            return {}, {"qid": row["qid"], "frame_count": 32, "assistant_tokens_including_eos": 10, "prompt_tokens": 20}

        return [patch("student_pilot.batches.load_processor", return_value=object()),
                patch.object(diagnostic_data, "target_tokens", side_effect=lambda processor, row: tokens(row)),
                patch.object(diagnostic_data, "encode_training", side_effect=encode)]

    def with_patches(self, patches, function):
        for item in patches:
            item.start()
        try:
            return function()
        finally:
            for item in reversed(patches):
                item.stop()

    def test_receipt_refuses_undeclared_drops(self):
        self.sealed()
        manifest = copy.deepcopy(self.full)
        dropped = manifest["rows"].pop()
        manifest["input_audits"].pop()
        manifest["pre_evaluation_drops"] = [{"qid": dropped["qid"], "reason": "hand_removed", "limit": 1,
                                              "target_tokens_including_eos": 10, "complete_target_sha256": digest_json(dropped["target"])}]
        manifest["counts"] = provisional_data.training_counts(manifest["rows"], manifest["input_audits"])
        manifest["training_ready"] = True
        self.forge(manifest)
        with self.assertRaisesRegex(ValueError, "Undeclared provisional training exclusion"):
            self.with_patches(self.tokenizer_patches(lambda row: 10),
                              lambda: provisional_data.load_training(self.training_path, LABEL))

    def test_forged_receipt_cannot_admit_a_fitting_row_as_a_token_limit_drop(self):
        from student_pilot import diagnostic_data

        self.sealed()
        manifest = copy.deepcopy(self.full)
        dropped = manifest["rows"].pop()
        manifest["input_audits"].pop()
        manifest["pre_evaluation_drops"] = [{"qid": dropped["qid"], "reason": "complete_target_exceeds_predeclared_token_limit",
                                              "limit": diagnostic_data.TRAINING["max_target_tokens_including_eos"],
                                              "target_tokens_including_eos": 10, "complete_target_sha256": digest_json(dropped["target"])}]
        manifest["counts"] = provisional_data.training_counts(manifest["rows"], manifest["input_audits"])
        self.forge(manifest)
        with self.assertRaisesRegex(ValueError, "Dropped target fits the frozen token limit"):
            self.with_patches(self.tokenizer_patches(lambda row: 10) + [
                patch.object(provisional_data, "source_rows", side_effect=AssertionError("full source re-read"))],
                lambda: provisional_data.load_training(self.training_path, LABEL))

    def test_receipt_rechecks_genuine_drops_from_their_own_payloads_only(self):
        self.prepare_pool()
        heavy = self.protocol["division"]["train_candidate_qids"][0]
        tokens = lambda row: 10**6 if row["qid"] == heavy else 10
        self.training_path = self.root / "training_with_drop.json"
        self.with_patches(self.tokenizer_patches(tokens),
                          lambda: provisional_data.prepare_training(self.protocol_path, self.training_path, LABEL))
        full = self.with_patches(self.tokenizer_patches(tokens), lambda: provisional_data.load_training(self.training_path, LABEL))
        self.assertEqual([drop["qid"] for drop in full["pre_evaluation_drops"]], [heavy])
        self.with_patches(self.tokenizer_patches(tokens), lambda: provisional_data.seal_source(
            self.training_path, provisional_data.source_receipt_path(self.training_path), LABEL))
        read = []
        original = provisional_data._census_rows

        def spy(protocol, qids, label):
            read.append(set(qids))
            return original(protocol, qids, label)

        fast = self.with_patches(self.tokenizer_patches(tokens) + [
            patch.object(provisional_data, "source_rows", side_effect=AssertionError("full source re-read")),
            patch.object(provisional_data, "_census_rows", side_effect=spy)],
            lambda: provisional_data.load_training(self.training_path, LABEL))
        self.assertEqual(fast, full)
        self.assertEqual(read, [{heavy}])
        with self.assertRaisesRegex(ValueError, "Dropped complete target or token count changed"):
            self.with_patches(self.tokenizer_patches(lambda row: 10**6 + 1 if row["qid"] == heavy else 10),
                              lambda: provisional_data.load_training(self.training_path, LABEL))

    def test_seal_binds_exactly_the_bytes_it_validated(self):
        import hashlib

        self.prepare_pool()
        validated = self.training_path.read_bytes()
        original = provisional_data._admit_training

        def replace_during_validation(*args, **kwargs):
            result = original(*args, **kwargs)
            self.training_path.write_bytes(validated + b" ")
            return result

        with patch.object(provisional_data, "_admit_training", side_effect=replace_during_validation):
            provisional_data.seal_source(self.training_path, provisional_data.source_receipt_path(self.training_path), LABEL)
        self.assertEqual(load_json(provisional_data.source_receipt_path(self.training_path))["manifest"]["sha256"],
                         hashlib.sha256(validated).hexdigest())
        with self.assertRaisesRegex(ValueError, "Source receipt does not match"):
            provisional_data.load_training(self.training_path, LABEL)

    def test_receipt_from_other_code_or_label_is_refused(self):
        self.sealed()
        receipt = load_json(self.receipt_path)
        receipt["provenance"] = {**receipt["provenance"], "commit": "d" * 40}
        self.receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        with self.assertRaisesRegex(ValueError, "Source receipt does not match"):
            provisional_data.load_training(self.training_path, LABEL)
        receipt = load_json(self.receipt_path)
        receipt["provenance"] = {**receipt["provenance"], "commit": "c" * 40, "dirty": True}
        self.receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        with self.assertRaisesRegex(ValueError, "Source receipt does not match"):
            provisional_data.load_training(self.training_path, LABEL)
        receipt = {key: value for key, value in load_json(self.receipt_path).items() if key != "provisional_diagnostic"}
        self.receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        with self.assertRaises(ValueError):
            provisional_data.load_training(self.training_path, LABEL)

    def test_changed_candidate_source_after_sealing_is_refused(self):
        self.sealed()
        source = self.protocol["candidate_source"]["path"]
        with open(source, "a") as stream:
            stream.write("\n")
        with self.assertRaises(ValueError):
            provisional_data.load_training(self.training_path, LABEL)

    def test_seal_only_writes_the_fixed_receipt_once(self):
        self.prepare_pool()
        with self.assertRaisesRegex(ValueError, "fixed receipt path"):
            provisional_data.seal_source(self.training_path, self.root / "elsewhere.json", LABEL)
        provisional_data.seal_source(self.training_path, provisional_data.source_receipt_path(self.training_path), LABEL)
        with self.assertRaisesRegex(ValueError, "already has a source receipt"):
            provisional_data.seal_source(self.training_path, provisional_data.source_receipt_path(self.training_path), LABEL)

    def test_seal_refuses_a_manifest_that_fails_full_admission(self):
        self.prepare_pool()
        manifest = load_json(self.training_path)
        manifest["rows"][0] = {**manifest["rows"][0], "target": "changed"}
        self.training_path.write_text(json.dumps(manifest, indent=2) + "\n")
        with self.assertRaises(ValueError):
            provisional_data.seal_source(self.training_path, provisional_data.source_receipt_path(self.training_path), LABEL)
        self.assertFalse(provisional_data.source_receipt_path(self.training_path).exists())


if __name__ == "__main__":
    unittest.main()
