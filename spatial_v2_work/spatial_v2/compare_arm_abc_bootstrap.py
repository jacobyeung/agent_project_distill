"""Paired n=53 10k-bootstrap comparison & Linear 3D-Geometry Probe for KT-6 Stage-1A Arms A/B/C."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F

METRICS_COMPARE: Tuple[str, ...] = (
    "rot_med_deg",
    "rot_mean_deg",
    "rot_acc_5deg",
    "rot_acc_15deg",
    "trans_dir_med_deg",
    "trans_acc_15deg",
    "absrel",
    "si_absrel",
    "delta1",
    "scale_ratio",
    "gravity_err_deg",
    "fov_rel_err_pct",
)


def _load_per_clip_map(eval_json_path: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    data = json.loads(Path(eval_json_path).read_text())
    rows = data.get("per_clip") or data.get("per_capture")
    if not rows:
        raise RuntimeError(f"No per_clip or per_capture found in {eval_json_path}")
    by_id: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        cid = r.get("capture_id") or r.get("canonical")
        if not cid:
            raise RuntimeError(f"Missing capture_id/canonical in {eval_json_path}")
        by_id[str(cid)] = r
    return by_id, data


def paired_bootstrap_ci(
    vals_a: np.ndarray,
    vals_b: np.ndarray,
    n_resamples: int = 10000,
    seed: int = 20261128,
) -> Dict[str, float]:
    """Paired bootstrap CI for mean(vals_a - vals_b) over n captures."""
    diff = vals_a - vals_b
    n = len(diff)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_resamples, n))
    boot_means = diff[idx].mean(axis=1)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    point = float(diff.mean())
    p_two_sided = float(2.0 * min(np.mean(boot_means <= 0.0), np.mean(boot_means >= 0.0)))
    return {
        "mean_a": float(vals_a.mean()),
        "mean_b": float(vals_b.mean()),
        "delta": point,
        "ci95_lo": float(lo),
        "ci95_hi": float(hi),
        "p_two_sided": p_two_sided,
        "n_paired": int(n),
    }


def run_paired_bootstrap_suite(
    arm_a_eval: str,
    arm_b_eval: str,
    arm_c_eval: str,
    arm_c_step0_eval: Optional[str] = None,
    n_resamples: int = 10000,
) -> Dict[str, Any]:
    map_a, raw_a = _load_per_clip_map(arm_a_eval)
    map_b, raw_b = _load_per_clip_map(arm_b_eval)
    map_c, raw_c = _load_per_clip_map(arm_c_eval)

    ids_a, ids_b, ids_c = set(map_a.keys()), set(map_b.keys()), set(map_c.keys())
    if not (ids_a == ids_b == ids_c):
        raise RuntimeError(
            f"Capture ID mismatch! |A|={len(ids_a)}, |B|={len(ids_b)}, |C|={len(ids_c)}"
        )
    ordered_ids = sorted(ids_c)

    out: Dict[str, Any] = {
        "n_paired_clips": len(ordered_ids),
        "n_resamples": int(n_resamples),
        "arm_c_vs_arm_a": {},
        "arm_c_vs_arm_b": {},
        "arm_c_vs_arm_c_step0": {},
        "by_dataset": {},
    }

    for k in METRICS_COMPARE:
        va = np.array([float(map_a[cid][k]) for cid in ordered_ids], dtype=np.float64)
        vb = np.array([float(map_b[cid][k]) for cid in ordered_ids], dtype=np.float64)
        vc = np.array([float(map_c[cid][k]) for cid in ordered_ids], dtype=np.float64)
        if not (np.isfinite(va).all() and np.isfinite(vb).all() and np.isfinite(vc).all()):
            raise RuntimeError(f"Non-finite values found in metric {k!r}")
        out["arm_c_vs_arm_a"][k] = paired_bootstrap_ci(vc, va, n_resamples=n_resamples)
        out["arm_c_vs_arm_b"][k] = paired_bootstrap_ci(vc, vb, n_resamples=n_resamples)

    if arm_c_step0_eval and Path(arm_c_step0_eval).exists():
        map_c0, _ = _load_per_clip_map(arm_c_step0_eval)
        for k in METRICS_COMPARE:
            vc0 = np.array([float(map_c0[cid][k]) for cid in ordered_ids], dtype=np.float64)
            vc = np.array([float(map_c[cid][k]) for cid in ordered_ids], dtype=np.float64)
            out["arm_c_vs_arm_c_step0"][k] = paired_bootstrap_ci(vc, vc0, n_resamples=n_resamples)

    datasets = sorted({str(map_c[cid]["dataset"]) for cid in ordered_ids})
    for ds in datasets:
        ds_ids = [cid for cid in ordered_ids if str(map_c[cid]["dataset"]) == ds]
        out["by_dataset"][ds] = {
            "n_clips": len(ds_ids),
            "arm_a": {k: float(np.mean([map_a[cid][k] for cid in ds_ids])) for k in METRICS_COMPARE},
            "arm_b": {k: float(np.mean([map_b[cid][k] for cid in ds_ids])) for k in METRICS_COMPARE},
            "arm_c": {k: float(np.mean([map_c[cid][k] for cid in ds_ids])) for k in METRICS_COMPARE},
        }
        if arm_c_step0_eval and Path(arm_c_step0_eval).exists():
            map_c0, _ = _load_per_clip_map(arm_c_step0_eval)
            out["by_dataset"][ds]["arm_c_step0"] = {
                k: float(np.mean([map_c0[cid][k] for cid in ds_ids])) for k in METRICS_COMPARE
            }

    return out


@torch.no_grad()
def run_full_linear_3d_probe(
    arm_a_ckpt: str,
    arm_b_ckpt: str,
    arm_c_ckpt: str,
    max_train_clips: int = 80,
) -> Dict[str, Any]:
    """Runs held-out Linear 3D-Geometry Probe across Arm A (2k), Arm B (2k), and Arm C (trunk & bridge)."""
    from spatial_v2.data_k1_local import LocalK1CaptureDataset, collate_k1_batch
    from spatial_v2.geo_heads import unproject_depth
    from spatial_v2.stage1a_arm_c import Stage1AArmCMultiViewBridge
    from spatial_v2.stage1a_model import Stage1ACorrespondenceModel
    from spatial_v2.train_arm_c import _fit_and_eval_ridge_probe

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_ds = LocalK1CaptureDataset(
        split="train",
        num_views=16,
        grid_h=20,
        grid_w=20,
        random_subsample=False,
        load_qwen_rgb=True,
        load_da3_rgb=True,
    )
    val_ds = LocalK1CaptureDataset(
        split="val",
        num_views=16,
        grid_h=20,
        grid_w=20,
        random_subsample=False,
        load_qwen_rgb=True,
        load_da3_rgb=True,
    )
    train_indices = (
        np.linspace(0, len(train_ds) - 1, min(max_train_clips, len(train_ds)))
        .round()
        .astype(int)
        .tolist()
    )
    val_indices = list(range(len(val_ds)))

    # 1. Load Arm C checkpoint
    ckpt_c = torch.load(arm_c_ckpt, map_location=device, weights_only=False)
    arm_c = Stage1AArmCMultiViewBridge(
        trunk_mode=ckpt_c.get("trunk_mode", "last4"),
        rope_max_coord=int(ckpt_c.get("rope_max_coord", 27)),
    ).to(device)
    arm_c.load_state_dict(ckpt_c["trainable_state_dict"], strict=False)
    arm_c.eval()

    def _collect_arm_c_and_gt(ds: LocalK1CaptureDataset, indices: List[int]):
        f_trunk, f_vlm = [], []
        v_trunk, v_vlm = [], []
        y_logd, y_pcam, y_pworld, y_grav = [], [], [], []
        for idx in indices:
            batch = collate_k1_batch([ds[idx]])
            bg = {k: v.to(device, non_blocking=True) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
            out = arm_c(bg)

            valid_20 = bg["depth_valid"][0].float()
            d_gt_20 = bg["depth_gt"][0].float()
            pw_gt_20 = bg["pmap_gt"][0].float()
            eye_r = torch.eye(3, device=device, dtype=torch.float32).view(1, 1, 3, 3).expand(1, 16, 3, 3)
            zero_t = torch.zeros((1, 16, 3), device=device, dtype=torch.float32)
            pc_gt_20 = unproject_depth(
                d_gt_20.unsqueeze(0).clamp(min=1e-2), bg["K_fine"].float(), eye_r, zero_t
            )[0]

            v_den = F.avg_pool2d(valid_20.unsqueeze(1), 2, 2).squeeze(1)
            pick_10 = (v_den > 0.5).reshape(16, 100)
            v_den_safe = v_den.clamp_min(1e-6)

            d_10 = (F.avg_pool2d((d_gt_20 * valid_20).unsqueeze(1), 2, 2).squeeze(1) / v_den_safe).clamp(min=1e-2)
            pw_10 = (
                F.avg_pool2d((pw_gt_20 * valid_20.unsqueeze(-1)).permute(0, 3, 1, 2), 2, 2).permute(0, 2, 3, 1)
                / v_den_safe.unsqueeze(-1)
            )
            pc_10 = (
                F.avg_pool2d((pc_gt_20 * valid_20.unsqueeze(-1)).permute(0, 3, 1, 2), 2, 2).permute(0, 2, 3, 1)
                / v_den_safe.unsqueeze(-1)
            )

            s_20 = out.student_feats[0].float().reshape(16, 20, 20, -1).permute(0, 3, 1, 2)
            v_20 = out.vlm_tokens[0].float().reshape(16, 20, 20, -1).permute(0, 3, 1, 2)
            s_10 = F.avg_pool2d(s_20, 2, 2).permute(0, 2, 3, 1).reshape(16, 100, -1)
            v_10 = F.avg_pool2d(v_20, 2, 2).permute(0, 2, 3, 1).reshape(16, 100, -1)

            f_trunk.append(s_10[pick_10].cpu().numpy())
            f_vlm.append(v_10[pick_10].cpu().numpy())
            v_trunk.append(s_10.mean(dim=1).cpu().numpy())
            v_vlm.append(v_10.mean(dim=1).cpu().numpy())

            y_logd.append(torch.log(d_10).reshape(16, 100)[pick_10].unsqueeze(-1).cpu().numpy())
            y_pcam.append(pc_10.reshape(16, 100, 3)[pick_10].cpu().numpy())
            y_pworld.append(pw_10.reshape(16, 100, 3)[pick_10].cpu().numpy())
            y_grav.append(bg["gravity_gt"][0].float().cpu().numpy())

        return {
            "trunk_patch": np.concatenate(f_trunk, axis=0).astype(np.float64),
            "vlm_patch": np.concatenate(f_vlm, axis=0).astype(np.float64),
            "trunk_view": np.concatenate(v_trunk, axis=0).astype(np.float64),
            "vlm_view": np.concatenate(v_vlm, axis=0).astype(np.float64),
            "y_logd": np.concatenate(y_logd, axis=0).astype(np.float64),
            "y_pcam": np.concatenate(y_pcam, axis=0).astype(np.float64),
            "y_pworld": np.concatenate(y_pworld, axis=0).astype(np.float64),
            "y_grav": np.concatenate(y_grav, axis=0).astype(np.float64),
        }

    tr_c = _collect_arm_c_and_gt(train_ds, train_indices)
    va_c = _collect_arm_c_and_gt(val_ds, val_indices)
    del arm_c
    torch.cuda.empty_cache()

    def _eval_feats(x_p_tr, x_p_va, x_v_tr, x_v_va):
        pred_logd, m_logd = _fit_and_eval_ridge_probe(
            x_p_tr, tr_c["y_logd"], x_p_va, va_c["y_logd"], l2_reg=100.0
        )
        d_pred = np.exp(np.clip(pred_logd[:, 0], math.log(1e-2), math.log(100.0)))
        d_true = np.exp(va_c["y_logd"][:, 0])
        absrel = float(np.mean(np.abs(d_pred - d_true) / d_true))
        delta1 = float(np.mean(np.maximum(d_pred / d_true, d_true / d_pred) < 1.25))

        _, m_pcam = _fit_and_eval_ridge_probe(x_p_tr, tr_c["y_pcam"], x_p_va, va_c["y_pcam"], l2_reg=100.0)
        _, m_pworld = _fit_and_eval_ridge_probe(x_p_tr, tr_c["y_pworld"], x_p_va, va_c["y_pworld"], l2_reg=100.0)
        pred_grav, m_grav = _fit_and_eval_ridge_probe(x_v_tr, tr_c["y_grav"], x_v_va, va_c["y_grav"], l2_reg=50.0)
        gp = pred_grav / np.clip(np.linalg.norm(pred_grav, axis=-1, keepdims=True), 1e-6, None)
        gt = va_c["y_grav"] / np.clip(np.linalg.norm(va_c["y_grav"], axis=-1, keepdims=True), 1e-6, None)
        grav_deg = float(np.mean(np.degrees(np.arccos(np.clip(np.sum(gp * gt, axis=-1), -1.0, 1.0)))))
        return {
            "feature_dim": int(x_p_tr.shape[1]),
            "log_depth_r2": m_logd["r2"],
            "depth_absrel": absrel,
            "depth_delta1": delta1,
            "pmap_cam_r2": m_pcam["r2"],
            "pmap_cam_l2_m": m_pcam["l2_err"],
            "pmap_world_r2": m_pworld["r2"],
            "pmap_world_l2_m": m_pworld["l2_err"],
            "gravity_r2": m_grav["r2"],
            "gravity_err_deg": grav_deg,
        }

    results: Dict[str, Any] = {
        "num_train_clips": len(train_indices),
        "num_val_clips": len(val_indices),
        "num_train_patches": int(tr_c["y_logd"].shape[0]),
        "num_val_patches": int(va_c["y_logd"].shape[0]),
        "arms": {
            "arm_c_da3_multiview_trunk_3072d": _eval_feats(
                tr_c["trunk_patch"], va_c["trunk_patch"], tr_c["trunk_view"], va_c["trunk_view"]
            ),
            "arm_c_vlm_geometry_bridge_4096d": _eval_feats(
                tr_c["vlm_patch"], va_c["vlm_patch"], tr_c["vlm_view"], va_c["vlm_view"]
            ),
        },
    }

    for arm_key, arm_type, ckpt_path in [
        ("arm_a_epi_vit_step2000", "epi_vit", arm_a_ckpt),
        ("arm_b_corresp_stem_step2000", "corresp_stem", arm_b_ckpt),
    ]:
        if ckpt_path and Path(ckpt_path).exists():
            ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
            ab = Stage1ACorrespondenceModel(
                arm=arm_type,
                teacher_dim=int(ckpt.get("teacher_dim", 1536)),
                tiny=bool(ckpt.get("tiny", False)),
            ).to(device)
            sd = ckpt.get("model_state_dict") or ckpt.get("trainable_state_dict")
            ab.load_state_dict(sd, strict=False)
            ab.eval()

            def _collect_ab(ds: LocalK1CaptureDataset, indices: List[int]):
                fp, fv = [], []
                for idx in indices:
                    batch = collate_k1_batch([ds[idx]])
                    bg = {k: v.to(device, non_blocking=True) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
                    out = ab(
                        bg[ab.rgb_key()],
                        timestamps=bg["timestamps"],
                        view_mask=bg["view_mask"],
                    )
                    valid_20 = bg["depth_valid"][0].float()
                    v_den = F.avg_pool2d(valid_20.unsqueeze(1), 2, 2).squeeze(1)
                    pick_10 = (v_den > 0.5).reshape(16, 100)
                    sf = out.student_tap_flat[0].float()  # [16, 100, D]
                    fp.append(sf[pick_10].cpu().numpy())
                    fv.append(sf.mean(dim=1).cpu().numpy())
                return (
                    np.concatenate(fp, axis=0).astype(np.float64),
                    np.concatenate(fv, axis=0).astype(np.float64),
                )

            p_tr, v_tr = _collect_ab(train_ds, train_indices)
            p_va, v_va = _collect_ab(val_ds, val_indices)
            results["arms"][arm_key] = _eval_feats(p_tr, p_va, v_tr, v_va)
            results["arms"][arm_key]["checkpoint"] = str(ckpt_path)
            del ab
            torch.cuda.empty_cache()

    return results


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm-a-eval", required=True)
    p.add_argument("--arm-b-eval", required=True)
    p.add_argument("--arm-c-eval", required=True)
    p.add_argument("--arm-c-step0-eval", default="")
    p.add_argument("--arm-a-ckpt", default="")
    p.add_argument("--arm-b-ckpt", default="")
    p.add_argument("--arm-c-ckpt", default="")
    p.add_argument("--out-json", required=True)
    p.add_argument("--run-probe", action="store_true")
    args = p.parse_args()

    res: Dict[str, Any] = {
        "bootstrap": run_paired_bootstrap_suite(
            arm_a_eval=args.arm_a_eval,
            arm_b_eval=args.arm_b_eval,
            arm_c_eval=args.arm_c_eval,
            arm_c_step0_eval=args.arm_c_step0_eval or None,
        )
    }
    if args.run_probe and args.arm_c_ckpt:
        res["linear_3d_probe"] = run_full_linear_3d_probe(
            arm_a_ckpt=args.arm_a_ckpt,
            arm_b_ckpt=args.arm_b_ckpt,
            arm_c_ckpt=args.arm_c_ckpt,
        )
    Path(args.out_json).write_text(json.dumps(res, indent=2))
    print(f"Wrote {args.out_json}", flush=True)


if __name__ == "__main__":
    main()
