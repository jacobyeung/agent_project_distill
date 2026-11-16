"""headcall-fullft: the headcall training block inside the full fine-tuning trainer.

Config normalization; the pinned sidecar and its join to admitted rows; the encoder (tool-response masking, forced
carriers, queried depth points first) on the tiny Qwen3.5 processor and 32 real PNG frames; the prompt-preserving splice;
scheduled sampling (swaps, the decision rule rejecting a swap that changes the answer, FSDP-matched forward counts);
the full_export warm start from a milestone export written by the trainer's own writer; and a 2-rank CPU/gloo FSDP full
fine-tuning forward/backward on the tiny model with camera and point-depth heads that runs all of it together.

Run from the tree root: LANE_TEST_OUTPUT=... HEADCALL_TEST_CACHE=... python -m unittest tests.test_headcall_fullft
"""
import copy
import hashlib
import json
import os
import socket
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import nullcontext
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "headcall"))

import common  # noqa: E402,F401  (tree root and tests/headcall on the path, TINY, CACHE)
from common import CACHE, TINY, tokenizer  # noqa: E402
from rows_fixture import direction_row, distance_row  # noqa: E402

import torch  # noqa: E402

from headcall import derive as D  # noqa: E402
from headcall import rows as R  # noqa: E402
from headcall.heads import HeadBackend, NoisyHeads, OracleHeads  # noqa: E402
from headcall.protocol import CallError, exchanges  # noqa: E402
from headcall.training import IGNORE, tool_token_ids  # noqa: E402

GROUPS, SLOTS = 16, 8
SMALL_DEPTH = {"weight": 0.5, "d_proj": 16, "mlp_hidden": 16, "num_heads": 2, "context_depth": 1, "vit_layers": [1, 2, 4],
               "num_points_per_frame": SLOTS}
PIN = {"path": "/fixture/bank.npz", "sha256": "0" * 64}


def output_root(prefix):
    root = os.environ.get("LANE_TEST_OUTPUT") or CACHE
    os.makedirs(root, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=root))


def frames_dir():
    import numpy
    from PIL import Image
    os.makedirs(CACHE, exist_ok=True)
    root = tempfile.mkdtemp(prefix="hcfull_frames_", dir=CACHE)
    rng = numpy.random.RandomState(3)
    frames = []
    for k in range(32):
        path = os.path.join(root, "f%02d.png" % k)
        Image.fromarray((rng.rand(64, 64, 3) * 255).astype(numpy.uint8), "RGB").save(path)
        with open(path, "rb") as handle:
            frames.append({"path": path, "sha256": hashlib.sha256(handle.read()).hexdigest()})
    return frames


def processor():
    from transformers import AutoProcessor
    proc = AutoProcessor.from_pretrained(TINY)
    proc.tokenizer.padding_side = "right"
    return proc


def zero_record(bank_points=0):
    """A camera record of a scene outside the bank (no masks) unless bank_points > 0, which fills group 1."""
    uv = [[[0.0, 0.0]] * SLOTS for _ in range(GROUPS)]
    depth = [[0.0] * SLOTS for _ in range(GROUPS)]
    mask = [[False] * SLOTS for _ in range(GROUPS)]
    for k in range(bank_points):
        uv[1][k], depth[1][k], mask[1][k] = [100.0 + k, 200.0], 2.0 + k, True
    return {"camera": [[0.0] * 9 for _ in range(GROUPS)], "camera_mask": [False] * GROUPS, "trajectory_scale": 0.0,
            "lm_weight": 1.0, "gravity": [0.0, 0.0, 0.0], "gravity_mask": False,
            "point_depth": {"uv": uv, "depth": depth, "mask": mask}}


def student_input(frames, question="How far apart are the chair and the lamp, in meters?", options=()):
    return {"question": question, "options": list(options), "frames": frames, "frame_indices": list(range(0, 64, 2)),
            "timestamps": [i / 2.0 for i in range(0, 64, 2)], "fps": 2.0, "total_num_frames": 64}


def admitted(base, frames, qid, target=None):
    """An admitted training row (the fields admission keeps) plus its camera record."""
    options = base.get("options") or []
    return {"qid": qid, "dataset": "d1", "scene": "s1", "category": base["category"], "pool": "r1x",
            "answer": base["answer"], "target": base["target"] if target is None else target,
            "student_input": student_input(frames, options=options), "_camera": zero_record()}


def answer_only(row):
    return "<think>\n\n</think>\n\n" + row["answer"]


def headcall_entry(base, row):
    from student_pilot.auxiliary_targets import input_identity
    return {"qid": row["qid"], "kind": "headcall", "target_sha256": R.text_sha256(row["target"]),
            "input_sha256": input_identity(row), "head_calls": base["head_calls"],
            "target_template": base["target_template"], "head_derived": base["head_derived"]}


