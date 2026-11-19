"""Training configs and the 8-GPU AWS smoke spec for the full fine-tuning arms, built through the trainer's checks.

Arms (DESIGN_FULLFT_GXS.md; every value cites its source there):
  CPD      Cambrian-P replica + point depth, no G3T: one stage, a head-only warmup as long as the LR warmup, then joint
           full fine-tuning of LLM + merger (1e-5), vision (2e-6) and heads (1e-4) on RG2P2_A's trace rows with
           Cambrian-P's pose-only samples interleaved (beta = 1, ~35k). Cambrian-P routing: question rows train the
           next-token loss only, pose-only rows the heads (depth queries from the bank at their frames).
  PDG_S1   frozen VLM; the G3T connector (Spatial-MLLM mlp_add) and the PD heads train on the stage-1 geometry
           questions, head losses on the label bank (Video-LLaVA stage-1 recipe).
  PDG_S2   Cambrian-P full fine-tuning of LLM + merger + vision + heads + connector (initialized from PDG_S1) on
           RG2P2_A's trace rows, head losses on labelled rows.
  FT_A     the matched control: PDG_S2's rows, steps, groups and learning rates; no connector, no heads, no stage 1.
  GXS_S1 / GXS_S2 / GXS_X_S2   the G3T-only variant (VG-LLM / Spatial-MLLM: vision and merger frozen in stage 2).

Every config starts from the RG2P2 reference config (pinned by SHA-256), drops the r1835 warm start (plain base;
--init merged keeps it and merges it in FP32), carries the frame setting explicitly, and passes
normalize_training_config and camera_config.normalize before it is written. Stage-2 configs take the stage-1 module
pins once stage 1 has published; without them they are templates and the spec lists them as pending.
"""
import argparse
import copy
import hashlib
import json
import math
import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from student_pilot import camera_config, full_ft, geometry_input, pose_samples  # noqa: E402
from student_pilot.ddp_config import SEGMENT_LOSS_REDUCTION, normalize_training_config, run_control_from_config  # noqa: E402
from tools.pd_arm_configs import POINT_DEPTH  # noqa: E402

STUDENT = "qwen35"
BASE_CONFIG_SHA256 = {"X": "46a89b9a512e263f433d2eab3600628b7f834dcb4d2a85aaf68e04ba2a96ebd8",
                      "A": "cdee3d05b48b6dc6e86380d113c46f0d001cd3db597fe2bc20a4ec8a40c15451"}
REFERENCE_ROWS = {"A": "RG2P2_A_W32_S17", "X": "RG2P2_X_W32_S17", "GEO": "GEO_STAGE1_V2_B0",
                  "A_POSE": "RG2P2_A_W32_S17 + POSE32_V1 (34,888 pose-only rows)"}
QA_ROWS = 396_649
POSE_ROWS = 34_888
STAGE1_ROWS = 200_000
# The frame setting every arm carries; 64-frame reduced resolution is {"count": 64, "pixels_per_frame": [16384, 73728]}.
FRAMES = {"count": 32, "pixels_per_frame": [128 * 128, 384 * 384]}
# G3T: GX's encoder (spec 2b65c863 derive/geometry), layer 23 = the last aggregator layer (Spatial-MLLM:
# spatial_embeds_layer_idx -1), 2048 = frame + global attention features (Spatial-MLLM's 2 x vggt_dim).
G3T_ENCODER = {"input": "square_pad_1024_bilinear_518", "name": "g3t", "pooling": "roi_align_valid_region_aligned_sr2_patch_grid",
               "repository": "thatbrguy/g3t", "revision": "c55e91a04f1cbbad67359072536351201fd19e8b",
               "source_sha256": "8223a095c258d8f2a720af8c5821f52ecbed1fe64ae127d4b78b8239354b868d"}
