"""Paired Habitat R2R-CE GT Depth-Scale Diagnostic: V-C Raw vs Analytical FoV-Fix vs DA3-Nested vs ScaleAnchor.

Evaluates 100 paired Habitat frames (20 rand100 episodes x 5 trajectory viewpoints across 6 val_unseen MP3D scenes,
512x512, HFOV=90 deg, h_cam=1.25 m) on:
1. Dense valid-frustum metric depth accuracy (`0.3m < d_gt < 10.0m`):
   - Median pixel scale ratio `median(d_pred / d_gt)` and IQR (`q75 - q25`)
   - Global median ratio of medians across frames/episodes
   - `AbsRel = mean(|d_pred - d_gt| / d_gt)`
   - Scale-invariant `SI-AbsRel = mean(|s_oracle * d_pred - d_gt| / d_gt)` where `s_oracle = median(d_gt / d_pred)`
   - Threshold accuracy `delta1 = P(max(d_pred/d_gt, d_gt/d_pred) < 1.25)`
   - `RMSE` (metres)
2. Lower-half navigation floor/obstacle region (`v in [0.5, 0.95]`, `0.3m < d_gt < 10.0m`):
   - Median `d_pred / d_gt`, `AbsRel`, `delta1 < 1.25`
3. Waypoint Click-Lift & Travel-Leg accuracy at `(u_click, v_click)`:
   - Click depth ratio `d_pred(u,v) / d_gt(u,v)`
   - Commanded travel leg error `|L_pred - L_gt|` (metres, where `L = clamp(r - 0.5, 0, 2.0)`)
   - Forward step count error `|steps_pred - steps_gt|` (steps of 0.25m)
   - Saturation rate `P(L_pred == 2.0m)` vs GT saturation rate `P(L_gt == 2.0m)`

Computes 10,000-resample episode-clustered bootstrap 95% confidence intervals and writes:
- Per-frame JSONL: `work_nav_e0_probe/out/depth_diag_per_frame.jsonl`
- Summary JSON: `work_nav_e0_probe/out/depth_diag_summary.json`
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Dict, List
import numpy as np

from depth_models import StandaloneVCDepth, StandaloneDA3Depth
from vla_where.nav import bearing_range, travel, focal

OUT_DIR = Path("/scratch/jjyeung/orch_home_distill/work_nav_e0_probe/out")
IN_NPZ = OUT_DIR / "habitat_rand100_smoke20_rgb_gtdepth_100frames.npz"
IN_META = OUT_DIR / "habitat_rand100_smoke20_rgb_gtdepth_100frames_meta.json"
OUT_JSONL = OUT_DIR / "depth_diag_per_frame.jsonl"
OUT_SUMMARY = OUT_DIR / "depth_diag_summary.json"

ARMS = [
    "vc_raw",
    "vc_cond90_raw",
    "vc_fovfix_pred",
    "vc_fovfix_cond90",
    "vc_fovfix_58deg",
    "vc_fovfix_e0",
    "vc_scale_anchor",
    "da3_raw",
    "da3_fovfix",
    "da3_scale_anchor",
    "da3_scale_svd",
]


def eval_depth_map(
    d_pred: np.ndarray,
    d_gt: np.ndarray,
    u_click: float,
    v_click: float,
    d_gt_click: float,
    leg_gt_click: float,
    hfov_deg: float = 90.0,
) -> dict:
    H, W = d_gt.shape
    valid = np.isfinite(d_gt) & (d_gt > 0.3) & (d_gt < 10.0) & np.isfinite(d_pred) & (d_pred > 1e-3)
    if np.sum(valid) < 32:
        return {}

    p = d_pred[valid].astype(np.float64)
    g = d_gt[valid].astype(np.float64)
    ratios = p / g
    med_ratio = float(np.median(ratios))
    q25_ratio = float(np.percentile(ratios, 25))
    q75_ratio = float(np.percentile(ratios, 75))
    iqr_ratio = q75_ratio - q25_ratio
    abs_rel = float(np.mean(np.abs(p - g) / g))
    rmse = float(np.sqrt(np.mean((p - g) ** 2)))
    max_rg = np.maximum(p / g, g / p)
    delta1 = float(np.mean(max_rg < 1.25))
    delta2 = float(np.mean(max_rg < 1.25 ** 2))

    # Scale-invariant oracle-aligned metrics
    s_oracle = float(np.median(g / p))
    p_si = p * s_oracle
    si_abs_rel = float(np.mean(np.abs(p_si - g) / g))
    si_delta1 = float(np.mean(np.maximum(p_si / g, g / p_si) < 1.25))

    # Lower-half floor/obstacle region (v in [0.5, 0.95])
    yy = np.arange(H)[:, None]
    lower_mask = valid & (yy >= int(0.50 * H)) & (yy < int(0.95 * H))
    if np.sum(lower_mask) >= 16:
        pl = d_pred[lower_mask].astype(np.float64)
        gl = d_gt[lower_mask].astype(np.float64)
        l_med_ratio = float(np.median(pl / gl))
        l_abs_rel = float(np.mean(np.abs(pl - gl) / gl))
        l_delta1 = float(np.mean(np.maximum(pl / gl, gl / pl) < 1.25))
    else:
        l_med_ratio, l_abs_rel, l_delta1 = med_ratio, abs_rel, delta1

    # Click point evaluation (3x3 median around u_click, v_click)
    px_x = min(max(int(u_click * W), 0), W - 1)
    px_y = min(max(int(v_click * H), 0), H - 1)
    y0, y1 = max(0, px_y - 1), min(H, px_y + 2)
    x0, x1 = max(0, px_x - 1), min(W, px_x + 2)
    d_click_pred = float(np.median(d_pred[y0:y1, x0:x1]))

    f_px = focal(W, hfov_deg)
    px_pred = d_click_pred * (u_click * W - W / 2.0) / f_px
    _, rng_pred = bearing_range(px_pred, d_click_pred)
    leg_pred = travel(rng_pred)

    steps_gt = int(round(leg_gt_click / 0.25))
    steps_pred = int(round(leg_pred / 0.25))

    click_ratio = d_click_pred / max(d_gt_click, 0.1) if d_gt_click > 0.1 else 1.0
    click_abs_rel = abs(d_click_pred - d_gt_click) / max(d_gt_click, 0.1) if d_gt_click > 0.1 else 0.0
    leg_err_m = abs(leg_pred - leg_gt_click)
    step_err = abs(steps_pred - steps_gt)

    return {
        "med_ratio": med_ratio,
        "q25_ratio": q25_ratio,
        "q75_ratio": q75_ratio,
        "iqr_ratio": iqr_ratio,
        "abs_rel": abs_rel,
        "si_abs_rel": si_abs_rel,
        "rmse_m": rmse,
        "delta1": delta1,
        "delta2": delta2,
        "si_delta1": si_delta1,
        "lower_med_ratio": l_med_ratio,
        "lower_abs_rel": l_abs_rel,
        "lower_delta1": l_delta1,
        "d_click_pred_m": d_click_pred,
        "click_ratio": click_ratio,
        "click_abs_rel": click_abs_rel,
        "leg_pred_m": leg_pred,
        "leg_err_m": leg_err_m,
        "steps_pred": steps_pred,
        "steps_gt": steps_gt,
        "step_err": step_err,
        "leg_saturated_2m": float(leg_pred >= 1.999),
        "gt_saturated_2m": float(leg_gt_click >= 1.999),
    }


def bootstrap_ci_episode_clustered(
    records: List[dict],
    arm: str,
    key: str,
    stat: str = "mean",
    n_boot: int = 5000,
    seed: int = 42,
) -> dict:
    """Episode-clustered bootstrap 95% CI across the 20 episodes."""
    by_ep: Dict[int, List[float]] = {}
    for r in records:
        if arm in r["arms"] and key in r["arms"][arm]:
            by_ep.setdefault(int(r["ep_idx"]), []).append(float(r["arms"][arm][key]))
    ep_keys = sorted(by_ep.keys())
    ep_vals = [np.mean(by_ep[k]) if stat == "mean" else np.median(by_ep[k]) for k in ep_keys]
    arr = np.asarray(ep_vals, dtype=np.float64)
    all_vals = np.asarray([float(r["arms"][arm][key]) for r in records if arm in r["arms"]], dtype=np.float64)

    point = float(np.mean(all_vals) if stat == "mean" else np.median(all_vals))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
    samples = arr[idx]
    boot_stat = np.mean(samples, axis=1) if stat == "mean" else np.median(samples, axis=1)
    lo, hi = float(np.percentile(boot_stat, 2.5)), float(np.percentile(boot_stat, 97.5))
    return {"point": point, "ci95": [lo, hi]}


def main():
    t0 = time.monotonic()
    data = np.load(IN_NPZ)
    rgbs = data["rgb"]
    depths = data["depth"]
    meta = json.loads(IN_META.read_text())["records"]

    print(f"Loaded {len(meta)} Habitat RGB+GT-depth frames: rgb={rgbs.shape}, depth={depths.shape}")
    vc_model = StandaloneVCDepth(device="cuda")
    da3_model = StandaloneDA3Depth(device="cuda")

    # Group frame indices by episode so V-C and DA3 can also see the episode history prefix up to each frame
    by_ep: Dict[int, List[int]] = {}
    for idx, rec in enumerate(meta):
        by_ep.setdefault(int(rec["ep_idx"]), []).append(idx)

    out_records = []
    ep_rolling_da3_scales: Dict[int, List[float]] = {}
    ep_rolling_vc_scales: Dict[int, List[float]] = {}
    for idx, rec in enumerate(meta):
        ep_idx = int(rec["ep_idx"])
        ep_frames = [rgbs[i] for i in by_ep[ep_idx] if i <= idx]
        d_gt = depths[idx]

        # Run V-C on the episode prefix up to current frame
        vc_out = vc_model.infer_single_or_clip(ep_frames, query_grid_size=64, hab_hfov_deg=90.0)
        # Run DA3-Nested on the current frame
        da3_out = da3_model.infer_single_or_window([rgbs[idx]], process_res=504, hab_hfov_deg=90.0)

        # Update rolling episode ScaleAnchor from valid floor-plane SVD fits (fallback to s_fov_da3 if frame 0 has no floor)
        if da3_out["anchor_info"].get("svd_valid"):
            ep_rolling_da3_scales.setdefault(ep_idx, []).append(float(da3_out["s_anchor"]))
        if ep_rolling_da3_scales.get(ep_idx):
            s_da3_ep = float(np.median(ep_rolling_da3_scales[ep_idx]))
        else:
            s_da3_ep = float(da3_out["s_fov_da3"])

        if vc_out["anchor_info"].get("svd_valid"):
            ep_rolling_vc_scales.setdefault(ep_idx, []).append(float(vc_out["s_anchor"]))
        if ep_rolling_vc_scales.get(ep_idx):
            s_vc_ep = float(np.median(ep_rolling_vc_scales[ep_idx]))
        else:
            s_vc_ep = float(vc_out["s_anchor"])

        combined_maps = {
            "vc_raw": vc_out["vc_raw"],
            "vc_cond90_raw": vc_out["vc_cond90_raw"],
            "vc_fovfix_pred": vc_out["vc_fovfix_pred"],
            "vc_fovfix_cond90": vc_out["vc_fovfix_cond90"],
            "vc_fovfix_58deg": vc_out["vc_fovfix_58deg"],
            "vc_fovfix_e0": vc_out["vc_fovfix_e0"],
            "vc_scale_anchor": (vc_out["vc_raw"] * s_vc_ep).astype(np.float32),
            "da3_raw": da3_out["da3_raw"],
            "da3_fovfix": da3_out["da3_fovfix"],
            "da3_scale_anchor": (da3_out["da3_raw"] * s_da3_ep).astype(np.float32),
            "da3_scale_svd": da3_out["da3_scale_svd"],
        }

        arm_metrics = {}
        for arm_name, d_map in combined_maps.items():
            arm_metrics[arm_name] = eval_depth_map(
                d_map,
                d_gt,
                u_click=float(rec["u_click"]),
                v_click=float(rec["v_click"]),
                d_gt_click=float(rec["d_gt_click_m"]),
                leg_gt_click=float(rec["leg_gt_click_m"]),
                hfov_deg=90.0,
            )

        row = {
            **rec,
            "vc_pred_fov_x_deg": vc_out["pred_fov_x_deg"],
            "vc_pred_fov_y_deg": vc_out["pred_fov_y_deg"],
            "vc_s_fov_pred": vc_out["s_fov_pred"],
            "vc_s_anchor": vc_out["s_anchor"],
            "da3_pred_hfov_deg": da3_out["pred_hfov_deg"],
            "da3_s_fov": da3_out["s_fov_da3"],
            "da3_s_anchor": da3_out["s_anchor"],
            "da3_s_svd": da3_out["anchor_info"]["s_svd"],
            "arms": arm_metrics,
        }
        out_records.append(row)
        if (idx + 1) % 20 == 0 or (idx + 1) == len(meta):
            print(
                f"[{idx+1}/{len(meta)}] vc_raw ratio={arm_metrics['vc_raw']['med_ratio']:.3f} "
                f"vc_fovfix_pred ratio={arm_metrics['vc_fovfix_pred']['med_ratio']:.3f} "
                f"da3_raw ratio={arm_metrics['da3_raw']['med_ratio']:.3f} "
                f"da3_anchor ratio={arm_metrics['da3_scale_anchor']['med_ratio']:.3f}"
            )

    with OUT_JSONL.open("w") as f:
        for r in out_records:
            f.write(json.dumps(r) + "\n")

    # Aggregate summary with episode-clustered bootstrap 95% CIs
    arm_summaries = {}
    for arm in ARMS:
        arm_summaries[arm] = {
            "med_ratio_median": bootstrap_ci_episode_clustered(out_records, arm, "med_ratio", stat="median"),
            "med_ratio_mean": bootstrap_ci_episode_clustered(out_records, arm, "med_ratio", stat="mean"),
            "iqr_ratio_median": bootstrap_ci_episode_clustered(out_records, arm, "iqr_ratio", stat="median"),
            "abs_rel": bootstrap_ci_episode_clustered(out_records, arm, "abs_rel", stat="mean"),
            "si_abs_rel": bootstrap_ci_episode_clustered(out_records, arm, "si_abs_rel", stat="mean"),
            "rmse_m": bootstrap_ci_episode_clustered(out_records, arm, "rmse_m", stat="mean"),
            "delta1": bootstrap_ci_episode_clustered(out_records, arm, "delta1", stat="mean"),
            "delta2": bootstrap_ci_episode_clustered(out_records, arm, "delta2", stat="mean"),
            "si_delta1": bootstrap_ci_episode_clustered(out_records, arm, "si_delta1", stat="mean"),
            "lower_med_ratio": bootstrap_ci_episode_clustered(out_records, arm, "lower_med_ratio", stat="median"),
            "lower_abs_rel": bootstrap_ci_episode_clustered(out_records, arm, "lower_abs_rel", stat="mean"),
            "lower_delta1": bootstrap_ci_episode_clustered(out_records, arm, "lower_delta1", stat="mean"),
            "click_ratio_median": bootstrap_ci_episode_clustered(out_records, arm, "click_ratio", stat="median"),
            "click_abs_rel": bootstrap_ci_episode_clustered(out_records, arm, "click_abs_rel", stat="mean"),
            "leg_err_m": bootstrap_ci_episode_clustered(out_records, arm, "leg_err_m", stat="mean"),
            "step_err": bootstrap_ci_episode_clustered(out_records, arm, "step_err", stat="mean"),
            "leg_saturated_2m": bootstrap_ci_episode_clustered(out_records, arm, "leg_saturated_2m", stat="mean"),
        }

    vc_fovs_x = [r["vc_pred_fov_x_deg"] for r in out_records]
    vc_fovs_y = [r["vc_pred_fov_y_deg"] for r in out_records]
    da3_fovs = [r["da3_pred_hfov_deg"] for r in out_records]

    summary = {
        "n_episodes": len(by_ep),
        "n_frames": len(out_records),
        "wall_seconds": round(time.monotonic() - t0, 2),
        "vc_predicted_fov_deg": {
            "hfov_median": float(np.median(vc_fovs_x)),
            "hfov_mean": float(np.mean(vc_fovs_x)),
            "hfov_iqr": float(np.percentile(vc_fovs_x, 75) - np.percentile(vc_fovs_x, 25)),
            "vfov_median": float(np.median(vc_fovs_y)),
            "vfov_mean": float(np.mean(vc_fovs_y)),
            "implied_focal_scale_ratio_median": float(np.median([r["vc_s_fov_pred"] for r in out_records])),
            "implied_raw_overshoot_factor_median": float(1.0 / np.median([r["vc_s_fov_pred"] for r in out_records])),
        },
        "da3_predicted_fov_deg": {
            "hfov_median": float(np.median(da3_fovs)),
            "hfov_mean": float(np.mean(da3_fovs)),
            "implied_focal_scale_ratio_median": float(np.median([r["da3_s_fov"] for r in out_records])),
        },
        "arms": arm_summaries,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print("DIAG_SUMMARY_OK:", json.dumps(summary["vc_predicted_fov_deg"], sort_keys=True))


if __name__ == "__main__":
    main()
