"""E03-A: Registered J1-T Box-Tolerance Diagnostic (Prompts Builder + Frozen SAM 3 Box Runner).

Implements the exact registered J1-T specification from
/scratch/jjyeung/orch_n30/lever10/work/PRICING_C2_C3.md (lines 19-61) WITHOUT
modifying /scratch/jjyeung/orch_n30/lever8/j1 (kept 100% read-only):

Arms:
  - k'          : exact GT tight box (parity gate: IoU >= 0.95 on >= 95% of J1 k anchors)
  - kB(0.9)     : GT tight box degraded to IoU 0.90 (seed 20261122)
  - kB(0.7)     : GT tight box degraded to IoU 0.70 (seed 20261122)
  - kB(0.7)/s2  : GT tight box degraded to IoU 0.70 (seed 20261123, spread check)
  - kB(0.5)     : GT tight box degraded to IoU 0.50 (seed 20261122)
  - kP-miss     : GT tight box ONLY on anchors with GT area >= 1% of frame (768 px on 240x320)
  - kP-fp       : GT tight box on GT anchors + h1's pick box (from J1 out/detect) on GT-empty anchors

Usage:
  # 1) Build registered PROMPTS_J1T.json on CPU (~2s, 0 GPU):
  CUDA_VISIBLE_DEVICES= /scratch/jjyeung/envs/p1cpu/bin/python -B run_e03_j1t_smoke.py --build-prompts
  # 2) Run 1-capture GPU smoke & k' parity check (~20s on GPU 4 under vnice.sh):
  CUDA_VISIBLE_DEVICES=4 /data3/shared/scripts/vnice/vnice.sh \
    /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B run_e03_j1t_smoke.py \
    --run-gpu --captures scannet/scene0642_01
  # 3) Run full 46-capture J1-T (~8-10 min on 1x 49GB Ada):
  CUDA_VISIBLE_DEVICES=0 /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B run_e03_j1t_smoke.py \
    --run-gpu --captures all
"""
from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
J1_ROOT = Path("/scratch/jjyeung/orch_n30/lever8/j1")
J1_KIT = J1_ROOT / "kit"
if str(J1_KIT) not in sys.path:
    sys.path.insert(0, str(J1_KIT))

SEED_PRIMARY = 20261122
SEED_SECOND = 20261123
GRID_PIXELS = 240 * 320  # 76,800


# ---------------------------------------------------------------------------
# Registered J1-T Box-Degradation Sampler (PRICING_C2_C3.md L35-37)
# ---------------------------------------------------------------------------