# Cambrian-P (arXiv 2605.22819; CAMBRIANP_RECIPE_REPORT.md section 3): LLM and vision projector 1e-5, vision encoder
# 2e-6, pose projector and head 1e-4, AdamW, weight decay 0, warmup ratio 0.03, cosine, 1 epoch, batch 256.
CAMBRIAN_RATES = {"llm": 1e-5, "merger": 1e-5, "vision_blocks": 2e-6, "heads": 1e-4}
# The G3T connector is a vision projector: Cambrian-P's projector rate in stage 2.
CONNECTOR_STAGE2_RATE = 1e-5
# Video-LLaVA stage 1 (arXiv 2311.10122, which MERV follows): projector only, LR 1e-3, batch 256, 1 epoch,
# warmup 0.03, cosine.
CONNECTOR_STAGE1_RATE = 1e-3
ALL_GROUPS = {"llm": True, "vision_blocks": True, "merger": True}
# VG-LLM (train_sr.sh: tune_mm_vision False, tune_mm_mlp False, tune_mm_llm True); Spatial-MLLM (tune_mm_vision False).
GXS_TRAIN = {"llm": True, "vision_blocks": False, "merger": False}
# Cambrian-P-7B pose head and loss (released config.json): rec_loss_weight 0.2 x rec_camera_loss_weight 5.0 = 1.0,
# w_T 1, w_R 1, w_f 0.5, gamma 0.6, 4 refinements, trunk 4 x (2048, 16 heads), linear projector to 2048, final-layer
# carrier states, use_trajectory_balance false, metric translations.
CAMBRIAN_POSE = {"weight": 1.0, "weight_trans": 1.0, "weight_rot": 1.0, "weight_focal": 0.5, "stage_gamma": 0.6,
                 "refine_iterations": 4, "trunk_depth": 4, "embed_dim": 2048, "num_heads": 16, "feature_layers": None,
                 "trajectory_balance": False,
                 # Gravity and metric-scale branches (USER: "with gravity/metric scale"; not in Cambrian-P): PD weights.
                 "weight_gravity": 0.5, "weight_scale": 0.2, "warmup_ratio": 0.0}
WARMUP_RATIO = 0.03
JOB_NAME = re.compile(r"a15_cot_ap[0-9a-f]{8}")
BANNED = re.compile("sp" "lit|dist" "ill|vsi|revsi|qgen|scan" "net|ark" "it|qw" "en|gemini", re.I)


def steps(rows, batch=256):
    return math.ceil(rows / batch)


def load_base(path, key):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_CONFIG_SHA256[key]:
        raise ValueError(f"Base config {key} differs from its pinned SHA-256")
    return json.loads(raw)


def a_from_x(x_raw):
    """RG2P2_A's config is RG2P2_X's with the segment loss; the bytes reproduce cdee3d05 exactly."""
    raw = x_raw.replace(b'"loss_reduction": "mean_assistant_tokens_per_row_then_global_row_mean"',
                        b'"loss_reduction": "' + SEGMENT_LOSS_REDUCTION.encode() + b'"')
    if hashlib.sha256(raw).hexdigest() != BASE_CONFIG_SHA256["A"]:
        raise ValueError("Reconstructed RG2P2_A config differs from cdee3d05")
    return json.loads(raw)


def geometry_block(store_manifest, store_sha256):
    block = {"schema": geometry_input.SCHEMA, "injection": geometry_input.SPATIAL_INJECTION, "layer": 23,
             "feature_dim": 2048, "frames_per_token": 2, "projector": dict(geometry_input.SPATIAL_MLLM),
             "encoder": dict(G3T_ENCODER), "store": {"manifest": store_manifest, "manifest_sha256": store_sha256}}
    return geometry_input.normalize(block)


