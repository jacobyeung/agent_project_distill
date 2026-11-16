"""The derivation the traces state: unprojection, movements, directions and decisions."""
import math
import unittest

import numpy

import common  # noqa: F401  (puts the package on the path)
from headcall import derive as D
from headcall.geometry import Reference, backproject, rotation_from_angles, unproject
from headcall.protocol import PoseValue, format_value, parse_response
from rows_fixture import closest_row, direction_row, distance_row, motion_row


def camera(heading, pitch, roll, position):
    pose = numpy.eye(4)
    pose[:3, :3] = numpy.array(rotation_from_angles(heading, pitch, roll))
    pose[:3, 3] = position
    return pose


class Unproject(unittest.TestCase):
    def test_equals_the_exact_pinhole_with_a_centred_principal_point(self):
        """With frame 1 at the world origin facing +y, the reference is the world; unproject of the exact pose
        values equals backproject with intrinsics (fx = W / 2 tan(fov_w / 2), cx = W / 2)."""
        first = camera(0.0, 0.0, 0.0, [0.0, 0.0, 0.0])
        rng = numpy.random.default_rng(5)
        for _ in range(50):
            h, p, r = rng.uniform(-180, 180), rng.uniform(-40, 30), rng.uniform(-15, 15)
            pose = camera(h, p, r, rng.uniform(-3, 3, 3))
            poses = [first] + [pose] * 31
            width, height, fov_w, fov_h = 640.0, 480.0, 60.0, 47.0
            fx = width / (2 * math.tan(math.radians(fov_w) / 2))
            fy = height / (2 * math.tan(math.radians(fov_h) / 2))
            k = [[fx, 0, width / 2], [0, fy, height / 2], [0, 0, 1]]
            ref = Reference([q.tolist() for q in poses], intrinsics=[k] * 32, calibration_hw=(480, 640))
            value = ref.pose(2)
            numpy.testing.assert_allclose(value.view_deg, (fov_w, fov_h), atol=1e-9)
            point, depth = (int(rng.integers(0, 1001)), int(rng.integers(0, 1001))), float(rng.uniform(0.5, 6))
            exact = backproject(point, depth, k, pose.tolist(), (480, 640))
            numpy.testing.assert_allclose(unproject(point, depth, value), exact, atol=1e-9)

    def test_printed_values_reproduce_the_derived_text(self):
        value = PoseValue((0.123, 1.456, -0.2), 33.3, -12.4, 2.6, (58.4, 45.1))
        printed = parse_response("pose", format_value("pose", value))
        items = [{"kind": "point", "pose": 0, "depth": 1, "at": [700, 300]}]
        texts, results = D.evaluate(items, [printed, 1.84])
        self.assertEqual(texts[0], D.point_text(unproject([700, 300], 1.84, printed)))
        self.assertEqual(results[0], D.printed_point(unproject([700, 300], 1.84, printed)))
        with self.assertRaises(ValueError):
            D.evaluate(items, [None, 1.84])  # an error response has no derived value


class Directions(unittest.TestCase):
    def test_angle_sign_and_labels(self):
        self.assertAlmostEqual(D.horizontal_angle((0, 0), (0, 1), (-1, 1)), 45.0)  # left is positive
        options = ["front-left", "front-right", "back-left", "back-right"]
        self.assertEqual(D.direction_label(45.0, options), "front-left")
        self.assertEqual(D.direction_label(-100.0, options), "back-right")
        self.assertEqual(D.direction_label(140.0, ["left", "right", "back"]), "back")
        self.assertEqual(D.direction_label(100.0, ["left", "right", "back"]), "left")
        self.assertIsNone(D.direction_label(10.0, ["north", "south"]))
        self.assertEqual(D.direction_text(-23.4), "23 degrees right of straight ahead, in front")
        self.assertEqual(D.counterclockwise(-52.0), 308)

    def test_answer_supported(self):
        row = direction_row()
        _, results = D.evaluate(row["head_derived"], D.values_of([r["name"] for r in row["head_calls"]],
                                                                 [r["response"] for r in row["head_calls"]]))
        self.assertTrue(D.answer_supported(row, row["head_derived"], results))
        self.assertFalse(D.answer_supported(dict(row, answer="B"), row["head_derived"], results))
        abs_row = {"answer": "308", "options": []}
        items = [{"kind": "absolute_direction", "points": [0, 1, 2]}]
        self.assertTrue(D.answer_supported(abs_row, items, [-60.0]))   # 300 vs 308: within 15 degrees
        self.assertFalse(D.answer_supported(abs_row, items, [-80.0]))  # 280 vs 308

    def test_moved_from_the_origin(self):
        items = [{"kind": "moved", "from": None, "to": 0}]
        texts, _ = D.evaluate(items, [PoseValue((3.0, 4.0, 0.0), -20.0, 0.0)])
        self.assertEqual(texts, ["moved 5.00 m, turned 20 degrees right"])


