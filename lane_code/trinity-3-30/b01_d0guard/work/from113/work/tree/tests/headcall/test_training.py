import re
import unittest

from common import ids, one, tokenizer, tiny_model
from headcall import derive as D
from headcall.heads import ConstantHeads, NoisyHeads, OracleHeads, TinyStateHeads
from headcall.protocol import (Call, PoseValue, exchange, exchanges, format_value, parse_response, strip_exchanges)
from headcall.training import (DEFAULT_MAX_DEPTH_QUERIES, DEFAULT_MAX_POSE_QUERIES, IGNORE, Schedule, ScheduledSampler,
                               collate_head_queries, encode_example, head_query_targets, mask_tool_responses,
                               phase1_point_depth_targets, tool_token_ids)
from rows_fixture import direction_row, distance_row

PROMPT = "<|im_start|>user\nHow far apart are the chair and the lamp?<|im_end|>\n<|im_start|>assistant\n<think>\n"


def synthetic_row(qid="q1"):
    return distance_row(qid)


def encode(tok, prompt_ids, target, token_ids=None, **kw):
    return encode_example(tok, prompt_ids, target, token_ids, require_carriers=False, **kw)


class Masking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok = tokenizer()
        cls.ids = tool_token_ids(cls.tok)

    def test_mask_spans(self):
        row = synthetic_row()
        prompt_ids = ids(PROMPT)
        input_ids, labels = encode(self.tok, prompt_ids, row["target"], self.ids)
        r_open, r_close = self.ids["<tool_response>"], self.ids["</tool_response>"]
        opens = [i for i, t in enumerate(input_ids) if t == r_open]
        closes = [i for i, t in enumerate(input_ids) if t == r_close]
        self.assertEqual(len(opens), 4)
        masked = set(range(len(prompt_ids)))
        for a, b in zip(opens, closes):
            masked |= set(range(a, b + 1))
            self.assertEqual(input_ids[a - 1], self.ids["</tool_call>"])
            self.assertEqual(labels[a - 1], self.ids["</tool_call>"])  # the model learns to close its call
            self.assertNotEqual(labels[b + 1], IGNORE)  # and to continue after the response
        for i, (token, label) in enumerate(zip(input_ids, labels)):
            self.assertEqual(label, IGNORE if i in masked else token, i)
        self.assertEqual(input_ids[-1], one("<|im_end|>"))
        self.assertEqual(labels[-1], one("<|im_end|>"))

    def test_tensor_labels(self):
        import torch
        row = synthetic_row()
        input_ids, labels = encode(self.tok, ids(PROMPT), row["target"], self.ids)
        tensor = mask_tool_responses(torch.tensor(input_ids), torch.tensor(input_ids), self.ids)
        prompt = len(ids(PROMPT))
        self.assertEqual(tensor[prompt:].tolist(), labels[prompt:])

    def test_protocol_errors(self):
        c_open, c_close = self.ids["<tool_call>"], self.ids["</tool_call>"]
        r_open, r_close = self.ids["<tool_response>"], self.ids["</tool_response>"]
        a, b = one("a"), one("b")
        bad = {
            "not after call": [a, r_open, b, r_close],
            "space before response": [c_open, a, c_close, one(" "), r_open, b, r_close],
            "nested": [c_open, a, c_close, r_open, r_open, b, r_close],
            "stray close": [a, r_close],
            "call inside response": [c_open, a, c_close, r_open, c_open, r_close],
        }
        for name, seq in bad.items():
            with self.assertRaises(ValueError, msg=name):
                mask_tool_responses(seq, list(seq), self.ids)
        unterminated = [c_open, a, c_close, r_open, b]
        with self.assertRaises(ValueError, msg="unterminated"):
            mask_tool_responses(unterminated, list(unterminated), self.ids, allow_truncated=False)
        self.assertEqual(
            mask_tool_responses(unterminated, list(unterminated), self.ids, allow_truncated=True),
            [c_open, a, c_close, IGNORE, IGNORE],
        )
        good = [c_open, a, c_close, r_open, b, r_close, a]
        self.assertEqual(mask_tool_responses(good, list(good), self.ids),
                         [c_open, a, c_close, IGNORE, IGNORE, IGNORE, a])

    def test_right_truncation_inside_tool_response(self):
        row = synthetic_row()
        prompt_ids = ids(PROMPT)
        full_ids, _ = encode(self.tok, prompt_ids, row["target"], self.ids)
        r_open = self.ids["<tool_response>"]
        first_open = full_ids.index(r_open)
        cut = first_open + 3  # slice right inside the first <tool_response>...</tool_response>
        trunc_ids, trunc_labels = encode(self.tok, prompt_ids, row["target"], self.ids, max_seq_len=cut,
                                         allow_truncated=True)
        self.assertEqual(len(trunc_ids), cut)
        self.assertEqual(len(trunc_labels), cut)
        self.assertEqual(trunc_labels[first_open:], [IGNORE] * (cut - first_open))
        self.assertEqual(trunc_labels[first_open - 1], self.ids["</tool_call>"])
        with self.assertRaises(ValueError):
            encode(self.tok, prompt_ids, row["target"], self.ids, max_seq_len=cut, allow_truncated=False)
        # an unterminated response that truncation did not cause is bad data, never masked silently
        with self.assertRaises(ValueError):
            encode(self.tok, prompt_ids, row["target"].rsplit("</tool_response>", 1)[0], self.ids)

    def test_prompt_needs_phase1_carriers(self):
        with self.assertRaises(ValueError):
            encode_example(self.tok, ids(PROMPT), synthetic_row()["target"], self.ids)

    def test_decode_time_tokens_equal_training_tokens(self):
        """Tokenizing the full target equals model text + separately encoded responses + model text."""
        targets = [synthetic_row()["target"], direction_row()["target"],
                   'x<tool_call>{"name": "pose", "frame": 1}</tool_call><tool_response>position (0.00, 0.00, '
                   '0.00) m, heading 0 degrees, pitch 0 degrees, roll 0 degrees</tool_response>, then 2.5',
                   'a<tool_call>{"name": "depth", "frame": 32, "point": [0, 1000]}</tool_call>'
                   '<tool_response>12.30 m</tool_response>\n\nb']
        for target in targets:
            pieces, cursor = [], 0
            for start, call_end, end, body, response in exchanges(target):
                pieces += ids(target[cursor:call_end])
                pieces += ids("<tool_response>" + response + "</tool_response>")
                cursor = end
            pieces += ids(target[cursor:])
            self.assertEqual(pieces, ids(target))

    def test_hf_loss_matches_masked_loss(self):
        import torch
        model = tiny_model()
        row = synthetic_row()
        input_ids, labels = encode(self.tok, ids(PROMPT), row["target"], self.ids)
        x, y = torch.tensor([input_ids]), torch.tensor([labels])
        with torch.no_grad():
            out = model(input_ids=x, labels=y)
            logits = out.logits[0, :-1].float()
            target = y[0, 1:]
            keep = target != IGNORE
            manual = torch.nn.functional.cross_entropy(logits[keep], target[keep])
        self.assertAlmostEqual(float(out.loss), float(manual), places=4)
        response_positions = [i for i in range(len(labels)) if labels[i] == IGNORE and i >= len(ids(PROMPT))]
        self.assertGreater(len(response_positions), 10)


