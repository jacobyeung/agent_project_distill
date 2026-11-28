"""KT-6 Stage-1A Arm C Trainer, Evaluator & Linear 3D-Geometry Probe (`train_arm_c.py`).

Incorporates all 3 Codex Astra `GO_AFTER_FIXES` items (`codex_recheck_spatial_v2.md`):
  1. Passes `pmap_valid = batch["depth_valid"]` into `SpatialV2CompositeLoss` so invalid depth
     pixels zeroed in `pmap_gt` are excluded from `PoseAnd4DLoss` pointmap denominators.
  2. Uses a dedicated seeded `torch.Generator` for `DataLoader` shuffling plus a
     `(seed, epoch, capture_idx)`-keyed deterministic view sampler (`DeterministicEpochK1Dataset`)
     so training order and view subsampling are invariant to model-init RNG draw counts.
  3. Reports exact finite denominators (`num_valid`, `num_total`, `num_failed`) for every
     evaluation metric and fails explicitly if any primary metric is non-finite.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from spatial_v2.config import LossWeightsConfig, SpatialForcing2Config
from spatial_v2.data_k1_local import (
    DEFAULT_MANIFEST_PATH,
    LocalK1CaptureDataset,
    collate_k1_batch,
)
from spatial_v2.eval_stage1a import compute_clip_geometry_metrics
from spatial_v2.geo_heads import unproject_depth
from spatial_v2.losses import SpatialV2CompositeLoss
from spatial_v2.stage1a_arm_c import DEFAULT_DA3_DIR, Stage1AArmCMultiViewBridge

PRIMARY_METRIC_KEYS: Tuple[str, ...] = (
    "rot_med_deg",
    "rot_mean_deg",
    "rot_acc_5deg",
    "rot_acc_15deg",
    "trans_dir_med_deg",
    "trans_dir_mean_deg",
    "trans_acc_15deg",
    "absrel",
    "si_absrel",
    "delta1",
    "scale_ratio",
    "gravity_err_deg",
    "fov_rel_err_pct",
)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class DeterministicEpochK1Dataset(Dataset):
    """Wraps LocalK1CaptureDataset with `(seed, epoch, capture_idx)`-keyed view sampling (Codex Fix 2)."""

    def __init__(
        self,
        base_ds: LocalK1CaptureDataset,
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.base = base_ds
        self.seed = int(seed)
        self.epoch = 0

    @property
    def split_sha256(self) -> str:
        return str(self.base.split_summary["split_sha256"])

    @property
    def records(self):
        return self.base.records

    def set_epoch(self, epoch: int) -> None:
        self.epoch = int(epoch)

    def __len__(self) -> int:
        return len(self.base.records)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        # Codex Fix 2: re-seed local RNG deterministically from (seed, epoch, capture_idx)
        # before each item load so view subsampling never depends on worker order or prior draws.
        self.base.rng = np.random.default_rng([self.seed, self.epoch, int(idx)])
        return self.base[idx]


def _aggregate_metrics_strict(
    records: List[Dict[str, Any]],
    fail_on_nan: bool = True,
) -> Dict[str, Any]:
    """Aggregates per-clip metrics with explicit finite denominators (Codex Fix 3)."""
    if not records:
        raise RuntimeError("Evaluation received 0 clip records")

    num_total = len(records)
    keys = [k for k in records[0].keys() if isinstance(records[0][k], (int, float))]
    out: Dict[str, Any] = {
        "num_clips_total": int(num_total),
        "metric_denominators": {},
    }

    for k in keys:
        raw_vals = [float(r[k]) for r in records]
        finite_vals = [v for v in raw_vals if math.isfinite(v)]
        num_valid = len(finite_vals)
        num_failed = num_total - num_valid

        out["metric_denominators"][k] = {
            "num_valid": int(num_valid),
            "num_total": int(num_total),
            "num_failed": int(num_failed),
        }
        if fail_on_nan and k in PRIMARY_METRIC_KEYS and num_failed > 0:
            raise RuntimeError(
                f"Metric {k!r} had {num_failed}/{num_total} non-finite clip evaluations!"
            )

        out[k] = float(np.mean(finite_vals)) if finite_vals else float("nan")
        if k in ("rot_med_deg", "trans_dir_med_deg", "absrel", "gravity_err_deg", "fov_rel_err_pct"):
            out[f"{k}_median_over_clips"] = float(np.median(finite_vals)) if finite_vals else float("nan")

    return out


@torch.no_grad()
def evaluate_arm_c_model(
    model: Stage1AArmCMultiViewBridge,
    val_loader: DataLoader,
    device: torch.device,
    fail_on_nan: bool = True,
) -> Dict[str, Any]:
    """Runs K1-heldout (n=53) evaluation with strict denominator tracking and latency profiling."""
    model.eval()
    all_records: List[Dict[str, Any]] = []
    by_dataset: Dict[str, List[Dict[str, Any]]] = {}
    clip_times_ms: List[float] = []
    bridge_times_ms: List[float] = []

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    t_start = time.perf_counter()
    for batch in val_loader:
        batch_gpu: Dict[str, Any] = {}
        for k, v in batch.items():
            batch_gpu[k] = v.to(device, non_blocking=True) if isinstance(v, torch.Tensor) else v

        if device.type == "cuda":
            torch.cuda.synchronize(device)
        t0 = time.perf_counter()
        out = model(batch_gpu)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        t1 = time.perf_counter()

        # Also time VLMGeometryBridge isolated latency
        bsz, n_views, h2, w2, _ = out.pmap_pred.shape
        eye_r = torch.eye(3, device=device, dtype=torch.float32).view(1, 1, 3, 3).expand(bsz, n_views, 3, 3)
        zero_t = torch.zeros((bsz, n_views, 3), device=device, dtype=torch.float32)
        pmap_cam = unproject_depth(out.depth_out.depth, out.K_pred_fine, eye_r, zero_t)
        plucker_fine = F.interpolate(
            out.plucker_pred.permute(0, 1, 4, 2, 3).reshape(bsz * n_views, 6, *out.plucker_pred.shape[2:4]),
            size=(h2, w2),
            mode="bilinear",
            align_corners=False,
        ).reshape(bsz, n_views, 6, h2, w2).permute(0, 1, 3, 4, 2)

        if device.type == "cuda":
            torch.cuda.synchronize(device)
        tb0 = time.perf_counter()
        _ = model.vlm_bridge(
            patch_tokens=out.student_feats,
            pmap_world=out.pmap_pred,
            pmap_cam=pmap_cam,
            plucker_fine=plucker_fine,
            log_depth=out.depth_out.log_depth,
            sigma_depth=out.depth_out.sigma_depth,
            gravity=out.pose_out.gravity,
        )
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        tb1 = time.perf_counter()

        clip_times_ms.append((t1 - t0) * 1000.0 / max(1, bsz))
        bridge_times_ms.append((tb1 - tb0) * 1000.0 / max(1, bsz))

        for b in range(bsz):
            rec = compute_clip_geometry_metrics(
                rot_pred=out.pose_out.rot_canon[b],
                trans_pred=out.pose_out.trans_canon[b],
                depth_pred=out.depth_out.depth[b],
                gravity_pred=out.pose_out.gravity[b],
                log_fx_w_pred=out.pose_out.log_fx_w[b],
                rot_gt=batch_gpu["rot_gt"][b],
                trans_gt=batch_gpu["trans_gt"][b],
                depth_gt=batch_gpu["depth_gt"][b],
                depth_valid=batch_gpu["depth_valid"][b],
                gravity_gt=batch_gpu["gravity_gt"][b],
                log_fx_w_gt=batch_gpu["log_fx_w_gt"][b],
                view_mask=batch_gpu["view_mask"][b],
            )
            rec["capture_id"] = batch["capture_id"][b]
            ds_name = batch["dataset"][b]
            rec["dataset"] = ds_name
            all_records.append(rec)
            by_dataset.setdefault(ds_name, []).append(rec)

    elapsed = time.perf_counter() - t_start
    overall = _aggregate_metrics_strict(all_records, fail_on_nan=fail_on_nan)
    dataset_summary = {
        ds: _aggregate_metrics_strict(recs, fail_on_nan=fail_on_nan)
        for ds, recs in sorted(by_dataset.items())
    }
    peak_mem_gb = (
        float(torch.cuda.max_memory_allocated(device) / (1024 ** 3))
        if device.type == "cuda"
        else 0.0
    )

    return {
        "num_clips": len(all_records),
        "elapsed_sec": float(elapsed),
        "ms_per_clip": float(np.mean(clip_times_ms)) if clip_times_ms else 0.0,
        "vlm_bridge_ms_per_clip": float(np.mean(bridge_times_ms)) if bridge_times_ms else 0.0,
        "peak_vram_gb": peak_mem_gb,
        "overall": overall,
        "by_dataset": dataset_summary,
        "per_clip": all_records,
    }


def compute_vlm_bridge_linear_3d_loss(
    out,
    batch: Dict[str, torch.Tensor],
) -> torch.Tensor:
    """Supervises `vlm_linear_3d_pred` (`[B, N, P, 10]`) directly against GT 3D geometry."""
    pred = out.vlm_linear_3d_pred.float()  # [B, N, P, 10]: [pmap_world(3), pmap_cam(3), log_d(1), grav(3)]
    bsz, n_views, n_patches, _ = pred.shape

    valid = batch["depth_valid"].bool().reshape(bsz, n_views, n_patches)
    valid_f = valid.float()
    denom = valid_f.sum().clamp(min=1.0)

    pmap_w_gt = batch["pmap_gt"].float().reshape(bsz, n_views, n_patches, 3)
    eye_r = torch.eye(3, device=pred.device, dtype=torch.float32).view(1, 1, 3, 3).expand(bsz, n_views, 3, 3)
    zero_t = torch.zeros((bsz, n_views, 3), device=pred.device, dtype=torch.float32)
    pmap_c_gt = unproject_depth(
        batch["depth_gt"].float().clamp(min=1e-2),
        batch["K_fine"].float(),
        eye_r,
        zero_t,
    ).reshape(bsz, n_views, n_patches, 3)

    log_d_gt = torch.log(batch["depth_gt"].float().clamp(min=1e-2, max=100.0)).reshape(bsz, n_views, n_patches, 1)
    grav_gt = F.normalize(batch["gravity_gt"].float(), dim=-1, eps=1e-6).unsqueeze(2).expand(bsz, n_views, n_patches, 3)

    loss_pw = (
        F.smooth_l1_loss(pred[..., 0:3], pmap_w_gt, reduction="none").mean(dim=-1) * valid_f
    ).sum() / denom
    loss_pc = (
        F.smooth_l1_loss(pred[..., 3:6], pmap_c_gt, reduction="none").mean(dim=-1) * valid_f
    ).sum() / denom
    loss_ld = (
        F.smooth_l1_loss(pred[..., 6:7], log_d_gt, reduction="none").squeeze(-1) * valid_f
    ).sum() / denom
    loss_gv = (1.0 - F.cosine_similarity(pred[..., 7:10], grav_gt, dim=-1)).mean()

    return loss_pw + loss_pc + 0.5 * loss_ld + 0.5 * loss_gv


def _fit_and_eval_ridge_probe(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    l2_reg: float = 1e2,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Fits closed-form ridge regression W = (X^T X + lambda I)^{-1} X^T Y and evaluates on val."""
    n_tr, d_feat = x_train.shape
    x_tr_aug = np.concatenate([x_train, np.ones((n_tr, 1), dtype=np.float64)], axis=1)
    x_va_aug = np.concatenate([x_val, np.ones((x_val.shape[0], 1), dtype=np.float64)], axis=1)

    xtx = x_tr_aug.T @ x_tr_aug
    reg = np.eye(d_feat + 1, dtype=np.float64) * float(l2_reg)
    reg[-1, -1] = 1e-4
    w = np.linalg.solve(xtx + reg, x_tr_aug.T @ y_train)
    y_pred = x_va_aug @ w

    ss_res = np.sum((y_val - y_pred) ** 2, axis=0)
    ss_tot = np.sum((y_val - np.mean(y_val, axis=0, keepdims=True)) ** 2, axis=0) + 1e-12
    r2 = float(np.mean(1.0 - ss_res / ss_tot))
    rmse = float(np.sqrt(np.mean((y_val - y_pred) ** 2)))
    l2_err = float(np.mean(np.linalg.norm(y_val - y_pred, axis=-1)))
    return y_pred, {"r2": r2, "rmse": rmse, "l2_err": l2_err}


