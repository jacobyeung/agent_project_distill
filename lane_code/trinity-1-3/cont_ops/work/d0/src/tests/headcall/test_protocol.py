import unittest

from common import ROOT  # noqa: F401  (puts headcall on the path)
from headcall.geometry import (Reference, angles_of_rotation, grid_to_raster, pose_from_gravity_rt, raster_to_grid,
                               rotation_from_angles)
from headcall.heads import HeadContext, Phase1Heads
from headcall.protocol import (DEPTH_FRAMES, EXPECTED_TRANSFORMERS_VERSION, FRAME_ANCHORS, FRAME_ORIGIN, GROUPS,
                               POSE_FRAMES, Call, CallError, PoseValue, anchor_candidates, anchor_frame, exchange,
                               exchanges, format_depth, format_pose, frame_to_group, group_of_frame, group_to_frame,
                               max_frame_index, parse_call, parse_response, render_call, render_response,
                               strip_exchanges)


class RoundTrip(unittest.TestCase):
    def test_render_parse(self):
        for call in (Call("depth", 4, (412, 280)), Call("depth", 32, (0, 1000)), Call("pose", 1, None),
                     Call("pose", 32, None)):
            text = render_call(call)
            body = text[len("<tool_call>"):-len("</tool_call>")]
            parsed = parse_call(body)
            self.assertEqual(parsed.call, call)
            self.assertTrue(parsed.strict, parsed)

    def test_spec_example(self):
        self.assertEqual(render_call(Call("depth", 4, (412, 280))),
                         '<tool_call>{"name": "depth", "frame": 4, "point": [412, 280]}</tool_call>')
        self.assertEqual(render_response(format_depth(1.84)), "<tool_response>1.84 m</tool_response>")

    def test_response_values(self):
        self.assertAlmostEqual(parse_response("depth", format_depth(1.844)), 1.84)
        pose = PoseValue((0.321, -1.1, 0.05), -35.4, 12.6, 3.4, (60.2, 46.7))
        text = format_pose(pose)
        self.assertEqual(text, "position (0.32, -1.10, 0.05) m, heading 35 degrees right, pitch 13 degrees up, "
                               "roll 3 degrees left, view 60 x 47 degrees")
        back = parse_response("pose", text)
        self.assertEqual(back.position, (0.32, -1.10, 0.05))
        self.assertEqual((back.heading_deg, back.pitch_deg, back.roll_deg, back.view_deg), (-35.0, 13.0, 3.0,
                                                                                            (60.0, 47.0)))
        self.assertEqual(format_pose(back), text)
        # the origin frame has no view (phase 1's pose head predicts none for frame 1)
        self.assertEqual(format_pose(PoseValue((0.0, -0.001, 0.0), 0.2, -0.3)),
                         "position (0.00, 0.00, 0.00) m, heading 0 degrees, pitch 0 degrees, roll 0 degrees")
        self.assertIsNone(parse_response("pose", "position (0.00, 0.00, 0.00) m, heading 0 degrees, pitch 0 degrees,"
                                                 " roll 0 degrees, view 60 x degrees"))
        self.assertIsNone(parse_response("depth", "error: no surface"))

    def test_bad_values_rejected(self):
        for bad in (0.0, -1.0, float("nan"), float("inf"), "1.0"):
            with self.assertRaises(ValueError):
                format_depth(bad)
        with self.assertRaises(ValueError):
            render_response("1 m</tool_response>")
        with self.assertRaises(CallError):
            render_call(Call("depth", 0, (1, 2)))
        with self.assertRaises(CallError):
            render_call(Call("depth", 1, (1, 2)))
        for odd in range(3, 32, 2):
            with self.assertRaises(CallError):
                render_call(Call("pose", odd, None))
            with self.assertRaises(CallError):
                render_call(Call("depth", odd, (100, 100)))

    def test_exchanges(self):
        text = ("a " + exchange(Call("pose", 2, None), PoseValue((0, 0, 0), 10, 0)) + " b "
                + exchange(Call("depth", 2, (5, 6)), 2.5) + " c <tool_call>{\"name\": \"pose\", \"frame\": 4}"
                "</tool_call> d")
        found = exchanges(text)
        self.assertEqual(len(found), 3)
        self.assertEqual(found[1][4], "2.50 m")
        self.assertIsNone(found[2][4])
        self.assertEqual(text[found[0][0]:found[0][1]], render_call(Call("pose", 2, None)))
        self.assertEqual(strip_exchanges(text), "a  b  c  d")