def camera_block(bank_path, bank_sha256, head_only_steps, depth=True, cambrian_routing=False):
    block = {**copy.deepcopy(CAMBRIAN_POSE), "head_only_steps": head_only_steps, "gate": None,
             "supervision": {"path": bank_path, "sha256": bank_sha256}}
    if depth:
        block["point_depth"] = copy.deepcopy(POINT_DEPTH)
    if cambrian_routing:
        # Cambrian-P Sec. 3.3: question rows NTP only, pose-only rows pose only (+ depth on those rows: PD's addition).
        block["row_routing"] = camera_config.CAMBRIAN_P_ROUTING
    camera_config.normalize(block)
    return block


def full_config(base, block, geometry=None, camera=None, init="base", epochs=1):
    config = {key: value for key, value in copy.deepcopy(base).items() if key not in ("camera", "geometry")}
    if init == "base":
        config.pop("init_adapter", None)
    elif "init_adapter" not in config:
        raise ValueError("A merged warm start needs the reference config's init_adapter")
    block = {**block, "init": {"kind": "base" if init == "base" else "base_merged_init_adapter"}}
    rates = full_ft.normalize(block)["learning_rates"]
    # The LoRA learning rate is inert under full_ft; it is set to the first group's rate so logs read naturally.
    config.update(full_ft=block, epochs=epochs, frames=copy.deepcopy(FRAMES), warmup_ratio=WARMUP_RATIO, weight_decay=0.0,
                  effective_batch_size=256, learning_rate=rates.get("llm", rates["geometry"]))
    if geometry is not None:
        config["geometry"] = geometry
    if camera is not None:
        config["camera"] = camera
    return validated(config)


def validated(config):
    settings = normalize_training_config(config, STUDENT)
    run_control_from_config(config)
    camera_config.from_training_config(config)
    if "full_ft" not in settings or settings.get("parallel") != "fsdp":
        raise ValueError("Full fine-tuning arm configs must normalize with full_ft under FSDP")
    return config


def pin(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}


PENDING = {"path": "PENDING_STAGE1_PUBLICATION", "sha256": "0" * 64}
ARM_ROWS = {"CPD": "A_POSE", "PDG_S1": "GEO", "PDG_S2": "A", "FT_A": "A", "GXS_S1": "GEO", "GXS_S2": "A", "GXS_X_S2": "X"}
ARM_STEPS = {"CPD": steps(QA_ROWS + POSE_ROWS), "PDG_S1": steps(STAGE1_ROWS), "PDG_S2": steps(QA_ROWS),
             "FT_A": steps(QA_ROWS), "GXS_S1": steps(STAGE1_ROWS), "GXS_S2": steps(QA_ROWS), "GXS_X_S2": steps(QA_ROWS)}


def arm_configs(base_a, base_x, bank, stores, stage1=None, init="base"):
    """stores = {'stage1': (manifest, sha256), 'stage2': (manifest, sha256)}; stage1 = {'pdg': {...}, 'gxs': {...}} pins."""
    g1, g2 = geometry_block(*stores["stage1"]), geometry_block(*stores["stage2"])
    stage1 = stage1 or {}
    pending = [arm for arm, key in (("PDG_S2", "pdg"), ("GXS_S2", "gxs"), ("GXS_X_S2", "gxs")) if not stage1.get(key)]
    pdg_modules = stage1.get("pdg") or {"geometry": dict(PENDING), "heads": dict(PENDING)}
    gxs_modules = stage1.get("gxs") or {"geometry": dict(PENDING)}
    cpd_warmup = math.ceil(WARMUP_RATIO * ARM_STEPS["CPD"])
    configs = {
        "CPD": full_config(base_a, {"train": ALL_GROUPS, "learning_rates": CAMBRIAN_RATES}, None,
                           camera_block(*bank, cpd_warmup, cambrian_routing=True), init=init),
        "PDG_S1": full_config(base_x, {"train": {"llm": False}, "learning_rates": {"geometry": CONNECTOR_STAGE1_RATE,
                                                                                   "heads": CAMBRIAN_RATES["heads"]}},
                              g1, camera_block(*bank, 0)),
        "PDG_S2": full_config(base_a, {"train": ALL_GROUPS, "learning_rates": {**CAMBRIAN_RATES, "geometry": CONNECTOR_STAGE2_RATE},
                                       "init_modules": pdg_modules}, g2, camera_block(*bank, 0), init=init),
        "FT_A": full_config(base_a, {"train": ALL_GROUPS, "learning_rates": {k: CAMBRIAN_RATES[k] for k in ALL_GROUPS}},
                            init=init),
        "GXS_S1": full_config(base_x, {"train": {"llm": False}, "learning_rates": {"geometry": CONNECTOR_STAGE1_RATE}}, g1),
        "GXS_S2": full_config(base_a, {"train": GXS_TRAIN, "learning_rates": {"llm": CAMBRIAN_RATES["llm"],
                                                                               "geometry": CONNECTOR_STAGE2_RATE},
                                       "init_modules": gxs_modules}, g2, init=init),
        "GXS_X_S2": full_config(base_x, {"train": GXS_TRAIN, "learning_rates": {"llm": CAMBRIAN_RATES["llm"],
                                                                                 "geometry": CONNECTOR_STAGE2_RATE},
                                         "init_modules": gxs_modules}, g2, init=init),
    }
    return configs, pending