@torch.no_grad()
def run_linear_3d_geometry_probe(
    arm_c_model: Stage1AArmCMultiViewBridge,
    manifest_path: str,
    device: torch.device,
    arm_a_ckpt: Optional[str] = None,
    arm_b_ckpt: Optional[str] = None,
    max_train_clips: int = 80,
) -> Dict[str, Any]:
    """Runs linear 3D-geometry probe on Arm C vs Arm A and Arm B tokens on K1-heldout (n=53)."""
    from spatial_v2.stage1a_model import Stage1ACorrespondenceModel

    train_ds = LocalK1CaptureDataset(
        manifest_path=manifest_path,
        split="train",
        num_views=16,
        grid_h=20,
        grid_w=20,
        random_subsample=False,
        load_qwen_rgb=True,
        load_da3_rgb=True,
    )
    val_ds = LocalK1CaptureDataset(
        manifest_path=manifest_path,
        split="val",
        num_views=16,
        grid_h=20,
        grid_w=20,
        random_subsample=False,
        load_qwen_rgb=True,
        load_da3_rgb=True,
    )

    train_indices = np.linspace(0, len(train_ds) - 1, min(max_train_clips, len(train_ds))).round().astype(int).tolist()
    val_indices = list(range(len(val_ds)))

    def _collect_targets_and_arm_c(ds: LocalK1CaptureDataset, indices: List[int]):
        feats_trunk, feats_vlm = [], []
        y_logd, y_pcam, y_pworld = [], [], []
        v_feats_trunk, v_feats_vlm, y_grav = [], [], []

        arm_c_model.eval()
        for idx in indices:
            item = ds[idx]
            batch = collate_k1_batch([item])
            batch_gpu = {
                k: v.to(device, non_blocking=True) if isinstance(v, torch.Tensor) else v
                for k, v in batch.items()
            }
            out = arm_c_model(batch_gpu)

            # Pool 20x20 valid depth & 3D coordinates to 10x10 (100 tokens/view) so Arm A/B (100 tokens/view)
            # and Arm C (400 -> 100 tokens/view) are evaluated on the exact same 10x10 patch grid!
            valid_20 = batch_gpu["depth_valid"][0].float()       # [16, 20, 20]
            d_gt_20 = batch_gpu["depth_gt"][0].float()           # [16, 20, 20]
            pw_gt_20 = batch_gpu["pmap_gt"][0].float()           # [16, 20, 20, 3]
            eye_r = torch.eye(3, device=device, dtype=torch.float32).view(1, 1, 3, 3).expand(1, 16, 3, 3)
            zero_t = torch.zeros((1, 16, 3), device=device, dtype=torch.float32)
            pc_gt_20 = unproject_depth(
                d_gt_20.unsqueeze(0).clamp(min=1e-2),
                batch_gpu["K_fine"].float(),
                eye_r,
                zero_t,
            )[0]  # [16, 20, 20, 3]

            # Masked average pool 20x20 -> 10x10
            v_den = F.avg_pool2d(valid_20.unsqueeze(1), kernel_size=2, stride=2).squeeze(1)  # [16, 10, 10]
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

            # Pool Arm C 20x20 tokens -> 10x10 tokens for exact spatial alignment
            s_20 = out.student_feats[0].float().reshape(16, 20, 20, -1).permute(0, 3, 1, 2)
            v_20 = out.vlm_tokens[0].float().reshape(16, 20, 20, -1).permute(0, 3, 1, 2)
            s_10 = F.avg_pool2d(s_20, 2, 2).permute(0, 2, 3, 1).reshape(16, 100, -1)
            v_10 = F.avg_pool2d(v_20, 2, 2).permute(0, 2, 3, 1).reshape(16, 100, -1)

            feats_trunk.append(s_10[pick_10].cpu().numpy())
            feats_vlm.append(v_10[pick_10].cpu().numpy())
            y_logd.append(torch.log(d_10).reshape(16, 100)[pick_10].unsqueeze(-1).cpu().numpy())
            y_pcam.append(pc_10.reshape(16, 100, 3)[pick_10].cpu().numpy())
            y_pworld.append(pw_10.reshape(16, 100, 3)[pick_10].cpu().numpy())

            v_feats_trunk.append(s_10.mean(dim=1).cpu().numpy())
            v_feats_vlm.append(v_10.mean(dim=1).cpu().numpy())
            y_grav.append(batch_gpu["gravity_gt"][0].float().cpu().numpy())

        return {
            "trunk_patch": np.concatenate(feats_trunk, axis=0).astype(np.float64),
            "vlm_patch": np.concatenate(feats_vlm, axis=0).astype(np.float64),
            "trunk_view": np.concatenate(v_feats_trunk, axis=0).astype(np.float64),
            "vlm_view": np.concatenate(v_feats_vlm, axis=0).astype(np.float64),
            "y_logd": np.concatenate(y_logd, axis=0).astype(np.float64),
            "y_pcam": np.concatenate(y_pcam, axis=0).astype(np.float64),
            "y_pworld": np.concatenate(y_pworld, axis=0).astype(np.float64),
            "y_grav": np.concatenate(y_grav, axis=0).astype(np.float64),
        }

    tr_c = _collect_targets_and_arm_c(train_ds, train_indices)
    va_c = _collect_targets_and_arm_c(val_ds, val_indices)

    def _evaluate_feature_set(
        x_patch_tr: np.ndarray,
        x_patch_va: np.ndarray,
        x_view_tr: np.ndarray,
        x_view_va: np.ndarray,
    ) -> Dict[str, Any]:
        pred_logd, m_logd = _fit_and_eval_ridge_probe(
            x_patch_tr, tr_c["y_logd"], x_patch_va, va_c["y_logd"], l2_reg=100.0
        )
        d_pred = np.exp(np.clip(pred_logd[:, 0], math.log(1e-2), math.log(100.0)))
        d_true = np.exp(va_c["y_logd"][:, 0])
        absrel = float(np.mean(np.abs(d_pred - d_true) / d_true))
        ratio = np.maximum(d_pred / d_true, d_true / d_pred)
        delta1 = float(np.mean(ratio < 1.25))

        _, m_pcam = _fit_and_eval_ridge_probe(
            x_patch_tr, tr_c["y_pcam"], x_patch_va, va_c["y_pcam"], l2_reg=100.0
        )
        _, m_pworld = _fit_and_eval_ridge_probe(
            x_patch_tr, tr_c["y_pworld"], x_patch_va, va_c["y_pworld"], l2_reg=100.0
        )
        pred_grav, m_grav = _fit_and_eval_ridge_probe(
            x_view_tr, tr_c["y_grav"], x_view_va, va_c["y_grav"], l2_reg=50.0
        )
        g_pred_norm = pred_grav / np.clip(np.linalg.norm(pred_grav, axis=-1, keepdims=True), 1e-6, None)
        g_true_norm = va_c["y_grav"] / np.clip(np.linalg.norm(va_c["y_grav"], axis=-1, keepdims=True), 1e-6, None)
        grav_deg = float(
            np.mean(np.degrees(np.arccos(np.clip(np.sum(g_pred_norm * g_true_norm, axis=-1), -1.0, 1.0))))
        )

        return {
            "feature_dim": int(x_patch_tr.shape[1]),
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
        "arms": {},
    }

    results["arms"]["arm_c_da3_multiview_trunk_3072d"] = _evaluate_feature_set(
        tr_c["trunk_patch"], va_c["trunk_patch"], tr_c["trunk_view"], va_c["trunk_view"]
    )
    results["arms"]["arm_c_vlm_geometry_bridge_4096d"] = _evaluate_feature_set(
        tr_c["vlm_patch"], va_c["vlm_patch"], tr_c["vlm_view"], va_c["vlm_view"]
    )

    for arm_key, arm_type, ckpt_path in [
        ("arm_a_epi_vit", "epi_vit", arm_a_ckpt),
        ("arm_b_corresp_stem", "corresp_stem", arm_b_ckpt),
    ]:
        if ckpt_path and Path(ckpt_path).exists():
            ab_model = Stage1ACorrespondenceModel(
                arm=arm_type,
                grid_h=20,
                grid_w=20,
            ).to(device)
            ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
            if "trainable_state_dict" in ckpt:
                ab_model.load_state_dict(ckpt["trainable_state_dict"], strict=False)
            ab_model.eval()

            def _collect_ab(ds: LocalK1CaptureDataset, indices: List[int]):
                f_patch, f_view = [], []
                for idx in indices:
                    item = ds[idx]
                    batch = collate_k1_batch([item])
                    batch_gpu = {
                        k: v.to(device, non_blocking=True) if isinstance(v, torch.Tensor) else v
                        for k, v in batch.items()
                    }
                    out = ab_model(batch_gpu)
                    valid_20 = batch_gpu["depth_valid"][0].float()
                    v_den = F.avg_pool2d(valid_20.unsqueeze(1), kernel_size=2, stride=2).squeeze(1)
                    pick_10 = (v_den > 0.5).reshape(16, 100)
                    sf = out.student_tap_flat[0].float()  # [16, 100, 4096]
                    f_patch.append(sf[pick_10].cpu().numpy())
                    f_view.append(sf.mean(dim=1).cpu().numpy())
                return (
                    np.concatenate(f_patch, axis=0).astype(np.float64),
                    np.concatenate(f_view, axis=0).astype(np.float64),
                )

            p_tr, v_tr = _collect_ab(train_ds, train_indices)
            p_va, v_va = _collect_ab(val_ds, val_indices)
            results["arms"][arm_key] = _evaluate_feature_set(p_tr, p_va, v_tr, v_va)
            results["arms"][arm_key]["checkpoint"] = str(ckpt_path)
            del ab_model
            torch.cuda.empty_cache()

    return results


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="KT-6 Stage-1A Arm C Trainer & Evaluator")
    p.add_argument("--trunk-mode", type=str, choices=["last4", "lora16", "frozen"], default="last4")
    p.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST_PATH)
    p.add_argument("--da3-dir", type=str, default=DEFAULT_DA3_DIR)
    p.add_argument("--out-dir", type=str, required=True)
    p.add_argument("--num-views", type=int, default=16)
    p.add_argument("--grid-size", type=int, default=20)
    p.add_argument("--rope-max-coord", type=int, default=27)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=4)
    p.add_argument("--max-steps", type=int, default=1000)
    p.add_argument("--eval-every", type=int, default=250)
    p.add_argument("--save-every", type=int, default=500)
    p.add_argument("--log-every", type=int, default=10)
    p.add_argument("--trunk-lr", type=float, default=5e-6)
    p.add_argument("--head-lr", type=float, default=2e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--warmup-steps", type=int, default=50)
    p.add_argument("--max-grad-norm", type=float, default=1.0)
    p.add_argument("--w-bridge-3d", type=float, default=0.5)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--eval-only", action="store_true")
    p.add_argument("--run-linear-probe", action="store_true")
    p.add_argument(
        "--arm-a-ckpt",
        type=str,
        default="/scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_s1a_arm_a_v1/ckpt_latest.pt",
    )
    p.add_argument(
        "--arm-b-ckpt",
        type=str,
        default="/scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_s1a_arm_b_v1/ckpt_latest.pt",
    )
    p.add_argument("--allow-partial-eval", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    seed_everything(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "train_log.jsonl"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    base_train_ds = LocalK1CaptureDataset(
        manifest_path=args.manifest,
        split="train",
        num_views=args.num_views,
        grid_h=args.grid_size,
        grid_w=args.grid_size,
        random_subsample=True,
        seed=args.seed,
        load_qwen_rgb=False,
        load_da3_rgb=True,
    )
    base_val_ds = LocalK1CaptureDataset(
        manifest_path=args.manifest,
        split="val",
        num_views=args.num_views,
        grid_h=args.grid_size,
        grid_w=args.grid_size,
        random_subsample=False,
        seed=args.seed,
        load_qwen_rgb=False,
        load_da3_rgb=True,
    )
    train_ds = DeterministicEpochK1Dataset(base_train_ds, seed=args.seed)
    val_ds = DeterministicEpochK1Dataset(base_val_ds, seed=args.seed)

    val_loader = DataLoader(
        val_ds,
        batch_size=1,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_k1_batch,
        pin_memory=True,
    )

    model = Stage1AArmCMultiViewBridge(
        da3_dir=args.da3_dir,
        trunk_mode=args.trunk_mode,
        grid_hw=(args.grid_size, args.grid_size),
        rope_max_coord=args.rope_max_coord,
    ).to(device)

    param_info = model.parameter_Breakdown()
    meta = {
        "arm": "da3_multiview_bridge",
        "trunk_mode": args.trunk_mode,
        "rope_max_coord": args.rope_max_coord,
        "split_sha256": val_ds.split_sha256,
        "train_captures": len(train_ds),
        "val_captures": len(val_ds),
        **param_info,
        "codex_fixes": [
            "pmap_valid=depth_valid passed into SpatialV2CompositeLoss",
            "DeterministicEpochK1Dataset + seeded torch.Generator for DataLoader",
            "Explicit finite denominators (num_valid/num_total/num_failed) on every eval metric",
        ],
        "args": vars(args),
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2))
    print(
        f"[Arm C Init] mode={args.trunk_mode} | total={param_info['total_params']/1e6:.2f}M | "
        f"trainable={param_info['trainable_params']/1e6:.2f}M "
        f"(trunk={param_info['trunk_trainable_params']/1e6:.2f}M, "
        f"heads={param_info['geo_heads_trainable_params']/1e6:.2f}M, "
        f"bridge={param_info['vlm_bridge_trainable_params']/1e6:.2f}M) | "
        f"train={len(train_ds)} | val={len(val_ds)} (sha256={val_ds.split_sha256[:12]})",
        flush=True,
    )

    print("[Arm C] Running Step-0 zero-shot evaluation on K1-heldout (n=53)...", flush=True)
    eval0 = evaluate_arm_c_model(
        model, val_loader, device, fail_on_nan=not args.allow_partial_eval
    )
    (out_dir / "eval_step_000000.json").write_text(json.dumps(eval0, indent=2))
    ov0 = eval0["overall"]
    print(
        f"[Eval step=0] rot_med={ov0['rot_med_deg']:.2f} deg "
        f"(med_clip={ov0['rot_med_deg_median_over_clips']:.2f} deg, "
        f"<5={ov0['rot_acc_5deg']*100:.1f}%, <15={ov0['rot_acc_15deg']*100:.1f}%) | "
        f"trans_med={ov0['trans_dir_med_deg']:.2f} deg (<15={ov0['trans_acc_15deg']*100:.1f}%) | "
        f"absrel={ov0['absrel']:.4f} | si_absrel={ov0['si_absrel']:.4f} | "
        f"delta1={ov0['delta1']*100:.1f}% | scale={ov0['scale_ratio']:.3f} | "
        f"grav={ov0['gravity_err_deg']:.2f} deg | fov_err={ov0['fov_rel_err_pct']:.2f}% | "
        f"latency={eval0['ms_per_clip']:.1f} ms/clip (bridge={eval0['vlm_bridge_ms_per_clip']:.2f} ms) | "
        f"vram={eval0['peak_vram_gb']:.2f} GiB",
        flush=True,
    )

    if args.eval_only:
        if args.run_linear_probe:
            probe_res = run_linear_3d_geometry_probe(
                arm_c_model=model,
                manifest_path=args.manifest,
                device=device,
                arm_a_ckpt=args.arm_a_ckpt,
                arm_b_ckpt=args.arm_b_ckpt,
            )
            (out_dir / "linear_3d_probe.json").write_text(json.dumps(probe_res, indent=2))
        return

    sf2_cfg = SpatialForcing2Config(tap_layers=(16,), teacher_dim=3072, probe_hidden_dim=1024)
    w_cfg = LossWeightsConfig()
    criterion = SpatialV2CompositeLoss(sf2_cfg=sf2_cfg, weights_cfg=w_cfg, lm_hidden_size=3072).to(device)

    trunk_params = [
        p
        for n, p in model.named_parameters()
        if p.requires_grad and (n.startswith("da3.backbone") or n.startswith("da3.cam_dec"))
    ]
    head_params = [
        p
        for n, p in model.named_parameters()
        if p.requires_grad and not (n.startswith("da3.backbone") or n.startswith("da3.cam_dec"))
    ] + [p for p in criterion.parameters() if p.requires_grad]

    param_groups = [
        {"params": head_params, "lr": args.head_lr, "name": "heads_and_bridge"},
    ]
    if trunk_params:
        param_groups.append({"params": trunk_params, "lr": args.trunk_lr, "name": "da3_multiview_trunk"})

    optimizer = torch.optim.AdamW(param_groups, weight_decay=args.weight_decay)

    def lr_scale(step: int) -> float:
        if step < args.warmup_steps:
            return float(step + 1) / float(max(1, args.warmup_steps))
        prog = float(step - args.warmup_steps) / float(max(1, args.max_steps - args.warmup_steps))
        return 0.1 + 0.9 * 0.5 * (1.0 + math.cos(math.pi * min(1.0, prog)))

    model.train()
    model.da3_metric.eval()
    model.da3.head.eval()
    model.frozen_tail_blocks.eval()

    optimizer.zero_grad(set_to_none=True)
    step = 0
    micro_step = 0
    epoch = 0
    t_interval = time.perf_counter()

    while step < args.max_steps:
        train_ds.set_epoch(epoch)
        # Codex Fix 2: dedicated seeded torch.Generator for DataLoader shuffle
        loader_gen = torch.Generator()
        loader_gen.manual_seed(args.seed + epoch * 10007)
        train_loader = DataLoader(
            train_ds,
            batch_size=args.batch_size,
            shuffle=True,
            num_workers=args.num_workers,
            collate_fn=collate_k1_batch,
            pin_memory=True,
            drop_last=True,
            generator=loader_gen,
        )

        for batch in train_loader:
            if step >= args.max_steps:
                break

            batch_gpu: Dict[str, Any] = {}
            for k, v in batch.items():
                batch_gpu[k] = v.to(device, non_blocking=True) if isinstance(v, torch.Tensor) else v

            out = model(batch_gpu)

            valid_mask = batch_gpu["depth_valid"].unsqueeze(-1)
            pmap_pred_masked = torch.where(valid_mask, out.pmap_pred, torch.zeros_like(out.pmap_pred))
            pmap_gt_masked = torch.where(valid_mask, batch_gpu["pmap_gt"], torch.zeros_like(batch_gpu["pmap_gt"]))

            # Codex Fix 1: pass depth_valid as pmap_valid into SpatialV2CompositeLoss
            targets = {
                "depth_gt": batch_gpu["depth_gt"],
                "depth_valid": batch_gpu["depth_valid"],
                "pmap_valid": batch_gpu["depth_valid"],
                "metric_scale_locked": batch_gpu["metric_scale_locked"],
                "rot_gt": batch_gpu["rot_gt"],
                "trans_gt": batch_gpu["trans_gt"],
                "gravity_gt": batch_gpu["gravity_gt"],
                "log_fx_w_gt": batch_gpu["log_fx_w_gt"],
                "log_fy_h_gt": batch_gpu["log_fy_h_gt"],
                "plucker_gt": batch_gpu["plucker_gt"],
                "pmap_gt": pmap_gt_masked,
            }
            comp_loss, loss_dict = criterion(
                student_taps={16: out.student_feats},
                teacher_feats=out.teacher_feats,
                depth_out=out.depth_out,
                pose_out=out.pose_out,
                targets=targets,
                pmap_pred=pmap_pred_masked,
                view_mask=batch_gpu["view_mask"],
            )
            bridge_3d_loss = compute_vlm_bridge_linear_3d_loss(out, batch_gpu)
            total_loss = comp_loss + args.w_bridge_3d * bridge_3d_loss

            (total_loss / float(args.grad_accum)).backward()
            micro_step += 1

            if micro_step % args.grad_accum == 0:
                scale = lr_scale(step)
                for pg in optimizer.param_groups:
                    base_lr = args.trunk_lr if pg["name"] == "da3_multiview_trunk" else args.head_lr
                    pg["lr"] = base_lr * scale

                all_trainable = trunk_params + head_params
                grad_norm = torch.nn.utils.clip_grad_norm_(all_trainable, args.max_grad_norm)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                step += 1

                if step % args.log_every == 0 or step == 1:
                    dt = time.perf_counter() - t_interval
                    t_interval = time.perf_counter()
                    rec = {
                        "step": step,
                        "epoch": epoch,
                        "lr_head": float(optimizer.param_groups[0]["lr"]),
                        "lr_trunk": float(optimizer.param_groups[-1]["lr"]) if trunk_params else 0.0,
                        "grad_norm": float(grad_norm.item() if isinstance(grad_norm, torch.Tensor) else grad_norm),
                        "sec_per_step": dt / float(args.log_every if step > 1 else 1),
                        "loss_total": float(total_loss.detach().item()),
                        "loss_bridge_3d": float(bridge_3d_loss.detach().item()),
                        **{k: float(v.detach().item()) for k, v in loss_dict.items()},
                    }
                    with open(log_path, "a") as f:
                        f.write(json.dumps(rec) + "\n")
                    print(
                        f"[ArmC|{args.trunk_mode}] step={step}/{args.max_steps} "
                        f"loss={rec['loss_total']:.4f} (depth={rec.get('depth_total', 0.0):.3f} "
                        f"pose={rec.get('pose', 0.0):.3f} pmap={rec.get('pmap', 0.0):.3f} "
                        f"grav={rec.get('gravity', 0.0):.3f} fov={rec.get('fov', 0.0):.3f} "
                        f"bridge3d={rec['loss_bridge_3d']:.3f}) "
                        f"gnorm={rec['grad_norm']:.2f} ({rec['sec_per_step']:.2f}s/step)",
                        flush=True,
                    )

                if step % args.eval_every == 0 or step == args.max_steps:
                    eval_res = evaluate_arm_c_model(
                        model, val_loader, device, fail_on_nan=not args.allow_partial_eval
                    )
                    eval_file = out_dir / f"eval_step_{step:06d}.json"
                    eval_file.write_text(json.dumps(eval_res, indent=2))
                    ov = eval_res["overall"]
                    print(
                        f"[Eval step={step}] rot_med={ov['rot_med_deg']:.2f} deg "
                        f"(med_clip={ov['rot_med_deg_median_over_clips']:.2f} deg, "
                        f"<5={ov['rot_acc_5deg']*100:.1f}%, <15={ov['rot_acc_15deg']*100:.1f}%) | "
                        f"trans_med={ov['trans_dir_med_deg']:.2f} deg (<15={ov['trans_acc_15deg']*100:.1f}%) | "
                        f"absrel={ov['absrel']:.4f} | si_absrel={ov['si_absrel']:.4f} | "
                        f"delta1={ov['delta1']*100:.1f}% | scale={ov['scale_ratio']:.3f} | "
                        f"grav={ov0['gravity_err_deg']:.2f}->{ov['gravity_err_deg']:.2f} deg | "
                        f"fov_err={ov0['fov_rel_err_pct']:.2f}%->{ov['fov_rel_err_pct']:.2f}%",
                        flush=True,
                    )
                    trainable_sd = {
                        k: v.detach().cpu()
                        for k, v in model.state_dict().items()
                        if any(
                            k.startswith(pfx)
                            for pfx in (
                                "pose_head",
                                "depth_head",
                                "vlm_bridge",
                                "da3.cam_dec",
                                "da3.backbone.pretrained.norm",
                                "da3.backbone.pretrained.blocks.36",
                                "da3.backbone.pretrained.blocks.37",
                                "da3.backbone.pretrained.blocks.38",
                                "da3.backbone.pretrained.blocks.39",
                            )
                        )
                        or "lora_" in k
                    }
                    ckpt_payload = {
                        "step": step,
                        "trunk_mode": args.trunk_mode,
                        "rope_max_coord": args.rope_max_coord,
                        "trainable_state_dict": trainable_sd,
                        "eval_overall": ov,
                    }
                    torch.save(ckpt_payload, out_dir / "ckpt_latest.pt")
                    if step % args.save_every == 0 or step == args.max_steps:
                        torch.save(ckpt_payload, out_dir / f"ckpt_step_{step:06d}.pt")
                    model.train()
                    model.da3_metric.eval()
                    model.da3.head.eval()
                    model.frozen_tail_blocks.eval()

        epoch += 1

    if args.run_linear_probe:
        print("[Arm C] Running Linear 3D-Geometry Probe across Arm C vs Arm A & Arm B...", flush=True)
        probe_res = run_linear_3d_geometry_probe(
            arm_c_model=model,
            manifest_path=args.manifest,
            device=device,
            arm_a_ckpt=args.arm_a_ckpt,
            arm_b_ckpt=args.arm_b_ckpt,
        )
        (out_dir / "linear_3d_probe.json").write_text(json.dumps(probe_res, indent=2))
        for arm_name, m in probe_res["arms"].items():
            print(
                f"[Linear3DProbe|{arm_name} (d={m['feature_dim']})] "
                f"P_world R2={m['pmap_world_r2']:.3f} (L2={m['pmap_world_l2_m']:.3f}m) | "
                f"P_cam R2={m['pmap_cam_r2']:.3f} (L2={m['pmap_cam_l2_m']:.3f}m) | "
                f"logD R2={m['log_depth_r2']:.3f} (AbsRel={m['depth_absrel']:.3f}, d1={m['depth_delta1']*100:.1f}%) | "
                f"Grav R2={m['gravity_r2']:.3f} ({m['gravity_err_deg']:.2f} deg)",
                flush=True,
            )


if __name__ == "__main__":
    main()
