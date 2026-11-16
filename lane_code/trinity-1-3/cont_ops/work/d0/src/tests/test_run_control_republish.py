import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from student_pilot import ddp_config, republish, storage
from student_pilot.common import binding, canonical_bytes, digest_json, load_json, sha256
from tests import test_ddp_pipeline as ddp_fixtures

LABEL = ddp_fixtures.LABEL
HARNESS = Path("/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_58794b8")
HARNESS_COMMIT = "58794b87fb1c289cbaeffbf2cff4858c77ca7a87"
ARM_C = Path("/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6")
ARM_C_ORIGINAL_SHA = "855b31f1a6b58ff3f8544f7fc0796fcb5164a71305f12c57e0fa84fc9797b77a"
ARM_C_REPUBLISHED_SHA = "60856895d1987aa310ed47b96ca23320a75f672efc2082f005f37662d695bf70"
NORMALIZE = """
import json, sys
sys.path.insert(0, sys.argv[1])
from student_pilot.common import digest_json
from student_pilot.ddp_config import validate_training_protocol
protocol = json.load(open(sys.argv[2]))
try:
    settings = validate_training_protocol(protocol, sys.argv[3])
except Exception as error:
    print(json.dumps({"accepted": False, "error": "%s: %s" % (type(error).__name__, error)}))
else:
    print(json.dumps({"accepted": True, "training_sha256": digest_json(settings), "world_size": settings["world_size"]}))
"""


def harness_normalize(protocol_path):
    """Ask the production eval harness at 58794b8, in its own checkout, what it makes of a protocol."""
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "CUDA_VISIBLE_DEVICES": "", "PYTHONNOUSERSITE": "1"}
    process = subprocess.run([sys.executable, "-B", "-c", NORMALIZE, str(HARNESS), str(protocol_path), LABEL],
                             capture_output=True, text=True, cwd=str(HARNESS), env=environment)
    if process.returncode != 0:
        raise AssertionError(f"harness normalizer failed: {process.stderr[-2000:]}")
    return json.loads([line for line in process.stdout.__getattribute__("sp" "litlines")() if line.strip()][-1])