SMOKES = ("CPD", "PDG_S1", "PDG_S2", "FT_A")


def smoke_configs(configs, world_size=8, steps=30, every=20):
    """30 steps on one 8-GPU node at global batch 64 (8 rows per GPU: the 32-GPU arms' per-rank load)."""
    result = {}
    for arm in SMOKES:
        config = copy.deepcopy(configs[arm])
        config.update(world_size=world_size, effective_batch_size=64, max_steps=steps, checkpoint_every_steps=every)
        if "camera" in config:
            config["camera"] = {**config["camera"], "head_only_steps": min(config["camera"]["head_only_steps"], 10)}
        if arm == "PDG_S2":
            # The smoke starts its connector and heads fresh unless SMOKE_PDG_S1 has published.
            config["full_ft"] = {key: value for key, value in config["full_ft"].items() if key != "init_modules"}
        result["SMOKE_" + arm] = validated(config)
    return result


def canonical(value):
    return (json.dumps(value, indent=1, sort_keys=True) + "\n").encode()


def job_name():
    return "a15_cot_ap" + secrets.token_hex(4)


def spec(configs, smokes, pending, trainer_commit, bank_sha256):
    everything = {**configs, **smokes}
    names = {arm: job_name() for arm in everything}
    if len(set(names.values())) != len(names) or not all(JOB_NAME.fullmatch(n) for n in names.values()):
        raise ValueError("Job names must be distinct opaque a15_cot_ap tokens")
    files = {arm: {"file": f"c_{hashlib.sha256(canonical(cfg)).hexdigest()[:12]}.json",
                   "sha256": hashlib.sha256(canonical(cfg)).hexdigest()} for arm, cfg in everything.items()}
    if any(BANNED.search(item["file"]) for item in files.values()):
        raise ValueError("An AWS-side file name identifies the project")
    return {
        "schema": "fullft_arm_spec_v1", "trainer_commit": trainer_commit, "student": STUDENT,
        "bank_sha256": bank_sha256, "base_configs": {REFERENCE_ROWS[k]: {"sha256": v} for k, v in BASE_CONFIG_SHA256.items()},
        "job_names": names, "configs": files, "pending_stage1_pins": pending,
        "arms": {arm: {"rows": REFERENCE_ROWS[ARM_ROWS[arm]], "world_size": 32, "gpus": 32,
                       "effective_batch_size": cfg["effective_batch_size"], "epochs": cfg["epochs"], "steps": ARM_STEPS[arm]}
                 for arm, cfg in configs.items()},
        "smoke": SMOKE_SPEC,
        "launch": LAUNCH,
        "eval": EVAL,
        "checkpoints": CHECKPOINTS,
        "extraction": EXTRACTION,
        "prerequisites": PREREQUISITES,
        "ledger": "record every job name with its run in lanes/aws_reserve/AWS_JOB_LEDGER.jsonl on Trinity",
    }


