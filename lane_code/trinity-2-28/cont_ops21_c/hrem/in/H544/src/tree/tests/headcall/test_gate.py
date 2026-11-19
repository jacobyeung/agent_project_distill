"""The phase-1 gate on held-out rows: phase 1's scenes and thresholds, refusals as failures, re-executed decisions."""
import gzip
import json
import os
import tempfile
import unittest

import common  # noqa: F401  (puts the package on the path)
from headcall import gate_eval, phase1
from headcall.heads import HeadBackend, NoisyHeads, OracleHeads
from headcall.protocol import CallError
from rows_fixture import direction_row, distance_row

HELDOUT = phase1.heldout_scenes()


def rows_on(scenes):
    rows = []
    for k, scene in enumerate(scenes):
        for make in (direction_row, distance_row):
            row = make(qid="%s%d" % (make.__name__[:3], k))
            row["dataset"], row["scene"] = scene
            rows.append(row)
    return rows


class Refuser(HeadBackend):
    """Oracle values except one call kind, which the head refuses."""

    def __init__(self, refuse):
        self.oracle, self.refuse = OracleHeads(), refuse

    def begin(self, context):
        HeadBackend.begin(self, context)
        self.oracle.begin(context)

    def depth(self, frame, point):
        if self.refuse == "depth":
            raise CallError("head", "refused")
        return self.oracle.depth(frame, point)

    def pose(self, frame):
        if self.refuse == "pose":
            raise CallError("head", "refused")
        return self.oracle.pose(frame)


class RollOnly(OracleHeads):
    def pose(self, frame):
        value = OracleHeads.pose(self, frame)
        return value._replace(roll_deg=value.roll_deg + 8.0)


class Gate(unittest.TestCase):
    rows = rows_on(HELDOUT[:3])

    def test_uses_phase1_thresholds_and_scene_list(self):
        self.assertEqual(len(HELDOUT), 38)
        self.assertEqual(phase1.gate_thresholds(), phase1.gate_eval().GATE)
        self.assertEqual(phase1.gate_thresholds()["rotation_deg_median_max"], 5.2)
        self.assertEqual(phase1.gate_thresholds()["depth_abs_err_m_median_max"], 0.20)
        report = gate_eval.evaluate(self.rows, OracleHeads(), HELDOUT, [])
        self.assertEqual(report["thresholds"], phase1.gate_eval().GATE)

    def test_refuses_rows_off_the_list_or_in_training(self):
        off = [dict(self.rows[0], scene="v000000000000")]
        with self.assertRaises(ValueError):
            gate_eval.evaluate(off, OracleHeads(), HELDOUT, [])
        with self.assertRaises(ValueError):
            gate_eval.evaluate(self.rows, OracleHeads(), HELDOUT, [HELDOUT[0]])
        with self.assertRaises(ValueError):
            gate_eval.evaluate([], OracleHeads(), HELDOUT, [])

    def test_oracle_passes(self):
        report = gate_eval.evaluate(self.rows, OracleHeads(), HELDOUT, [])
        self.assertTrue(report["passed"], report["checks"])
        self.assertEqual(report["summary"]["row_decision_agreement"], 1.0)
        self.assertEqual(report["summary"]["rotation_deg"]["median"], 0.0)

    def test_a_refusal_is_a_failure_never_gt(self):
        for kind in ("depth", "pose"):
            report = gate_eval.evaluate(self.rows, Refuser(kind), HELDOUT, [])
            self.assertFalse(report["passed"])
            self.assertFalse(report["checks"]["call_refusals"])
            self.assertGreater(report["summary"]["call_refusals"], 0)
            self.assertEqual(report["summary"]["row_decision_agreement"], 0.0)
            if kind == "depth":
                self.assertEqual(report["summary"]["depth_abs_rel"], float("inf"))
            else:
                self.assertEqual(report["summary"]["position_m"]["median"], float("inf"))

    def test_rotation_error_sees_roll(self):
        report = gate_eval.evaluate(self.rows, RollOnly(), HELDOUT, [])
        self.assertAlmostEqual(report["summary"]["rotation_deg"]["median"], 8.0, places=6)
        self.assertFalse(report["checks"]["rotation_deg_median"])
        self.assertTrue(report["checks"]["heading_deg_median"])

    def test_decisions_are_re_executed_from_head_responses(self):
        class Behind(OracleHeads):  # the plant's depth puts it behind the stool: back-left
            def depth(self, frame, point):
                return 0.8 if tuple(point) == (300, 500) else OracleHeads.depth(self, frame, point)
        report = gate_eval.evaluate(self.rows, Behind(), HELDOUT, [])
        flipped = [r for r in report["per_row"] if r["category"] == "object_rel_direction_hard"]
        self.assertTrue(all(r["gt_decision"] == ["label", "front-left"] or r["gt_decision"] == ("label", "front-left")
                            for r in flipped))
        self.assertTrue(all(tuple(r["head_decision"]) == ("label", "back-left") for r in flipped))
        self.assertEqual(report["summary"]["row_decisions"]["object_rel_direction_hard"]["rate"], 0.0)
        self.assertEqual(report["summary"]["row_decisions"]["object_abs_distance"]["rate"], 1.0)

    def test_noisy_heads_inside_and_outside(self):
        inside = NoisyHeads(OracleHeads(), depth_log_sigma=0.01, position_sigma_m=0.01, heading_sigma_deg=0.5,
                            pitch_sigma_deg=0.5, roll_sigma_deg=0.3, view_sigma_deg=0.2, seed=2)
        self.assertTrue(gate_eval.evaluate(self.rows, inside, HELDOUT, [])["checks"]["position_m_median"])
        outside = NoisyHeads(OracleHeads(), depth_log_sigma=0.5, position_sigma_m=0.8, heading_sigma_deg=30.0,
                             pitch_sigma_deg=10.0, seed=2)
        report = gate_eval.evaluate(self.rows, outside, HELDOUT, [])
        self.assertFalse(report["passed"])
        self.assertFalse(report["checks"]["position_m_median"])

    def test_shuffled_control_draws_real_outputs(self):
        result = gate_eval.evaluate_with_shuffled(self.rows, OracleHeads(), HELDOUT, [])
        self.assertTrue(result["heads"]["passed"])
        self.assertGreater(result["shuffle_pool_values"], 0)
        self.assertFalse(result["shuffled"]["passed"])

    def test_cli_refuses_before_loading_a_checkpoint(self):
        tmp = tempfile.mkdtemp(dir=os.environ.get("HEADCALL_TEST_CACHE"))  # left in place: no deletions
        with gzip.open(os.path.join(tmp, "rows_g_heldout_calls.jsonl.gz"), "wt") as stream:
            stream.write(json.dumps(dict(self.rows[0], scene="v000000000000")) + "\n")
        census = os.path.join(tmp, "TRAINING_SCENES.json")
        json.dump({"scenes": []}, open(census, "w"))
        with self.assertRaises(ValueError):
            gate_eval.main(["--rows", tmp, "--training-scenes", census, "--out", os.path.join(tmp, "r.json"),
                            "--student", "x", "--adapter-dir", "x", "--heads-json", "x", "--heads-pt", "x"])


if __name__ == "__main__":
    unittest.main()
