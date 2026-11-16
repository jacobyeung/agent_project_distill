"""The decode prefill of a model with phase 1's camera heads: one forward, carrier embeddings in the cache.

A tiny Qwen3.5 (the test asset's config with a 4-block ViT, so phase 1's point-depth head can read ViT blocks 1, 2
and 4) gets phase 1's camera, gravity, scale and point-depth heads through phase 1's own attach(). The learned
carrier tokens c_first / c_rest are set well away from zero so that a cache built from the raw <|fim_middle|>
embedding differs measurably from one built with training's embedding hook.
"""
import unittest

from common import TINY, Script, eos_ids, ids, one, tokenizer
from headcall import phase1
from headcall.decode import DecodeConfig, _language_core, headcall_generate
from headcall.heads import Phase1Heads
from headcall.protocol import Call, render_call

SMALL_DEPTH = {"weight": 0.5, "d_proj": 16, "mlp_hidden": 16, "num_heads": 2, "context_depth": 1, "vit_layers": [1, 2, 4],
               "num_points_per_frame": 8}


def camera_model():
    import torch
    from transformers import AutoConfig, AutoModelForImageTextToText
    config = AutoConfig.from_pretrained(TINY)
    config.vision_config.depth = 4
    torch.manual_seed(0)
    model = AutoModelForImageTextToText.from_config(config).float().eval()
    settings = phase1._module("camera_config").normalize({
        "weight": 1.0, "weight_gravity": 0.5, "weight_scale": 0.2, "embed_dim": 16, "num_heads": 2, "trunk_depth": 2,
        "refine_iterations": 2, "supervision": {"path": "/fixture/bank.npz", "sha256": "0" * 64},
        "point_depth": dict(SMALL_DEPTH)})
    heads = phase1.auxiliary_losses().attach(model, None, tokenizer(), settings)
    with torch.no_grad():
        heads.camera.tokens.normal_(0.0, 0.5)
        heads.camera.head.pose_branch.fc2.bias[7:9] += 1.0  # a printable field of view (~57 degrees) when untrained
    return model


