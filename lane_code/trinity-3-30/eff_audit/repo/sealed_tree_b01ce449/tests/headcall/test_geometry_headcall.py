"""Head-call forwards of a geometry-input model (HC/HX on PDG v3): the gated G3T connector receives the row's features
in the decode prefill, in the scheduled-sampling session forward and in the matched discarded forward, exactly once per
vision forward; a forward that would drop them refuses.

A tiny Qwen3.5 gets phase 1's camera and point-depth heads (test_prefill.camera_model) and PDG v3's gated
Spatial-MLLM connector (geometry_input.attach) with its tanh gate opened, so the features measurably move the states the
heads read.
"""
import unittest

from common import tokenizer
from test_prefill import camera_model, video64_batch
from headcall import phase1
from headcall.decode import DecodeConfig, headcall_generate
from headcall.heads import Phase1Heads

FEATURE_DIM = 4


def gated_settings():
    from student_pilot import geometry_input
    return geometry_input.normalize({
        "schema": geometry_input.SCHEMA, "injection": geometry_input.GATED_SPATIAL_INJECTION, "layer": 23,
        "feature_dim": FEATURE_DIM, "frames_per_token": 2,
        "projector": dict(geometry_input.SPATIAL_MLLM_GATED),
        "encoder": {"name": "g3t", "repository": "fixture", "revision": "fixture", "source_sha256": "0" * 64,
                    "input": "square_pad_518", "pooling": "roi_align_valid_region"},
        "store": {"manifest": "/fixture/manifest.jsonl", "manifest_sha256": "0" * 64}})


def geometry_model():
    import torch
    from student_pilot import geometry_input
    model = camera_model()
    module = geometry_input.attach(model, gated_settings())
    with torch.no_grad():
        module.projector.gate.fill_(0.5)
    model.eval()
    return model, module


def features(batch, seed):
    import torch
    from student_pilot import geometry_input
    tokens = int(batch["video_grid_thw"].prod(-1).sum()) // 4
    generator = torch.Generator().manual_seed(seed)
    return torch.randn(tokens, geometry_input.token_width(gated_settings()), generator=generator)


class GeometryHeadcallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.geometry = geometry_model()
        cls.batch = video64_batch()

    def test_prefill_feeds_the_features_once_and_they_reach_the_head_states(self):
        import torch
        calls = self.geometry.calls
        _, first = phase1.prefill(self.model, {**self.batch, "geometry_features": features(self.batch, 1)})
        self.assertEqual(self.geometry.calls, calls + 1)
        self.assertIsNone(self.geometry._pending)
        _, again = phase1.prefill(self.model, {**self.batch, "geometry_features": features(self.batch, 1)})
        _, other = phase1.prefill(self.model, {**self.batch, "geometry_features": features(self.batch, 2)})
        self.assertTrue(torch.equal(first["carrier_states"], again["carrier_states"]))
        self.assertFalse(torch.allclose(first["carrier_states"], other["carrier_states"]))

    def test_forwards_without_features_refuse_and_leave_nothing_pending(self):
        with self.assertRaisesRegex(ValueError, "needs the row's geometry features"):
            phase1.prefill(self.model, dict(self.batch))
        with self.assertRaisesRegex(ValueError, "needs the row's geometry features"):
            phase1.session_forward(self.model, dict(self.batch))
        from headcall.rows import discarded_forward
        with self.assertRaisesRegex(ValueError, "needs the row's geometry features"):
            discarded_forward(self.model, dict(self.batch))
        self.assertIsNone(self.geometry._pending)

    def test_features_on_a_model_without_geometry_refuse(self):
        plain = camera_model()
        with self.assertRaisesRegex(ValueError, "without a geometry input"):
            phase1.prefill(plain, {**self.batch, "geometry_features": features(self.batch, 1)})

    def test_session_forward_equals_the_decode_prefill(self):
        """Training's scheduled-sampling session and the evaluator's decode prefill read the same head states."""
        import numpy
        feats = features(self.batch, 3)
        _, states = phase1.prefill(self.model, {**self.batch, "geometry_features": feats})
        decode = phase1.session_from_states(self.model, states)
        session = phase1.session_forward(self.model, {**self.batch, "geometry_features": feats})
        numpy.testing.assert_allclose(session.raw_pose, decode.raw_pose, rtol=1e-5, atol=1e-6)
        numpy.testing.assert_allclose(session.depth(2, [500, 500]), decode.depth(2, [500, 500]), rtol=1e-5, atol=1e-6)

    def test_discarded_forward_consumes_the_features(self):
        from headcall.rows import discarded_forward
        calls = self.geometry.calls
        discarded_forward(self.model, {**self.batch, "geometry_features": features(self.batch, 4)})
        self.assertEqual(self.geometry.calls, calls + 1)
        self.assertIsNone(self.geometry._pending)

    def test_prompt_batch_keeps_the_geometry_features(self):
        import torch
        from headcall.rows import prompt_batch
        feats = features(self.batch, 5)
        labels = torch.full_like(self.batch["input_ids"], -100)
        labels[0, -2:] = self.batch["input_ids"][0, -2:]
        encoding = {**self.batch, "labels": labels, "geometry_features": feats}
        prompt = prompt_batch(encoding)
        self.assertIs(prompt["geometry_features"], feats)
        self.assertEqual(prompt["input_ids"].shape[1], self.batch["input_ids"].shape[1] - 2)

    def test_headcall_decode_of_a_geometry_model_prefills_once(self):
        calls = self.geometry.calls
        config = DecodeConfig([tokenizer().eos_token_id], max_new_tokens=6, max_calls=4, max_call_tokens=32)
        result = headcall_generate(self.model, {**self.batch, "geometry_features": features(self.batch, 6)}, tokenizer(),
                                   Phase1Heads.from_model(self.model), config)
        self.assertEqual(self.geometry.calls, calls + 1)  # the prefill; cached decode steps run no vision forward
        self.assertEqual(len(result.tokens), 6)


class EvaluatorHeadcallArmTests(unittest.TestCase):
    """A head-call arm's publication (training headcall block) refuses any eval option but carriers insert + decode."""

    def test_headcall_arm_refuses_without_carriers_or_decode(self):
        from student_pilot.orchard_eval.contracts import attached_pins
        publication = {"geometry": None, "camera": None, "auxiliary_heads": None, "weights": "full_weights",
                       "headcall": {"arm": "HX"}}
        for carriers, headcall in ((None, None), ("none", None), ("none", "decode"), ("insert", None), ("insert", "none")):
            with self.assertRaisesRegex(ValueError, "head-call arm"):
                attached_pins({}, "/fixture", publication, None, carriers, headcall)

    def test_other_publications_are_unchanged(self):
        from student_pilot.orchard_eval.contracts import attached_pins
        publication = {"geometry": None, "camera": None, "auxiliary_heads": None, "weights": "full_weights",
                       "headcall": None}
        self.assertEqual(attached_pins({"x": 1}, "/fixture", publication, None, None, None), {"x": 1})


if __name__ == "__main__":
    unittest.main()
