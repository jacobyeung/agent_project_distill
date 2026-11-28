"""Comprehensive paired statistical evaluation for KT-1b (E04: G3T vs DA3-only vs DA3+TT-BA vs Geo-Maj@3).

Computes exact paired metrics, worst-quartile ATE & >15 deg rotation reductions, win/tie/loss counts,
and 10,000-draw bootstrap 95% confidence intervals (seed 20261120) on:
  1) Live GPU 4 dev-S1 run (28 captures: 16 ARKit, 12 ScanNet/ScanNet++)
  2) Full 38-capture dev-S1 G3T baseline from CAMERA_SPLIT.json
  3) Full 296-capture K1 cached evaluation (159 ARKit, 137 ScanNet/ScanNet++), pairing G3T tower.npz
     against DA3-only and DA3+TT-BA.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ttba_lm as T

TREE = Path("/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872")
if str(TREE) not in sys.path:
    sys.path.insert(0, str(TREE))
from student_pilot import camera_targets

DEVS1_DIR = HERE / "out_e04_devs1"
K1_OUT_DIR = HERE / "out_e04_k1_full"
K1_MANIFEST = Path("/scratch/jjyeung/orch_n30/geo_k1/stage/K1_MANIFEST.arkit_timing.json")
K1_DA3_PRED = Path("/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3")
K1_TOWERS = Path("/scratch/jjyeung/k1/run_tower_sam_2")
K1_DECIDE_JSON = Path("/scratch/jjyeung/orch_n30/geo_k1/out/decide_heldout_once.json")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _norm(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if (np.isfinite(n) and n >= 1e-6) else np.array([0.0, 0.0, 1.0])


def g3t_c2w_from_tower_npz(tower_path: Path) -> np.ndarray:
    with np.load(tower_path, allow_pickle=False) as z:
        slots = z["anchor_slots"].astype(int)
        raw = z["raw_pose"][slots]
    R_init = np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw])
    g1 = _norm(np.mean(-R_init[:, :, 1], axis=0))
    R, t, _ = camera_targets.to_gravity_reference_frame(raw, g1)
    C = np.repeat(np.eye(4, dtype=np.float64)[None], len(slots), axis=0)
    C[:, :3, :3], C[:, :3, 3] = R, t
    return C


def bootstrap_stat(vals: list[float] | np.ndarray, fn=np.median, n_boot: int = 10000, seed: int = 20261120) -> dict[str, Any]:
    arr = np.asarray(vals, dtype=np.float64)
    if len(arr) == 0:
        return dict(est=None, ci95=[None, None])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
    samples = fn(arr[idx], axis=1)
    est = float(fn(arr))
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return dict(est=round(est, 4), ci95=[round(float(lo), 4), round(float(hi), 4)])


def worst_quartile_mean(vals: list[float] | np.ndarray) -> float:
    arr = np.sort(np.asarray(vals, dtype=np.float64))
    if len(arr) == 0:
        return 0.0
    k = max(1, int(np.ceil(0.25 * len(arr))))
    return float(np.mean(arr[-k:]))


def summarize_subset(rows: list[dict[str, Any]], arms: tuple[str, ...]) -> dict[str, Any]:
    if not rows:
        return {}
    out: dict[str, Any] = dict(n=len(rows), arms={}, comparisons={})
    for arm in arms:
        rot_max = np.array([r[arm]["rotation_max_deg"] for r in rows], dtype=np.float64)
        rot_rms = np.array([r[arm]["rotation_rms_deg"] for r in rows], dtype=np.float64)
        t_rms = np.array([r[arm]["translation_rms_m"] for r in rows], dtype=np.float64)
        classes = [r[arm]["cls"] for r in rows]
        gt15 = int(np.sum(rot_max > 15.0))
        gt60 = int(np.sum(rot_max > 60.0))
        wq_ate = worst_quartile_mean(t_rms)
        p75_ate = float(np.percentile(t_rms, 75))
        wq_rot = worst_quartile_mean(rot_max)
        out["arms"][arm] = dict(
            n=len(rows),
            pass_n=sum(c == "pass" for c in classes),
            pass_rate=round(sum(c == "pass" for c in classes) / len(rows), 4),
            moderate_n=sum(c == "moderate" for c in classes),
            gross_n=sum(c == "gross" for c in classes),
            gross_rate=round(sum(c == "gross" for c in classes) / len(rows), 4),
            rot_gt15_n=gt15,
            rot_gt15_rate=round(gt15 / len(rows), 4),
            rot_gt60_n=gt60,
            median_rot_max_deg=bootstrap_stat(rot_max, np.median),
            mean_rot_max_deg=bootstrap_stat(rot_max, np.mean),
            median_rot_rms_deg=bootstrap_stat(rot_rms, np.median),
            mean_rot_rms_deg=bootstrap_stat(rot_rms, np.mean),
            median_trans_rms_m=bootstrap_stat(t_rms, np.median),
            mean_trans_rms_m=bootstrap_stat(t_rms, np.mean),
            p75_trans_rms_m=round(p75_ate, 4),
            worst_quartile_mean_trans_rms_m=round(wq_ate, 4),
            worst_quartile_mean_rot_max_deg=round(wq_rot, 3),
        )

    # Paired comparisons vs g3t and vs da3_only
    if "g3t" in arms and "da3_only" in arms:
        g_gt15 = out["arms"]["g3t"]["rot_gt15_n"]
        d_gt15 = out["arms"]["da3_only"]["rot_gt15_n"]
        g_wq_ate = out["arms"]["g3t"]["worst_quartile_mean_trans_rms_m"]
        d_wq_ate = out["arms"]["da3_only"]["worst_quartile_mean_trans_rms_m"]
        g_p75_ate = out["arms"]["g3t"]["p75_trans_rms_m"]
        d_p75_ate = out["arms"]["da3_only"]["p75_trans_rms_m"]

        d_rot_diff = [r["da3_only"]["rotation_max_deg"] - r["g3t"]["rotation_max_deg"] for r in rows]
        d_ate_diff = [r["da3_only"]["translation_rms_m"] - r["g3t"]["translation_rms_m"] for r in rows]
        out["comparisons"]["da3_only_vs_g3t"] = dict(
            rot_gt15_rel_reduction=round((g_gt15 - d_gt15) / g_gt15, 4) if g_gt15 > 0 else 0.0,
            wq_ate_rel_reduction=round((g_wq_ate - d_wq_ate) / g_wq_ate, 4) if g_wq_ate > 0 else 0.0,
            p75_ate_rel_reduction=round((g_p75_ate - d_p75_ate) / g_p75_ate, 4) if g_p75_ate > 0 else 0.0,
            mean_rot_max_delta_deg=bootstrap_stat(d_rot_diff, np.mean),
            median_rot_max_delta_deg=bootstrap_stat(d_rot_diff, np.median),
            mean_trans_rms_delta_m=bootstrap_stat(d_ate_diff, np.mean),
            median_trans_rms_delta_m=bootstrap_stat(d_ate_diff, np.median),
            da3_wins_rot_max=sum(r["da3_only"]["rotation_max_deg"] < r["g3t"]["rotation_max_deg"] - 1e-4 for r in rows),
            da3_wins_trans_rms=sum(r["da3_only"]["translation_rms_m"] < r["g3t"]["translation_rms_m"] - 1e-5 for r in rows),
        )

    for cand in ("da3_ttba", "da3_ttba_drop005", "geomaj3"):
        if cand in arms and "da3_only" in arms:
            rot_diff = [r[cand]["rotation_max_deg"] - r["da3_only"]["rotation_max_deg"] for r in rows]
            rms_diff = [r[cand]["rotation_rms_deg"] - r["da3_only"]["rotation_rms_deg"] for r in rows]
            ate_diff = [r[cand]["translation_rms_m"] - r["da3_only"]["translation_rms_m"] for r in rows]
            out["comparisons"][f"{cand}_vs_da3_only"] = dict(
                mean_rot_max_delta_deg=bootstrap_stat(rot_diff, np.mean),
                median_rot_max_delta_deg=bootstrap_stat(rot_diff, np.median),
                mean_rot_rms_delta_deg=bootstrap_stat(rms_diff, np.mean),
                mean_trans_rms_delta_m=bootstrap_stat(ate_diff, np.mean),
                wins_rot_max=sum(r[cand]["rotation_max_deg"] < r["da3_only"]["rotation_max_deg"] - 1e-4 for r in rows),
                ties_rot_max=sum(abs(r[cand]["rotation_max_deg"] - r["da3_only"]["rotation_max_deg"]) <= 1e-4 for r in rows),
                losses_rot_max=sum(r[cand]["rotation_max_deg"] > r["da3_only"]["rotation_max_deg"] + 1e-4 for r in rows),
                wins_rot_rms=sum(r[cand]["rotation_rms_deg"] < r["da3_only"]["rotation_rms_deg"] - 1e-4 for r in rows),
                ties_rot_rms=sum(abs(r[cand]["rotation_rms_deg"] - r["da3_only"]["rotation_rms_deg"]) <= 1e-4 for r in rows),
                losses_rot_rms=sum(r[cand]["rotation_rms_deg"] > r["da3_only"]["rotation_rms_deg"] + 1e-4 for r in rows),
            )
    return out


def eval_devs1_stats() -> dict[str, Any]:
    cap_files = sorted((DEVS1_DIR / "captures").glob("*.json"))
    rows = [json.loads(p.read_text()) for p in cap_files]
    arms = ("g3t", "da3_only", "da3_ttba", "geomaj3")
    return dict(
        total_captures=len(rows),
        all=summarize_subset(rows, arms),
        arkit=summarize_subset([r for r in rows if r["dataset"] == "arkitscenes"], arms),
        scannet_family=summarize_subset([r for r in rows if r["dataset"] != "arkitscenes"], arms),
        per_capture_rows=rows,
    )


def eval_k1_stats() -> dict[str, Any]:
    manifest = json.loads(K1_MANIFEST.read_text())
    tower_index = {}
    for p in sorted(K1_TOWERS.glob("*/PHASE_COMPLETE.json")):
        rec = json.loads(p.read_text())
        tower_index[rec["capture_sha256"]] = p.parent / "tower.npz"

    rows = []
    for c in manifest["captures"]:
        key = _digest(c)
        pfile = K1_DA3_PRED / key[:16] / "pred.npz"
        tfile = tower_index.get(key)
        gt_info = c.get("gt")
        if not pfile.is_file() or tfile is None or not tfile.is_file() or not gt_info or not Path(gt_info["path"]).is_file():
            continue
        with np.load(pfile, allow_pickle=False) as z:
            slots = z["anchor_slots"].astype(int)
            da3_c2w = z["c2w"][slots].astype(np.float64)
            da3_K = z["intrinsics"][slots].astype(np.float64)
            dgrid = z["depth_grid64"][slots].astype(np.float64)
        with np.load(gt_info["path"], allow_pickle=False) as g:
            valid = g["valid"].astype(bool)
            gt_c2w = g["c2w"].astype(np.float64)
        if valid.sum() < 4:
            continue

        g3t_c2w = g3t_c2w_from_tower_npz(tfile)
        g3t_fit_se3 = T.align_trajectory_rigid(g3t_c2w[valid], gt_c2w[valid], with_scale=False)
        g3t_fit_sim3 = T.align_trajectory_rigid(g3t_c2w[valid], gt_c2w[valid], with_scale=True)
        da3_fit = T.align_trajectory_rigid(da3_c2w[valid], gt_c2w[valid], with_scale=False)

        corr = T.build_depth_correspondences(da3_c2w, da3_K, dgrid, np.linspace(0, 1000, 51), frame_offsets=(1, 2, 4), stride=4)
        if len(corr.src_idx) >= 20:
            ttba_35 = T.run_ttba_lm(da3_c2w, da3_K, corr, max_iters=5, min_rel_drop=0.35)
            ttba_05 = T.run_ttba_lm(da3_c2w, da3_K, corr, max_iters=5, min_rel_drop=0.05)
        else:
            empty_res = T.TTBAResult(
                c2w=da3_c2w, scale=1.0, committed=False, initial_cost=0.0, final_cost=0.0,
                rel_cost_drop=0.0, iterations=0, wall_ms=0.0, inlier_ratio=0.0, cost_history=[],
            )
            ttba_35, ttba_05 = empty_res, empty_res

        fit_35 = T.align_trajectory_rigid(ttba_35.c2w[valid], gt_c2w[valid], with_scale=False)
        fit_05 = T.align_trajectory_rigid(ttba_05.c2w[valid], gt_c2w[valid], with_scale=False)

        # Note: G3T raw translation is unscaled; report Sim(3)-aligned translation RMS for G3T so scale does not penalize G3T pose!
        rows.append(dict(
            capture=c["canonical"],
            dataset=c["canonical"].split("/")[0],
            k1_split=c.get("k1_split", "unknown"),
            g3t=dict(
                translation_rms_m=round(g3t_fit_sim3["translation_rms_m"], 4),
                translation_rms_unscaled_m=round(g3t_fit_se3["translation_rms_m"], 4),
                rotation_rms_deg=round(g3t_fit_sim3["rotation_rms_deg"], 3),
                rotation_max_deg=round(g3t_fit_sim3["rotation_max_deg"], 3),
                cls=g3t_fit_sim3["cls"],
            ),
            da3_only=dict(
                translation_rms_m=round(da3_fit["translation_rms_m"], 4),
                rotation_rms_deg=round(da3_fit["rotation_rms_deg"], 3),
                rotation_max_deg=round(da3_fit["rotation_max_deg"], 3),
                cls=da3_fit["cls"],
            ),
            da3_ttba=dict(
                translation_rms_m=round(fit_35["translation_rms_m"], 4),
                rotation_rms_deg=round(fit_35["rotation_rms_deg"], 3),
                rotation_max_deg=round(fit_35["rotation_max_deg"], 3),
                cls=fit_35["cls"],
                committed=bool(ttba_35.committed),
                rel_cost_drop=round(ttba_35.rel_cost_drop, 4),
                ttba_wall_ms=round(ttba_35.wall_ms, 2),
            ),
            da3_ttba_drop005=dict(
                translation_rms_m=round(fit_05["translation_rms_m"], 4),
                rotation_rms_deg=round(fit_05["rotation_rms_deg"], 3),
                rotation_max_deg=round(fit_05["rotation_max_deg"], 3),
                cls=fit_05["cls"],
                committed=bool(ttba_05.committed),
                rel_cost_drop=round(ttba_05.rel_cost_drop, 4),
            ),
        ))

    arms = ("g3t", "da3_only", "da3_ttba", "da3_ttba_drop005")
    return dict(
        total_captures=len(rows),
        all=summarize_subset(rows, arms),
        arkit=summarize_subset([r for r in rows if r["dataset"] == "arkitscenes"], arms),
        scannet_family=summarize_subset([r for r in rows if r["dataset"] != "arkitscenes"], arms),
        ttba_commit_count_drop035=sum(1 for r in rows if r["da3_ttba"]["committed"]),
        ttba_commit_count_drop005=sum(1 for r in rows if r["da3_ttba_drop005"]["committed"]),
    )


def main() -> int:
    devs1 = eval_devs1_stats()
    k1 = eval_k1_stats()
    full = dict(devs1=devs1, k1_cached=k1)
    out_path = HERE / "out_e04_full_analysis.json"
    out_path.write_text(json.dumps(full, indent=1) + "\n")
    print(json.dumps(dict(
        devs1_n=devs1["total_captures"],
        devs1_arkit_comp=devs1["arkit"].get("comparisons", {}),
        k1_n=k1["total_captures"],
        k1_arkit_comp=k1["arkit"].get("comparisons", {}),
    ), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