def box_iou_cxcywh(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    """Exact 2D box IoU for normalized [cx, cy, w, h] boxes."""
    ax0, ay0, ax1, ay1 = a[0] - 0.5 * a[2], a[1] - 0.5 * a[3], a[0] + 0.5 * a[2], a[1] + 0.5 * a[3]
    bx0, by0, bx1, by1 = b[0] - 0.5 * b[2], b[1] - 0.5 * b[3], b[0] + 0.5 * b[2], b[1] + 0.5 * b[3]
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - inter
    return float(inter / union) if union > 0.0 else 0.0


def _move_and_clip_box(box: list[float], theta: float, s: float, r: float, m: float) -> list[float]:
    """Apply registered move (cx + 0.5 m w cos theta, cy + 0.5 m h sin theta,
    w exp(s m + r m), h exp(s m - r m)) and clip edges to [0, 1].
    """
    cx, cy, w, h = map(float, box)
    ncx = cx + 0.5 * m * w * math.cos(theta)
    ncy = cy + 0.5 * m * h * math.sin(theta)
    nw = w * math.exp((s + r) * m)
    nh = h * math.exp((s - r) * m)
    x0 = max(0.0, min(1.0, ncx - 0.5 * nw))
    y0 = max(0.0, min(1.0, ncy - 0.5 * nh))
    x1 = max(0.0, min(1.0, ncx + 0.5 * nw))
    y1 = max(0.0, min(1.0, ncy + 0.5 * nh))
    if x1 <= x0:
        x1 = min(1.0, x0 + 1e-4)
        x0 = max(0.0, x1 - 1e-4)
    if y1 <= y0:
        y1 = min(1.0, y0 + 1e-4)
        y0 = max(0.0, y1 - 1e-4)
    return [0.5 * (x0 + x1), 0.5 * (y0 + y1), x1 - x0, y1 - y0]


def sample_degraded_box(
    true_box: list[float],
    target_iou: float,
    rng: np.random.Generator,
    *,
    tol: float = 0.01,
    bisect_steps: int = 40,
    max_redraws: int = 20,
) -> tuple[list[float], float, bool]:
    """Registered J1-T bisection box sampler (PRICING_C2_C3.md L35-37).

    Returns (box_cxcywh, achieved_iou, reached_target).
    """
    best_box = list(true_box)
    best_iou = 1.0
    best_err = abs(1.0 - target_iou)

    for _ in range(max_redraws):
        theta = float(rng.uniform(0.0, 2.0 * math.pi))
        s = 1.0 if rng.random() < 0.5 else -1.0
        r = float(rng.uniform(-0.2, 0.2))

        lo, hi = 0.0, 4.0
        cand_hi = _move_and_clip_box(true_box, theta, s, r, hi)
        iou_hi = box_iou_cxcywh(cand_hi, true_box)
        if abs(iou_hi - target_iou) < best_err:
            best_box, best_iou, best_err = cand_hi, iou_hi, abs(iou_hi - target_iou)

        # IoU decreases monotonically from 1.0 (m=0) as m grows; if even m=4 is above target, redraw
        if iou_hi > target_iou + tol:
            continue

        for _ in range(bisect_steps):
            mid = 0.5 * (lo + hi)
            cand = _move_and_clip_box(true_box, theta, s, r, mid)
            val = box_iou_cxcywh(cand, true_box)
            err = abs(val - target_iou)
            if err < best_err:
                best_box, best_iou, best_err = cand, val, err
            if val > target_iou:
                lo = mid
            else:
                hi = mid
        if best_err <= tol:
            return best_box, float(best_iou), True

    return best_box, float(best_iou), bool(best_err <= tol)


def build_prompts_j1t(out_path: Path) -> dict[str, Any]:
    """Build PROMPTS_J1T.json from read-only lever8/j1/out/{PROMPTS_J1.json, detect/}."""
    import j1_common as G
    import select_j1 as S

    p_j1 = G.read_json(G.PROMPTS_J1)
    rng_main = np.random.default_rng(SEED_PRIMARY)
    rng_s2 = np.random.default_rng(SEED_SECOND)

    arm_specs = [
        ("k_prime", None, None),
        ("kB_0.9", 0.9, rng_main),
        ("kB_0.7", 0.7, rng_main),
        ("kB_0.7_s2", 0.7, rng_s2),
        ("kB_0.5", 0.5, rng_main),
    ]
    stats: dict[str, dict[str, Any]] = {name: dict(ious=[], unreachable=0, count=0) for name, _, _ in arm_specs}
    stats["kP_miss"] = dict(kept=0, dropped=0)
    stats["kP_fp"] = dict(gt_boxes=0, fp_boxes=0)

    out_caps = []
    for c in p_j1["captures"]:
        cap = c["capture"]
        # Load J1 detect file if available to extract h1 false-positive boxes for kP-fp
        det_path = G.DETECT / (G.stub(cap) + ".json.gz")
        det_text = G.read_json(det_path)["text"] if det_path.is_file() else {}
        # Map instance_id -> operand prompt names in this capture
        iid_to_prompts: dict[int, list[str]] = {}
        for op in c["operands"]:
            iid_to_prompts.setdefault(int(op["instance_id"]), [])
            if op["prompt"] not in iid_to_prompts[int(op["instance_id"])]:
                iid_to_prompts[int(op["instance_id"])].append(op["prompt"])

        arm_units: dict[str, list[dict[str, Any]]] = {name: [] for name, _, _ in arm_specs}
        arm_units["kP_miss"] = []
        arm_units["kP_fp"] = []

        for u in c["k_units"]:
            iid = int(u["instance_id"])
            gt_slots = {b["slot"] for b in u["boxes"]}

            # 1) k' and kB(*) arms
            for name, target_iou, rng in arm_specs:
                new_boxes = []
                for b in u["boxes"]:
                    if target_iou is None:
                        nb, got_iou, ok = list(b["box"]), 1.0, True
                    else:
                        nb, got_iou, ok = sample_degraded_box(b["box"], target_iou, rng)
                    stats[name]["ious"].append(got_iou)
                    stats[name]["count"] += 1
                    if not ok:
                        stats[name]["unreachable"] += 1
                    new_boxes.append(dict(slot=b["slot"], box=nb, achieved_iou=round(got_iou, 4), reached=ok, gt_pixels=b["gt_pixels"]))
                arm_units[name].append(dict(instance_id=iid, gt_sha256=u["gt_sha256"], boxes=new_boxes))

            # 2) kP-miss: GT box only where GT area >= 1% of frame (768 px on 240x320)
            miss_boxes = []
            for b in u["boxes"]:
                if b["gt_pixels"] >= 0.01 * GRID_PIXELS:
                    miss_boxes.append(dict(slot=b["slot"], box=list(b["box"]), gt_pixels=b["gt_pixels"]))
                    stats["kP_miss"]["kept"] += 1
                else:
                    stats["kP_miss"]["dropped"] += 1
            arm_units["kP_miss"].append(dict(instance_id=iid, gt_sha256=u["gt_sha256"], boxes=miss_boxes))

            # 3) kP-fp: GT anchors + h1 pick box on every GT-empty anchor where h1 fired
            fp_boxes = [dict(slot=b["slot"], box=list(b["box"]), source="gt", gt_pixels=b["gt_pixels"]) for b in u["boxes"]]
            stats["kP_fp"]["gt_boxes"] += len(fp_boxes)
            p_list = iid_to_prompts.get(iid, [])
            if det_text and p_list:
                # Use the first operand prompt for this instance (all share the same capture text pool)
                prompt_frames = det_text.get(p_list[0], [])
                for f_idx, props in enumerate(prompt_frames):
                    slot = f_idx + 1
                    if slot in gt_slots:
                        continue
                    pick_i = S.top1(props)
                    if pick_i is not None:
                        m240 = S.to_grid(G.unpack(props[pick_i]["mask"]))
                        fp_box = S.box_from_mask(m240)
                        if fp_box is not None:
                            fp_boxes.append(dict(slot=slot, box=fp_box, source="h1_fp", gt_pixels=0))
                            stats["kP_fp"]["fp_boxes"] += 1
            fp_boxes.sort(key=lambda x: x["slot"])
            arm_units["kP_fp"].append(dict(instance_id=iid, gt_sha256=u["gt_sha256"], boxes=fp_boxes))

        out_caps.append(dict(
            capture=cap,
            dataset=c["dataset"],
            arms=arm_units,
            total_box_prompts=sum(len(u["boxes"]) for units in arm_units.values() for u in units),
        ))

    # Summarize achieved IoU distributions
    sampler_summary = {}
    for name, target_iou, _ in arm_specs:
        arr = np.asarray(stats[name]["ious"], dtype=np.float64)
        sampler_summary[name] = dict(
            target_iou=target_iou,
            count=stats[name]["count"],
            unreachable=stats[name]["unreachable"],
            mean_iou=round(float(arr.mean()), 4) if len(arr) else None,
            p05_iou=round(float(np.percentile(arr, 5)), 4) if len(arr) else None,
            p50_iou=round(float(np.percentile(arr, 50)), 4) if len(arr) else None,
            p95_iou=round(float(np.percentile(arr, 95)), 4) if len(arr) else None,
        )
    sampler_summary["kP_miss"] = stats["kP_miss"]
    sampler_summary["kP_fp"] = stats["kP_fp"]

    body = dict(
        schema="j1t-prompts-v1",
        seeds=dict(primary=SEED_PRIMARY, second=SEED_SECOND),
        frames_j1_sha256=G.sha256_file(G.FRAMES_J1),
        prompts_j1_sha256=G.sha256_file(G.PROMPTS_J1),
        totals=dict(
            captures=len(out_caps),
            total_box_prompts=sum(c["total_box_prompts"] for c in out_caps),
        ),
        sampler_summary=sampler_summary,
        captures=out_caps,
    )
    G.write_json(out_path, body)
    return body


def run_j1t_gpu(prompts_path: Path, out_dir: Path, captures_arg: str, device: str = "cuda", arms_filter: list[str] | None = None) -> int:
    """Run frozen SAM 3 box_detect over J1-T prompts and verify k' parity against lever8/j1/out/detect."""
    import torch
    import j1_common as G
    import select_j1 as S
    import detect as D

    prompts = G.read_json(prompts_path)
    frames_map = {c["capture"]: c for c in G.read_json(G.FRAMES_J1)["captures"]}
    want = "all" if captures_arg == "all" else set(x.strip() for x in captures_arg.split(",") if x.strip())
    work = [c for c in prompts["captures"] if want == "all" or c["capture"] in want]
    if not work:
        raise SystemExit("No matching captures for --captures=" + captures_arg)

    out_dir.mkdir(parents=True, exist_ok=True)
    S1, T_mod, F_mod, versions = D.served_modules()

    stop_flag = {"hit": False}
    def _on_term(sig, _frame):
        stop_flag["hit"] = True
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _on_term)

    if device == "cpu":
        D.cpu_redirect()

    t0 = time.perf_counter()
    tower = T_mod.Sam3Tower(dict(
        checkpoint_path=str(G.SAM3_CHECKPOINT),
        receipt_path=str(G.SAM3_RECEIPT),
        source_root=str(G.SAM3_SOURCE),
        device=device,
    ))
    tower._load()
    with torch.inference_mode(), tower._autocast():
        visual = tower._backend.model.backbone.forward_text(["visual"], device=str(tower.device))
    load_s = time.perf_counter() - t0
    print(json.dumps(dict(event="SAM3_LOADED", device=device, load_seconds=round(load_s, 2), captures=len(work))), flush=True)

    parity_total = 0
    parity_pass = 0
    parity_ious = []

    for idx, c in enumerate(work, 1):
        if stop_flag["hit"]:
            print(json.dumps(dict(event="SIGTERM_STOP", completed=idx - 1, total=len(work))), flush=True)
            break
        cap = c["capture"]
        out_file = out_dir / (G.stub(cap) + ".json.gz")
        if out_file.is_file():
            continue

        u0 = time.perf_counter()
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        images = D.load_images(frames_map[cap]["frames"], 32)
        e0 = time.perf_counter()
        features = tower.encode(images)
        encode_s = time.perf_counter() - e0

        b0 = time.perf_counter()
        arms_out: dict[str, dict[str, Any]] = {}
        n_boxes = 0
        for arm_name, units in c["arms"].items():
            if arms_filter and arm_name not in arms_filter:
                continue
            arm_dict = {}
            for u in units:
                anchors = [D.box_detect(tower, features, b["slot"] - 1, b["box"], visual, F_mod) for b in u["boxes"]]
                n_boxes += len(anchors)
                arm_dict[str(u["instance_id"])] = dict(instance_id=u["instance_id"], gt_sha256=u["gt_sha256"], anchors=anchors)
            arms_out[arm_name] = arm_dict
        box_s = time.perf_counter() - b0
        del features
        peak_gib = (torch.cuda.max_memory_reserved() / (2 ** 30)) if device == "cuda" else 0.0
        if device == "cuda":
            torch.cuda.empty_cache()

        # Check k' parity against banked lever8/j1/out/detect/<stub>.json.gz
        cap_par_ok, cap_par_tot = 0, 0
        ref_det_path = G.DETECT / (G.stub(cap) + ".json.gz")
        if "k_prime" in arms_out and ref_det_path.is_file():
            ref_k = G.read_json(ref_det_path)["k"]
            for iid_str, rec in arms_out["k_prime"].items():
                ref_by_slot = {a["slot"]: G.unpack(a["mask"]) for a in ref_k[iid_str]["anchors"]}
                for a in rec["anchors"]:
                    m_new = G.unpack(a["mask"])
                    m_ref = ref_by_slot[a["slot"]]
                    val = S.iou(m_new, m_ref)
                    parity_ious.append(val)
                    cap_par_tot += 1
                    parity_total += 1
                    if val >= 0.95:
                        cap_par_ok += 1
                        parity_pass += 1

        G.write_json(out_file, dict(
            schema="j1t-detect-v1",
            capture=cap,
            device=device,
            encode_seconds=round(encode_s, 3),
            box_seconds=round(box_s, 3),
            total_seconds=round(time.perf_counter() - u0, 3),
            box_prompts=n_boxes,
            cuda_peak_reserved_gib=round(peak_gib, 3),
            k_prime_parity=dict(pass_n=cap_par_ok, total=cap_par_tot),
            arms=arms_out,
        ), gz=True)
        print(json.dumps(dict(
            event="CAPTURE", idx=idx, total=len(work), capture=cap, box_prompts=n_boxes,
            encode_s=round(encode_s, 2), box_s=round(box_s, 2), peak_gib=round(peak_gib, 2),
            k_prime_parity=f"{cap_par_ok}/{cap_par_tot}",
        )), flush=True)

    summary = dict(
        event="DONE",
        captures=len(work),
        k_prime_parity_pass=parity_pass,
        k_prime_parity_total=parity_total,
        k_prime_parity_rate=round(parity_pass / parity_total, 4) if parity_total else None,
        k_prime_min_iou=round(min(parity_ious), 4) if parity_ious else None,
        wall_seconds=round(time.perf_counter() - t0, 2),
    )
    (out_dir / "SUMMARY_J1T.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary), flush=True)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="E03-A: J1-T registered box-tolerance diagnostic")
    ap.add_argument("--build-prompts", action="store_true", help="Build PROMPTS_J1T.json on CPU")
    ap.add_argument("--run-gpu", action="store_true", help="Run SAM 3 box_detect over PROMPTS_J1T.json")
    ap.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    ap.add_argument("--captures", default="scannet/scene0642_01")
    ap.add_argument("--arms", default=None, help="Optional comma-separated subset of arms")
    ap.add_argument("--out", default=str(HERE / "out_j1t"))
    args = ap.parse_args(argv)

    out_dir = Path(args.out).resolve()
    prompts_path = out_dir / "PROMPTS_J1T.json"
    if args.build_prompts or not prompts_path.is_file():
        body = build_prompts_j1t(prompts_path)
        print(json.dumps(dict(event="PROMPTS_BUILT", path=str(prompts_path), totals=body["totals"], sampler_summary=body["sampler_summary"]), indent=1))
    if args.run_gpu:
        arms_filter = [x.strip() for x in args.arms.split(",") if x.strip()] if args.arms else None
        return run_j1t_gpu(prompts_path, out_dir / "detect", args.captures, device=args.device, arms_filter=arms_filter)
    return 0


if __name__ == "__main__":
    sys.exit(main())
