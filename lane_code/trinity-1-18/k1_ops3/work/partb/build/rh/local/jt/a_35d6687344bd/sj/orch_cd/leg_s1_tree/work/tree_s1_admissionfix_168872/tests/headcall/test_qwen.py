"""Tiny Qwen3.5 (hidden 64, 3 linear-attention + 1 full-attention layers, real tokenizer) on CPU."""
import hashlib
import json
import os
import random
import time
import unittest

from common import CACHE, TINY, Script, eos_ids, ids, one, tokenizer, tiny_model
from headcall.decode import DecodeConfig, _language_core, headcall_generate, hf_engine, segment_generate
from headcall.eval_hook import evaluate_head_vs_shuffled
from headcall.heads import ConstantHeads, HeadContext, OracleHeads, TinyStateHeads
from headcall.protocol import (EXPECTED_TRANSFORMERS_VERSION, Call, exchanges, format_depth, parse_response,
                               render_call)
from headcall.training import IGNORE, encode_example, tool_token_ids

PROMPT = "<|im_start|>user\nIs the chair within 2 m of the camera?<|im_end|>\n<|im_start|>assistant\n<think>\n"
DEPTH = render_call(Call("depth", 4, (412, 280)))


class Forced(object):
    """Wraps a real model: records its next-token logits per position and makes the script's token the argmax."""

    def __init__(self, model, policy, prompt_length):
        self.model, self.policy, self.prompt_length = model, policy, prompt_length
        self.raw, self.history = [], []

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