def twin_entry(base, row):
    from student_pilot.auxiliary_targets import input_identity
    return {"qid": row["qid"], "kind": "queries", "target_sha256": R.text_sha256(row["target"]),
            "input_sha256": input_identity(row), "queries": R.twin_queries(base["head_calls"])}


def audits_of(proc, rows):
    from student_pilot.diagnostic_data import encode_training
    return {row["qid"]: encode_training(proc, row)[1] for row in rows}


def sampling_settings(**extra):
    return {**R.SAMPLING_DEFAULTS, "start_p": 1.0, "end_p": 1.0, **extra}


class ScaledHeads(HeadBackend):
    """GT depth times a factor (pose exact): within a loose tolerance gate, but a distance decision moves with it."""

    def __init__(self, factor):
        self.base, self.factor = OracleHeads(), factor

    def begin(self, context):
        self.base.begin(context)

    def depth(self, frame, point):
        return self.base.depth(frame, point) * self.factor

    def pose(self, frame):
        return self.base.pose(frame)


# ---------------------------------------------------------------------------------------------- config

class ConfigTests(unittest.TestCase):
    sidecar = {"path": "/x/HC.jsonl.gz", "sha256": "a" * 64}

    def test_arms_and_refusals(self):
        hc = R.normalize({"arm": "HC", "sidecar": self.sidecar, "scheduled_sampling": {"end_p": 0.5}})
        self.assertEqual(hc["scheduled_sampling"]["end_step"], 1000)
        self.assertEqual(R.normalize(hc), hc)
        hx = R.normalize({"arm": "HX", "sidecar": self.sidecar})
        self.assertIsNone(hx["scheduled_sampling"])
        for value in ({"arm": "HC", "sidecar": self.sidecar}, {"arm": "HX", "sidecar": self.sidecar, "scheduled_sampling": {}},
                      {"arm": "HY", "sidecar": self.sidecar}, {"arm": "HA", "sidecar": {"path": "/x"}},
                      {"arm": "HA", "sidecar": self.sidecar, "extra": 1}, {"arm": "HA", "sidecar": self.sidecar, "carriers": "x"},
                      {"arm": "HC", "sidecar": self.sidecar, "scheduled_sampling": {"start_step": 5, "end_step": 5}},
                      {"arm": "HC", "sidecar": self.sidecar, "scheduled_sampling": {"end_p": 1.5}}, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                R.normalize(value)

    def test_training_config_needs_full_ft_and_the_pd_routing(self):
        from student_pilot import camera_config, ddp_config
        base = {"world_size": 32, "effective_batch_size": 256, "parallel": "fsdp"}
        block = {"arm": "HX", "sidecar": self.sidecar}
        settings = ddp_config.normalize_training_config({**base, "full_ft": {"train": {"llm": True}}, "headcall": block}, "qwen35")
        self.assertEqual(settings["headcall"], R.normalize(block))
        self.assertEqual(ddp_config.normalize_training_config(json.loads(json.dumps(settings)), "qwen35"), settings)
        with self.assertRaisesRegex(ValueError, "full fine-tuning"):
            ddp_config.normalize_training_config({**base, "headcall": block}, "qwen35")
        self.assertIn("rows.py", [Path(pin["path"]).name for pin in ddp_config.runtime_bindings()])
        camera = camera_config.normalize({"weight": 1.0, "supervision": PIN, "point_depth": dict(SMALL_DEPTH)})
        R.check_camera(camera)
        with self.assertRaises(ValueError):
            R.check_camera(camera_config.normalize({"weight": 1.0, "supervision": PIN}))
        with self.assertRaises(ValueError):
            R.check_camera({**camera, "row_routing": camera_config.CAMBRIAN_P_ROUTING})


# ---------------------------------------------------------------------------------------------- sidecar and encoder

class RowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = processor()
        cls.frames = frames_dir()
        cls.base = distance_row("q1")
        cls.hc = admitted(cls.base, cls.frames, "q1")
        cls.x = admitted(cls.base, cls.frames, "q1", target=answer_only(cls.base))
        cls.plain = admitted(direction_row("q9"), cls.frames, "q9", target=answer_only(direction_row("q9")))
        cls.root = output_root("hcfull_rows_")

    def sidecar(self, name, arm, entries):
        path = self.root / name
        pin = R.write_sidecar(path, arm, entries, {"fixture": True})
        return {"arm": arm, "sidecar": pin, "scheduled_sampling": None}

    def test_sidecar_is_deterministic_and_joins_by_target_and_input(self):
        entries = [headcall_entry(self.base, self.hc)]
        a = R.write_sidecar(self.root / "a.jsonl.gz", "HC", entries, {"fixture": True})
        b = R.write_sidecar(self.root / "b.jsonl.gz", "HC", entries, {"fixture": True})
        self.assertEqual(a["sha256"], b["sha256"])
        joined, report = R.join([self.hc, self.plain], {"arm": "HC", "sidecar": a, "scheduled_sampling": None})
        self.assertIsNone(joined[1])
        self.assertEqual(report["headcall_rows"], 1)
        self.assertEqual(report["head_calls"], 4)
        self.assertEqual(report["depth_queries"], 2)

    def test_join_refuses_any_mismatch(self):
        good = headcall_entry(self.base, self.hc)
        cases = {"target": dict(good, target_sha256="0" * 64), "input": dict(good, input_sha256="0" * 64),
                 "qid": dict(good, qid="q_absent"), "kind": dict(twin_entry(self.base, self.hc)),
                 "template": dict(good, head_calls=[dict(good["head_calls"][0], response="position (9.99, 0.00, 0.00) m, "
                                                         "heading 0 degrees, pitch 0 degrees, roll 0 degrees, view 58 x 45 degrees")]
                                  + good["head_calls"][1:])}
        for name, entry in cases.items():
            block = self.sidecar(f"bad_{name}.jsonl.gz", "HC", [entry])
            with self.subTest(case=name), self.assertRaises((ValueError, KeyError)):
                R.join([self.hc, self.plain], block)
        tampered = self.sidecar("tampered.jsonl.gz", "HC", [good])
        tampered["sidecar"] = dict(tampered["sidecar"], sha256="1" * 64)
        with self.assertRaises(ValueError):
            R.join([self.hc], tampered)

    def encode(self, rows):
        from student_pilot import ddp_training
        ddp_training.HEADCALL.update(stats=Counter(), sampling=None)
        try:
            out = []
            for row in rows:
                single = ddp_training.encode_microbatch(self.processor, [row], audits_of(self.processor, [row]), [0])
                out.append(single)
            return out
        finally:
            ddp_training.HEADCALL.update(stats=None, sampling=None)

    def test_headcall_row_masks_responses_forces_carriers_and_puts_queries_first(self):
        tok = tokenizer()
        hc = R.attach([self.hc], [headcall_entry(self.base, self.hc)])[0]
        x = R.attach([self.x], [twin_entry(self.base, self.x)])[0]
        hc_batch, x_batch, plain_batch = self.encode([hc, x, self.plain])
        from headcall import phase1
        where = phase1.check_carriers(hc_batch["input_ids"][0].tolist(), tok)
        self.assertEqual(hc_batch["aux_camera_positions"][0].tolist(), where)
        tool = tool_token_ids(tok)
        inside, responses, closes = False, 0, 0
        for token, label in zip(hc_batch["input_ids"][0].tolist(), hc_batch["labels"][0].tolist()):
            if token == tool["<tool_response>"]:
                inside, responses = True, responses + 1
            if inside:
                self.assertEqual(label, IGNORE)
            if token == tool["</tool_response>"]:
                inside = False
            if token == tool["</tool_call>"]:
                closes += 1
                self.assertNotEqual(label, IGNORE)  # the student writes its own calls
        self.assertEqual((responses, closes), (4, 4))
        mask = hc_batch["aux_point_depth_mask"][0]
        self.assertEqual(int(mask.sum()), 2)
        self.assertTrue(bool(mask[1, 0]) and bool(mask[4, 0]))  # depth calls at frames 4 and 10
        self.assertAlmostEqual(float(hc_batch["aux_point_depth_gt"][0, 1, 0]), 0.862, places=5)
        self.assertEqual(hc_batch["aux_point_depth_uv"][0, 4, 0].tolist(), [700.0, 120.0])
        # The HX twin: the same carriers and depth targets; only the target text differs.
        end_hc, end_x = R.prompt_end(hc_batch), R.prompt_end(x_batch)
        self.assertEqual(hc_batch["input_ids"][0, :end_hc].tolist(), x_batch["input_ids"][0, :end_x].tolist())
        for key in ("aux_camera_positions", "aux_point_depth_uv", "aux_point_depth_gt", "aux_point_depth_mask",
                    "aux_camera_mask", "pixel_values_videos"):
            self.assertTrue(torch.equal(hc_batch[key], x_batch[key]), key)
        self.assertEqual(int((x_batch["labels"] != IGNORE).sum()), x_batch["input_ids"].shape[1] - end_x
                         - int((x_batch["attention_mask"] == 0).sum()))
        # A row without a sidecar entry stays the trainer's: no forced carriers outside the bank.
        self.assertTrue(bool((plain_batch["aux_camera_positions"] < 0).all()))

    def test_bank_points_fill_after_the_queries(self):
        entry = headcall_entry(self.base, self.hc)
        record = R.merge_point_depth(zero_record(bank_points=SLOTS), entry)
        pd = record["point_depth"]
        self.assertEqual(pd["uv"][1][0], [215.0, 529.0])
        self.assertEqual(pd["uv"][1][1:], [[100.0 + k, 200.0] for k in range(SLOTS - 1)])
        self.assertEqual(sum(pd["mask"][1]), SLOTS)
        self.assertEqual(sum(pd["mask"][4]), 1)
        self.assertEqual(R.depth_queries(entry), R.depth_queries(twin_entry(self.base, self.x)))

    def test_splice_equals_a_fresh_encode(self):
        hc = R.attach([self.hc], [headcall_entry(self.base, self.hc)])[0]
        batch = self.encode([hc])[0]
        records = self.base["head_calls"]
        responses = [r["response"] for r in records]
        responses[1] = "0.95 m"
        texts = D.evaluate(self.base["head_derived"], D.values_of([r["name"] for r in records], responses))[0]
        new_target = D.render(self.base["target_template"], responses, texts)
        spliced = R.splice(self.processor, batch, hc, new_target)
        from student_pilot import ddp_training
        fresh_row = dict(hc, target=new_target, _headcall=dict(hc["_headcall"], target_sha256=R.text_sha256(new_target)))
        ddp_training.HEADCALL.update(stats=Counter(), sampling=None)
        try:
            from student_pilot.diagnostic_data import encode_training
            audit = encode_training(self.processor, fresh_row)[1]
            fresh = ddp_training.encode_microbatch(self.processor, [fresh_row], {fresh_row["qid"]: audit}, [0])
        finally:
            ddp_training.HEADCALL.update(stats=None, sampling=None)
        for key in fresh:
            self.assertEqual(tuple(spliced[key].shape), tuple(fresh[key].shape), key)
            self.assertTrue(bool((spliced[key] == fresh[key]).all()), key)
        self.assertIsNone(R.splice(self.processor, batch, hc, new_target, max_length=8))


# ---------------------------------------------------------------------------------------------- arm configs

BASE_X = Path("/scratch/jjyeung/rung2_push/r2a_w32/config_w32.json")


@unittest.skipUnless(BASE_X.exists(), "the pinned RG2P2_X reference config is not on this host")
class ArmConfigTests(unittest.TestCase):
    def test_arms_differ_only_in_their_headcall_block(self):
        from student_pilot import ddp_config
        from tools import fullft_arm_configs as F
        from tools import headcall_arm_configs as H
        base_a = F.a_from_x(BASE_X.read_bytes())
        bank = ("/fixture/bank.npz", "5" * 64)
        init, heads = {"path": "/m/full_weights/full_weights.json", "sha256": "6" * 64}, {"path": "/m/h.pt", "sha256": "7" * 64}
        configs = {(arm, seed): H.arm_config(base_a, bank, arm, seed, {"path": f"/s/{arm}", "sha256": "8" * 64}, init, heads)
                   for arm in H.ARMS for seed in H.SEEDS}
        strip = lambda cfg: {k: v for k, v in cfg.items() if k not in ("headcall", "seed")}
        self.assertEqual(len({json.dumps(strip(cfg), sort_keys=True) for cfg in configs.values()}), 1)
        hc = ddp_config.normalize_training_config(configs[("HC", 17)], "qwen35")
        self.assertEqual(hc["full_ft"]["init"]["kind"], "full_export")
        rates = {k: v for k, v in hc["full_ft"]["learning_rates"].items() if k != "geometry"}  # inert: no connector
        self.assertEqual(rates, {"heads": 1e-4, "llm": 1e-5, "merger": 1e-5, "vision_blocks": 2e-6})
        self.assertEqual(hc["headcall"]["scheduled_sampling"]["end_step"], 1000)
        self.assertEqual(hc["loss_reduction"], ddp_config.SEGMENT_LOSS_REDUCTION)
        self.assertNotIn("row_routing", configs[("HC", 17)]["camera"])
        self.assertEqual(configs[("HC", 17)]["camera"]["head_only_steps"], 0)
        self.assertIsNone(configs[("HX", 18)]["headcall"]["scheduled_sampling"])
        self.assertEqual(configs[("HC", 18)]["headcall"]["scheduled_sampling"]["seed"], 18)


# ---------------------------------------------------------------------------------------------- HC candidate index

class IndexTests(unittest.TestCase):
    """tools/headcall_rows.py index: RG2P2_X's entries become HC's (inline rows, sharded targets) and admission's own
    loader accepts them; the HC sidecar then joins the admitted rows."""

    def test_rewritten_index_admits_and_joins(self):
        from student_pilot.auxiliary_targets import input_identity
        from student_pilot.provisional import load_provisional_candidates
        from tools import headcall_rows as T
        root = output_root("hcfull_index_")
        frames = frames_dir()
        label = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"
        commit = "a" * 40
        bases = {"q1": distance_row("q1"), "q2": direction_row("q2"), "q3": direction_row("q3")}
        lines, rows = [], {}
        for qid, base in bases.items():
            row = {"qid": qid, "dataset": "d1", "scene": "s1", "category": base["category"], "answer": base["answer"],
                   "target": answer_only(base), "provisional_diagnostic": label, "generation_commit": commit,
                   "validation_commit": commit, "student_input": student_input(frames, options=base["options"])}
            rows[qid] = row
            entry = {"qid": qid, "pool": "r1x", "scene": "s1", "question_type": base["category"], "answer": base["answer"],
                     "dataset": "d1", "generation_commit": commit, "validation_commit": commit, "provisional_diagnostic": label}
            if qid == "q2":  # an inline entry with a sharded target, as RG2VS's
                data = row["target"].encode()
                (root / "x_targets.txt").write_bytes(data)
                entry.update(row, target_path=str(root / "x_targets.txt"), target_offset=0, target_length=len(data),
                             sha256=hashlib.sha256(data).hexdigest())
            else:  # a row file, as T_base / X_base
                payload = json.dumps(row, sort_keys=True).encode()
                path = root / f"{qid}.json"
                path.write_bytes(payload)
                digest = hashlib.sha256(payload).hexdigest()
                entry.update(row_path=str(path), row_sha256=digest, target_path=str(path), sha256=digest)
            lines.append(json.dumps(entry, sort_keys=True))
        (root / "x_index.jsonl").write_text("\n".join(lines) + "\n")
        replace = [{"qid": qid, "category": bases[qid]["category"], "route": "headcall" if qid == "q1" else "plain",
                    "target": bases[qid]["target"], "input_sha256": input_identity(rows[qid]),
                    "x_target_sha256": R.text_sha256(rows[qid]["target"])} for qid in ("q1", "q2")]
        T.write_replace(root / "replace.jsonl.gz", replace, {"fixture": True})
        T.main(["index", "--x-index", str(root / "x_index.jsonl"), "--replace", str(root / "replace.jsonl.gz"),
                "--out", str(root / "hc")])
        admitted_rows = {row["qid"]: row for row in load_provisional_candidates(str(root / "hc/candidate_index.jsonl"), label)}
        self.assertEqual(admitted_rows["q1"]["target"], bases["q1"]["target"])
        self.assertEqual(admitted_rows["q2"]["target"], bases["q2"]["target"])
        self.assertEqual(admitted_rows["q3"]["target"], answer_only(bases["q3"]))
        sidecar = R.write_sidecar(root / "HC.jsonl.gz", "HC", [headcall_entry(bases["q1"], admitted_rows["q1"])], {})
        joined, report = R.join(list(admitted_rows.values()), {"arm": "HC", "sidecar": sidecar, "scheduled_sampling": None})
        self.assertEqual(report["headcall_rows"], 1)
        bad = [dict(replace[0], x_target_sha256="0" * 64)]
        T.write_replace(root / "bad.jsonl.gz", bad, {})
        with self.assertRaisesRegex(ValueError, "differs from the build"):
            T.main(["index", "--x-index", str(root / "x_index.jsonl"), "--replace", str(root / "bad.jsonl.gz"),
                    "--out", str(root / "hc_bad")])


# ---------------------------------------------------------------------------------------------- scheduled sampling

class CountingModel(torch.nn.Module):
    """Stands in for the wrapped model: counts no-grad forwards (each would be an FSDP collective)."""

    def __init__(self):
        super().__init__()
        self.forwards = 0

    def forward(self, **kwargs):
        self.forwards += 1
        return None


class SamplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = processor()
        cls.frames = frames_dir()
        cls.base = distance_row("q1")
        row = admitted(cls.base, cls.frames, "q1")
        cls.hc = {**row, "_headcall": headcall_entry(cls.base, row)}
        plain = direction_row("q9")
        cls.plain = admitted(plain, cls.frames, "q9", target=answer_only(plain))

    def run_batch(self, factory, weights=(1.0, 1.0), matched=None, step=7, **settings):
        from student_pilot import ddp_training
        sampling = R.Sampling(sampling_settings(**settings), heads_factory=factory)
        ddp_training.HEADCALL.update(stats=Counter(), sampling=sampling)
        rows = [self.hc, self.plain]
        try:
            collated = ddp_training.encode_microbatch(self.processor, rows, audits_of(self.processor, rows), [0, 1])
        finally:
            ddp_training.HEADCALL.update(stats=None, sampling=None)
        used, encodings, proc = sampling.take(collated)
        model = CountingModel()
        context = (patch.object(R, "matched_count", side_effect=lambda count, *a: matched) if matched is not None
                   else nullcontext())
        with context:
            out = R.scheduled_batch(sampling, model, collated, used, encodings, proc, list(weights), step,
                                    fsdp=matched is not None)
        return collated, out, sampling, model

    def test_swaps_rerender_every_derived_value_and_stay_masked(self):
        tok = tokenizer()
        factory = lambda model, prompt, context: NoisyHeads(OracleHeads(), depth_log_sigma=0.02, position_sigma_m=0.02,
                                                            heading_sigma_deg=1.0, seed=5)
        collated, trained, sampling, _ = self.run_batch(factory)
        self.assertEqual(sampling.stats["rows_swapped"], 1)
        self.assertEqual(sampling.stats["session_forwards"], 1)  # the plain row needs no session
        full = tok.decode(trained["input_ids"][0][trained["attention_mask"][0] == 1].tolist())
        found = exchanges(full)
        self.assertEqual(len(found), 4)
        self.assertNotEqual([e[4] for e in found], [r["response"] for r in self.base["head_calls"]])
        texts, _ = D.evaluate(self.base["head_derived"], D.values_of([r["name"] for r in self.base["head_calls"]],
                                                                     [e[4] for e in found]))
        for derived in texts:
            self.assertIn(derived, full)
        supervised = tok.decode(trained["input_ids"][0][trained["labels"][0] != IGNORE].tolist())
        self.assertNotIn("<tool_response>", supervised)
        kept, before = trained["attention_mask"][1] == 1, collated["attention_mask"][1] == 1
        self.assertEqual(trained["input_ids"][1][kept].tolist(), collated["input_ids"][1][before].tolist())

    def test_a_swap_that_changes_the_decision_is_rejected_whole(self):
        loose = {"depth_rel_tol": 10.0, "depth_abs_tol_m": 10.0}
        collated, trained, sampling, _ = self.run_batch(lambda m, p, c: ScaledHeads(1.6), **loose)
        self.assertIs(trained, collated)  # the derived distance misses the GT answer: GT target kept
        self.assertEqual(sampling.sampler.rejected_rows, 1)
        self.assertEqual(sampling.stats["rows_swapped"], 0)

    def test_padding_rows_never_sample_and_fsdp_ranks_match_forward_counts(self):
        calls = []

        def factory(model, prompt, context):
            calls.append(1)
            return OracleHeads()
        collated, trained, sampling, model = self.run_batch(factory, weights=(0.0, 1.0), matched=3)
        self.assertEqual(calls, [])  # the head-call row is a padding slot
        self.assertEqual(sampling.stats["discarded_forwards"], 3)
        self.assertEqual(model.forwards, 3)
        self.assertIs(trained, collated)

    def test_choice_is_a_pure_function_of_seed_qid_and_step(self):
        a = R.Sampling(sampling_settings(start_p=0.0, end_p=0.5, end_step=1000, seed=17))
        b = R.Sampling(sampling_settings(start_p=0.0, end_p=0.5, end_step=1000, seed=17))
        for step in (0, 1, 250, 999, 1400):
            self.assertEqual(a.sampler.chosen(self.hc["_headcall"], step), b.sampler.chosen(self.hc["_headcall"], step))
        self.assertEqual(a.sampler.schedule(0), 0.0)
        self.assertAlmostEqual(a.sampler.schedule(500), 0.25)
        self.assertEqual(a.sampler.schedule(1549), 0.5)


# ---------------------------------------------------------------------------------------------- full_export init

def write_milestone(root, model, heads, step=20):
    """The trainer's own milestone writer (ddp_checkpoints.save_milestone_export) on a single-process gloo group."""
    import torch.distributed as dist
    from student_pilot import ddp_checkpoints, ddp_config, fsdp_training
    settings = ddp_config.normalize_training_config({"world_size": 2, "parallel": "fsdp", "full_ft": {"train": {"llm": True}}},
                                                    "qwen35")
    header = {"student": "qwen35", "base": {"revision": "fixture"}, "base_sha256": "b" * 64,
              "protocol": {"sha256": "c" * 64}, "provenance": {"config_sha256": "d" * 64, "commit": "e" * 40},
              "world_size": 2, "parallel": "fsdp", "settings": settings}
    store = SimpleNamespace(root=Path(root))
    (Path(root) / "checkpoints").mkdir(parents=True, exist_ok=True)
    from student_pilot import full_ft
    base_names = [name for name, _ in full_ft.base_parameters(model)]
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{free_port()}", rank=0, world_size=1)
    try:
        with patch.object(ddp_checkpoints, "ensure_free_space", lambda *a: None), \
                patch.object(fsdp_training, "publication_state", lambda distributed: {
                name: value for name, value in model.state_dict().items() if not name.startswith("auxiliary_heads.")}):
            record = ddp_checkpoints.save_milestone_export(store, header, model, base_names, step, {"mode": "full"},
                                                           auxiliary_heads=heads)
    finally:
        dist.destroy_process_group()
    return Path(record["path"])


def free_port():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return server.getsockname()[1]


class FullExportTests(unittest.TestCase):
    def test_milestone_export_warm_starts_weights_and_heads_exactly(self):
        from student_pilot import auxiliary_losses, camera_config, full_ft
        from tests.fullft_toys import tiny_base
        from tests.test_full_ft import CarrierTokenizer
        trained = tiny_base()
        with torch.no_grad():
            for parameter in trained.parameters():
                parameter.add_(torch.randn_like(parameter) * 0.01)
        camera = camera_config.normalize({"weight": 1.0, "embed_dim": 16, "num_heads": 2, "trunk_depth": 2,
                                          "refine_iterations": 2, "supervision": PIN})
        heads = auxiliary_losses.attach(trained, None, CarrierTokenizer(), camera)
        with torch.no_grad():
            heads.camera.tokens.normal_(0.0, 0.5)
        milestone = write_milestone(output_root("hcfull_milestone_"), trained, heads)
        manifest, pins = full_ft.read_milestone(milestone)
        self.assertEqual(manifest["step"], 20)
        block = full_ft.normalize({"train": {"llm": True, "vision_blocks": True, "merger": True},
                                   "init": {"kind": "full_export", **pins["full_weights"]},
                                   "init_modules": {"heads": pins["heads"]}})
        fresh = tiny_base(seed=99)
        report = full_ft.load_init_export(fresh, block, "b" * 64)
        self.assertEqual(report["tensors"], len(full_ft.base_parameters(fresh)))
        expected = {name: value.to(torch.bfloat16) for name, value in trained.state_dict().items()
                    if not name.startswith("auxiliary_heads.")}
        for name, value in fresh.state_dict().items():
            self.assertTrue(torch.equal(value, expected[name]), name)
        full_ft.prepare_model(fresh, block)
        fresh_heads = auxiliary_losses.attach(fresh, None, CarrierTokenizer(), camera)
        loaded = full_ft.load_init_modules(block, heads=fresh_heads)
        self.assertEqual(loaded["heads"]["sha256"], pins["heads"]["sha256"])
        for name, value in fresh_heads.state_dict().items():
            self.assertTrue(torch.equal(value, heads.state_dict()[name]), name)
        with self.assertRaisesRegex(ValueError, "another base"):
            full_ft.load_init_export(tiny_base(seed=5), block, "f" * 64)
        wrong = full_ft.normalize({**block, "init": {**block["init"], "sha256": "0" * 64}})
        with self.assertRaisesRegex(ValueError, "differs from its pin"):
            full_ft.load_init_export(tiny_base(seed=5), wrong, "b" * 64)
        (milestone / "auxiliary_heads.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "differs from MILESTONE.json"):
            full_ft.read_milestone(milestone)


# ---------------------------------------------------------------------------------------------- end to end

def camera_model():
    from transformers import AutoConfig, AutoModelForImageTextToText
    from student_pilot import auxiliary_losses, camera_config, full_ft
    config = AutoConfig.from_pretrained(TINY)
    config.vision_config.depth = 4
    torch.manual_seed(0)
    model = AutoModelForImageTextToText.from_config(config).float()
    block = full_ft.normalize({"train": {"llm": True, "vision_blocks": True, "merger": True}})
    _, report = full_ft.prepare_model(model, block)
    camera = camera_config.normalize({"weight": 1.0, "weight_gravity": 0.5, "weight_scale": 0.2, "embed_dim": 16,
                                      "num_heads": 2, "trunk_depth": 2, "refine_iterations": 2, "supervision": PIN,
                                      "point_depth": dict(SMALL_DEPTH)})
    heads = auxiliary_losses.attach(model, None, tokenizer(), camera)
    with torch.no_grad():
        heads.camera.head.pose_branch.fc2.bias[7:9] += 1.0  # a printable field of view when untrained
    return model, heads, block, report


def e2e_worker(rank, port, root):
    """One rank: tiny Qwen3.5 + camera and point-depth heads, full FT under FSDP (CPU/gloo, BF16 compute). Rank 0's
    micro-batch holds a sampled head-call row (session forward on the wrapped model, NoisyHeads answers so swaps pass
    the gate) and a plain row; rank 1's head-call row is a padding slot, so it runs one discarded forward to match."""
    import torch.distributed as dist
    from student_pilot import ddp_core, ddp_training, fsdp_training, full_ft
    from student_pilot.ddp_config import SEGMENT_LOSS_REDUCTION
    torch.set_num_threads(2)
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=rank, world_size=2,
                            timeout=timedelta(seconds=180))
    try:
        frames = json.loads((Path(root) / "frames.json").read_text())
        proc = processor()
        model, heads, block, report = camera_model()
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.train()
        replicated = list(heads.parameters())
        wrapped = full_ft.wrap_full_model(model, replicated, dist.group.WORLD, torch.device("cpu"))
        base = distance_row(f"q{rank}a")
        hc = admitted(base, frames, f"q{rank}a")
        hc = {**hc, "_headcall": headcall_entry(base, hc)}
        plain_base = direction_row(f"q{rank}b")
        plain = admitted(plain_base, frames, f"q{rank}b", target=answer_only(plain_base))
        rows = [hc, plain]
        session_forwards = []

        def factory(model_, prompt, context):
            R.default_heads_factory(model_, prompt, context)  # the real session forward on the FSDP model
            session_forwards.append(1)
            return NoisyHeads(OracleHeads(), depth_log_sigma=0.02, position_sigma_m=0.02, heading_sigma_deg=1.0, seed=5)
        sampling = R.Sampling(sampling_settings(), heads_factory=factory)
        ddp_training.HEADCALL.update(stats=Counter(), sampling=sampling)
        collated = ddp_training.encode_microbatch(proc, rows, audits_of(proc, rows), [0, 1])
        used, encodings, _ = sampling.take(collated)
        weights = [1.0, 1.0] if rank == 0 else [0.0, 1.0]
        batch = R.scheduled_batch(sampling, wrapped, collated, used, encodings, proc, weights, 3,
                                  process_group=dist.group.WORLD, fsdp=True, max_length=16384)
        losses = ddp_core.row_losses(wrapped, batch, loss_reduction=SEGMENT_LOSS_REDUCTION)
        (losses * torch.tensor(weights)).sum().backward()
        fsdp_training.average_adapter_gradients(replicated, dist.group.WORLD)
        tool = tool_token_ids(tokenizer())
        inside = torch.zeros_like(batch["input_ids"][0], dtype=torch.bool)
        flag = False
        for i, token in enumerate(batch["input_ids"][0].tolist()):
            flag = flag or token == tool["<tool_response>"]
            inside[i] = flag
            if token == tool["</tool_response>"]:
                flag = False
        result = {"losses": losses.detach(), "camera": heads.last_terms.get("camera"),
                  "positions": batch["aux_camera_positions"].clone(),
                  "response_tokens": int(inside.sum()), "response_labels_supervised": int((batch["labels"][0][inside] != IGNORE).sum()),
                  "stats": dict(sampling.stats), "session_forwards": len(session_forwards),
                  "depth_grad": float(sum(p.grad.abs().sum() for p in heads.camera.point_depth.parameters() if p.grad is not None)),
                  "token_grad": float(heads.camera.tokens.grad.abs().sum()),
                  "finite": all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in replicated),
                  "flow": full_ft.check_gradient_flow(full_ft.sharded_groups(wrapped, block), report)}
        torch.save(result, Path(root) / f"e2e_rank{rank}.pt")
    finally:
        dist.destroy_process_group()


