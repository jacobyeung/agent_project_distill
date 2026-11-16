"""Training configs and the spec for the head-call arms HC, HX and HA and their 8-GPU smokes (DESIGN_HEADCALL_FULLFT.md).

  HC   head-call traces: RG2P2_X's 396,649 questions, HC's targets (head-call traces on 85,214 rows, plain G traces on
       50,989, answer-only elsewhere), tool responses masked, scheduled sampling 0 -> 0.5 over steps 0-1,000.
  HX   the matched control: the same rows with RG2P2_X's answer-only targets; the same carriers and queried depth points
       on the twins of HC's head-call rows; no sampling.
  HA   optional: the same setup on RG2P2_A's free-text GT traces.
Every arm: full fine-tuning at Cambrian-P's rates (LLM and merger 1e-5, vision 2e-6, heads 1e-4), CPD's final full weights
and camera + point-depth heads as init (full_ft init full_export + init_modules.heads), the PD row routing (every
labelled row trains the heads, with carriers), RG2P2_A's segment loss (bitwise the default on answer-only rows), seed
17 or 18, 1,550 steps at batch 256 on 32 GPUs. Configs start from the pinned RG2P2 reference config through
tools/fullft_arm_configs (its checks included) and pass normalize_training_config before they are written.
"""
import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from headcall import rows as R  # noqa: E402
from tools import fullft_arm_configs as F  # noqa: E402

PENDING = "0" * 64
SEEDS = (17, 18)
ARMS = ("HC", "HX", "HA")
ARM_ROWS = {"HC": "RG2P2_X_W32_S17 questions with HC_REPLACE targets (tools/headcall_rows.py index)",
            "HX": "RG2P2_X_W32_S17", "HA": "RG2P2_A_W32_S17"}
QA_ROWS = F.QA_ROWS
STEPS = F.steps(QA_ROWS)
SAMPLING = {"start_p": 0.0, "end_p": 0.5, "start_step": 0, "end_step": 1000}
# The 8-GPU smoke samples from step 0 and reaches p = 0.5 at step 20, so steps 1-30 measure the sampling forwards.
SMOKE_SAMPLING = {"start_p": 0.0, "end_p": 0.5, "start_step": 0, "end_step": 20}
SIDECAR_ROOT = "/project/community/jjyeung/distill/hc"


def opaque_pin(local, sha256):
    """The sidecar's code-aws path: an opaque name (its SHA-256 prefix) under the shared data root."""
    name = f"{sha256[:12]}.jsonl.gz"
    if F.BANNED.search(name):
        raise ValueError("An AWS-side file name identifies the project")
    return {"path": f"{SIDECAR_ROOT}/{name}", "sha256": sha256, "local": str(local)}


def arm_config(base_a, bank, arm, seed, sidecar, init, heads, sampling=SAMPLING):
    camera = F.camera_block(*bank, head_only_steps=0)  # CPD's heads start trained: no isolation, no ramp
    config = F.full_config(base_a, {"train": F.ALL_GROUPS, "learning_rates": F.CAMBRIAN_RATES}, camera=camera)
    config["full_ft"] = {**config["full_ft"], "init": {"kind": "full_export", **init}, "init_modules": {"heads": heads}}
    config["seed"] = seed
    config["headcall"] = {"arm": arm, "sidecar": {"path": sidecar["path"], "sha256": sidecar["sha256"]},
                          "scheduled_sampling": {**sampling, "seed": seed} if arm == "HC" else None}
    R.check_camera(F.camera_config.normalize(config["camera"]))
    return F.validated(config)


def smoke(config, sidecar, init, heads):
    config = copy.deepcopy(config)
    config.update(world_size=8, effective_batch_size=64, max_steps=30, checkpoint_every_steps=20)
    config["full_ft"] = {**config["full_ft"], "init": {"kind": "full_export", **init}, "init_modules": {"heads": heads}}
    config["headcall"] = {**config["headcall"], "sidecar": {"path": sidecar["path"], "sha256": sidecar["sha256"]}}
    if config["headcall"]["arm"] == "HC":
        config["headcall"]["scheduled_sampling"] = {**SMOKE_SAMPLING, "seed": config["seed"]}
    return F.validated(config)


