import json
import unittest
from types import SimpleNamespace

from common import FakeLM, Script, eos_ids, ids, one, tokenizer
from headcall.eval_hook import (evaluate_head_vs_shuffled, extract_final_answer, headcall_generator,
                                response_value_used_downstream)
from headcall.heads import ConstantHeads, HeadContext, HeadOutputPool, OracleHeads, ShuffledHeads
from headcall.protocol import Call, render_call

PROMPT = "<|im_start|>user\nq<|im_end|>\n<|im_start|>assistant\n<think>\n"
EFFECTIVE = {"do_sample": False, "num_beams": 1, "num_return_sequences": 1, "max_new_tokens": 16384,
             "eos_token_id": list(eos_ids()), "temperature": None, "top_p": None, "top_k": None}


def evaluator_finish(tokens, eos, cap):
    """The evaluator's own rule (benchmark_eval/generate.py)."""
    return "eos" if tokens and tokens[-1] in eos else "max_new_tokens" if len(tokens) == cap else None


class EvalHook(unittest.TestCase):
    def run_hook(self, segments, **effective):
        import torch
        prompt = ids(PROMPT)
        settings = dict(EFFECTIVE, **effective)
        processor = SimpleNamespace(tokenizer=tokenizer(), video_token_id=one("<|video_pad|>"))
        generate = headcall_generator(FakeLM(Script(segments), len(prompt)), processor, ConstantHeads(depth=2.25),
                                      settings)
        result = generate({"input_ids": torch.tensor([prompt])}, key="q1")
        self.assertIsNotNone(evaluator_finish(result["tokens"], settings["eos_token_id"], settings["max_new_tokens"]))
        json.dumps(result["headcall"])
        return result

    def test_result_shape(self):
        call = render_call(Call("depth", 4, (10, 990)))
        result = self.run_hook([ids("x " + call), ids(" so <answer>B</answer>") + [one("<|im_end|>")]])
        self.assertEqual(result["raw"], "x " + call + "<tool_response>2.25 m</tool_response> so <answer>B</answer>"
                                                      "<|im_end|>")
        self.assertIn("<answer>B</answer>", result["display"])
        record = result["headcall"]
        self.assertEqual(record["summary"]["finish_reason"], "eos")
        self.assertEqual(record["calls"][0]["call"], {"name": "depth", "frame": 4, "point": [10, 990]})
        self.assertTrue(record["calls"][0]["strict"])
        (start, end), = record["inserted_spans"]
        self.assertEqual(tokenizer().decode(result["tokens"][start:end]), "<tool_response>2.25 m</tool_response>")

    def test_cap_rule(self):
        result = self.run_hook(lambda i: ids(render_call(Call("pose", 2, None))), max_new_tokens=257)
        self.assertEqual(len(result["tokens"]), 257)

    def test_rejects_sampling(self):
        with self.assertRaises(ValueError):
            headcall_generator(None, SimpleNamespace(tokenizer=tokenizer()), ConstantHeads(),
                               dict(EFFECTIVE, do_sample=True))

    def test_head_vs_shuffled_ablation(self):
        import torch
        tok = tokenizer()
        prompt = ids(PROMPT)
        call_str = render_call(Call("depth", 4, (10, 990)))
        call_ids = ids("check " + call_str)
        close_id = one("</tool_response>")

        def policy(history):
            if close_id not in history:
                return call_ids[len(history)] if len(history) < len(call_ids) else one("a")
            close_pos = max(i for i, t in enumerate(history) if t == close_id)
            resp_open = one("<tool_response>")
            open_pos = max(i for i, t in enumerate(history[:close_pos]) if t == resp_open)
            resp_text = tok.decode(history[open_pos + 1:close_pos])
            val = float(resp_text.split()[0])
            ans = "Yes" if val < 2.0 else "No"
            tail = ids(" seen %.2f m </think>\n<answer>%s</answer>" % (val, ans)) + [one("<|im_end|>")]
            offset = len(history) - close_pos - 1
            return tail[offset] if offset < len(tail) else one("<|im_end|>")

        model = FakeLM(policy, len(prompt))
        processor = SimpleNamespace(tokenizer=tok, video_token_id=one("<|video_pad|>"))
        row_near = {"qid": "q_near", "scene": "s1",
                    "head_calls": [{"name": "depth", "frame": 4, "point": [10, 990], "gt": {"depth_m": 1.15}}]}
        row_far = {"qid": "q_far", "scene": "s2",
                   "head_calls": [{"name": "depth", "frame": 4, "point": [10, 990], "gt": {"depth_m": 3.85}}]}
        samples = [
            {"key": "q_near", "batch": {"input_ids": torch.tensor([prompt])}, "row": row_near, "gold": "Yes"},
            {"key": "q_far", "batch": {"input_ids": torch.tensor([prompt])}, "row": row_far, "gold": "No"},
        ]
        # the shuffled arm answers each call with the other sample's real head output: near gets 3.85, far 1.15
        report = evaluate_head_vs_shuffled(model, processor, OracleHeads(), samples, EFFECTIVE)
        self.assertEqual(report["shuffle_pool_values"], 2)
        self.assertEqual(report["head_acc"], 1.0)
        self.assertEqual(report["shuffled_acc"], 0.0)
        self.assertEqual(report["acc_delta_head_minus_shuffled"], 1.0)
        self.assertEqual(report["answer_changed_rate"], 1.0)
        self.assertEqual(report["head_used_downstream_rate"], 1.0)
        self.assertEqual(report["head_valid_call_rate"], 1.0)
        self.assertEqual(report["head_strict_call_rate"], 1.0)
        self.assertTrue(response_value_used_downstream(
            "check " + call_str + "<tool_response>1.15 m</tool_response> seen 1.15 m </think>\n<answer>Yes</answer>"
        ))
        self.assertEqual(extract_final_answer("<think>reasoning</think>\n<answer>Yes</answer><|im_end|>"), "Yes")

    def test_downstream_usage_sees_derived_points_and_motion(self):
        """A depth response is used when the trace prints the 3D point derived from it (not its literal), and a pose
        response when the trace prints the ego-motion derived from it."""
        from headcall.eval_hook import downstream_usage
        from rows_fixture import distance_row, motion_row
        row = distance_row()
        usage = downstream_usage(row["target"])
        self.assertEqual([u["name"] for u in usage], ["pose", "depth", "pose", "depth"])
        self.assertEqual([u["how"] for u in usage if u["name"] == "depth"], ["derived_point", "derived_point"])
        self.assertTrue(response_value_used_downstream(row["target"]))
        stripped = row["target"].split("point (", 1)[0]  # the derivation never printed
        self.assertFalse(any(u["used"] for u in downstream_usage(stripped) if u["name"] == "depth"))
        motion = downstream_usage(motion_row()["target"])
        self.assertEqual([u["how"] for u in motion], [None, "derived_motion"])

    def test_strict_accuracy_is_reported_apart(self):
        import torch
        tok = tokenizer()
        prompt = ids(PROMPT)
        lenient = "<tool_call>{'name': 'depth', 'frame': 4, 'point': [10, 990],}</tool_call>"
        segments = [ids("check " + lenient), ids(" so </think>\n<answer>Yes</answer>") + [one("<|im_end|>")]]
        processor = SimpleNamespace(tokenizer=tok, video_token_id=one("<|video_pad|>"))
        row = {"qid": "q1", "scene": "s1",
               "head_calls": [{"name": "depth", "frame": 4, "point": [10, 990], "gt": {"depth_m": 1.15}}]}
        other = {"qid": "q2", "scene": "s2",
                 "head_calls": [{"name": "depth", "frame": 4, "point": [10, 990], "gt": {"depth_m": 3.85}}]}
        samples = [{"key": "q1", "batch": {"input_ids": torch.tensor([prompt])}, "row": row, "gold": "Yes"},
                   {"key": "q2", "batch": {"input_ids": torch.tensor([prompt])}, "row": other, "gold": "Yes"}]
        report = evaluate_head_vs_shuffled(FakeLM(Script(segments), len(prompt)), processor, OracleHeads(), samples,
                                           EFFECTIVE)
        self.assertEqual(report["head_acc"], 1.0)
        self.assertEqual(report["head_acc_strict"], 0.0)   # every correct answer rested on a repaired call
        self.assertEqual(report["head_lenient_call_count"], 2)
        refused = headcall_generator(FakeLM(Script(segments), len(prompt)), processor, OracleHeads(), EFFECTIVE,
                                     allow_lenient=False)({"input_ids": torch.tensor([prompt])}, key="q1", row=row)
        self.assertEqual(refused["headcall"]["calls"][0]["error_code"], "lenient")
        self.assertEqual(refused["headcall"]["summary"]["lenient_refused"], 1)

    def test_shuffled_heads_only_permute_real_outputs(self):
        pool = HeadOutputPool()
        pool.add("a", ("d1", "s1"), "depth", 4, 1.25)
        pool.add("b", ("d1", "s2"), "depth", 8, 2.5)
        pool.add("b", ("d1", "s2"), "pose", 1, "origin-b")
        pool.add("c", ("d1", "s1"), "pose", 6, "anchor-c")
        heads = ShuffledHeads(pool)
        heads.begin(HeadContext([], key="a", row={"dataset": "d1", "scene": "s1"}))
        self.assertEqual(heads.depth(4, (1, 2)), 2.5)        # never its own sample or scene
        self.assertEqual(heads.pose(1), "origin-b")          # frame 1 draws only from other frame-1 outputs
        with self.assertRaises(Exception):
            heads.pose(6)                                      # the only anchor pose is from the same scene
        heads.begin(HeadContext([], key="z", row={"dataset": "d1", "scene": "s9"}))
        self.assertIn(heads.depth(30, (5, 5)), (1.25, 2.5))


if __name__ == "__main__":
    unittest.main()
