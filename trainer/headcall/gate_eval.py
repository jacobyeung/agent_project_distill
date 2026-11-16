"""Phase-1 accuracy gate on phase 2's held-out rows: the heads answer each row's own calls, scored with phase 1's agreed
thresholds, and every decision is re-executed from the heads' responses.

Rows and scenes. The rows are converted held-out rows (rows_*_heldout_calls.jsonl.gz). Every row's scene must be on
phase 1's held-out list (configs/gate_heldout_scenes_v1.json: the 38 scenes no phase-1 training row uses) and absent
from phase 2's training census (TRAINING_SCENES.json of the training conversion); anything else raises. There is no
fallback to other rows.

Calls. Each recorded call goes to the heads. A refusal (CallError) or a missing value is a failure: it enters the
error statistics as an infinite error, its row's decisions count as not preserved, and the gate's `call_refusals`
criterion fails. No GT value is ever substituted.

Statistics (phase 1's definitions and thresholds, student_pilot.gate_eval.GATE):
  pose, per unique (scene, frame) at the anchor frames 2..32: rotation error (geodesic of the full rotation:
  heading, pitch and roll), position and heading error in the gravity reference; medians gate
  (rotation <= 5.2 deg, position <= 0.25 m, heading <= 10 deg). Frame 1 is the origin by definition and is reported
  apart (pitch and roll only).
  depth, per unique (scene, frame, point): AbsRel (mean <= 0.10), delta < 1.25 (mean >= 0.90), absolute error
  (median <= 0.20 m).
  decisions: (a) phase 1's pairwise decisions over each row's derived points (near/far for points of one frame,
  left/right and front/back in the gravity reference, counted where GT differs by >= 0.20 m); (b) the row decisions
  the trace derives (headcall.derive.decision, the converters' own rule): direction labels and angles, movement
  direction, closest candidate, distance and displacement within 10% (or 0.10 m), re-executed from the heads' printed
  responses and compared with the same derivation on the GT responses (headcall.derive.same_decision). Both
  must reach phase 1's decision_agreement_min (0.85). Sizes have no derived decision and are not counted.
A criterion without a measurement fails.

Rows. Phase 1's 38 held-out scenes have no generated questions (the rung-1 bank and its qgen sources cover
training-side scenes only), so the held-out rows are headcall.gate_probe's GT probe rows: every derivation a
training trace states (directions, distances, closest candidate, camera movement and displacement), with the calls
and GT responses a converter would write, on those scenes only.

usage (on a GPU node, phase 1's checkpoint):
  python -m headcall.gate_eval --rows DIR --training-scenes TRAINING_SCENES.json --out REPORT.json \
      --student S --adapter-dir A --heads-json H --heads-pt P [--heldout LIST] [--shuffled]
a full fine-tuning checkpoint: a milestone export (CPD's init; MILESTONE.json verifies every file), or a publication's
full_weights/ with the run root's auxiliary_heads.json and auxiliary_heads.pt:
  python -m headcall.gate_eval ... --student S --milestone DIR/milestone_<step>
  python -m headcall.gate_eval ... --student S --full-weights ADAPTER/full_weights --heads-json H --heads-pt P
CPU dry run of the machinery (no checkpoint; GT or GT-plus-noise answers, never a gate result):
  python -m headcall.gate_eval --rows DIR --training-scenes TRAINING_SCENES.json --out REPORT.json \
      --dry-run oracle|noisy
"""
import argparse
import glob
import gzip
import json
import math
import os
from collections import OrderedDict, defaultdict

import numpy as np

from . import derive as D
from . import phase1
from .geometry import rotation_error_deg
from .heads import HeadContext, HeadOutputPool, RecordingHeads, ShuffledHeads, value_of_record
from .protocol import Call, CallError, format_value

SCHEMA = "headcall-phase1-gate-v2"
DECISION_MARGIN_M = 0.20


def load_rows(rows_dir):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('headcall/gate_eval.py:load_rows')
    rows = []
    for path in sorted(glob.glob(os.path.join(rows_dir, "rows_*_heldout_calls.jsonl.gz"))):
        with gzip.open(path, "rt") as stream:
            rows.extend(json.loads(line) for line in stream)
    return rows