def pins_of(path):
    data = json.loads(Path(path).read_text())
    return data["outputs"]


def build_spec(args):
    x_raw = Path(args.base_x).read_bytes()
    F.load_base(args.base_x, "X")
    base_a = F.a_from_x(x_raw)
    bank = (args.bank_path, args.bank_sha256)
    full = pins_of(Path(args.rows) / "BUILD.json")
    smoke_rows = json.loads((Path(args.smoke_rows) / "SUBSET.json").read_text())
    sidecars = {arm: opaque_pin(full[f"{arm}_SIDECAR"]["path"], full[f"{arm}_SIDECAR"]["sha256"]) for arm in ARMS}
    smoke_sidecars = {arm: opaque_pin(smoke_rows["outputs"][arm]["path"], smoke_rows["outputs"][arm]["sha256"])
                      for arm in ARMS}
    cpd_init = {"path": args.cpd_full_weights or "PENDING_CPD_FINAL/full_weights/full_weights.json",
                "sha256": args.cpd_full_weights_sha256 or PENDING}
    cpd_heads = {"path": args.cpd_heads or "PENDING_CPD_FINAL/auxiliary_heads.pt", "sha256": args.cpd_heads_sha256 or PENDING}
    smoke_init = {"path": "PENDING_SMOKE_CPD_MILESTONE_20/full_weights/full_weights.json", "sha256": PENDING}
    smoke_heads = {"path": "PENDING_SMOKE_CPD_MILESTONE_20/auxiliary_heads.pt", "sha256": PENDING}
    configs = {f"{arm}_S{seed}": arm_config(base_a, bank, arm, seed, sidecars[arm], cpd_init, cpd_heads)
               for arm in ARMS for seed in SEEDS}
    smokes = {f"SMOKE_{arm}": smoke(configs[f"{arm}_S17"], smoke_sidecars[arm], smoke_init, smoke_heads) for arm in ARMS}
    everything = {**configs, **smokes}
    names = {arm: F.job_name() for arm in everything}
    if len(set(names.values())) != len(names) or not all(F.JOB_NAME.fullmatch(name) for name in names.values()):
        raise ValueError("Job names must be distinct opaque a15_cot_ap tokens")
    files = {arm: {"file": f"c_{hashlib.sha256(F.canonical(cfg)).hexdigest()[:12]}.json",
                   "sha256": hashlib.sha256(F.canonical(cfg)).hexdigest()} for arm, cfg in everything.items()}
    pending = [] if args.cpd_full_weights_sha256 and args.cpd_heads_sha256 else [
        "CPD final: full_ft.init (full_weights/full_weights.json) and init_modules.heads (auxiliary_heads.pt) of every arm"]
    pending.append("SMOKE_CPD milestone_20 (run r1smkcpd8_4e6b2bcf): full_weights.json and auxiliary_heads.pt of every smoke")
    spec = {
        "schema": "headcall_arm_spec_v1", "trainer_commit": args.trainer_commit, "student": F.STUDENT,
        "bank_sha256": args.bank_sha256,
        "base_configs": {"RG2P2_X_W32_S17": {"sha256": F.BASE_CONFIG_SHA256["X"]},
                         "RG2P2_A_W32_S17 (rebuilt from X, the base of every arm)": {"sha256": F.BASE_CONFIG_SHA256["A"]}},
        "rows": {"build": {"path": str(Path(args.rows) / "BUILD.json"), "sha256": hashlib.sha256(
                     (Path(args.rows) / "BUILD.json").read_bytes()).hexdigest()},
                 "table": json.loads((Path(args.rows) / "TABLE.json").read_text())["totals"],
                 "sidecars": sidecars, "hc_replace": full["HC_REPLACE"],
                 "smoke_subset": {"scenes": len(smoke_rows["scenes"]), "counts": smoke_rows["counts"],
                                  "sidecars": smoke_sidecars, "hc_replace": smoke_rows["outputs"]["HC_REPLACE"]}},
        "job_names": names, "configs": files, "pending_pins": pending,
        "arms": {arm: {"rows": ARM_ROWS[arm.split("_")[0]], "seed": cfg["seed"], "world_size": 32, "gpus": 32,
                       "effective_batch_size": 256, "epochs": 1, "steps": STEPS,
                       "scheduled_sampling": cfg["headcall"]["scheduled_sampling"]}
                 for arm, cfg in configs.items()},
        "pairs": {"primary": "HC_S - HX_S on VSI-500 thinking on, positive at seeds 17 and 18; paired bootstrap pooled "
                             "over seeds", "secondary": ["HC - HA (head calls vs free-text GT traces)",
                                                         "HX - FT_A and HX - CPD (unmatched references)"],
                  "order": "the three arms admit the same 396,649 qids; admission sorts by qid and the seed shuffles, so "
                           "batch_plan question_order_sha256 is equal in HC, HX, HA and FT_A at the same seed"},
        "smoke": SMOKE, "launch": F.LAUNCH, "eval": EVAL, "gate": GATE, "estimates": ESTIMATES,
        "prerequisites": PREREQUISITES,
        "ledger": "record every job name with its run in lanes/aws_reserve/AWS_JOB_LEDGER.jsonl on Trinity",
    }
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=False)
    for arm, cfg in everything.items():
        with (out / files[arm]["file"]).open("xb") as handle:
            handle.write(F.canonical(cfg))
    with (out / "SPEC.json").open("x") as handle:
        handle.write(json.dumps(spec, indent=1) + "\n")
    print(json.dumps({"spec": str(out / "SPEC.json"), "configs": {arm: item["file"] for arm, item in files.items()},
                      "pending": pending}))