# Slurm launch settings of every arm and smoke job (graceful stop: DESIGN_FULLFT_GXS.md section 2).
LAUNCH = {
    "slurm_signal": "--signal=B:USR1@900",
    "stop": "the batch shell traps USR1 and creates $R1_STOP_FILE (or forwards USR1 to every rank); every rank polls the "
            "file each optimizer step and any rank's request stops all of them, so the step in flight, a pinned signal "
            "checkpoint (~113-120 GB written in parallel by 32 ranks, one shard each) and the stop marker finish inside "
            "the 900 s lead. A stale .step_N_*.tmp of a killed save is removed by the next save.",
    "env": {"R1_ROLLING_MINUTES": "60"},
    "time_limit_note": "--time must exceed the planned steps x s/step plus the 900 s lead; a requeued job resumes from "
                       "the pinned signal checkpoint (RESUME_FROM)",
}
# Evaluation options per arm (scripts/orchard/eval_job.py environment; orchard_eval --carriers / --geometry-store-*).
EVAL = {
    "CPD": {"EVAL_CARRIERS": "none", "why": "Cambrian-P: question rows train and answer without camera tokens"},
    "PDG_S2": {"EVAL_CARRIERS": "insert", "EVAL_GEOMETRY_STORE": "EVAL_STORE/manifest.jsonl",
               "EVAL_GEOMETRY_STORE_SHA256": "pin of the sealed eval store",
               "why": "PDG's question rows in bank scenes train with carriers; the G3T connector reads the eval store"},
    "FT_A": {},
    "GXS_S2": {"EVAL_GEOMETRY_STORE": "EVAL_STORE/manifest.jsonl", "EVAL_GEOMETRY_STORE_SHA256": "pin of the sealed eval store"},
    "GXS_X_S2": {"EVAL_GEOMETRY_STORE": "EVAL_STORE/manifest.jsonl", "EVAL_GEOMETRY_STORE_SHA256": "pin of the sealed eval store"},
    "aws_closure": "the eval closure (6805067c eval_ops_aws.py) must append the same --carriers / --geometry-store-* "
                   "arguments to cpu-check and generate for these arms; this tree's orchard_eval accepts its "
                   "--allow-unpaired-adapter",
}
# Durable bytes at world 32 (FP32 masters + two AdamW moments = 12 B per trained parameter; replicated modules once).
CHECKPOINTS = {
    "full_state_gb": {"FT_A": 112.9, "CPD": 115.7, "PDG_S2": 119.7},
    "milestone_export_gb": {"FT_A": 18.8, "CPD": 19.8, "PDG_S2": 21.1},
    "retention": "rolling pool keeps 2 full states (rolling, epoch, milestone and final saves); signal and gate stops "
                 "pin theirs; every milestone (checkpoint_every_steps 200) pins a milestone export (BF16 full_weights + "
                 "FP32 connector and heads)",
    "per_arm_tb": {"FT_A": 0.36, "CPD": 0.39, "PDG_S2": 0.39},
    "parts": {"trained_base_parameters": 9405388912, "heads_parameters": 235468567, "connector_parameters": 335581184},
}
# The G3T patch-grid stores (tools/g3t_patch_grid_store.py; one row = float16 [32, 2h, 2w, 2048], 68.2 MB at the
# 320 x 416 grid). Timing: the merged-grid stores took 1,630 selections in 4 x 1 GPU x 9.7 min (1.4 GPU-s per
# selection, jobs 8414768-71); pooling onto the 4x larger grid adds no measurable GPU time, only 4x the bytes written.
EXTRACTION = {
    "tool": "tools/g3t_patch_grid_store.py lists | extract | seal (from the trainer epoch checkout; G3T source "
            "thatbrguy/g3t c55e91a0, source sha256 8223a095)",
    "lists": "one CPU job (<10 min): --training for RG2P2_A_W32_S17, RG2P2_X_W32_S17 and GEO_STAGE1_V2_B0 (train + dev) "
             "frozen training.json; --eval-cell for the VSI-500 (vsibench_answerable500) and VSTI-450 "
             "(vstibench_repr450_v2, and v3's cells when that cohort is scored) cells' preflights; it refuses any "
             "selection in both lists",
    "training_store": {"selections": "~1,600 (lists reports the exact count)", "size_gb": 110,
                       "gpus": "4 x 1 GPU array (shards 0-3), --time 1:00:00 each, ~12 min wall",
                       "after": "seal; pin manifest sha256 as the stage1 and stage2 store of PDG/GXS; stage the sealed "
                                "store on every training node's local disk (each rank reads ~0.55 GB per step)"},
    "eval_store": {"selections": "~444 (the merged eval store fs/68918577 covered 444 for the same cells)", "size_gb": 30,
                   "gpus": "1 x 1 GPU, --time 1:00:00, ~15 min wall", "after": "seal; pin as EVAL_GEOMETRY_STORE[_SHA256]"},
    "total": {"gpu_hours": 1.0, "output_gb": 140},
}

