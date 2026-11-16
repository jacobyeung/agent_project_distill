import copy
import json
import os
from pathlib import Path
import unittest
import uuid

import continuation_packet as packet


class PacketProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.primary, cls.sources, cls.admission_pins, cls.evidence_pins, cls.raw = packet.load_inputs()
        cls.evidence = {
            key: json.loads(cls.raw[Path(pin["path"]).name])
            for key, pin in cls.evidence_pins.items()
            if key not in ("slot_sha_record", "terminal_accounting")
        }
        cls.selector = packet.native_selector()
        cls.base = json.loads((packet.ROOT / "source_k_b02e4385.json").read_bytes())
        cls.auth = json.loads((packet.ROOT / "source_k_4.json").read_bytes())
        cls.arm_map = json.loads((packet.ROOT / "source_k_1.json").read_bytes())
        cls.launch = json.loads((packet.ROOT / "source_k_launch.json").read_bytes())
        cls.contract = json.loads((packet.ROOT / "canary_contract.json").read_bytes())
        cls.derived = json.loads((packet.ROOT / "admission_06.json").read_bytes())
        cls.cases = packet.ROOT / "unit_cases"
        cls.cases.mkdir(exist_ok=True)

    def arguments(self, **changes):
        values = dict(base=copy.deepcopy(self.base), derived=copy.deepcopy(self.derived),
                      auth=copy.deepcopy(self.auth), arm_map=copy.deepcopy(self.arm_map),
                      launch=copy.deepcopy(self.launch), binding=copy.deepcopy(self.evidence["native_binding"]),
                      contract=copy.deepcopy(self.contract))
        values.update(changes)
        return packet.prove_arguments(**values)

    def slot(self, **changes):
        values = {
            key: self.raw[Path(self.evidence_pins[name]["path"]).name]
            for key, name in (("raw_slot", "slot_record"), ("raw_sha", "slot_sha_record"),
                              ("raw_complete", "native_complete"))
        }
        values.update(binding=copy.deepcopy(self.evidence["native_binding"]),
                      reader=copy.deepcopy(self.evidence["terminal_reader_result"]),
                      reconciliation=copy.deepcopy(self.evidence["reconciliation"]))
        values.update(changes)
        return packet.verify_slot(**values)

    def selector_case(self, checkpoint=True, corrupt=False, missing_rng=False, slot_step=544, marker_run="469ddece"):
        case = self.cases / uuid.uuid4().hex
        root, persistent = case / "native" / "469ddece", case / "persistent"
        root.mkdir(parents=True)
        persistent.mkdir()
        binding = copy.deepcopy(self.evidence["native_binding"])
        (root / "binding.json").write_bytes(packet.canonical(binding) + b"\n")
        (persistent / "binding.json").write_bytes((root / "binding.json").read_bytes())
        (persistent / "binding.json.sha256").write_text(packet.sha((root / "binding.json").read_bytes()) + "\n")
        (persistent / "RUN.json").write_text(json.dumps(dict(run=marker_run, first_job="169097", started_utc="fixture-only")))
        archive = b"synthetic selector archive, not a tensor or a state-restore fixture"
        (persistent / "A.tar").write_bytes(archive)
        (persistent / "A.sha256").write_text(packet.sha(archive) + "\n")
        (persistent / "A.json").write_text(json.dumps(dict(slot="A", step=slot_step, bytes=len(archive), verified=True)))
        if checkpoint:
            directory = root / packet.CHECKPOINT
            (directory / "shards").mkdir(parents=True)
            complete = copy.deepcopy(self.evidence["native_complete"])
            for name, pin in complete["files"].items():
                content = ("synthetic selector payload " + name).encode()
                pin.update(bytes=len(content), sha256=packet.sha(content))
                if not (missing_rng and name == "rng003.pt"):
                    (directory / name).write_bytes(content + (b"corrupt" if corrupt and name == "replicated.pt" else b""))
            (directory / "complete.json").write_bytes(packet.canonical(complete) + b"\n")
        return root, persistent

    def test_complete_build_proofs_pass_without_launch_authority(self):
        result = packet.evaluate()
        self.assertEqual(result["status"], "PASS_CPU_METADATA_AND_ARGUMENT_PROOFS_ONLY")
        self.assertFalse(result["launch_authorized"])
        self.assertFalse(result["reservation_authorized"])
        self.assertEqual(result["native_calls"], 0)

    def test_access_time_update_does_not_invalidate_unchanged_bytes(self):
        path = packet.ROOT / ("access_time_" + uuid.uuid4().hex + ".txt")
        path.write_bytes(b"unchanged bounded metadata")
        os.utime(path, ns=(0, path.stat().st_mtime_ns))
        self.assertEqual(packet.read_local(path.name), b"unchanged bounded metadata")

    def test_actual_slot_metadata_matches_wrapper_publication(self):
        self.assertEqual(self.slot()["status"], "PASS_HELD_METADATA_AGREEMENT")

    def test_wrong_slot_rejected(self):
        slot = copy.deepcopy(self.evidence["slot_record"])
        slot["slot"] = "B"
        with self.assertRaises(ValueError):
            self.slot(raw_slot=packet.canonical(slot))

    def test_boolean_slot_step_rejected(self):
        slot = copy.deepcopy(self.evidence["slot_record"])
        slot["step"] = True
        with self.assertRaises(ValueError):
            self.slot(raw_slot=packet.canonical(slot))

    def test_unverified_slot_rejected(self):
        slot = copy.deepcopy(self.evidence["slot_record"])
        slot["verified"] = False
        with self.assertRaises(ValueError):
            self.slot(raw_slot=packet.canonical(slot))

    def test_archive_digest_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.slot(raw_sha=b"0" * 64 + b"\n")

    def test_complete_marker_bytes_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.slot(raw_complete=packet.json_bytes(self.evidence["native_complete"]))

    def test_unstable_terminal_read_rejected(self):
        reader = copy.deepcopy(self.evidence["terminal_reader_result"])
        reader["files"]["A.json"]["stable"] = False
        with self.assertRaises(ValueError):
            self.slot(reader=reader)

    def test_changed_archive_size_rejected(self):
        reader = copy.deepcopy(self.evidence["terminal_reader_result"])
        reader["archives"]["A.tar"]["identity"]["bytes"] -= 1
        with self.assertRaises(ValueError):
            self.slot(reader=reader)

    def test_unexpected_slot_B_rejected(self):
        reader = copy.deepcopy(self.evidence["terminal_reader_result"])
        reader["files"]["B.json"]["status"] = "OK"
        with self.assertRaises(ValueError):
            self.slot(reader=reader)

    def test_wrong_source_prefix_rejected(self):
        reconciliation = copy.deepcopy(self.evidence["reconciliation"])
        reconciliation["baseline"]["prefix_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.slot(reconciliation=reconciliation)

    def test_all_nine_checkpoint_payloads_are_required(self):
        complete = copy.deepcopy(self.evidence["native_complete"])
        complete["files"].pop("rng003.pt")
        with self.assertRaises(ValueError):
            packet.checkpoint_inventory(complete, self.evidence["native_binding"])

    def test_extra_checkpoint_payload_rejected(self):
        complete = copy.deepcopy(self.evidence["native_complete"])
        complete["files"]["other.pt"] = complete["files"]["replicated.pt"]
        with self.assertRaises(ValueError):
            packet.checkpoint_inventory(complete, self.evidence["native_binding"])

    def test_boolean_payload_size_rejected(self):
        complete = copy.deepcopy(self.evidence["native_complete"])
        complete["files"]["rng000.pt"]["bytes"] = True
        with self.assertRaises(ValueError):
            packet.checkpoint_inventory(complete, self.evidence["native_binding"])

    def test_missing_rank_layout_rejected(self):
        complete = copy.deepcopy(self.evidence["native_complete"])
        complete["layouts"].pop()
        with self.assertRaises(ValueError):
            packet.checkpoint_inventory(complete, self.evidence["native_binding"])

    def test_native_dispatch_selects_latest_without_smoke(self):
        result = self.arguments()
        self.assertEqual(result["resume_pin"], "latest")
        self.assertIsNone(result["smoke_steps"])
        self.assertEqual(result["remaining_steps"], 456)
        self.assertIn("--nproc-per-node=4", result["launcher_argv_with_symbolic_paths"])

    def test_resetting_schedule_to_remaining_steps_rejected(self):
        derived = copy.deepcopy(self.derived)
        derived["recipe"]["steps"] = 456
        with self.assertRaises(ValueError):
            self.arguments(derived=derived)

    def test_changing_sampler_seed_rejected(self):
        derived = copy.deepcopy(self.derived)
        derived["recipe"]["seed"] += 1
        with self.assertRaises(ValueError):
            self.arguments(derived=derived)

    def test_changing_world_rejected(self):
        derived = copy.deepcopy(self.derived)
        derived["world_size"] = 8
        with self.assertRaises(ValueError):
            self.arguments(derived=derived)

    def test_changing_wall_rule_rejected(self):
        derived = copy.deepcopy(self.derived)
        derived["recipe"]["stop_before_seconds"] = 1800
        with self.assertRaises(ValueError):
            self.arguments(derived=derived)

    def test_cold_start_argument_rejected(self):
        auth = copy.deepcopy(self.auth)
        auth["resume"] = None
        with self.assertRaises(ValueError):
            self.arguments(auth=auth)

    def test_configuration_permission_is_not_new_GO(self):
        auth = copy.deepcopy(self.auth)
        auth["production_go_granted"] = True
        with self.assertRaises(ValueError):
            self.arguments(auth=auth)

    def test_wrong_arm_configuration_rejected(self):
        with self.assertRaises(ValueError):
            self.arguments(arm_map={"0": "other"})

    def test_wrong_run_directory_rejected(self):
        launch = copy.deepcopy(self.launch)
        launch["run_directory"] = "/tmp/other"
        with self.assertRaises(ValueError):
            self.arguments(launch=launch)

    def test_native_selector_chooses_u_for_complete_metadata_fixture(self):
        root, persistent = self.selector_case()
        self.assertEqual(self.selector.main(root, persistent, "990001"), "u")

    def test_native_selector_refuses_corrupted_fixture_payload(self):
        root, persistent = self.selector_case(corrupt=True)
        with self.assertRaises(ValueError):
            self.selector.main(root, persistent, "990001")

    def test_native_selector_refuses_missing_rng(self):
        root, persistent = self.selector_case(missing_rng=True)
        with self.assertRaises(ValueError):
            self.selector.main(root, persistent, "990001")

    def test_native_selector_refuses_cold_fallback_over_slot(self):
        root, persistent = self.selector_case(checkpoint=False)
        with self.assertRaises(ValueError):
            self.selector.main(root, persistent, "990001")

    def test_native_selector_refuses_older_checkpoint(self):
        root, persistent = self.selector_case(slot_step=545)
        with self.assertRaises(ValueError):
            self.selector.main(root, persistent, "990001")

    def test_native_selector_refuses_foreign_run_marker(self):
        root, persistent = self.selector_case(marker_run="foreign")
        with self.assertRaises(ValueError):
            self.selector.main(root, persistent, "990001")

    def test_native_selector_requires_actual_job_identity(self):
        root, persistent = self.selector_case()
        with self.assertRaises(ValueError):
            self.selector.main(root, persistent, None)

    def test_input_inventory_rejects_escape(self):
        with self.assertRaises(ValueError):
            packet.input_inventory({"x": {"path": "/logical/inputs/../escape", "sha256": "a" * 64}},
                                   {}, "/logical/inputs")

    def test_input_inventory_rejects_conflicting_pins(self):
        with self.assertRaises(ValueError):
            packet.input_inventory({"x": [{"path": "/logical/inputs/a", "sha256": "a" * 64},
                                          {"path": "/logical/inputs/a", "sha256": "b" * 64}]},
                                   {}, "/logical/inputs")

    def test_external_staged_inputs_are_not_inventoried(self):
        result = packet.input_inventory({"x": {"path": "/external/model", "sha256": "a" * 64}},
                                        {}, "/logical/inputs")
        self.assertEqual(result["members"], [])
        self.assertFalse(result["staged_inputs_presence_verified_now"])

    def test_timing_is_conditional_and_preserves_original_slot(self):
        result = packet.timing_projection(self.evidence["terminal_snapshot"], self.evidence["native_audit"],
                                          self.evidence["reconciliation"], self.derived)
        self.assertFalse(result["completion_guaranteed"])
        self.assertFalse(result["restore_measured"])
        self.assertFalse(result["fresh_project_space_gate_passed"])
        self.assertEqual(result["reference_free_after_B_bytes"], 439526359040 - 112988477440)
        self.assertTrue(result["slot_A_preserved_while_B_is_written"])


if __name__ == "__main__":
    os.umask(0o077)
    unittest.main(verbosity=2)