def derived_of(row, responses=None):
    responses = responses or [r["response"] for r in row["head_calls"]]
    return D.evaluate(row["head_derived"], D.values_of([r["name"] for r in row["head_calls"]], responses))


class MetricDecisions(unittest.TestCase):
    """distance, closest, ego_motion, movement_direction and displacement, and the one decision rule the converters,
    scheduled sampling and the gate share."""

    def test_distance_text_units_and_decision(self):
        items = [{"kind": "distance", "points": [0, 1], "unit": "cm"}]
        self.assertEqual(D.length_text(1.234, "cm"), "123 cm")
        self.assertEqual(D.length_text(1.234), "1.23 m")
        row = distance_row()
        texts, results = derived_of(row)
        self.assertTrue(texts[2].endswith(" m"))
        self.assertEqual(D.decision(row, row["head_derived"], results), ("distance", results[2]))
        self.assertTrue(D.answer_supported(row, row["head_derived"], results))
        far = dict(row, answer="%.2f" % (results[2] * 1.5))
        self.assertFalse(D.answer_supported(far, row["head_derived"], results))
        cm_row = {"answer": str(int(round(results[2] * 100))), "options": []}
        self.assertTrue(D.answer_supported(cm_row, row["head_derived"][:2] + items, results))

    def test_distance_tolerance_is_ten_percent_or_ten_centimetres(self):
        self.assertTrue(D.same_decision(("distance", 3.0), ("distance", 3.29)))
        self.assertFalse(D.same_decision(("distance", 3.0), ("distance", 3.31)))
        self.assertTrue(D.same_decision(("distance", 0.5), ("distance", 0.59)))
        self.assertFalse(D.same_decision(("distance", 0.5), ("distance", 0.61)))
        self.assertIsNone(D.same_decision(None, ("distance", 1.0)))

    def test_closest_candidate(self):
        row = closest_row()
        texts, results = derived_of(row)
        self.assertTrue(texts[3].endswith("so the closest is the lamp"), texts[3])
        self.assertEqual(D.decision(row, row["head_derived"], results), ("closest", "lamp"))
        self.assertTrue(D.answer_supported(row, row["head_derived"], results))
        self.assertFalse(D.answer_supported(dict(row, answer="B"), row["head_derived"], results))

    def test_ego_motion_in_the_first_cameras_heading_frame(self):
        a = PoseValue((1.0, 2.0, 0.0), 90.0, 0.0)          # facing -x
        b = PoseValue((-1.0, 2.5, 0.3), 45.0, 0.0)         # 2 m along -x (forward), 0.5 m along +y
        forward, right, up, turn = D.ego_motion(a, b)
        self.assertAlmostEqual(forward, 2.0)
        self.assertAlmostEqual(right, 0.5)                 # facing -x (west, y north), +y is to the right
        self.assertAlmostEqual(up, 0.3)
        self.assertAlmostEqual(turn, -45.0)
        self.assertEqual(D.movement_label((2.0, -0.5, 0.3, 0.0)), "forward")
        self.assertEqual(D.movement_label((-0.2, -0.5, 0.0, 0.0)), "left")
        with self.assertRaises(ValueError):
            D.movement_label((0.501, 0.499, 0.0, 0.0))     # both print 0.50: degenerate

    def test_movement_and_displacement_rows(self):
        row = motion_row()
        texts, results = derived_of(row)
        self.assertIn("1.50 m forward and 0.40 m right", texts[0])
        self.assertEqual(texts[1], "Forward motion dominates, so the primary direction is Forward")
        self.assertTrue(D.answer_supported(row, row["head_derived"], results))
        self.assertFalse(D.answer_supported(dict(row, answer="C"), row["head_derived"], results))
        no_option = dict(row, options=["A. Left", "B. Backward"], answer="A")
        self.assertFalse(D.answer_supported(no_option, row["head_derived"], results))
        disp = motion_row(category="camera_displacement")
        texts, results = derived_of(disp)
        self.assertEqual(texts[1], "about 1.55 m")
        self.assertTrue(D.answer_supported(disp, disp["head_derived"], results))
        self.assertFalse(D.answer_supported(dict(disp, answer="2.20"), disp["head_derived"], results))

    def test_gate_uses_the_same_decision(self):
        from headcall import gate_eval
        for row in (distance_row(), closest_row(), motion_row(), motion_row(category="camera_displacement"),
                    direction_row()):
            _, results = derived_of(row)
            self.assertEqual(gate_eval.row_decision(row, results), D.decision(row, row["head_derived"], results))


if __name__ == "__main__":
    unittest.main()