class Repairs(unittest.TestCase):
    CASES = [
        (' \n{"name": "depth", "frame": 4, "point": [412, 280]}\n ', ()),
        ('```json\n{"name": "depth", "frame": 4, "point": [412, 280]}\n```', ("code_fence",)),
        ('<function=depth>\n<parameter=frame>\n4\n</parameter>\n<parameter=point>\n[412, 280]\n</parameter>\n'
         '</function>', ("xml_function",)),
        ('{"name": "depth", "frame": 4, "point": [412, 280],}', ("trailing_comma",)),
        ('{"name": "depth", "frame": 4, "point": [412, 280]', ("closed_brackets",)),
        ('{"name": "depth", "frame": 4, "point": [412, 280', ("closed_brackets",)),
        ('{name: "depth", frame: 4, point: [412, 280]}', ("bare_keys",)),
        ("{'name': 'depth', 'frame': 4, 'point': (412, 280)}", ("python_literal",)),
        ('call: {"name": "depth", "frame": 4, "point": [412, 280]} done', ("surrounding_text",)),
        ('{"function": {"name": "depth", "arguments": "{\\"frame\\": 4, \\"point\\": [412, 280]}"}}',
         ("function_wrapper", "arguments_wrapper")),
        ('{"name": "depth", "arguments": {"frame": 4, "point": [412, 280]}}', ("arguments_wrapper",)),
        ('{"name": "point_depth", "frame": 4, "point": [412, 280]}', ("name_alias",)),
        ('{"name": "Depth", "frame": 4, "point": [412, 280]}', ("name_alias",)),
        ('{"name": "depth", "frame_index": 4, "point": [412, 280]}', ("frame_key",)),
        ('{"name": "depth", "frame": "4", "point": [412, 280]}', ("frame_type",)),
        ('{"name": "depth", "frame": 4.0, "point": [412, 280]}', ("frame_type",)),
        ('{"name": "depth", "frame": 4, "point": [411.6, 280.4]}', ("rounded_point",)),
        ('{"name": "depth", "frame": 4, "point": {"x": 412, "y": 280}}', ("point_dict",)),
        ('{"name": "depth", "frame": 4, "x": 412, "y": 280}', ("separate_xy",)),
        ('{"name": "depth", "frame": 4, "point": "(412, 280)"}', ("point_string",)),
        ('{"name": "depth", "frame": 4, "pixel": [412, 280]}', ()),
    ]

    def test_repairs(self):
        for body, expected in self.CASES:
            parsed = parse_call(body)
            self.assertEqual(parsed.call, Call("depth", 4, (412, 280)), body)
            for label in expected:
                self.assertIn(label, parsed.repairs, body)
            self.assertEqual(parsed.strict, not expected, body)

    def test_extra_keys_are_not_strict(self):
        parsed = parse_call('{"name": "pose", "frame": 6, "reason": "check"}')
        self.assertEqual(parsed.call, Call("pose", 6, None))
        self.assertEqual(parsed.extra, ("reason",))
        self.assertFalse(parsed.strict)


class Invalid(unittest.TestCase):
    CASES = [
        ("", "json"), ("depth at frame 4", "json"), ("[1, 2]", "json"), ('{"frame": 4}', "name"),
        ('{"name": "segment", "frame": 4}', "name"), ('{"name": 7, "frame": 4}', "name"),
        ('{"name": "pose"}', "frame"), ('{"name": "pose", "frame": 0}', "frame"),
        ('{"name": "pose", "frame": 3}', "frame"), ('{"name": "pose", "frame": 31}', "frame"),
        ('{"name": "depth", "frame": 1, "point": [412, 280]}', "frame"),
        ('{"name": "depth", "frame": 3, "point": [412, 280]}', "frame"),
        ('{"name": "pose", "frame": 33}', "frame"), ('{"name": "pose", "frame": true}', "frame"),
        ('{"name": "pose", "frame": "third"}', "frame"), ('{"name": "pose", "frame": 2.5}', "frame"),
        ('{"name": "depth", "frame": 4}', "point"), ('{"name": "depth", "frame": 4, "point": [412]}', "point"),
        ('{"name": "depth", "frame": 4, "point": [412, 280, 1]}', "point"),
        ('{"name": "depth", "frame": 4, "point": [-1, 280]}', "point"),
        ('{"name": "depth", "frame": 4, "point": [412, 1001]}', "point"),
        ('{"name": "depth", "frame": 4, "point": ["a", "b"]}', "point"),
        ('{"name": "depth", "frame": 4, "point": [NaN, 2]}', "point"),
        ('{"name": "depth", "frame": 4, "point": "near the chair"}', "point"),
        ('{"name": "depth", "frame": 4, "point": [true, 2]}', "point"),
        ('{{{{', "json"), ('{"name": "depth", "frame": 4, "point": [412, 280]' + "]" * 5000, "json"),
    ]

    def test_invalid(self):
        for body, code in self.CASES:
            parsed = parse_call(body)
            self.assertFalse(parsed.valid, body[:80])
            self.assertEqual(parsed.error.code, code, body[:80])

    def test_never_raises(self):
        for body in (None, 3, "\x00", "{" * 10000, '{"name": "depth", "frame": 1e400, "point": [1, 2]}',
                     '<function=pose><parameter=frame>x</parameter></function>'):
            parsed = parse_call(body)
            self.assertFalse(parsed.valid)

    def test_pose_frame_range_float(self):
        self.assertEqual(parse_call('{"name": "pose", "frame": 2.5}').error.code, "frame")