def check_scenes(rows, heldout, training_scenes):
    """Every row on phase 1's held-out list and none in the training census (phase 1's gate_eval.check_heldout rule)."""
    if not rows:
        raise ValueError("The gate needs at least one held-out row")
    heldout, training = {tuple(s) for s in heldout}, {tuple(s) for s in training_scenes}
    if heldout & training:
        raise ValueError("The held-out list overlaps the training census")
    for row in rows:
        key = (row.get("dataset"), row.get("scene"))
        if key not in heldout:
            raise ValueError("Row %s: scene %s is not on phase 1's held-out list" % (row.get("qid"), key))
        if key in training:
            raise ValueError("Row %s: scene %s is in the training census" % (row.get("qid"), key))


def call_of(record):
    return Call(record["name"], int(record["frame"]), tuple(record["point"]) if record.get("point") else None)


def ask(heads, row):
    """The heads' value for every call of the row (None for a refusal) and the refusals."""
    heads.begin(HeadContext([], key=row.get("qid"), row=row))
    values, refusals = [], []
    for record in row.get("head_calls") or []:
        try:
            values.append(heads.answer(call_of(record)))
        except CallError as error:
            values.append(None)
            refusals.append({"qid": row.get("qid"), "index": record["index"], "name": record["name"],
                             "frame": record["frame"], "code": error.code, "error": str(error)[:200]})
    return values, refusals


def wrap(angle):
    return abs((float(angle) + 180.0) % 360.0 - 180.0)


def pose_errors(gt, pred):
    if pred is None:
        return {"rotation_deg": math.inf, "position_m": math.inf, "heading_deg": math.inf, "pitch_deg": math.inf,
                "roll_deg": math.inf}
    return {"rotation_deg": rotation_error_deg(pred, gt),
            "position_m": float(np.linalg.norm(np.subtract(pred.position, gt.position))),
            "heading_deg": wrap(pred.heading_deg - gt.heading_deg), "pitch_deg": abs(pred.pitch_deg - gt.pitch_deg),
            "roll_deg": wrap(pred.roll_deg - gt.roll_deg)}


def depth_errors(gt, pred):
    if pred is None or not pred > 0:
        return {"abs_rel": math.inf, "ratio": math.inf, "abs_err_m": math.inf}
    return {"abs_rel": abs(pred - gt) / gt, "ratio": max(pred / gt, gt / pred), "abs_err_m": abs(pred - gt)}


def derived_results(row, responses):
    """(results, error) of the row's derivation from these response texts (None for a refused call)."""
    if any(r is None for r in responses):
        return None, "refused_call"
    try:
        _, results = D.evaluate(row["head_derived"], D.values_of([r["name"] for r in row["head_calls"]], responses))
        return results, None
    except ValueError as error:
        return None, str(error)[:120]


def row_decision(row, results):
    """The row's derived decision (headcall.derive.decision: the same function the converters and scheduled sampling
    use): ('label'|'angle'|'distance'|'closest', value), or None."""
    return D.decision(row, row["head_derived"], results)


def same_decision(gt, pred):
    """headcall.derive.same_decision: the converters' and scheduled sampling's agreement rule."""
    return D.same_decision(gt, pred)


def decide(decisions, name, gt_delta, pred_delta, margin=DECISION_MARGIN_M):
    """Phase 1's gate_eval.decide: sign agreement on pairs whose GT difference clears the margin (a missing
    prediction counts as disagreement)."""
    hits, total = decisions.get(name, (0, 0))
    for g, p in zip(gt_delta, pred_delta):
        if abs(g) >= margin:
            total += 1
            hits += int(p is not None and np.sign(g) == np.sign(p))
    decisions[name] = (hits, total)


