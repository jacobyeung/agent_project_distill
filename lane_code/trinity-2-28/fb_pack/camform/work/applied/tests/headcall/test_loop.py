import unittest

from common import FakeLM, Script, eos_ids, fake_engine, ids, one, tokenizer
from headcall.decode import DecodeConfig, headcall_generate, segment_generate
from headcall.heads import ConstantHeads, HeadContext
from headcall.protocol import Call, PoseValue, exchanges, render_call

PROMPT = "<|im_start|>user\nq<|im_end|>\n<|im_start|>assistant\n<think>\n"
DEPTH = render_call(Call("depth", 4, (412, 280)))
POSE = render_call(Call("pose", 8, None))


def run_both(test, segments, heads=None, **config):
    """Decode a script with both loops and require identical results; returns the HF-loop result."""
    import torch
    tok = tokenizer()
    prompt = ids(PROMPT)
    heads = heads or ConstantHeads(depth=1.84, pose=PoseValue((0.32, 1.1, 0.05), 35.0, -12.0, -2.0, (58.0, 45.0)))
    cfg = DecodeConfig(eos_ids(), **config)
    policy = Script(segments)
    model = FakeLM(policy, len(prompt))
    batch = {"input_ids": torch.tensor([prompt]), "attention_mask": torch.ones(1, len(prompt), dtype=torch.long)}
    first = headcall_generate(model, batch, tok, heads, cfg)
    second = segment_generate(fake_engine(policy, len(prompt)), prompt, tok, heads, cfg, HeadContext(prompt))
    test.assertEqual(first.tokens, second.tokens)
    test.assertEqual(first.inserted, second.inserted)
    test.assertEqual(first.finish_reason, second.finish_reason)
    test.assertEqual([(c.body, c.response, c.error_code) for c in first.calls],
                     [(c.body, c.response, c.error_code) for c in second.calls])
    test.assertEqual(model.steps, len(first.tokens) - (first.finish_reason == "eos"))
    test.assertEqual(len(first.tokens), len(first.inserted))
    if first.finish_reason == "max_new_tokens":
        test.assertEqual(len(first.tokens), cfg.max_new_tokens)
    else:
        test.assertLessEqual(len(first.tokens), cfg.max_new_tokens)
    return first


def text(result):
    return tokenizer().decode(result.tokens)


def model_text(result):
    return tokenizer().decode([t for t, i in zip(result.tokens, result.inserted) if not i])