class Sampling(unittest.TestCase):
    def test_schedule(self):
        s = Schedule(0.0, 0.5, 100, 300)
        self.assertEqual([s(0), s(100), s(200), s(300), s(1000)], [0.0, 0.0, 0.25, 0.5, 0.5])

    def test_replace_all_re_renders_every_derived_value(self):
        row = synthetic_row()
        sampler = ScheduledSampler(Schedule(1.0, 1.0), NoisyHeads(OracleHeads(), seed=4), seed=3)
        new, replaced = sampler(row, step=10)
        self.assertEqual(replaced, [0, 1, 2, 3])
        old_found, new_found = exchanges(row["target"]), exchanges(new["target"])
        self.assertEqual([e[3] for e in old_found], [e[3] for e in new_found])  # calls unchanged
        responses = [e[4] for e in new_found]
        changed = sum(response != record["response"] for record, response in zip(row["head_calls"], responses))
        self.assertGreaterEqual(changed, 3)
        for record, response in zip(row["head_calls"], responses):
            self.assertIsNotNone(parse_response(record["name"], response))
        # every derived point after a swapped response follows the swapped responses, none keeps its GT text
        texts, _ = D.evaluate(row["head_derived"], D.values_of([r["name"] for r in row["head_calls"]], responses))
        stated = re.findall(r"point \([^)]*\)", strip_exchanges(new["target"]))
        points = [t for t, item in zip(texts, row["head_derived"]) if item["kind"] == "point"]
        self.assertEqual(stated, points)
        self.assertTrue(all(t != item["text"] for t, item in zip(texts, row["head_derived"])))
        self.assertIn("between the located points: " + texts[-1] + ".", new["target"])  # the distance follows too
        encode(tokenizer(), ids(PROMPT), new["target"])  # still a valid masked example
        again, _ = sampler(row, step=10)
        self.assertEqual(again["target"], new["target"])

    def test_probability(self):
        row = synthetic_row()
        sampler = ScheduledSampler(Schedule(0.5, 0.5), NoisyHeads(OracleHeads()), seed=3)
        counts = [len(sampler(dict(row, qid="q%d" % i), step=1)[1]) for i in range(400)]
        self.assertAlmostEqual(sum(counts) / (4.0 * len(counts)), 0.5, delta=0.06)
        none, replaced = ScheduledSampler(Schedule(0.0, 0.0), ConstantHeads())(row, step=5)
        self.assertIs(none, row)
        self.assertEqual(replaced, [])

    def test_unanswerable_keeps_gt(self):
        row = synthetic_row()
        gt_pose = PoseValue((0.12, -0.43, 0.3), -117.2, -12.6, 1.4, (58.0, 45.0))
        new, replaced = ScheduledSampler(
            Schedule(1.0, 1.0), ConstantHeads(pose=gt_pose, depth=float("nan"))
        )(row, step=1)
        self.assertEqual(replaced, [0])  # the frame-4 pose; the frame-10 pose is far off, both depths refuse
        self.assertEqual(exchanges(new["target"])[1][4], row["head_calls"][1]["response"])

    def test_tolerance_gate_covers_position_heading_pitch_roll_view(self):
        row = synthetic_row()
        gt = PoseValue((0.12, -0.43, 0.3), -117.2, -12.6, 1.4, (58.0, 45.0))
        sampler = ScheduledSampler(Schedule(1.0, 1.0), ConstantHeads(), seed=3)
        record = row["head_calls"][0]
        self.assertTrue(sampler.within_tolerance(record, gt))
        for bad in (gt._replace(position=(0.5, -0.43, 0.3)), gt._replace(heading_deg=-129.0),
                    gt._replace(pitch_deg=-24.0), gt._replace(roll_deg=13.0), gt._replace(view_deg=(70.0, 45.0)),
                    gt._replace(view_deg=None)):
            self.assertFalse(sampler.within_tolerance(record, bad), bad)
        far_heads = ConstantHeads(depth=9.99, pose=PoseValue((5.0, 5.0, 5.0), 45.0, 0.0, 0.0, (58.0, 45.0)))
        sampler = ScheduledSampler(Schedule(1.0, 1.0), far_heads, seed=3)
        new, replaced = sampler(row, step=10)
        self.assertEqual(replaced, [])
        self.assertEqual(new["target"], row["target"])
        self.assertEqual((sampler.attempted_swaps, sampler.accepted_swaps, sampler.rejected_swaps), (4, 0, 4))
        self.assertEqual(sampler.acceptance_rate(), 0.0)

    def test_swaps_that_change_the_decision_are_rejected_whole(self):
        row = direction_row()
        pose = PoseValue((0.0, 0.0, 0.0), 0.0, 0.0, 0.0, (60.0, 46.0))

        class Shift(ConstantHeads):
            def depth(self, frame, point):
                return {(500, 500): 1.15, (500, 400): 2.85, (300, 500): 2.32}[tuple(point)]
        sampler = ScheduledSampler(Schedule(1.0, 1.0), Shift(pose=pose), seed=1)
        new, replaced = sampler(row, step=0)
        self.assertEqual(replaced, [0, 1, 2, 3])  # a decision-preserving set of swaps is kept
        self.assertNotEqual(new["target"], row["target"])
        self.assertIn("point (0.00, 1.15, 0.00)", new["target"])

        class Swing(ConstantHeads):  # a plant depth that moves it behind the stool (back-left, not front-left)
            def depth(self, frame, point):
                return {(500, 500): 1.0, (500, 400): 3.0, (300, 500): 0.8}[tuple(point)]
        swing = Swing(pose=pose)
        sampler = ScheduledSampler(Schedule(1.0, 1.0), swing, seed=1, depth_abs_tol_m=2.0, depth_rel_tol=1.0)
        new, replaced = sampler(row, step=0)
        _, results = D.evaluate(row["head_derived"], D.values_of(
            [r["name"] for r in row["head_calls"]], [format_value("pose", swing.value_pose), "1.00 m", "3.00 m",
                                                     "0.80 m"]))
        self.assertFalse(D.answer_supported(row, row["head_derived"], results))
        self.assertEqual(replaced, [])
        self.assertEqual(new["target"], row["target"])
        self.assertEqual(sampler.rejected_rows, 1)

    def test_untemplated_rows_are_never_swapped(self):
        row = synthetic_row()
        row.pop("target_template")
        sampler = ScheduledSampler(Schedule(1.0, 1.0), NoisyHeads(OracleHeads()), seed=3)
        new, replaced = sampler(row, step=1)
        self.assertIs(new, row)
        self.assertEqual(sampler.untemplated_rows, 1)


