"""Held-out Stage-1A geometric evaluator (rotation, trans-dir, metric/SI AbsRel, gravity, FoV).

Evaluates strictly on the leakage-verified held-out K1 validation split (53 captures, 50 rooms,
0 overlap with train / R0 / dev-S1 / BENCH v2 / withheld-80) with per-dataset breakdown.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import torch
from torch.utils.data import DataLoader

from .data_k1_local import (
    DEFAULT_EXCL_DIR,
    DEFAULT_FRAMES_ROOT,
    DEFAULT_MANIFEST_PATH,
    LocalK1CaptureDataset,
    collate_k1_batch,
)
from .geo_heads import so3_log
from .stage1a_model import (
    DEFAULT_DA3_CKPT,
    DEFAULT_QWEN_VISUAL_CKPT,
    ArmType,
    Stage1ACorrespondenceModel,
)


def compute_clip_geometry_metrics(
    rot_pred: torch.Tensor,
    trans_pred: torch.Tensor,
    depth_pred: torch.Tensor,
    gravity_pred: torch.Tensor,
    log_fx_w_pred: torch.Tensor,
    rot_gt: torch.Tensor,
    trans_gt: torch.Tensor,
    depth_gt: torch.Tensor,
    depth_valid: torch.Tensor,
    gravity_gt: torch.Tensor,
    log_fx_w_gt: torch.Tensor,
    view_mask: Optional[torch.Tensor] = None,
    min_baseline_m: float = 0.05,
) -> Dict[str, float]:
    """Compute exact held-out geometric error metrics for a single multi-view clip [N, ...]."""
    rp = rot_pred.detach().float().cpu()
    tp = trans_pred.detach().float().cpu()
    dp = depth_pred.detach().float().cpu()
    gp = torch.nn.functional.normalize(gravity_pred.detach().float().cpu(), dim=-1, eps=1e-7)
    fp = log_fx_w_pred.detach().float().cpu()

    rg = rot_gt.detach().float().cpu()
    tg = trans_gt.detach().float().cpu()
    dg = depth_gt.detach().float().cpu()
    dv = depth_valid.detach().bool().cpu() & (dg > 1e-4)
    gg = torch.nn.functional.normalize(gravity_gt.detach().float().cpu(), dim=-1, eps=1e-7)
    fg = log_fx_w_gt.detach().float().cpu()

    n_views = rp.shape[0]
    vm = torch.ones(n_views, dtype=torch.bool) if view_mask is None else view_mask.detach().bool().cpu()

    # 1. Pairwise relative rotation & translation direction errors
    idx_i, idx_j = torch.triu_indices(n_views, n_views, offset=1)
    pair_valid = vm[idx_i] & vm[idx_j]

    rot_errs_deg: List[float] = []
    trans_dir_errs_deg: List[float] = []
    if pair_valid.any():
        ii = idx_i[pair_valid]
        jj = idx_j[pair_valid]

        r_ij_p = rp[jj] @ rp[ii].transpose(-1, -2)
        t_ij_p = tp[jj] - (r_ij_p @ tp[ii].unsqueeze(-1)).squeeze(-1)
        r_ij_g = rg[jj] @ rg[ii].transpose(-1, -2)
        t_ij_g = tg[jj] - (r_ij_g @ tg[ii].unsqueeze(-1)).squeeze(-1)

        w_err = so3_log(r_ij_g.transpose(-1, -2) @ r_ij_p)
        ang_deg = w_err.norm(dim=-1) * (180.0 / math.pi)
        rot_errs_deg = ang_deg.tolist()

        g_norm = t_ij_g.norm(dim=-1)
        p_norm = t_ij_p.norm(dim=-1)
        has_b = g_norm > min_baseline_m
        if has_b.any():
            u_g = t_ij_g[has_b] / g_norm[has_b].unsqueeze(-1)
            u_p = t_ij_p[has_b] / p_norm[has_b].clamp_min(1e-7).unsqueeze(-1)
            cos_t = (u_g * u_p).sum(dim=-1).clamp(-1.0, 1.0)
            t_deg = torch.acos(cos_t) * (180.0 / math.pi)
            trans_dir_errs_deg = t_deg.tolist()

    # 2. Metric depth AbsRel, scale-invariant AbsRel, delta < 1.25, median scale ratio
    dv_eff = dv & vm[:, None, None]
    if dv_eff.any():
        d_p_v = dp[dv_eff].clamp_min(1e-4)
        d_g_v = dg[dv_eff].clamp_min(1e-4)
        absrel = float(((d_p_v - d_g_v).abs() / d_g_v).mean().item())
        ratio = d_p_v / d_g_v
        scale_ratio = float(torch.median(ratio).item())
        s_align = float(torch.median(d_g_v / d_p_v).item())
        si_absrel = float(((d_p_v * s_align - d_g_v).abs() / d_g_v).mean().item())
        thresh = torch.maximum(ratio, 1.0 / ratio.clamp_min(1e-6))
        delta1 = float((thresh < 1.25).float().mean().item())
    else:
        absrel = float("nan")
        si_absrel = float("nan")
        delta1 = float("nan")
        scale_ratio = float("nan")

    # 3. Gravity & FoV errors
    if vm.any():
        g_cos = (gp[vm] * gg[vm]).sum(dim=-1).clamp(-1.0, 1.0)
        grav_err = float((torch.acos(g_cos) * (180.0 / math.pi)).mean().item())
        fx_p = torch.exp(fp[vm])
        fx_g = torch.exp(fg[vm])
        fov_err_pct = float(((fx_p - fx_g).abs() / fx_g.clamp_min(1e-6)).mean().item() * 100.0)
    else:
        grav_err = float("nan")
        fov_err_pct = float("nan")

    rot_arr = np.asarray(rot_errs_deg, dtype=np.float64)
    td_arr = np.asarray(trans_dir_errs_deg, dtype=np.float64)
    return {
        "rot_med_deg": float(np.median(rot_arr)) if rot_arr.size else float("nan"),
        "rot_mean_deg": float(np.mean(rot_arr)) if rot_arr.size else float("nan"),
        "rot_acc_5deg": float(np.mean(rot_arr < 5.0)) if rot_arr.size else float("nan"),
        "rot_acc_15deg": float(np.mean(rot_arr < 15.0)) if rot_arr.size else float("nan"),
        "trans_dir_med_deg": float(np.median(td_arr)) if td_arr.size else float("nan"),
        "trans_dir_mean_deg": float(np.mean(td_arr)) if td_arr.size else float("nan"),
        "trans_acc_15deg": float(np.mean(td_arr < 15.0)) if td_arr.size else float("nan"),
        "absrel": absrel,
        "si_absrel": si_absrel,
        "delta1": delta1,
        "scale_ratio": scale_ratio,
        "gravity_err_deg": grav_err,
        "fov_rel_err_pct": fov_err_pct,
    }


def _aggregate_metrics(rows: Sequence[Dict[str, object]]) -> Dict[str, float]:
    keys = (
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
    out: Dict[str, float] = {"num_captures": float(len(rows))}
    for k in keys:
        vals = [float(r[k]) for r in rows if k in r and math.isfinite(float(r[k]))]
        out[k] = float(np.mean(vals)) if vals else float("nan")
        if k in ("rot_med_deg", "trans_dir_med_deg", "absrel"):
            out[f"{k}_median_over_clips"] = float(np.median(vals)) if vals else float("nan")
    return out


@torch.no_grad()
def evaluate_stage1a_model(
    model: Stage1ACorrespondenceModel,
    val_loader: DataLoader,
    device: torch.device,
    amp_dtype: torch.dtype = torch.bfloat16,
    max_samples: Optional[int] = None,
) -> Dict[str, object]:
    """Evaluate a Stage1ACorrespondenceModel on held-out K1 captures."""
    was_training = model.training
    model.eval()
    rgb_key = model.rgb_key()

    t0 = time.monotonic()
    per_capture: List[Dict[str, object]] = []
    seen = 0

    for batch in val_loader:
        rgb = batch[rgb_key].to(device, non_blocking=True)
        timestamps = batch["timestamps"].to(device, non_blocking=True)
        view_mask = batch["view_mask"].to(device, non_blocking=True)

        use_amp = device.type == "cuda" and amp_dtype != torch.float32
        with torch.amp.autocast(device_type=device.type, dtype=amp_dtype, enabled=use_amp):
            out = model(rgb, timestamps=timestamps, view_mask=view_mask)

        bsz = rgb.shape[0]
        for b in range(bsz):
            m = compute_clip_geometry_metrics(
                rot_pred=out.pose_out.rot[b],
                trans_pred=out.pose_out.trans[b],
                depth_pred=out.depth_out.depth[b],
                gravity_pred=out.pose_out.gravity[b],
                log_fx_w_pred=out.pose_out.log_fx_w[b],
                rot_gt=batch["rot_gt"][b],
                trans_gt=batch["trans_gt"][b],
                depth_gt=batch["depth_gt"][b],
                depth_valid=batch["depth_valid"][b],
                gravity_gt=batch["gravity_gt"][b],
                log_fx_w_gt=batch["log_fx_w_gt"][b],
                view_mask=batch["view_mask"][b],
            )
            m["capture_id"] = batch["capture_id"][b]
            m["room_id"] = batch["room_id"][b]
            m["dataset"] = batch["dataset"][b]
            per_capture.append(m)
            seen += 1
            if max_samples is not None and seen >= max_samples:
                break
        if max_samples is not None and seen >= max_samples:
            break

    elapsed = time.monotonic() - t0
    if was_training:
        model.train()

    by_dataset: Dict[str, Dict[str, float]] = {}
    for ds in sorted({str(r["dataset"]) for r in per_capture}):
        by_dataset[ds] = _aggregate_metrics([r for r in per_capture if r["dataset"] == ds])

    return {
        "arm": model.arm,
        "overall": _aggregate_metrics(per_capture),
        "by_dataset": by_dataset,
        "eval_seconds": round(elapsed, 2),
        "per_capture": per_capture,
    }


def format_eval_summary(res: Dict[str, object]) -> str:
    ov = res["overall"]
    lines = [
        f"[Eval arm={res['arm']}] n={int(ov['num_captures'])} ({res['eval_seconds']:.1f}s) | "
        f"Rot med={ov['rot_med_deg']:.2f}deg (<5={ov['rot_acc_5deg']*100:.1f}%, <15={ov['rot_acc_15deg']*100:.1f}%) | "
        f"TransDir med={ov['trans_dir_med_deg']:.2f}deg (<15={ov['trans_acc_15deg']*100:.1f}%) | "
        f"AbsRel={ov['absrel']:.4f} (SI={ov['si_absrel']:.4f}, d1={ov['delta1']*100:.1f}%, scale={ov['scale_ratio']:.3f}) | "
        f"Grav={ov['gravity_err_deg']:.2f}deg | FoV={ov['fov_rel_err_pct']:.1f}%"
    ]
    for ds, m in res.get("by_dataset", {}).items():
        lines.append(
            f"  - {ds:12s} (n={int(m['num_captures']):2d}): "
            f"Rot={m['rot_med_deg']:.2f}deg, TransDir={m['trans_dir_med_deg']:.2f}deg, "
            f"AbsRel={m['absrel']:.4f}, SI-AbsRel={m['si_absrel']:.4f}, d1={m['delta1']*100:.1f}%"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate KT-6 Stage-1A checkpoint on held-out K1 rooms.")
    ap.add_argument("--checkpoint", type=str, required=True)
    ap.add_argument("--arm", type=str, choices=("epi_vit", "corresp_stem"), default=None)
    ap.add_argument("--num-views", type=int, default=8)
    ap.add_argument("--grid-h", type=int, default=20)
    ap.add_argument("--grid-w", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--max-samples", type=int, default=None)
    ap.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST_PATH)
    ap.add_argument("--frames-root", type=str, default=DEFAULT_FRAMES_ROOT)
    ap.add_argument("--excl-dir", type=str, default=DEFAULT_EXCL_DIR)
    ap.add_argument("--qwen-ckpt", type=str, default=DEFAULT_QWEN_VISUAL_CKPT)
    ap.add_argument("--da3-ckpt", type=str, default=DEFAULT_DA3_CKPT)
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    arm: ArmType = args.arm or ckpt.get("arm", "epi_vit")
    teacher_dim = int(ckpt.get("teacher_dim", 3072))
    tiny = bool(ckpt.get("tiny", False))

    model = Stage1ACorrespondenceModel(
        arm=arm,
        teacher_dim=teacher_dim,
        qwen_ckpt=None,
        da3_ckpt=None,
        freeze_backbone=False,
        gradient_checkpointing=False,
        tiny=tiny,
    )
    model.load_state_dict(ckpt["model_state_dict"], strict=True)
    device = torch.device(args.device)
    amp_dtype = torch.bfloat16 if device.type == "cuda" else torch.float32
    model = model.to(device)

    val_ds = LocalK1CaptureDataset(
        split="val",
        num_views=args.num_views,
        grid_h=args.grid_h,
        grid_w=args.grid_w,
        manifest_path=args.manifest,
        frames_root=args.frames_root,
        excl_dir=args.excl_dir,
        load_qwen_rgb=(arm == "epi_vit"),
        load_da3_rgb=(arm == "corresp_stem"),
        max_captures=args.max_samples,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
        collate_fn=collate_k1_batch,
    )

    res = evaluate_stage1a_model(model, val_loader, device=device, amp_dtype=amp_dtype, max_samples=args.max_samples)
    res["checkpoint"] = str(Path(args.checkpoint).resolve())
    res["split_summary"] = val_ds.split_summary
    print(format_eval_summary(res), flush=True)

    if args.out:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(res, indent=2) + "\n")
        print(f"Saved held-out eval metrics -> {out_p}", flush=True)


if __name__ == "__main__":
    main()