def pairwise_decisions(decisions, row, gt_results, pred_results, pred_values):
    items = row["head_derived"]
    points = [k for k, item in enumerate(items) if item["kind"] == "point"]
    for a in range(len(points)):
        for b in range(a + 1, len(points)):
            i, j = points[a], points[b]
            pa = pred_results[i] if pred_results is not None else None
            pb = pred_results[j] if pred_results is not None else None
            for axis, name in ((0, "point_left_right"), (1, "point_front_back")):
                decide(decisions, name, [gt_results[i][axis] - gt_results[j][axis]],
                       [None if pa is None or pb is None else pa[axis] - pb[axis]])
            di, dj = items[i]["depth"], items[j]["depth"]
            if row["head_calls"][di]["frame"] == row["head_calls"][dj]["frame"]:
                gi, gj = value_of_record(row["head_calls"][di]), value_of_record(row["head_calls"][dj])
                qi, qj = pred_values[di], pred_values[dj]
                decide(decisions, "depth_near_far", [gi - gj], [None if qi is None or qj is None else qi - qj])


def stats(values):
    values = np.asarray(values, dtype=np.float64)
    if not values.size:
        return None
    finite = values[np.isfinite(values)]
    return {"n": int(values.size), "refused": int(values.size - finite.size), "median": float(np.median(values)),
            "p90": float(np.percentile(values, 90)), "mean": float(values.mean())}


def evaluate(rows, heads, heldout, training_scenes, gate=None):
    """The gate report of a head backend on held-out rows (see the module docstring)."""
    gate = gate or phase1.gate_thresholds()
    check_scenes(rows, heldout, training_scenes)
    pose_items, origin_items, depth_items = OrderedDict(), OrderedDict(), OrderedDict()
    pair_decisions, row_counts, refusals = {}, defaultdict(lambda: [0, 0]), []
    per_row = []
    for row in rows:
        values, refused = ask(heads, row)
        refusals.extend(refused)
        scene = (row["dataset"], row["scene"])
        for record, value in zip(row["head_calls"], values):
            gt = value_of_record(record)
            if record["name"] == "pose":
                key = scene + (record["frame"],)
                target = origin_items if record["frame"] == 1 else pose_items
                target.setdefault(key, pose_errors(gt, value))
            else:
                key = scene + (record["frame"], tuple(record["point"]))
                depth_items.setdefault(key, depth_errors(gt, value))
        if not row.get("head_derived"):
            continue
        gt_responses = [r["response"] for r in row["head_calls"]]
        pred_responses = [format_value(r["name"], v) if v is not None else None for r, v in zip(row["head_calls"], values)]
        gt_results, gt_error = derived_results(row, gt_responses)
        if gt_results is None:
            raise ValueError("Row %s: its GT responses do not derive (%s)" % (row.get("qid"), gt_error))
        pred_results, pred_error = derived_results(row, pred_responses)
        pred_values = D.values_of([r["name"] for r in row["head_calls"]], pred_responses)
        pairwise_decisions(pair_decisions, row, gt_results, pred_results, pred_values)
        gt_dec = row_decision(row, gt_results)
        pred_dec = row_decision(row, pred_results) if pred_results is not None else None
        same = same_decision(gt_dec, pred_dec)
        if same is not None:
            row_counts[row["category"]][1] += 1
            row_counts[row["category"]][0] += int(same)
        per_row.append({"qid": row["qid"], "category": row["category"], "gt_decision": gt_dec,
                        "head_decision": pred_dec, "preserved": same, "derive_error": pred_error})
    pose_list, depth_list = list(pose_items.values()), list(depth_items.values())
    pooled = {k: [item[k] for item in pose_list] for k in ("rotation_deg", "position_m", "heading_deg", "pitch_deg",
                                                             "roll_deg")}
    origin = {k: [item[k] for item in origin_items.values()] for k in ("pitch_deg", "roll_deg")}
    abs_rel = [item["abs_rel"] for item in depth_list]
    ratios = np.asarray([item["ratio"] for item in depth_list], dtype=np.float64)
    hits, total = sum(h for h, _ in pair_decisions.values()), sum(t for _, t in pair_decisions.values())
    r_hits, r_total = sum(h for h, _ in row_counts.values()), sum(t for _, t in row_counts.values())
    summary = OrderedDict([
        ("rows", len(rows)), ("scenes", len({(r["dataset"], r["scene"]) for r in rows})),
        ("calls", sum(len(r.get("head_calls") or []) for r in rows)), ("call_refusals", len(refusals)),
        ("rotation_deg", stats(pooled["rotation_deg"])), ("position_m", stats(pooled["position_m"])),
        ("heading_deg", stats(pooled["heading_deg"])), ("pitch_deg", stats(pooled["pitch_deg"])),
        ("roll_deg", stats(pooled["roll_deg"])),
        ("origin_pitch_deg", stats(origin["pitch_deg"])), ("origin_roll_deg", stats(origin["roll_deg"])),
        ("depth_points", len(depth_list)),
        ("depth_abs_rel", float(np.mean(abs_rel)) if abs_rel else None),
        ("depth_delta125", float(np.mean(ratios < 1.25)) if ratios.size else None),
        ("depth_abs_err_m", stats([item["abs_err_m"] for item in depth_list])),
        ("pairwise_decisions", {k: {"agree": h, "total": t, "rate": h / t if t else None}
                                for k, (h, t) in sorted(pair_decisions.items())}),
        ("decision_agreement", hits / total if total else None),
        ("row_decisions", {k: {"preserved": h, "total": t, "rate": h / t if t else None}
                           for k, (h, t) in sorted(row_counts.items())}),
        ("row_decision_agreement", r_hits / r_total if r_total else None)])

    def at_most(value, limit):
        return "not_measured" if value is None else bool(value <= limit)

    def median(stat):
        return None if stat is None else stat["median"]
    checks = OrderedDict([
        ("call_refusals", len(refusals) == 0),
        ("rotation_deg_median", at_most(median(summary["rotation_deg"]), gate["rotation_deg_median_max"])),
        ("position_m_median", at_most(median(summary["position_m"]), gate["position_m_median_max"])),
        ("heading_deg_median", at_most(median(summary["heading_deg"]), gate["heading_deg_median_max"])),
        ("depth_abs_rel", at_most(summary["depth_abs_rel"], gate["depth_abs_rel_max"])),
        ("depth_delta125", "not_measured" if summary["depth_delta125"] is None
         else bool(summary["depth_delta125"] >= gate["depth_delta125_min"])),
        ("depth_abs_err_m_median", at_most(median(summary["depth_abs_err_m"]), gate["depth_abs_err_m_median_max"])),
        ("decision_agreement", "not_measured" if summary["decision_agreement"] is None
         else bool(summary["decision_agreement"] >= gate["decision_agreement_min"])),
        ("row_decision_agreement", "not_measured" if summary["row_decision_agreement"] is None
         else bool(summary["row_decision_agreement"] >= gate["decision_agreement_min"]))])
    return OrderedDict([
        ("schema", SCHEMA), ("heldout_contract", "phase1_heldout_scenes_only_never_training_or_benchmark"),
        ("passed", all(v is True for v in checks.values())), ("checks", checks), ("thresholds", dict(gate)),
        ("summary", summary), ("refusals", refusals[:200]), ("per_row", per_row)])