def video_batch(mode="native"):
    import numpy
    import torch
    from transformers import AutoProcessor
    from transformers.video_utils import VideoMetadata
    processor = AutoProcessor.from_pretrained(TINY)
    video = (numpy.random.RandomState(0).rand(4, 64, 64, 3) * 255).astype(numpy.uint8)
    metadata = VideoMetadata(total_num_frames=4, fps=2.0, frames_indices=[0, 1, 2, 3], width=64, height=64)
    messages = [{"role": "user", "content": [{"type": "video"}, {"type": "text", "text": "How far is the chair?"}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    batch = dict(processor(text=[text], videos=[video], video_metadata=[metadata], do_sample_frames=False,
                           return_tensors="pt", return_metadata=True))
    batch.pop("video_metadata", None)
    if mode == "split":
        grid = batch["video_grid_thw"]
        batch["video_grid_thw"] = torch.tensor([[1, int(grid[0, 1]), int(grid[0, 2])]] * int(grid[0, 0]))
    elif mode == "1d":
        batch.pop("mm_token_type_ids")
    return batch


def video32_batch():
    """A 32-frame video prompt: 16 temporal groups, the layout phase 1's carriers need."""
    import numpy
    from transformers import AutoProcessor
    from transformers.video_utils import VideoMetadata
    processor = AutoProcessor.from_pretrained(TINY)
    video = (numpy.random.RandomState(1).rand(32, 32, 32, 3) * 255).astype(numpy.uint8)
    metadata = VideoMetadata(total_num_frames=32, fps=2.0, frames_indices=list(range(32)), width=32, height=32)
    messages = [{"role": "user", "content": [{"type": "video"}, {"type": "text", "text": "Where is the chair?"}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    batch = dict(processor(text=[text], videos=[video], video_metadata=[metadata], do_sample_frames=False,
                           return_tensors="pt", return_metadata=True))
    batch.pop("video_metadata", None)
    return batch


def full_logits(model, batch, tokens):
    import torch
    feed = {k: v for k, v in batch.items() if k not in ("input_ids", "attention_mask", "mm_token_type_ids")
            and not k.startswith("aux_")}
    feed["input_ids"] = torch.cat([batch["input_ids"], torch.tensor([tokens])], dim=1)
    if "mm_token_type_ids" in batch:
        mm = batch["mm_token_type_ids"]
        feed["mm_token_type_ids"] = torch.cat([mm, mm.new_zeros((1, len(tokens)))], dim=1)
    _language_core(model).rope_deltas = None
    with torch.no_grad():
        return model(**feed, use_cache=False).logits[0]


class CacheEquivalence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = tiny_model()

    def check(self, batch):
        import torch
        prompt_length = batch["input_ids"].shape[1]
        script = Script([ids("look " + DEPTH), ids(" then " + DEPTH), ids(" so near") + [one("<|im_end|>")]])
        forced = Forced(self.model, script, prompt_length)
        result = headcall_generate(forced, batch, tokenizer(), ConstantHeads(depth=1.84), DecodeConfig(eos_ids()))
        self.assertEqual(result.finish_reason, "eos")
        self.assertEqual(sum(result.inserted), 2 * len(ids("<tool_response>1.84 m</tool_response>")))
        reference = full_logits(self.model, batch, result.tokens)
        self.assertEqual(len(forced.raw), len(result.tokens))
        worst = 0.0
        for position, logits in forced.raw:
            worst = max(worst, float((logits - reference[position]).abs().max()))
        self.assertLess(worst, 1e-4, "cached loop logits differ from one uncached forward")
        return result, reference

    def test_text_prompt(self):
        import torch
        import transformers
        self.assertEqual(transformers.__version__, EXPECTED_TRANSFORMERS_VERSION)
        prompt = ids(PROMPT)
        self.check({"input_ids": torch.tensor([prompt]), "attention_mask": torch.ones(1, len(prompt), dtype=torch.long)})

    def test_video_prompt_split_grid(self):
        self.check(video_batch(mode="split"))

    def test_video_prompt_3d_positions(self):
        batch = video_batch(mode="native")
        self.check(batch)
        self.assertNotEqual(int(_language_core(self.model).rope_deltas[0, 0]), 0)

    def test_carriers_in_training_and_decode_prompts(self):
        """Phase 1's 16 carriers: inserted by its own insert_carriers into the training prompt and the decode
        prefill; the cached loop over a carrier-bearing prompt equals one uncached forward."""
        import torch
        from headcall import phase1
        from headcall.training import encode_prompt_batch

        tok = tokenizer()
        batch = video32_batch()
        with_carriers = phase1.insert_carriers(dict(batch), tok)
        where = phase1.check_carriers(with_carriers["input_ids"][0].tolist(), tok)
        self.assertEqual(with_carriers["aux_camera_positions"][0].tolist(), where)
        self.assertEqual(with_carriers["input_ids"].shape[1], batch["input_ids"].shape[1] + 16)
        with self.assertRaises(ValueError):
            phase1.check_carriers(batch["input_ids"][0].tolist(), tok)
        train = encode_prompt_batch(batch, tok, "look " + DEPTH + "<tool_response>1.84 m</tool_response> near")
        prompt_length = with_carriers["input_ids"].shape[1]
        self.assertEqual(train["input_ids"][0, :prompt_length].tolist(), with_carriers["input_ids"][0].tolist())
        self.assertTrue(bool((train["labels"][0, :prompt_length] == IGNORE).all()))
        self.assertEqual(train["mm_token_type_ids"].shape, train["input_ids"].shape)
        self.assertEqual(train["attention_mask"].shape, train["input_ids"].shape)

        class CarrierHeads(ConstantHeads):
            needs_carriers = True
        with self.assertRaises(ValueError):
            headcall_generate(self.model, batch, tok, CarrierHeads(depth=1.84), DecodeConfig(eos_ids()))
        result, _ = self.check(with_carriers)
        self.assertEqual(result.finish_reason, "eos")

    def test_chunked_continuation_matches_on_5121(self):
        """Under transformers 5.12.1, multi-token GatedDeltaNet cache continuation matches uncached forward."""
        import torch
        prompt = ids(PROMPT)
        chunk = ids("look " + DEPTH + "<tool_response>1.84 m</tool_response>")
        reference = full_logits(self.model, {"input_ids": torch.tensor([prompt])}, chunk)
        _language_core(self.model).rope_deltas = None
        with torch.no_grad():
            out = self.model(input_ids=torch.tensor([prompt]), use_cache=True)
            positions = torch.arange(len(prompt), len(prompt) + len(chunk))
            chunked = self.model(input_ids=torch.tensor([chunk]), past_key_values=out.past_key_values, use_cache=True,
                                 cache_position=positions).logits[0]
        gap = float((chunked - reference[len(prompt):]).abs().max())
        self.assertLess(gap, 1e-4, "multi-token cache continuation should match under transformers 5.12.1")

    def test_state_heads_read_prefill(self):
        import torch
        batch = video_batch(mode="native")
        torch.manual_seed(0)
        heads = TinyStateHeads(hidden_size=64).eval()
        prompt_length = batch["input_ids"].shape[1]
        script = Script([ids(DEPTH), ids(render_call(Call("pose", 2, None))), [one("<|im_end|>")]])
        seen = []
        original = heads.begin

        def begin(context):
            seen.append(context)
            original(context)

        heads.begin = begin
        result = headcall_generate(Forced(self.model, script, prompt_length), batch, tokenizer(), heads,
                                   DecodeConfig(eos_ids()), video_token_id=one("<|video_pad|>"))
        context = seen[0]
        self.assertEqual(len(context.hidden_states), 5)  # embeddings + 4 layers
        self.assertEqual(tuple(context.hidden_states[-1].shape), (1, prompt_length, 64))
        self.assertEqual(len(context.video_positions()), 8)
        self.assertEqual([c.error_code for c in result.calls], [None, None])
        self.assertIsNotNone(parse_response("depth", result.calls[0].response))
        self.assertIsNotNone(parse_response("pose", result.calls[1].response))


TRAIN = {"steps": 400, "batch": 16, "lr": 3e-3, "seed": 0, "near": [0.4, 1.95], "far": [2.05, 3.95]}


def example(depth):
    near = depth < 2.0
    return ("Locate the chair. " + DEPTH + "<tool_response>" + format_depth(depth) + "</tool_response> It is "
            + ("near" if near else "far") + ".\n</think>\n\n" + ("Yes" if near else "No"))


def train_tiny():
    """Teach the tiny model one call and a decision that depends only on the inserted value; cached on disk."""
    import torch
    torch.set_num_threads(min(16, torch.get_num_threads()))
    key = hashlib.sha256(json.dumps([TRAIN, example(1.0), PROMPT], sort_keys=True).encode()).hexdigest()[:12]
    path = os.path.join(CACHE, "tiny_headcall_%s.pt" % key)
    model = tiny_model()
    if os.path.exists(path):
        model.load_state_dict(torch.load(path))
        with open(path + ".json") as handle:
            return model.eval(), json.load(handle)
    torch.manual_seed(TRAIN["seed"])
    rng = random.Random(TRAIN["seed"])
    tok, token_ids, prompt = tokenizer(), tool_token_ids(tokenizer()), ids(PROMPT)
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=TRAIN["lr"], weight_decay=0.0)
    start, losses = time.time(), []
    for step in range(TRAIN["steps"]):
        rows = []
        for i in range(TRAIN["batch"]):
            low, high = TRAIN["near"] if i % 2 == 0 else TRAIN["far"]
            # a text-only toy prompt: no video, so no carriers (require_carriers=False)
            rows.append(encode_example(tok, prompt, example(rng.uniform(low, high)), token_ids, require_carriers=False))
        width = max(len(x) for x, _ in rows)
        x = torch.tensor([a + [0] * (width - len(a)) for a, _ in rows])
        y = torch.tensor([b + [IGNORE] * (width - len(b)) for _, b in rows])
        mask = torch.tensor([[1] * len(a) + [0] * (width - len(a)) for a, _ in rows])
        hidden = model.model(input_ids=x, attention_mask=mask).last_hidden_state[:, :-1]
        target = y[:, 1:]
        keep = target != IGNORE
        loss = torch.nn.functional.cross_entropy(model.lm_head(hidden[keep]).float(), target[keep])
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    log = {"train": TRAIN, "seconds": round(time.time() - start, 1), "first_loss": losses[0],
           "last_loss": sum(losses[-20:]) / 20.0}
    os.makedirs(CACHE, exist_ok=True)
    torch.save(model.state_dict(), path)
    with open(path + ".json", "w") as handle:
        json.dump(log, handle)
    return model.eval(), log


class LearnsToCall(unittest.TestCase):
    """The student's skill in miniature: emit a strict call, then let the inserted value decide the answer."""

    @classmethod
    def setUpClass(cls):
        import torch
        torch.set_num_threads(min(8, torch.get_num_threads()))
        cls.model, cls.log = train_tiny()
        prompt = ids(PROMPT)
        cls.batch = {"input_ids": torch.tensor([prompt]), "attention_mask": torch.ones(1, len(prompt), dtype=torch.long)}

    def decode(self, depth, **config):
        return headcall_generate(self.model, self.batch, tokenizer(), ConstantHeads(depth=depth),
                                 DecodeConfig(eos_ids(), max_new_tokens=80, **config))

    def test_calls_and_uses_value(self):
        for depth in (0.55, 1.3, 1.9, 2.1, 2.8, 3.7):  # the training range; a leading 9 was never seen
            result = self.decode(depth)
            text = tokenizer().decode(result.tokens)
            self.assertEqual(result.finish_reason, "eos", text)
            self.assertEqual(len(result.calls), 1, text)
            self.assertTrue(result.calls[0].parse.strict, text)
            self.assertEqual(result.calls[0].parse.call, Call("depth", 4, (412, 280)))
            self.assertEqual(exchanges(text)[0][4], format_depth(depth))
            near = depth < 2.0
            self.assertTrue(text.endswith(("near" if near else "far") + ".\n</think>\n\n" + ("Yes" if near else "No")
                                          + "<|im_end|>"), (depth, text))

    def test_hf_engine_matches_cached_loop(self):
        heads = ConstantHeads(depth=2.6)
        cfg = DecodeConfig(eos_ids(), max_new_tokens=80)
        cached = headcall_generate(self.model, self.batch, tokenizer(), heads, cfg)
        prompt = self.batch["input_ids"][0].tolist()
        segmented = segment_generate(hf_engine(self.model, self.batch), prompt, tokenizer(), heads, cfg,
                                     HeadContext(prompt))
        self.assertEqual(cached.tokens, segmented.tokens)
        self.assertEqual(cached.inserted, segmented.inserted)

    def test_call_cap_still_terminates(self):
        result = self.decode(1.2, max_calls=0)
        self.assertEqual(result.calls[0].error_code, "limit")
        self.assertIn(result.finish_reason, ("eos", "max_new_tokens"))

    def test_head_vs_shuffled_on_trained_tiny_qwen(self):
        from types import SimpleNamespace
        processor = SimpleNamespace(tokenizer=tokenizer(), video_token_id=one("<|video_pad|>"))
        effective = {"do_sample": False, "num_beams": 1, "num_return_sequences": 1, "max_new_tokens": 80,
                     "eos_token_id": list(eos_ids())}
        samples = []
        for idx, d in enumerate((0.65, 1.25, 1.75, 2.35, 3.10, 3.65)):
            row = {"qid": "q%d" % idx,
                   "head_calls": [{"name": "depth", "frame": 4, "point": [412, 280], "gt": {"depth_m": d}}]}
            samples.append({"key": row["qid"], "batch": self.batch, "row": row, "gold": "Yes" if d < 2.0 else "No"})
        report = evaluate_head_vs_shuffled(self.model, processor, OracleHeads(), samples, effective)
        self.assertEqual(report["head_acc"], 1.0)
        self.assertGreater(report["acc_delta_head_minus_shuffled"], 0.0)
        self.assertGreater(report["answer_changed_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