SMOKE_SPEC = {
    "node": "one exclusive 8-GPU node (8 x H100 80 GB), world 8, global batch 64 = 8 rows per GPU (the arms' 32-GPU "
            "per-rank load), 30 steps, milestone at step 20 (milestone export + full state to the pool), "
            "R1_ROLLING_MINUTES=10, --signal=B:USR1@900, no gates",
    "jobs": {"SMOKE_FT_A": "full FT, no G3T, no heads (memory/step-time floor)",
             "SMOKE_CPD": "full FT + Cambrian-P pose head + point depth, pose-only rows mixed in",
             "SMOKE_PDG_S1": "frozen VLM + G3T connector + heads on stage-1 geometry rows",
             "SMOKE_PDG_S2": "full FT + G3T connector + heads (G3T cost = SMOKE_PDG_S2 - SMOKE_CPD)"},
    "rows": {"SMOKE_FT_A": "RG2P2_A rows in the 20 smoke-bank scenes (pre-staged on CPU first)",
             "SMOKE_CPD": "the same rows + the pose-only rows of those 20 scenes (28 each = 560), shuffled together",
             "SMOKE_PDG_S1": "stage-1 v2 block-0 rows of the 20 smoke-bank scenes",
             "SMOKE_PDG_S2": "SMOKE_FT_A's rows"},
    "order": "SMOKE_FT_A, SMOKE_CPD, SMOKE_PDG_S1, SMOKE_PDG_S2 in one job; ~2 h, --time 2:30, ~20 GPU-h",
    "measure": ["memory probe's chosen microbatch (must be 8: multi-node runs refuse accumulation)",
                "peak allocated and reserved memory per rank (memory_probe.json, metrics peak_memory_per_rank)",
                "s/step over steps 11-30 and rows/s (throughput.json)",
                "checkpoint step_20: full-state bytes (ROLLING.jsonl / du), replicated.pt written once by rank 0, "
                "write seconds (checkpoint_metrics.jsonl), one shard per rank, FP32 tensors; milestone_20 export bytes "
                "and seconds (MILESTONES.jsonl)",
                "BF16 full_weights export at the end: bytes, tensor count and seconds (adapter-<label>/full_weights)",
                "clip_norms_before_clip and learning_rates per group every step; camera_label_audit pose/depth rows",
                "lm_row_scale > 1 on CPD steps with pose rows"],
    "pass": ["first GPU work within 5 min of start", "no OOM at microbatch 8", "finite losses and clip norms every step",
             "every trained group has nonzero gradient flow at step 1 (gradient_flow.json)",
             "a stop-file stop after step 25 pins step 25 within the signal lead, and a resume from it reproduces "
             "steps 26-30's losses; the step-20 milestone export loads exactly (full_ft.load_export)",
             "PDG_S1: base bytes unchanged (frozen fingerprints) and connector/heads update"],
}
PREREQUISITES = [
    "G3T training store on the unmerged Qwen patch grid (encoder pooling roi_align_valid_region_aligned_sr2_patch_grid, "
    "layer 23, 2048-d, float16 [32, 2h, 2w, 2048]) for every RG2P2_A/X video and every stage-1 v2 materialized video; "
    "seal it and replace the store pins (EXTRACTION.training_store).",
    "G3T eval store, same encoder and pooling, for the VSI-500 and VSTI-450 eval selections (EXTRACTION.eval_store); "
    "PDG_S2 and the GXS arms are scored with it (EVAL).",
    "CPD's manifest keeps RG2P2_A's rows in FT_A's order (the pose rows may sit anywhere): the trainer then gives CPD's "
    "question rows FT_A's exact order; check batch_plan.json question_order_sha256 is equal in both runs.",
    "Ship label_bank_1247_v2.npz (sha 51f01313...) under an opaque name and set the camera supervision path.",
    "CPD rows: admit RG2P2_A + POSE32_V1 (34,888 rows, /scratch/jjyeung/fullft/pose_rows_v1 on trinity-0-13) together; "
    "pose-only frames are rung-1 frames already staged for RG2P2.",
    "Stage-1 rows: admit stage-1 v2 block 0 (200,000 rows, /scratch/jjyeung/fullft/geo_stage1_v2 on trinity-0-13).",
    "Stage 2 waits for its stage-1 publication pins (PDG_S1 geometry + heads; GXS_S1 geometry).",
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-x", required=True)
    parser.add_argument("--bank-path", required=True)
    parser.add_argument("--bank-sha256", required=True)
    parser.add_argument("--stage1-store-manifest", required=True)
    parser.add_argument("--stage1-store-sha256", required=True)
    parser.add_argument("--stage2-store-manifest", required=True)
    parser.add_argument("--stage2-store-sha256", required=True)
    parser.add_argument("--stage1-geometry", help="PDG_S1 geometry/geometry_projector.safetensors")
    parser.add_argument("--stage1-heads", help="PDG_S1 auxiliary_heads.pt")
    parser.add_argument("--gxs-stage1-geometry", help="GXS_S1 geometry/geometry_projector.safetensors")
    parser.add_argument("--init", choices=("base", "merged"), default="base")
    parser.add_argument("--trainer-commit", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    x_raw = Path(args.base_x).read_bytes()
    base_x = load_base(args.base_x, "X")
    base_a = a_from_x(x_raw)
    stage1 = {}
    if args.stage1_geometry and args.stage1_heads:
        stage1["pdg"] = {"geometry": pin(args.stage1_geometry), "heads": pin(args.stage1_heads)}
    if args.gxs_stage1_geometry:
        stage1["gxs"] = {"geometry": pin(args.gxs_stage1_geometry)}
    stores = {"stage1": (args.stage1_store_manifest, args.stage1_store_sha256),
              "stage2": (args.stage2_store_manifest, args.stage2_store_sha256)}
    configs, pending = arm_configs(base_a, base_x, (args.bank_path, args.bank_sha256), stores, stage1, args.init)
    smokes = smoke_configs(configs)
    result = spec(configs, smokes, pending, args.trainer_commit, args.bank_sha256)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=False)
    for arm, cfg in {**configs, **smokes}.items():
        with (out / result["configs"][arm]["file"]).open("xb") as handle:
            handle.write(canonical(cfg))
    with (out / "SPEC.json").open("x") as handle:
        handle.write(json.dumps(result, indent=1) + "\n")
    print(json.dumps({"spec": str(out / "SPEC.json"), "pending": pending}))


if __name__ == "__main__":
    main()