def evaluate_with_shuffled(rows, heads, heldout, training_scenes, seed=31):
    """The gate report of the heads and of the shuffled control: every call answered with a real head output
    recorded for another row (another scene), from the same pass."""
    pool = HeadOutputPool()
    report = evaluate(rows, RecordingHeads(heads, pool), heldout, training_scenes)
    shuffled = evaluate(rows, ShuffledHeads(pool, seed=seed), heldout, training_scenes)
    return OrderedDict([("heads", report), ("shuffled", shuffled), ("shuffle_pool_values", len(pool)),
                        ("row_decision_agreement_minus_shuffled",
                         None if report["summary"]["row_decision_agreement"] is None
                         or shuffled["summary"]["row_decision_agreement"] is None
                         else report["summary"]["row_decision_agreement"]
                         - shuffled["summary"]["row_decision_agreement"])])


class Phase1CheckpointHeads(object):
    """Phase1Heads over a phase-1 checkpoint: each row's prompt is encoded by phase 1's own encoder
    (diagnostic_data.encode_prompt), carriers are inserted, and HeadSession.from_forward builds the row's session."""

    def __init__(self, student, adapter_dir, heads_json, heads_pt, device="cuda:0"):
        import torch
        from .heads import Phase1Heads

        driver = phase1.gate_driver()
        self.model, self.processor, self.load_report = driver.load_checkpoint(student, adapter_dir, heads_json,
                                                                              heads_pt, device=device)
        encode_prompt = phase1._module("diagnostic_data").encode_prompt
        head_api = phase1.head_api()
        context = torch.autocast("cuda", dtype=torch.bfloat16)

        def session(ctx):
            batch = encode_prompt(self.processor, ctx.row)[0]
            batch = {k: v.to(device) if hasattr(v, "to") else v for k, v in batch.items()}
            batch = phase1.insert_carriers(batch, self.processor.tokenizer)
            return head_api.HeadSession.from_forward(self.model, batch, forward_context=context)
        self.heads = Phase1Heads(session)