def video64_batch():
    import numpy
    from transformers import AutoProcessor
    from transformers.video_utils import VideoMetadata
    processor = AutoProcessor.from_pretrained(TINY)
    video = (numpy.random.RandomState(2).rand(32, 64, 64, 3) * 255).astype(numpy.uint8)
    metadata = VideoMetadata(total_num_frames=32, fps=2.0, frames_indices=list(range(32)), width=64, height=64)
    messages = [{"role": "user", "content": [{"type": "video"}, {"type": "text", "text": "Where is the chair?"}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    batch = dict(processor(text=[text], videos=[video], video_metadata=[metadata], do_sample_frames=False,
                           return_tensors="pt", return_metadata=True))
    batch.pop("video_metadata", None)
    return phase1.insert_carriers(batch, tokenizer())


class Forced(object):
    """A model wrapper whose next token follows a script (attributes such as the heads resolve on the model)."""

    def __init__(self, model, policy, prompt_length):
        self.model, self.policy, self.prompt_length = model, policy, prompt_length
        self.raw, self.history = [], []

    def __getattr__(self, name):
        return getattr(self.__dict__["model"], name)

    def __call__(self, **kwargs):
        import torch
        out = self.model(**kwargs)
        if kwargs.get("past_key_values") is None:
            self.history = kwargs["input_ids"][0].tolist()
        else:
            self.history.append(int(kwargs["input_ids"][0, 0]))
        self.raw.append((len(self.history) - 1, out.logits[0, -1].clone()))
        forced = torch.full_like(out.logits[:, -1:], -1e4)
        forced[0, 0, self.policy(self.history[self.prompt_length:])] = 0.0
        out.logits = forced
        return out


class SinglePrefill(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = camera_model()
        cls.batch = video64_batch()

    def multi_token_forwards(self, run):
        """Number of forwards over more than one token while `run()` executes (final-norm calls)."""
        calls = []
        norm = phase1.auxiliary_losses().final_norm(self.model)
        handle = norm.register_forward_hook(lambda module, args, output: calls.append(output.shape[1]))
        try:
            result = run()
        finally:
            handle.remove()
        return sum(1 for length in calls if length > 1), result

    def test_one_forward_builds_the_session(self):
        import numpy
        heads = Phase1Heads.from_model(self.model)
        config = DecodeConfig(eos_ids(), max_new_tokens=4)
        count, _ = self.multi_token_forwards(lambda: headcall_generate(self.model, self.batch, tokenizer(), heads,
                                                                       config))
        self.assertEqual(count, 1, "the prefill must be the only multi-token forward (no second session forward)")
        reference = phase1.head_api().HeadSession.from_forward(self.model, self.batch)
        numpy.testing.assert_allclose(heads.session.raw_pose, reference.raw_pose, atol=1e-5)
        numpy.testing.assert_allclose(heads.session.gravity_up, reference.gravity_up, atol=1e-5)
        self.assertAlmostEqual(heads.session.depth(4, [300, 700]), reference.depth(4, [300, 700]), places=5)
        r, t, info = heads.session.pose(8)
        r0, t0, _ = reference.pose(8)
        numpy.testing.assert_allclose(r, r0, atol=1e-5)
        numpy.testing.assert_allclose(t, t0, atol=1e-5)

    def test_cache_holds_the_learned_carrier_embeddings(self):
        import torch
        tok = tokenizer()
        prompt_length = self.batch["input_ids"].shape[1]
        pose = render_call(Call("pose", 4, None))
        script = Script([ids("look " + pose), ids(" so near") + [one("<|im_end|>")]])
        forced = Forced(self.model, script, prompt_length)
        heads = Phase1Heads.from_model(self.model)
        result = headcall_generate(forced, self.batch, tok, heads, DecodeConfig(eos_ids()))
        self.assertEqual(result.finish_reason, "eos")
        self.assertEqual(len(result.calls), 1)
        self.assertIsNone(result.calls[0].error_code)
        feed = {k: v for k, v in self.batch.items() if k not in ("input_ids", "attention_mask", "mm_token_type_ids")
                and not k.startswith("aux_")}
        feed["input_ids"] = torch.cat([self.batch["input_ids"], torch.tensor([result.tokens])], dim=1)
        feed["mm_token_type_ids"] = torch.cat([self.batch["mm_token_type_ids"],
                                               self.batch["mm_token_type_ids"].new_zeros((1, len(result.tokens)))], 1)
        aux = phase1.auxiliary_losses()

        def uncached(with_hook):
            _language_core(self.model).rope_deltas = None
            handle = aux.camera_inputs(self.model, self.model.auxiliary_heads, self.batch) if with_hook else None
            try:
                with torch.no_grad():
                    return self.model(**feed, use_cache=False).logits[0]
            finally:
                if handle is not None:
                    handle.remove()
        trained, raw = uncached(True), uncached(False)
        worst = max(float((logits - trained[position]).abs().max()) for position, logits in forced.raw)
        self.assertLess(worst, 1e-4, "cached decode differs from one forward with the camera-token embeddings")
        gap = max(float((logits - raw[position]).abs().max()) for position, logits in forced.raw)
        self.assertGreater(gap, 1e-3, "the carrier embeddings must matter (raw <|fim_middle|> gives other logits)")

    def test_unprintable_head_value_is_a_refusal(self):
        from headcall.heads import HeadBackend
        from headcall.protocol import CallError, PoseValue

        class ZeroView(HeadBackend):
            def pose(self, frame):
                return PoseValue((0.0, 0.0, 0.0), 0.0, 0.0, 0.0, (0.0, 0.0))
        with self.assertRaises(CallError) as caught:
            ZeroView().answer(Call("pose", 4, None))
        self.assertEqual(caught.exception.code, "head")

    def test_prompt_without_carriers_is_refused(self):
        batch = {k: v for k, v in self.batch.items() if k != "aux_camera_positions"}
        with self.assertRaises(ValueError):
            phase1.prefill(self.model, dict(batch, aux_camera_positions=self.batch["aux_camera_positions"][:, :8]))


if __name__ == "__main__":
    unittest.main()