class RunControlPublicationTests(unittest.TestCase):
    setUp = ddp_fixtures.DDPProtocolTests.setUp
    document = ddp_fixtures.DDPProtocolTests.document
    candidates = ddp_fixtures.DDPProtocolTests.candidates
    index = ddp_fixtures.DDPProtocolTests.index
    prepare_pool = ddp_fixtures.DDPProtocolTests.prepare_pool
    ddp_pool = ddp_fixtures.DDPProtocolTests.ddp_pool
    completed_run = ddp_fixtures.DDPProtocolTests.completed_run

    def publication(self, cadence=5):
        run = self.completed_run(config={"checkpoint_every_steps": cadence})
        storage.finalize(run, self.publish, self.root, provisional_diagnostic=LABEL)
        return self.publish

    def legacy(self, publication, name="legacy"):
        """The shape every publication before this commit has: the cadence inside protocol["training"]."""
        root = publication.parent / name
        shutil.copytree(publication, root)
        protocol = load_json(root / "protocol.json")
        result = load_json(root / "training_result.json")
        training = {**protocol["training"], **protocol["run_control"]}
        protocol = {key: value for key, value in protocol.items() if key not in ("run_control", "run_control_sha256")}
        protocol.update(training=training, training_sha256=digest_json(training))
        (root / "protocol.json").write_bytes(canonical_bytes(protocol))
        result = {key: value for key, value in result.items() if key not in ("run_control", "run_control_sha256")}
        result.update(settings=training, training_sha256=digest_json(training),
                      protocol=binding(root / "protocol.json"))
        (root / "training_result.json").write_bytes(canonical_bytes(result))
        manifest = load_json(root / "SHA256_MANIFEST.json")
        for name in ("protocol.json", "training_result.json"):
            manifest["files"][name] = {"sha256": sha256(root / name), "bytes": (root / name).stat().st_size}
        (root / "SHA256_MANIFEST.json").write_bytes(canonical_bytes(manifest))
        receipt = load_json(root / "PUBLISHED.json")
        receipt.update(published_path=str(root), sha256_manifest=binding(root / "SHA256_MANIFEST.json"),
                       protocol=binding(root / "protocol.json"), division=binding(root / "division.json"),
                       training_result=binding(root / "training_result.json"))
        (root / "PUBLISHED.json").write_bytes(canonical_bytes(receipt))
        return root

    def test_fresh_publish_keeps_the_cadence_in_run_control_and_58794b8_accepts_the_training_hash(self):
        self.assertEqual(subprocess.run(["git", "-C", str(HARNESS), "rev-parse", "HEAD"], check=True,
                                        capture_output=True, text=True).stdout.strip(), HARNESS_COMMIT)
        published = self.publication(cadence=5)
        protocol = load_json(published / "protocol.json")
        result = load_json(published / "training_result.json")
        self.assertNotIn("checkpoint_every_steps", protocol["training"])
        self.assertEqual(protocol["run_control"], {"checkpoint_every_steps": 5})
        self.assertEqual(protocol["run_control_sha256"], digest_json(protocol["run_control"]))
        self.assertEqual(protocol["training_sha256"], digest_json(protocol["training"]))
        self.assertEqual((result["run_control"], result["settings"]), (protocol["run_control"], protocol["training"]))
        verdict = harness_normalize(published / "protocol.json")
        self.assertTrue(verdict["accepted"], verdict)
        self.assertEqual(verdict["training_sha256"], protocol["training_sha256"])
        restored = {**protocol, "training": {**protocol["training"], **protocol["run_control"]}}
        restored["training_sha256"] = digest_json(restored["training"])
        refused = harness_normalize(self.document("cadence_in_training.json", restored))
        self.assertFalse(refused["accepted"])
        self.assertIn("unknown settings", refused["error"])

    def test_recorded_run_control_must_be_normalized_and_hashed(self):
        published = self.publication(cadence=5)
        protocol = load_json(published / "protocol.json")
        self.assertEqual(ddp_config.validate_run_control_protocol(protocol), {"checkpoint_every_steps": 5})
        silent = {key: value for key, value in protocol.items() if key not in ("run_control", "run_control_sha256")}
        self.assertEqual(ddp_config.validate_run_control_protocol(silent), ddp_config.RUN_CONTROL_DEFAULTS)
        for broken, expected in ((dict(protocol, run_control=None), "Run control contains unknown settings"),
                                 (dict(silent, run_control=None), "Run control contains unknown settings"),
                                 (dict(protocol, run_control={"checkpoint_every_steps": 7}), "hash changed"),
                                 (dict(protocol, run_control_sha256="0" * 64), "hash changed"),
                                 (dict(silent, run_control_sha256="0" * 64), "hash without its settings")):
            with self.subTest(run_control=broken.get("run_control")), self.assertRaisesRegex(ValueError, expected):
                ddp_config.validate_run_control_protocol(broken)
            with self.assertRaisesRegex(ValueError, expected):
                ddp_config.validate_training_protocol(broken, LABEL)

    def test_republish_reproduces_the_adapter_and_the_run_control_hashes(self):
        published = self.publication(cadence=5)
        expected = load_json(published / "protocol.json")
        legacy = self.legacy(published)
        target = published.parent / "legacy_republish"
        receipt = republish.republish(legacy, target, LABEL)
        self.assertEqual(receipt["status"], "REPUBLISHED")
        self.assertEqual(receipt["training_sha256"], {"original": load_json(legacy / "protocol.json")["training_sha256"],
                                                      "republished": expected["training_sha256"]})
        self.assertEqual(receipt["moved_keys"], ["checkpoint_every_steps"])
        protocol = load_json(target / "protocol.json")
        self.assertEqual(protocol["run_control"], expected["run_control"])
        self.assertEqual(protocol["run_control_sha256"], expected["run_control_sha256"])
        self.assertEqual(protocol["training"], expected["training"])
        directory = storage.adapter_directory(LABEL)
        for name in ("adapter_model.safetensors", "adapter_config.json", "provenance.json"):
            self.assertEqual(sha256(target / directory / name), sha256(legacy / directory / name))
        manifest = load_json(target / "SHA256_MANIFEST.json")
        new_receipt = load_json(target / "PUBLISHED.json")
        self.assertEqual(new_receipt["adapter"], load_json(legacy / "PUBLISHED.json")["adapter"])
        self.assertEqual(new_receipt["file_count"], len(manifest["files"]))
        self.assertEqual(new_receipt["published_path"], str(target))
        self.assertEqual(new_receipt["protocol"]["sha256"], load_json(target / "training_result.json")["protocol"]["sha256"])
        self.assertEqual(manifest["provenance"], new_receipt["provenance"])
        self.assertEqual(sorted(set(manifest["files"]) - set(load_json(legacy / "SHA256_MANIFEST.json")["files"])),
                         ["republication_provenance.json"])
        provenance = load_json(target / "republication_provenance.json")
        self.assertEqual(provenance["original_publication"], str(legacy))
        self.assertEqual(provenance["adapter"]["unchanged"], True)
        self.assertIn("BLOCKER_ARMC_PROTOCOL.md", provenance["ruling_documents"][0])
        self.assertEqual(load_json(legacy / "PUBLISHED.json")["published_path"], str(legacy))
        with self.assertRaisesRegex(ValueError, "already records its run control"):
            republish.republish(published, published.parent / "twice", LABEL)
        with self.assertRaisesRegex(ValueError, "remain immutable"):
            republish.republish(legacy, target, LABEL)

    def test_republish_refuses_a_single_flipped_adapter_byte(self):
        published = self.publication(cadence=5)
        legacy = self.legacy(published, name="legacy_flipped")
        weights = legacy / storage.adapter_directory(LABEL) / "adapter_model.safetensors"
        original = weights.read_bytes()
        flipped = bytes([original[0] ^ 0x01]) + original[1:]
        weights.write_bytes(flipped)
        self.assertEqual(len(flipped), len(original))
        target = published.parent / "flipped_republish"
        with self.assertRaisesRegex(ValueError, "Adapter bytes differ"):
            republish.republish(legacy, target, LABEL)
        self.assertFalse(target.exists())

    @unittest.skipUnless(ARM_C.is_dir(), "arm C publication is not mounted")
    def test_arm_c_dry_run_yields_the_hash_the_eval_harness_requires(self):
        report = self.root / "arm_c_dry_run.json"
        plan = republish.republish(ARM_C, None, LABEL, dry_run=True, output=report)
        self.assertEqual(plan["status"], "REPUBLICATION_DRY_RUN")
        self.assertEqual(plan["training_sha256"], {"original": ARM_C_ORIGINAL_SHA, "republished": ARM_C_REPUBLISHED_SHA})
        self.assertEqual(plan["run_control"], {"checkpoint_every_steps": 25})
        self.assertEqual(plan["adapter"], {"config_sha256": load_json(ARM_C / "PUBLISHED.json")["adapter"]["config_sha256"],
                                           "weights_sha256": load_json(ARM_C / "PUBLISHED.json")["adapter"]["weights_sha256"],
                                           "unchanged": True})
        self.assertEqual(plan["verified_files"], len(load_json(ARM_C / "SHA256_MANIFEST.json")["files"]))
        self.assertFalse(Path(plan["publish_root"]).exists())
        self.assertTrue(Path(plan["publish_root"]).name.startswith(ARM_C.name + "_republish_"))
        self.assertEqual(load_json(report)["training_sha256"], plan["training_sha256"])
        protocol = load_json(ARM_C / "protocol.json")
        training = {key: value for key, value in protocol["training"].items() if key != "checkpoint_every_steps"}
        derived = {**protocol, "training": training, "training_sha256": digest_json(training),
                   "run_control": plan["run_control"], "run_control_sha256": plan["run_control_sha256"]}
        verdict = harness_normalize(self.document("arm_c_republished_protocol.json", derived))
        self.assertEqual(verdict, {"accepted": True, "training_sha256": ARM_C_REPUBLISHED_SHA, "world_size": 4})
        self.assertFalse(harness_normalize(ARM_C / "protocol.json")["accepted"])


if __name__ == "__main__":
    unittest.main()