def load_full_ft_checkpoint(student, full_weights, heads_json, heads_pt, device="cuda:0"):
    """The pinned BF16 base with every base tensor replaced by a full fine-tuning export (full_ft.load_export, exact),
    plus the trained heads (auxiliary_losses.attach with the published settings, strict exact reload), in eval mode,
    and the student's processor. Returns (model, processor, load report)."""
    import hashlib
    import torch
    full_ft = phase1._module("full_ft")
    attach = phase1.auxiliary_losses().attach
    processor = phase1._module("batches").load_processor(student)
    model = phase1._module("runner").load_base(student, device=device)
    manifest, _ = full_ft.read_export(full_weights)
    from student_pilot.students import same_student
    if not same_student(manifest.get("base", {}).get("student"), student):
        raise ValueError("The full-weights export belongs to another student")
    weights = full_ft.load_export(model, full_weights)
    with open(heads_json) as handle:
        heads_manifest = json.load(handle)
    if "camera" not in heads_manifest:
        raise ValueError("The checkpoint has no camera heads")
    settings = (heads_manifest["settings"] if heads_manifest["settings"].get("pose_weight")
                or heads_manifest["settings"].get("depth_weight") else None)
    heads = attach(model, settings, processor.tokenizer, heads_manifest["camera"]["settings"])
    import io
    with open(heads_pt, "rb") as handle:
        payload = handle.read()
    with open(heads_json, "rb") as handle:
        heads_json_sha256 = hashlib.sha256(handle.read()).hexdigest()
    state = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
    heads.load_state_dict(state, strict=True)
    if any(not torch.equal(value.detach().cpu(), state[name]) for name, value in heads.state_dict().items()):
        raise ValueError("Head weights did not reload exactly")
    model.eval()
    model.requires_grad_(False)
    return model, processor, {"full_weights": weights, "export_training": manifest.get("training"),
                              "heads_sha256": hashlib.sha256(payload).hexdigest(),
                              "heads_json_sha256": heads_json_sha256}


def milestone_paths(directory):
    """(full_weights dir, heads json, heads pt, milestone report) of a milestone export, every file verified against
    MILESTONE.json (full_ft.read_milestone)."""
    full_ft = phase1._module("full_ft")
    manifest, pins = full_ft.read_milestone(directory)
    if pins["heads"] is None or "auxiliary_heads.json" not in manifest["files"]:
        raise ValueError("The milestone export has no trained heads")
    return (os.path.dirname(pins["full_weights"]["path"]), os.path.join(os.path.abspath(directory), "auxiliary_heads.json"),
            pins["heads"]["path"], {"milestone": os.path.abspath(directory), "step": manifest.get("step"),
                                    "identity": manifest.get("identity"), "pins": pins})


class FullFTCheckpointHeads(object):
    """Phase1Heads over a full fine-tuning checkpoint (milestone export or publication): each row's prompt is encoded
    by the trainer's encoder (diagnostic_data.encode_prompt), carriers are inserted, and HeadSession.from_forward
    builds the row's session."""

    def __init__(self, student, full_weights, heads_json, heads_pt, device="cuda:0"):
        import torch
        from .heads import Phase1Heads

        self.model, self.processor, self.load_report = load_full_ft_checkpoint(student, full_weights, heads_json,
                                                                               heads_pt, device=device)
        encode_prompt = phase1._module("diagnostic_data").encode_prompt
        head_api = phase1.head_api()
        context = torch.autocast("cuda", dtype=torch.bfloat16) if str(device).startswith("cuda") else None

        def session(ctx):
            batch = encode_prompt(self.processor, ctx.row)[0]
            batch = {k: v.to(device) if hasattr(v, "to") else v for k, v in batch.items()}
            batch = phase1.insert_carriers(batch, self.processor.tokenizer)
            return head_api.HeadSession.from_forward(self.model, batch, forward_context=context)
        self.heads = Phase1Heads(session)