@unittest.skipUnless(os.environ.get("HEADCALL_E2E", "1") == "1", "end-to-end CPU/gloo run disabled")
class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.test_full_ft import pair
        cls.root = output_root("hcfull_e2e_")
        (cls.root / "frames.json").write_text(json.dumps(frames_dir()))
        pair(e2e_worker, str(cls.root))

    def result(self, rank):
        return torch.load(self.root / f"e2e_rank{rank}.pt", weights_only=False)

    def test_one_fsdp_step_with_carriers_masking_sampling_and_heads(self):
        zero, one = self.result(0), self.result(1)
        for result in (zero, one):
            self.assertTrue(bool(torch.isfinite(result["losses"]).all()))
            self.assertTrue(bool((result["positions"][0] >= 0).all()))  # forced carriers on the head-call row
            self.assertTrue(bool((result["positions"][1] < 0).all()))  # none on the plain row outside the bank
            self.assertGreater(result["response_tokens"], 0)
            self.assertEqual(result["response_labels_supervised"], 0)  # responses never train the LM
            self.assertTrue(result["finite"])
            self.assertGreater(result["depth_grad"], 0)  # queried points supervise the depth head
            self.assertGreater(result["token_grad"], 0)  # c_first / c_rest learn
            self.assertEqual(set(result["flow"]), {"llm", "vision_blocks", "merger"})
        self.assertEqual(zero["session_forwards"], 1)
        self.assertEqual(zero["stats"].get("rows_swapped"), 1)  # NoisyHeads answers pass the gate and the decision
        self.assertEqual(one["session_forwards"], 0)
        self.assertEqual(one["stats"].get("discarded_forwards"), 1)  # matched to rank 0's one session forward


if __name__ == "__main__":
    unittest.main()