class HeadTargets(unittest.TestCase):
    def test_default_query_caps_are_80(self):
        self.assertEqual(DEFAULT_MAX_DEPTH_QUERIES, 80)
        self.assertEqual(DEFAULT_MAX_POSE_QUERIES, 80)
        targets = head_query_targets(synthetic_row())
        self.assertEqual(tuple(targets["depth_m"].shape), (80,))
        self.assertEqual(tuple(targets["pose"].shape), (80, 8))
        with self.assertRaises(ValueError):
            head_query_targets(synthetic_row(), max_depth=1)

    def test_phase1_point_depth_layout(self):
        targets = phase1_point_depth_targets(synthetic_row(), points_per_frame=4)
        self.assertEqual(targets["mask"][1][:2], [True, False])  # frame 4 -> group 1
        self.assertEqual(targets["uv"][4][0], [700.0, 120.0])    # frame 10 -> group 4
        self.assertAlmostEqual(targets["depth"][4][0], 3.415, places=5)

    def test_targets_and_loss(self):
        import torch
        row = synthetic_row()
        row["head_calls"].append(dict(row["head_calls"][1]))  # a repeated query counts once
        targets = head_query_targets(row, max_depth=4, max_pose=3)
        self.assertEqual(targets["depth_mask"].tolist(), [True, True, False, False])
        self.assertEqual(targets["pose_mask"].tolist(), [True, True, False])
        self.assertEqual(targets["depth_point"][1].tolist(), [700, 120])
        self.assertAlmostEqual(float(targets["pose"][0, 3]), -117.2, places=4)
        batch = collate_head_queries([targets, targets])
        self.assertEqual(tuple(batch["depth_point"].shape), (2, 4, 2))
        torch.manual_seed(0)
        heads = TinyStateHeads(hidden_size=64)
        states = torch.randn(40, 64)
        optimizer = torch.optim.Adam(heads.parameters(), lr=1e-2)
        losses = []
        for _ in range(60):
            loss = heads.loss(states, targets)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        self.assertTrue(all(map(lambda v: v == v, losses)))
        self.assertLess(losses[-1], 0.3 * losses[0])


if __name__ == "__main__":
    unittest.main()