def main(argv=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('headcall/gate_eval.py:main')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", required=True, help="directory of rows_*_heldout_calls.jsonl.gz")
    parser.add_argument("--training-scenes", required=True, help="TRAINING_SCENES.json of the training conversion")
    parser.add_argument("--heldout", default=None, help="phase 1's held-out list (default: its configs file)")
    parser.add_argument("--out", required=True)
    parser.add_argument("--student")
    parser.add_argument("--adapter-dir", help="a LoRA checkpoint (phase 1)")
    parser.add_argument("--full-weights", help="a full fine-tuning export directory (full_weights/)")
    parser.add_argument("--milestone", help="a full fine-tuning milestone export (milestone_<step>/)")
    parser.add_argument("--heads-json")
    parser.add_argument("--heads-pt")
    parser.add_argument("--shuffled", action="store_true", help="also score the shuffled control")
    parser.add_argument("--dry-run", choices=("oracle", "noisy"), default=None,
                        help="CPU machinery check without a checkpoint: the rows' GT answers, or GT plus NoisyHeads noise")
    args = parser.parse_args(argv)
    sources = [name for name in ("adapter_dir", "full_weights", "milestone") if getattr(args, name)]
    if not args.dry_run:
        if not args.student or len(sources) != 1:
            parser.error("--student and exactly one of --adapter-dir, --full-weights, --milestone are required "
                         "unless --dry-run")
        if args.milestone and (args.heads_json or args.heads_pt):
            parser.error("--milestone reads its heads from MILESTONE.json; drop --heads-json and --heads-pt")
        if not args.milestone and not (args.heads_json and args.heads_pt):
            parser.error("--heads-json and --heads-pt are required with --adapter-dir or --full-weights")
    if os.path.exists(args.out):
        raise SystemExit("the gate report already exists: " + args.out)
    rows = load_rows(args.rows)
    heldout = phase1.heldout_scenes(args.heldout)
    training = [tuple(s) for s in json.load(open(args.training_scenes))["scenes"]]
    check_scenes(rows, heldout, training)  # before loading any checkpoint
    if args.dry_run:
        from .heads import NoisyHeads, OracleHeads
        heads = OracleHeads() if args.dry_run == "oracle" else NoisyHeads(OracleHeads())
        checkpoint = {"dry_run": args.dry_run, "note": "machinery check on GT answers; not a gate result"}
    elif args.adapter_dir:
        backend = Phase1CheckpointHeads(args.student, args.adapter_dir, args.heads_json, args.heads_pt)
        heads = backend.heads
        checkpoint = {"student": args.student, "adapter_dir": args.adapter_dir, "heads_json": args.heads_json,
                      "heads_pt": args.heads_pt, "load_report": backend.load_report}
    else:
        milestone = None
        full_weights, heads_json, heads_pt = args.full_weights, args.heads_json, args.heads_pt
        if args.milestone:
            full_weights, heads_json, heads_pt, milestone = milestone_paths(args.milestone)
        backend = FullFTCheckpointHeads(args.student, full_weights, heads_json, heads_pt)
        heads = backend.heads
        checkpoint = {"student": args.student, "full_weights": full_weights, "heads_json": heads_json,
                      "heads_pt": heads_pt, "milestone": milestone, "load_report": backend.load_report}
    if args.shuffled:
        result = evaluate_with_shuffled(rows, heads, heldout, training)
        passed = result["heads"]["passed"]
    else:
        result = evaluate(rows, heads, heldout, training)
        passed = result["passed"]
    result = OrderedDict([("phase1", phase1.provenance()), ("checkpoint", checkpoint),
                          ("rows", os.path.abspath(args.rows)), ("report", result)])
    with open(args.out, "w") as stream:
        json.dump(result, stream, indent=1, default=lambda v: v.tolist() if hasattr(v, "tolist") else str(v))
    print(json.dumps({"gate_passed": passed, "dry_run": args.dry_run}))


if __name__ == "__main__":
    main()
