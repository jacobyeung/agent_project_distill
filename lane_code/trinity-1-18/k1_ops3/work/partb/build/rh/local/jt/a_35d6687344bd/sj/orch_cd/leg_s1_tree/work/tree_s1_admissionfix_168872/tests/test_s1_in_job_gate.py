import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from student_pilot.p3_provenance import file_pin, write


class InJobGateTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="in_job_gate_", dir=os.environ["TMPDIR"]))
        self.kit = self.directory / "kit"
        (self.kit / "k").mkdir(parents=True)
        self.run = self.directory / "run"
        self.inputs = self.run / "inputs"
        self.inputs.mkdir(parents=True)
        source = Path(__file__).resolve().parents[1] / "launch_s1/b"
        sys.path.insert(0, str(source))
        spec = importlib.util.spec_from_file_location("s1_in_job_test_gate", source / "d.py")
        self.gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.gate)
        self.logical = Path("/fixture/root/runs/12345678/inputs")
        self.cfg = dict(world_size=4, output=str(self.logical.parent), first_step_admission="all_rank_native_v1",
                        streams=dict(pointing=dict(path="/fixture/pointing", sha256="a"*64),
                                     routing=dict(path="/fixture/routing", sha256="c"*64)),
                        s1_routing=dict(schema="s1-routing-inputs-v1"),
                        scene_coverage=dict(schema="s1-scene-coverage-v1",
                            reference=dict(path="/fixture/scene_reference.json", sha256="1"*64),
                            source_map=dict(pointing=[dict(source="unit")])),
                        mdg=dict(confusers=dict(path="/fixture/confusers", sha256="b"*64)),
                        init_artifact=dict(artifact=dict(path="/fixture/parent", sha256="c"*64)),
                        preparation=dict(path="/fixture/preparation", sha256="d"*64),
                        preparation_output="/fixture/preparation", milestones=[1, 100, 200],
                        admission=dict(path="/fixture/review", sha256="e"*64))
        self.derived = copy.deepcopy(self.cfg)
        self.derived.pop("admission")
        self.derived["streams"]["pointing"] = self.put("pointing.json", dict(unit_fixture=True))
        self.routing_pin = self.put("routing_materialization.json", dict(schema="s1-routing-materialization-v1",
            status="PASS", inputs=self.cfg["s1_routing"], legacy=self.cfg["streams"]["routing"]))
        self.derived["streams"]["routing"] = self.put("routing.json", dict(materialization=self.routing_pin))
        self.derived["mdg"]["confusers"] = self.put("confusers.json", dict(chair=["table"]))
        self.derived["preparation_output"] = str(self.logical)
        self.launch = dict(source_revision="sha256:"+"f"*64,
                           run_directory=str(self.run), config=dict(file="k/cfg.json", sha256="a"*64),
                           source_seal=dict(tree_sha256="f"*64,
                                            archive=dict(path="/fixture/code.tar", sha256="b"*64)),
                           in_job_admission=dict(schema="s1-in-job-admission-v1",
                               directory=str(self.logical), frame_roots=["/fixture/frames"],
                               parent_grounding_required=True, gpu_first_step_required=True))
        parent = dict(schema="s1-parent-grounding-v1", status="PASS",
                      parent_artifact=self.cfg["init_artifact"]["artifact"],
                      confusers=self.derived["mdg"]["confusers"], exact_key_shape_coverage=True,
                      method="rebuild-from-parent-input-embedding-rows")
        self.parent_pin = self.put("parent.json", parent)
        self.frames_pin = self.put("frames.json", dict(all_retained_frames_exist=True,
                                                    sources=dict(pointing=dict(rows=1))))
        self.publish()

    def put(self, name, value):
        path = self.inputs / name
        path.write_text(json.dumps(value))
        return dict(path=str(self.logical / name), sha256=file_pin(path)["sha256"])

    def publish(self):
        seal = dict(schema="s1-run-seal-v1", tree_sha256=self.launch["source_seal"]["tree_sha256"],
                    archive=self.launch["source_seal"]["archive"],
                    config_sha256=self.gate.config_identity(self.derived))
        seal["sha256"] = self.gate.digest(seal)
        preparation = dict(config_sha256=self.gate.config_identity(self.derived), source_seal=seal,
                           streams=dict(pointing=dict(count=1)),
                           scene_filter_report=dict(coverage=dict(schema="s1-scene-coverage-result-v1",
                               status="PASS", policy=self.cfg["scene_coverage"], sources=dict(pointing=dict(unit=True)))))
        self.derived["preparation"] = self.put("preparation.json", preparation)
        value = dict(schema="s1-in-job-data-v1", status="PREPARED", production_authorized=False,
                     rehearsal=False, real_frames_verified=True, gpu_first_step_pending=True,
                     source_revision=self.launch["source_revision"], input_config=dict(sha256="a"*64),
                     world_size=4, input_streams=self.cfg["streams"], config=self.put("config.json", self.derived),
                     source_seal=seal, source_counts=dict(pointing=1), preparation=self.derived["preparation"],
                     scene_exclusions=preparation["scene_filter_report"],
                     frames=self.frames_pin, parent_grounding=self.parent_pin)
        value["routing_materialization"] = self.routing_pin
        (self.inputs / "data_receipt.json").write_text(json.dumps(value))
        (self.kit / "k/launch.json").write_text(json.dumps(self.launch))

    def test_reviewed_derivation_loads_from_a_restaged_host_directory(self):
        self.assertEqual(self.gate.effective(self.kit, self.cfg), self.derived)

    def test_self_consistent_unreviewed_configuration_change_is_rejected(self):
        self.derived["world_size"] = 8
        self.publish()
        with self.assertRaisesRegex(ValueError, "unreviewed training setting"):
            self.gate.effective(self.kit, self.cfg)

    def test_changed_proof_payload_and_foreign_parent_are_rejected(self):
        path = self.inputs / "frames.json"
        path.write_text("{}")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            self.gate.effective(self.kit, self.cfg)
        self.frames_pin = self.put("frames.json", dict(all_retained_frames_exist=True, sources=dict(pointing={})))
        parent = json.loads((self.inputs / "parent.json").read_text())
        parent["parent_artifact"]["sha256"] = "0"*64
        self.parent_pin = self.put("parent.json", parent)
        self.publish()
        with self.assertRaisesRegex(ValueError, "bound to this parent"):
            self.gate.effective(self.kit, self.cfg)

    def test_fixture_evidence_does_not_authorize_real_training(self):
        path = self.inputs / "data_receipt.json"
        value = json.loads(path.read_text())
        value.update(rehearsal=True, real_frames_verified=False)
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "rehearsal"):
            self.gate.effective(self.kit, self.cfg)

    def test_first_step_and_parent_requirements_cannot_be_disabled(self):
        for key in ("gpu_first_step_required", "parent_grounding_required"):
            value = copy.deepcopy(self.launch)
            value["in_job_admission"][key] = False
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "first-step contract"):
                self.gate.effective(self.kit, self.cfg, value)

    def test_scene_coverage_cannot_be_omitted_or_rebound(self):
        cfg = copy.deepcopy(self.cfg)
        cfg.pop("scene_coverage")
        with self.assertRaisesRegex(ValueError, "contract"):
            self.gate.effective(self.kit, cfg)
        path = self.inputs / "data_receipt.json"
        value = json.loads(path.read_text())
        value.pop("scene_exclusions")
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "scene exclusion coverage"):
            self.gate.effective(self.kit, self.cfg)


if __name__ == "__main__":
    unittest.main()
