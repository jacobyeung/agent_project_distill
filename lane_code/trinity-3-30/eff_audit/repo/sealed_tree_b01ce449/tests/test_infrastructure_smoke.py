import copy
import io
import json
from contextlib import redirect_stderr, redirect_stdout
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from student_pilot import infrastructure_smoke as smoke
from student_pilot.common import ARTIFACTS, binding


class InfrastructureSmokeTests(unittest.TestCase):
    def setUp(self):
        root = ARTIFACTS / "trainer_tests"
        root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="infrastructure_", dir=root))
        self.rows = []
        for index in range(6):
            row = {"qid": str(index), "dataset": "scannetpp", "scene": f"scene-{index}",
                   "division": "train" if index < 4 else "validation",
                   "student_input": {"question": "Synthetic CPU fixture", "options": [],
                                     "frames": [{"path": str(self.root / f"{frame}.png"), "sha256": "a" * 64} for frame in range(32)],
                                     "frame_indices": list(range(32)), "timestamps": [frame / 2 for frame in range(32)],
                                     "fps": 2.0, "total_num_frames": 32}}
            if index < 4:
                row["target"] = smoke.PLACEHOLDER
            self.rows.append(row)
        self.manifest = {"schema": smoke.MANIFEST_SCHEMA, "infrastructure_only": True, "detailed_distillation": False,
                         "benchmark_improvement_claim": False, "score_nomination_allowed": False,
                         "training_eligible": False, "purpose": smoke.SMOKE_PURPOSE, "rows": self.rows}
        self.path = self.root / "manifest.json"
        self.path.write_text(json.dumps(self.manifest))

    def test_manifest_is_exactly_four_training_and_two_answer_free_validation_rows(self):
        self.assertEqual(smoke.validate_manifest(self.manifest), self.manifest)
        self.assertEqual(smoke.load_manifest(self.path), self.manifest)
        self.assertFalse(any("target" in row for row in self.rows if row["division"] == "validation"))

    def test_nonplaceholder_targets_and_scientific_claims_are_refused(self):
        for change in ("target", "claim", "eligible", "schema", "validation_target"):
            manifest = copy.deepcopy(self.manifest)
            if change == "target":
                manifest["rows"][0]["target"] = "Not an infrastructure placeholder"
            elif change == "claim":
                manifest["benchmark_improvement_claim"] = True
            elif change == "eligible":
                manifest["training_eligible"] = True
            elif change == "schema":
                manifest["schema"] = "fixed-diagnostic-training-manifest-v1"
            else:
                manifest["rows"][4]["target"] = smoke.PLACEHOLDER
            with self.subTest(change=change), self.assertRaises(ValueError):
                smoke.validate_manifest(manifest)

    def test_scene_overlap_duplicate_ids_and_wrong_counts_are_refused(self):
        for change in ("scene", "qid", "count", "teacher_field"):
            manifest = copy.deepcopy(self.manifest)
            if change == "scene":
                manifest["rows"][4]["scene"] = manifest["rows"][0]["scene"]
            elif change == "qid":
                manifest["rows"][4]["qid"] = manifest["rows"][0]["qid"]
            elif change == "count":
                manifest["rows"] = manifest["rows"][:5]
            else:
                manifest["rows"][0]["teacher_answer"] = "forbidden"
            with self.subTest(change=change), self.assertRaises(ValueError):
                smoke.validate_manifest(manifest)

    def test_staging_may_change_only_frame_paths_and_must_remain_local(self):
        scratch = self.root / "scratch"
        scratch.mkdir()
        staged = copy.deepcopy(self.rows)
        for row in staged:
            for index, frame in enumerate(row["student_input"]["frames"]):
                frame["path"] = str(scratch / f"{index}.png")
        with patch.object(smoke, "scratch_directory", return_value=scratch):
            smoke.verify_staged_rows(self.rows, staged, scratch)
            staged[0]["student_input"]["question"] = "changed"
            with self.assertRaises(ValueError):
                smoke.verify_staged_rows(self.rows, staged, scratch)

    def test_work_ids_bind_student_and_manifest(self):
        one = smoke.work_id(self.path, "onethinker")
        qwen = smoke.work_id(self.path, "qwen35")
        self.assertNotEqual(one, qwen)
        self.assertEqual(one, smoke.work_id(self.path, "onethinker"))
        self.assertTrue(one.startswith("student_smoke__req232_onethinker__infra6__s17__"))

    def test_gpu_guard_refuses_other_nodes_devices_or_foreign_memory(self):
        for host, visible, memory in (("trinity-1-8", "7", 0), (smoke.SMOKE_HOST, "0", 0),
                                      (smoke.SMOKE_HOST, "7", 2049)):
            with self.subTest(host=host, visible=visible, memory=memory), \
                    patch.object(smoke.socket, "gethostname", return_value=host), \
                    patch.dict(smoke.os.environ, {"CUDA_VISIBLE_DEVICES": visible}), \
                    patch.object(smoke.shutil, "which", return_value=None), \
                    patch.object(smoke.subprocess, "run", side_effect=[SimpleNamespace(stdout="GPU-fixture\n"),
                                                                       SimpleNamespace(stdout=f"GPU-fixture, 999999999, {memory}\n")]), \
                    self.assertRaises(ValueError):
                smoke.gpu_snapshot()

    def test_gpu_guard_records_the_actual_foreign_allocation(self):
        with patch.object(smoke.socket, "gethostname", return_value=smoke.SMOKE_HOST), \
                patch.dict(smoke.os.environ, {"CUDA_VISIBLE_DEVICES": "7"}), \
                patch.object(smoke.shutil, "which", return_value=None), \
                patch.object(smoke.subprocess, "run", side_effect=[SimpleNamespace(stdout="GPU-fixture\n"),
                                                                   SimpleNamespace(stdout="GPU-fixture, 999999999, 542\n")]):
            result = smoke.gpu_snapshot()
        self.assertEqual(result["foreign_memory_mib"], 542)
        self.assertFalse(result["vnice_available"])

    def test_coordination_receipt_must_match_the_actual_fresh_lease(self):
        now = datetime.now(timezone.utc)
        work = smoke.work_id(self.path, "onethinker")
        root = self.root / "coord"
        lease_path = root / "LEASES" / f"{work}.lock" / "lease.json"
        lease_path.parent.mkdir(parents=True)
        lease = {"work_id": work, "agent_id": "cpu-fixture", "host": smoke.SMOKE_HOST,
                 "status": "running", "last_heartbeat": now.isoformat()}
        lease_path.write_text(json.dumps(lease))
        with patch.object(smoke, "COORD_ROOT", root), patch.dict(smoke.os.environ, {"AGENT_ID": "cpu-fixture"}):
            self.assertEqual(smoke.require_smoke_lease(lease_path, work)["work_id"], work)
            with self.assertRaises(ValueError):
                smoke.require_smoke_lease(lease_path, "wrong-work")
            lease["status"] = "completed"
            lease_path.write_text(json.dumps(lease))
            with self.assertRaises(ValueError):
                smoke.require_smoke_lease(lease_path, work)

    def test_diagnostic_cli_routes_both_students_to_the_isolated_smoke(self):
        from student_pilot import diagnostic

        for student in ("onethinker", "qwen35"):
            with patch.object(smoke, "train", return_value={"infrastructure_only": True}) as train, \
                    patch.object(diagnostic, "train") as benchmark_train, redirect_stdout(io.StringIO()):
                diagnostic.main(["train", "--manifest", str(self.path), "--output", "new-run", "--lease", "lease.json",
                                 "--student", student, "--infrastructure-smoke", "--scratch-root", "/scratch/jjyeung", "--stage-frames"])
            train.assert_called_once_with(str(self.path), "new-run", "lease.json", student, "/scratch/jjyeung", True)
            benchmark_train.assert_not_called()
            with patch.object(smoke, "evaluate", return_value={"infrastructure_only": True}) as evaluate, \
                    patch.object(diagnostic, "evaluate") as benchmark_evaluate, redirect_stdout(io.StringIO()):
                diagnostic.main(["evaluate", "--manifest", str(self.path), "--output", "new-eval", "--lease", "lease.json",
                                 "--student", student, "--infrastructure-smoke", "--scratch-root", "/scratch/jjyeung",
                                 "--variant", "adapter", "--training-run", "new-run"])
            evaluate.assert_called_once_with(str(self.path), "new-eval", "lease.json", student, "/scratch/jjyeung", "new-run", "adapter")
            benchmark_evaluate.assert_not_called()

    def test_diagnostic_cli_still_requires_the_native_protocol(self):
        from student_pilot import diagnostic

        base = ["train", "--manifest", str(self.path), "--output", "new-run", "--lease", "lease.json"]
        for arguments in (base, base + ["--infrastructure-smoke", "--protocol", "benchmark.json"]):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                diagnostic.main(arguments)
            self.assertEqual(error.exception.code, 2)

    def test_available_vnice_is_required(self):
        with patch.object(smoke.socket, "gethostname", return_value=smoke.SMOKE_HOST), \
                patch.dict(smoke.os.environ, {"CUDA_VISIBLE_DEVICES": "7", "STUDENT_SMOKE_VNICE_WRAPPED": "0"}), \
                patch.object(smoke.shutil, "which", return_value="/synthetic/vnice"), self.assertRaisesRegex(ValueError, "vnice"):
            smoke.gpu_snapshot()


if __name__ == "__main__":
    unittest.main()