class Geometry(unittest.TestCase):
    def test_grid_mapping(self):
        self.assertEqual(raster_to_grid(0, 0), (2, 2))
        self.assertEqual(raster_to_grid(319, 239), (998, 998))
        for xr, yr in ((0, 0), (160, 120), (319, 239), (17, 203)):
            self.assertEqual(grid_to_raster(raster_to_grid(xr, yr)), (yr, xr))

    def test_reference_pose(self):
        import numpy
        poses = [numpy.eye(4) for _ in range(32)]
        first = numpy.eye(4)
        first[:3, :3] = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]  # OpenCV camera looking along world +y, z up
        poses[0] = first
        turned = first.copy()
        angle = numpy.radians(30)
        yaw = numpy.array([[numpy.cos(angle), -numpy.sin(angle), 0], [numpy.sin(angle), numpy.cos(angle), 0],
                           [0, 0, 1]])
        turned[:3, :3] = yaw @ first[:3, :3]
        turned[:3, 3] = [1.0, 2.0, 0.5]
        poses[4] = turned
        ref = Reference(poses)
        p1 = ref.pose(1)
        self.assertAlmostEqual(p1.heading_deg, 0.0, places=6)
        self.assertAlmostEqual(p1.pitch_deg, 0.0, places=6)
        p5 = ref.pose(5)
        self.assertAlmostEqual(p5.heading_deg, 30.0, places=6)  # counter-clockwise from above is a left turn
        numpy.testing.assert_allclose(p5.position, (1.0, 2.0, 0.5), atol=1e-9)

    def test_group_addressing_and_phase1_adapters(self):
        import numpy
        self.assertEqual(EXPECTED_TRANSFORMERS_VERSION, "5.12.1")
        self.assertEqual(GROUPS, 16)
        self.assertEqual(FRAME_ORIGIN, 1)
        self.assertEqual(FRAME_ANCHORS, tuple(range(2, 33, 2)))
        self.assertEqual(POSE_FRAMES, (1,) + tuple(range(2, 33, 2)))
        self.assertEqual(DEPTH_FRAMES, tuple(range(2, 33, 2)))
        self.assertEqual(max_frame_index("frame"), 32)
        self.assertEqual(max_frame_index("group"), 16)
        self.assertEqual(group_of_frame(2), 0)
        self.assertEqual(group_of_frame(32), 15)
        self.assertEqual(frame_to_group(2), 1)
        self.assertEqual(frame_to_group(32), 16)
        for bad_f in (0, 1, 3, 5, 31, 33):
            with self.assertRaises(CallError):
                group_of_frame(bad_f)
            with self.assertRaises(CallError):
                frame_to_group(bad_f)
        self.assertEqual(group_to_frame(1), 2)
        self.assertEqual(group_to_frame(16), 32)
        self.assertEqual(anchor_frame(1, "pose"), 1)
        self.assertEqual(anchor_frame(1, "depth"), 2)
        self.assertEqual(anchor_frame(2, "depth"), 2)
        self.assertEqual(anchor_frame(3, "depth"), 4)
        self.assertEqual(anchor_frame(3, "pose"), 4)
        self.assertEqual(anchor_frame(31, "depth"), 32)
        self.assertEqual(anchor_frame(32, "depth"), 32)
        self.assertEqual(anchor_candidates(1, "pose"), (1,))
        self.assertEqual(anchor_candidates(1, "depth"), (2,))
        self.assertEqual(anchor_candidates(2, "depth"), (2,))
        self.assertEqual(anchor_candidates(3, "depth"), (4, 2))
        self.assertEqual(anchor_candidates(3, "pose"), (4,))
        self.assertEqual(anchor_candidates(31, "depth"), (32, 30))
        self.assertEqual(anchor_candidates(32, "depth"), (32,))

        parsed_g = parse_call('{"name": "pose", "frame": 16}', addressing="group")
        self.assertTrue(parsed_g.strict)
        self.assertFalse(parse_call('{"name": "pose", "frame": 17}', addressing="group").valid)

    def test_rotation_angles_round_trip(self):
        import numpy
        rng = numpy.random.default_rng(3)
        for _ in range(200):
            q = rng.normal(size=4)
            x, y, z, w = q / numpy.linalg.norm(q)
            rot = numpy.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                               [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                               [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
            if abs(rot[2, 2]) > 0.99:
                continue
            angles = angles_of_rotation([rot[:, 0], rot[:, 1], rot[:, 2]])
            numpy.testing.assert_allclose(numpy.array(rotation_from_angles(*angles)), rot, atol=1e-12)
        # roll left = the camera's right side raised (counterclockwise seen from behind)
        rot = numpy.array(rotation_from_angles(0.0, 0.0, 10.0))
        self.assertGreater(rot[2, 0], 0.0)


class Phase1Adapter(unittest.TestCase):
    """Phase1Heads wraps student_pilot.head_api.HeadSession: pose(frame) -> (R, t, info), depth(frame, point)."""

    class Session(object):
        def __init__(self):
            self.r0 = numpy_rotation(0.0, -8.0, 2.0)

        def pose(self, frame):
            if frame == 1:
                return self.r0, [0.0, 0.0, 0.0], {"fov_hw_rad": None}
            group = group_of_frame(frame)
            return numpy_rotation(10.0 * group, -5.0, 1.0), [0.1 * group, 1.0, 0.0], {
                "fov_hw_rad": [0.80, 1.05]}

        def depth(self, frame, point):
            group = group_of_frame(frame)
            if point[0] > 990:
                raise ValueError("Points must be [x, y] or [K, 2] on the [0, 1000] grid")
            return float(group + 1) + point[0] * 0.001

    def test_session_values(self):
        import math
        heads = Phase1Heads.from_session(self.Session())
        heads.begin(HeadContext([]))
        origin = heads.answer(Call("pose", 1, None))
        self.assertEqual(origin.position, (0.0, 0.0, 0.0))
        self.assertAlmostEqual(origin.pitch_deg, -8.0, places=9)  # frame 1 keeps its own elevation, never 0
        self.assertAlmostEqual(origin.roll_deg, 2.0, places=9)
        self.assertIsNone(origin.view_deg)
        p8 = heads.answer(Call("pose", 8, None))
        self.assertEqual(p8.position, (0.30000000000000004, 1.0, 0.0))
        self.assertAlmostEqual(p8.heading_deg, 30.0, places=9)
        self.assertAlmostEqual(p8.roll_deg, 1.0, places=9)
        self.assertAlmostEqual(p8.view_deg[0], math.degrees(1.05), places=9)  # horizontal = fov_w
        self.assertAlmostEqual(p8.view_deg[1], math.degrees(0.80), places=9)
        self.assertAlmostEqual(heads.answer(Call("depth", 8, (500, 500))), 4.5, places=9)

    def test_refusals_are_call_errors(self):
        heads = Phase1Heads.from_session(self.Session())
        heads.begin(HeadContext([]))
        for call in (Call("pose", 7, None), Call("depth", 1, (500, 500)), Call("depth", 7, (500, 500))):
            with self.assertRaises(CallError):
                heads.answer(call)
        with self.assertRaises(CallError) as caught:
            heads.answer(Call("depth", 8, (995, 500)))
        self.assertEqual(caught.exception.code, "head")

    def test_needs_carriers(self):
        self.assertTrue(Phase1Heads.needs_carriers)
        heads = Phase1Heads.from_model(object())
        with self.assertRaises(ValueError):
            heads.begin(HeadContext([], batch={"input_ids": None}))


def numpy_rotation(heading, pitch, roll):
    import numpy
    return numpy.array(rotation_from_angles(heading, pitch, roll))


if __name__ == "__main__":
    unittest.main()
