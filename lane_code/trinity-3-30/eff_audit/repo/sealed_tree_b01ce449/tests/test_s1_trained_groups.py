from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import torch

from evalpath.runtime import check_init_spec, evaluator_init_spec
from student_pilot import trained_groups as groups
from student_pilot.p3_provenance import file_pin, write


class TrainedGroupTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        self.model = torch.nn.Module()
        self.model.auxiliary_heads = torch.nn.ModuleDict({
            "pose": torch.nn.ModuleDict({"body": torch.nn.Linear(2, 2),
                                         "cam_token_connector": torch.nn.Linear(2, 2)}),
            "depth": torch.nn.Linear(2, 2), "gf1": torch.nn.Linear(2, 2), "mdg": torch.nn.Linear(2, 2)})
        groups.capture(self.model)
        self.initial = {name: value.clone() for name, value in self.model.auxiliary_heads.state_dict().items()}
        optimizer = torch.optim.SGD(self.model.parameters(), lr=.1)
        sum(value.square().sum() for value in self.model.parameters()).backward()
        groups.observe(self.model)
        optimizer.step()
        self.state = self.model.auxiliary_heads.state_dict()
        self.contract = groups.publish(self.model, self.model.state_dict(), 1)

    def test_complete_updated_groups_load(self):
        self.assertEqual(groups.validate(self.model, self.state, self.contract, 1),
                         ["camera_connector", "depth", "fusion", "grounding", "pose"])

    def test_every_missing_zero_and_cold_group_refuses(self):
        for name, entry in self.contract["groups"].items():
            with self.subTest(group=name, fault="missing"):
                state = dict(self.state)
                state.pop(entry["names"][0])
                with self.assertRaisesRegex(ValueError, "missing"):
                    groups.validate(self.model, state, self.contract, 1)
            with self.subTest(group=name, fault="zero"):
                state = dict(self.state)
                state.update({key: torch.zeros_like(state[key]) for key in entry["names"]})
                with self.assertRaisesRegex(ValueError, "zero"):
                    groups.validate(self.model, state, self.contract, 1)
            with self.subTest(group=name, fault="cold"):
                state = dict(self.state)
                state.update({key: self.initial[key] for key in entry["names"]})
                contract = deepcopy(self.contract)
                contract["groups"][name].update(final_sha256=entry["initial_sha256"], changed=False)
                with self.assertRaisesRegex(ValueError, "cold"):
                    groups.validate(self.model, state, contract, 1)

    def test_decay_without_gradient_evidence_is_cold(self):
        contract = deepcopy(self.contract)
        contract["groups"]["fusion"]["gradient_steps"] = 0
        with self.assertRaisesRegex(ValueError, "cold"):
            groups.validate(self.model, self.state, contract, 1)

    def test_scalar_fingerprint(self):
        self.assertTrue(groups.fingerprint({"scale": torch.tensor(1.)})[1])

    def test_restore_refuses_a_changed_training_origin(self):
        rebuilt = deepcopy(self.model)
        for module in rebuilt.modules():
            if isinstance(module, torch.nn.Linear):
                module.reset_parameters()
        groups.capture(rebuilt)
        self.assertNotEqual(rebuilt.trained_group_state, self.model.trained_group_state)
        with self.assertRaisesRegex(ValueError, "initialization differs"):
            groups.restore(rebuilt, self.model.trained_group_state)

    def test_native_fsdp_restore_updates_the_published_module(self):
        from datetime import timedelta
        import torch.distributed as dist
        from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
        saved = deepcopy(self.model.trained_group_state)
        rebuilt = deepcopy(self.model)
        rebuilt.auxiliary_heads.load_state_dict(self.initial)
        rebuilt.language = torch.nn.Linear(2, 2)
        groups.capture(rebuilt)
        store = dist.TCPStore("127.0.0.1", 0, 1, True, timeout=timedelta(seconds=20))
        dist.init_process_group("gloo", store=store, rank=0, world_size=1)
        try:
            wrapped = FSDP(rebuilt, device_id=torch.device("cpu"),
                           ignored_modules=[rebuilt.auxiliary_heads], use_orig_params=True)
            groups.restore(wrapped, saved)
            self.assertEqual(rebuilt.trained_group_state, saved)
            self.assertNotIn("trained_group_state", wrapped.__dict__)
        finally:
            dist.destroy_process_group()

    def test_init_spec_covers_all_loaded_groups(self):
        root = Path(tempfile.mkdtemp(prefix="eval-init-", dir=os.environ["TMPDIR"]))
        artifact = root / "artifact.json"
        write(artifact, dict(trained_groups=self.contract, mdg=dict(tau=.25), trace_program_version="3.14"))
        pin = file_pin(artifact)
        receipt = dict(depth_enabled=True, geometry_online=dict(gf1={"stage": 2}), mdg={"present": True},
                       trace_program_version="3.14")
        spec = evaluator_init_spec(receipt, pin)
        self.assertEqual(check_init_spec(receipt, pin), spec)
        for name in spec["groups"]:
            changed = {**spec, "groups": [value for value in spec["groups"] if value != name]}
            with self.subTest(group=name), self.assertRaisesRegex(ValueError, "omits"):
                check_init_spec(receipt, pin, changed)
        write(root / "cold.json", dict(mdg=dict(tau=.25), trace_program_version="3.14"))
        with self.assertRaisesRegex(ValueError, "contract"):
            check_init_spec(receipt, file_pin(root / "cold.json"))

    def test_native_v314_loader_requires_the_group_contract_before_weights(self):
        from student_pilot import carrier_c1_run as run, full_ft
        root = Path(tempfile.mkdtemp(prefix="group-contract-", dir=os.environ["TMPDIR"]))
        self.model.trace_program_version = "3.14"
        self.model.carrier_placement = "append_after_temporal_group_video_tokens_v1"
        self.model.training_mode = "mixed"
        self.model.frame_layout = "spread"
        self.model.carrier_position_policy = "native_v1"
        write(root / "weights.json", {})
        torch.save(self.state, root / "heads.pt")
        artifact = dict(schema="carrier-c1-artifact-v1", trace_program_version="3.14",
                        pose_backing="lm_final_norm", depth_backing="lm_final_norm",
                        placement=self.model.carrier_placement, training_mode=self.model.training_mode,
                        full_weights=file_pin(root / "weights.json"), heads=file_pin(root / "heads.pt"))
        write(root / "artifact.json", artifact)
        with patch.object(full_ft, "load_export") as weights:
            with self.assertRaisesRegex(ValueError, "trained.*contract"):
                run.load_artifact(self.model, file_pin(root / "artifact.json"))
        weights.assert_not_called()


if __name__ == "__main__":
    unittest.main()
