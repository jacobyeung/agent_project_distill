from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import numpy as np

from student_pilot.carrier_c1_routing import OwnGeometry
from student_pilot.live_trace313 import LiveSession


class GroundingRuntimeTests(unittest.TestCase):
    def geometry(self):
        poses = np.zeros((32, 9), dtype=np.float32)
        poses[:, 6] = 1.
        poses[:, 7:] = 1.2
        return OwnGeometry(poses, [0., -1., 0.],
                           lambda frame, uv: np.full(len(uv), 2., dtype=np.float32))

    def test_missing_configured_geometry_binds_same_checkpoint_heads(self):
        owner = NS(geometry=None, geometry_error="geometry_missing", allow_own_geometry_fallback=True)
        session = LiveSession(owner, program_version="3.14")
        own = self.geometry()
        session.bind_state(NS(geometry=own, geometry_error=None))
        self.assertIs(session.geometry.geometry, own)
        self.assertIs(owner.geometry, session.geometry)
        self.assertIsNone(owner.geometry_error)
        self.assertEqual(owner.geometry_source, "same_checkpoint_own")

    def test_missing_own_values_refuse(self):
        owner = NS(geometry=None, geometry_error="geometry_missing", allow_own_geometry_fallback=True)
        session = LiveSession(owner, program_version="3.14")
        with self.assertRaisesRegex(ValueError, "same_checkpoint_geometry_unavailable"):
            session.bind_state(NS(geometry=None, geometry_error="missing_camera"))

    def test_configured_geometry_is_not_replaced(self):
        geo = NS(kind="gt")
        owner = NS(geometry=geo, allow_own_geometry_fallback=True)
        session = LiveSession(owner, program_version="3.14")
        session.bind_state(NS(geometry=self.geometry(), geometry_error=None))
        self.assertIs(session.geometry, geo)

    def test_names_come_from_question_and_options_only(self):
        from student_pilot.s1_grounding import candidate_names
        self.assertEqual(candidate_names("How far is the chair from the table?", []), ("chair", "table"))
        self.assertNotIn("bed", candidate_names("How large is the room?", []))
        self.assertEqual(candidate_names("Which object?", ["A. chair", "B. table"]), ("chair", "table"))

    def test_default_policy_and_frame_identity_are_bound(self):
        from student_pilot.s1_grounding import build_backend
        row = dict(question_type="object_abs_distance",
                   student_input=dict(question="How far is the chair from the table?", options=[]))
        batch = dict(frame_indices=list(range(32)), video_sha256="a"*64)
        root = Path(__file__).parents[3] / "work/tmp/tests/runtime_backend"
        root.mkdir(exist_ok=True)
        backend = build_backend(row, batch, dict(sha256="b"*64), root)
        self.assertEqual(backend.config["ground_candidate_policy"]["name"], "routed_default_v1")
        self.assertEqual(backend.config["candidate_universe"], ["chair", "table"])
        self.assertTrue(backend.allow_own_geometry_fallback)
        with self.assertRaisesRegex(ValueError, "source_indices"):
            build_backend(row, {**batch, "frame_indices": [0]*32}, dict(sha256="b"*64), root)


if __name__ == "__main__":
    unittest.main()