SMOKE = {
    "node": "one exclusive 8-GPU node (8 x H100 80 GB), world 8, global batch 64 = 8 rows per GPU (the arms' per-rank "
            "load), 30 steps, milestone at step 20, R1_ROLLING_MINUTES=10, --signal=B:USR1@900",
    "jobs": {"SMOKE_HC": "HC: sidecar join, masking, forced carriers, queried depth, scheduled sampling 0 -> 0.5 over "
                         "steps 0-20 (FSDP-matched session forwards)",
             "SMOKE_HX": "HX: the same rows' answer-only targets, same carriers and depth points, no sampling",
             "SMOKE_HA": "HA: RG2P2_A's traces, same carriers and depth points, no sampling"},
    "rows": "each arm's rows in the 20 smoke-bank scenes (label bank smoke20 v2 87bf2a90; tools/headcall_rows.py subset): "
            "the smoke sidecars hold 1,407 head-call rows each, HC_REPLACE 2,193 targets",
    "init": "SMOKE_CPD's milestone_20 export (run r1smkcpd8_4e6b2bcf; full_ft.read_milestone gives both pins): this tests "
            "the full_export warm start on CPD's real export layout",
    "order": "SMOKE_HX, SMOKE_HC, SMOKE_HA in one allocation; ~2 h, --time 2:30, ~20 GPU-h",
    "measure": ["headcall_rows.json join audit (headcall_rows, depth_queries, head_calls)",
                "metrics headcall: session_forwards, discarded_forwards, rows_swapped, responses_swapped, "
                "swaps_rejected_length and the cumulative swap counts per step",
                "s/step over steps 11-30 (HC - HX = the sampling cost) and peak memory per rank",
                "init_export in adapters.json and the full_ft record (manifest sha256, tensors)",
                "gradient_flow.json (llm, vision_blocks, merger, heads) and clip norms per family"],
    "pass": ["the join refuses nothing and counts the smoke sidecar's rows", "no OOM at 8 rows per GPU, finite losses",
             "HC swaps rows after step 0 and every rank's session-forward count matches (no hang)",
             "step-1 losses of HX equal those of a run without the headcall block on the same init, except on the "
             "sidecar rows (carriers and depth targets)", "the step-20 milestone export loads exactly",
             "a stop after step 25 resumes bit-exactly (the sampler's choice is a pure function of seed, qid, step)"],
}
EVAL = {
    "all_arms": {"EVAL_CARRIERS": "insert", "EVAL_HEADCALL": "decode",
                 "why": "HC answers its calls from its heads; HX and HA use the same decoder so the three differ only in "
                        "the trained weights (they emit few or no calls; the summary counts them)"},
    "cells": ["vsibench_answerable500 thinking on (primary) and off", "VSTI-450 v3 (vstibench_repr_450_v3.json d7c16986) "
              "thinking on and off"],
    "decoding": "greedy, max_new_tokens 4,096 including inserted responses, max_calls 80, call tokens 128, lenient calls "
                "executed and counted apart",
    "parse": "strict student-answer-v1 primary; tools/headcall_eval_summary.py reports the lenient rescore apart, plus "
             "calls per item, valid, strict, lenient, refused, value-used rate per type",
    "aws_closure": "the eval closure must append --carriers insert --headcall decode to cpu-check and generate",
}
GATE = {
    "tool": "python -m headcall.gate_eval --rows <heldout_gate2> --training-scenes TRAINING_SCENES.json --shuffled",
    "rows": "phase 2's 1,368 GT probe rows on the 38 held-out scenes (out_fix/heldout_gate2; sha-checked held-out bank)",
    "runs": ["init: CPD final (--milestone or --full-weights + its heads) before any arm launches (go/no-go)",
             "HC_S17 and HC_S18 final heads; HX and HA final heads for the same table"],
    "thresholds": "median rotation <= 5.2 deg, position <= 0.25 m, heading <= 10 deg; AbsRel <= 0.10, delta<1.25 >= "
                  "0.90, median depth error <= 0.20 m; pairwise and row decisions >= 0.85; 0 refusals",
    "where": "one GPU with the probe frames (receipt paths on /data2) and the checkpoint: a Trinity GPU after pulling "
             "the ~20 GB export, or code-aws after staging the 38 scenes' frames",
}
ESTIMATES = {
    "HX_s_per_step": "~22-25 (FT_A ~21.5 plus carriers and head losses on bank rows; the smoke measures it)",
    "HC_s_per_step": "HX plus the sampling forwards: one batch-1 no-grad prompt forward per sampled row, matched to the "
                     "busiest rank; unmeasured, the smoke measures it (choices sheet: 12-15 h per HC run)",
    "gpu_hours": "2 seeds x (HC + HX) ~1,400-1,600 GPU-h; HA adds ~600-700 per seed",
    "checkpoints": "full state ~115.7 GB (CPD's), milestone export ~19.8 GB, ~0.39 TB per arm on the durable root",
}
PREREQUISITES = [
    "CPD final export: pin its full_weights/full_weights.json and auxiliary_heads.pt into every arm (rerun this tool "
    "with --cpd-full-weights/--cpd-heads); run the gate on it first.",
    "SMOKE_CPD milestone_20 pins into the smokes (full_ft.read_milestone on milestone_20).",
    "Ship the six sidecars (HC/HX/HA full and smoke20) under their opaque names to SIDECAR_ROOT and the label bank "
    "(already shipped for CPD).",
    "HC's frozen rows: on code-aws, tools/headcall_rows.py index --x-index RG2P2_X_W32_S17/candidate_index.jsonl "
    "--replace HC_REPLACE.jsonl.gz --out <frozen HC dir>; then prepare and admit HC like RG2P2_X (same inherited division "
    "7d100257); HX and HA prepare from RG2P2_X's and RG2P2_A's frozen rows with their own configs.",
    "Cross-family review of the headcall-fullft branch, then the 8-GPU smoke; no arm launches before both.",
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-x", required=True)
    parser.add_argument("--bank-path", required=True)
    parser.add_argument("--bank-sha256", required=True)
    parser.add_argument("--rows", required=True, help="tools/headcall_rows.py build output")
    parser.add_argument("--smoke-rows", required=True, help="tools/headcall_rows.py subset output (smoke scenes)")
    parser.add_argument("--cpd-full-weights")
    parser.add_argument("--cpd-full-weights-sha256")
    parser.add_argument("--cpd-heads")
    parser.add_argument("--cpd-heads-sha256")
    parser.add_argument("--trainer-commit", required=True)
    parser.add_argument("--output-dir", required=True)
    build_spec(parser.parse_args(argv))


if __name__ == "__main__":
    main()