class Loop(unittest.TestCase):
    def test_round_trip(self):
        r = run_both(self, [ids("look " + DEPTH), ids(" then " + POSE), ids(" so 2 m") + [one("<|im_end|>")]])
        self.assertEqual(r.finish_reason, "eos")
        self.assertEqual(text(r), "look " + DEPTH + "<tool_response>1.84 m</tool_response> then " + POSE +
                         "<tool_response>position (0.32, 1.10, 0.05) m, heading 35 degrees left, pitch 12 degrees "
                         "down, roll 2 degrees right, view 58 x 45 degrees</tool_response> so 2 m<|im_end|>")
        self.assertEqual([c.error_code for c in r.calls], [None, None])
        self.assertTrue(all(c.parse.strict for c in r.calls))
        inserted = tokenizer().decode([t for t, i in zip(r.tokens, r.inserted) if i])
        self.assertEqual(inserted, "<tool_response>1.84 m</tool_response><tool_response>position (0.32, 1.10, "
                                   "0.05) m, heading 35 degrees left, pitch 12 degrees down, roll 2 degrees right, "
                                   "view 58 x 45 degrees</tool_response>")
        self.assertEqual(model_text(r), "look " + DEPTH + " then " + POSE + " so 2 m<|im_end|>")
        self.assertEqual(r.summary()["valid_calls"], 2)
        for key in ("prefill_s", "decode_s", "head_s", "total_s"):
            self.assertGreaterEqual(r.timing[key], 0.0)

    def test_call_limit(self):
        r = run_both(self, lambda i: ids(POSE), max_calls=3, max_new_tokens=300)
        self.assertEqual(r.finish_reason, "max_new_tokens")
        codes = [c.error_code for c in r.calls]
        self.assertEqual(codes[:3], [None, None, None])
        self.assertTrue(len(codes) > 3 and all(c == "limit" for c in codes[3:]))
        self.assertIn("error: call limit reached; answer without more calls", text(r))

    def test_unclosed_call_is_closed(self):
        r = run_both(self, [ids("<tool_call>{\"name\": \"depth\", \"frame\": 4, \"point\": [412,"),
                            [one("<|im_end|>")]], max_call_tokens=12)
        self.assertEqual(r.finish_reason, "eos")
        close = one("</tool_call>")
        forced = [i for i, (t, flag) in enumerate(zip(r.tokens, r.inserted)) if t == close and flag]
        self.assertEqual(len(forced), 1)
        self.assertEqual(forced[0], 13)  # <tool_call> + 12 tokens, then the loop's </tool_call>
        self.assertEqual(r.calls[0].error_code, "point")

    def test_runaway_call(self):
        r = run_both(self, lambda i: [one("<tool_call>")], max_call_tokens=20, max_new_tokens=500)
        self.assertEqual(r.finish_reason, "max_new_tokens")
        self.assertTrue(all(c.error_code == "json" for c in r.calls))

    def test_unopened_close(self):
        r = run_both(self, [ids("hi</tool_call>"), [one("<|im_end|>")]])
        self.assertEqual(r.calls[0].error_code, "unopened")
        self.assertIn("<tool_response>error: </tool_call> without <tool_call></tool_response>", text(r))

    def test_malformed_and_xml_calls(self):
        xml = "<tool_call><function=depth><parameter=frame>4</parameter><parameter=point>[412, 280]</parameter>" \
              "</function></tool_call>"
        r = run_both(self, [ids("<tool_call>{\"name\": \"depth\", \"frame\": 40}</tool_call>"), ids(xml),
                            ids("<tool_call>{'name': 'pose', 'frame': 8,}</tool_call>"), [one("<|im_end|>")]])
        self.assertEqual([c.error_code for c in r.calls], ["frame", None, None])
        self.assertIn("xml_function", r.calls[1].parse.repairs)
        self.assertFalse(r.calls[1].parse.strict)
        self.assertEqual(r.calls[1].response, "1.84 m")
        self.assertEqual(r.summary()["strict_calls"], 0)

    def test_head_error(self):
        r = run_both(self, [ids(DEPTH), [one("<|im_end|>")]], heads=ConstantHeads(depth=float("nan")))
        self.assertEqual(r.calls[0].error_code, "head")
        self.assertIn("<tool_response>error: the depth head returned no value</tool_response>", text(r))

    def test_cap_inside_response(self):
        call = ids("look " + DEPTH)
        r = run_both(self, [call, [one("<|im_end|>")]], max_new_tokens=len(call) + 3)
        self.assertEqual(r.finish_reason, "max_new_tokens")
        self.assertEqual(r.inserted[-3:], [True, True, True])
        self.assertEqual(r.calls[0].inserted_tokens, 3)

    def test_cap_at_forced_close(self):
        opening = ids("<tool_call>{\"name\": ")
        r = run_both(self, [opening + [one("a")] * 50], max_call_tokens=len(opening) - 1,
                     max_new_tokens=len(opening))
        self.assertEqual(r.finish_reason, "max_new_tokens")
        self.assertEqual(r.calls, [])
        self.assertEqual(r.inserted, [False] * len(opening))

    def test_cap_on_close_token(self):
        call = ids(DEPTH)
        r = run_both(self, [call], max_new_tokens=len(call))
        self.assertEqual(r.finish_reason, "max_new_tokens")
        self.assertEqual(len(r.calls), 1)
        self.assertEqual(r.calls[0].inserted_tokens, 0)

    def test_self_written_response(self):
        r = run_both(self, [ids("<tool_response>5 m</tool_response>"), [one("<|im_end|>")]])
        self.assertEqual(r.self_responses, 1)
        self.assertEqual(r.calls, [])
        self.assertFalse(any(r.inserted))

    def test_eos_first(self):
        r = run_both(self, [[one("<|endoftext|>")]])
        self.assertEqual((r.finish_reason, len(r.tokens)), ("eos", 1))

    def test_no_eos(self):
        r = run_both(self, [ids("abc")], max_new_tokens=17)
        self.assertEqual((r.finish_reason, len(r.tokens)), ("max_new_tokens", 17))

    def test_exchanges_of_output(self):
        r = run_both(self, [ids(DEPTH), ids(DEPTH), [one("<|im_end|>")]])
        found = exchanges(text(r))
        self.assertEqual([e[4] for e in found], ["1.84 m", "1.84 m"])

    def test_batch_size_one(self):
        import torch
        with self.assertRaises(ValueError):
            headcall_generate(FakeLM(Script([[0]]), 2), {"input_ids": torch.zeros(2, 2, dtype=torch.long)},
                              tokenizer(), ConstantHeads(), DecodeConfig(eos_ids()))

    def test_sampling_is_seeded(self):
        import torch
        tok = tokenizer()
        prompt = ids(PROMPT)

        class Uniform(FakeLM):
            def __call__(self, **kwargs):
                out = FakeLM.__call__(self, **kwargs)
                out.logits[:] = 0.0
                out.logits[0, 0, 1000:] = -1e4
                return out

        batch = {"input_ids": torch.tensor([prompt])}
        cfg = DecodeConfig(eos_ids(), max_new_tokens=30, do_sample=True, top_p=0.5, seed=5)
        a = headcall_generate(Uniform(Script([[0]]), len(prompt)), batch, tok, ConstantHeads(), cfg)
        b = headcall_generate(Uniform(Script([[0]]), len(prompt)), batch, tok, ConstantHeads(), cfg)
        self.assertEqual(a.tokens, b.tokens)
        self.assertTrue(all(t < 1000 for t in a.tokens))
        self.assertGreater(len(set(a.tokens)), 5)


if __name__ == "__main__":
    unittest.main()
