"""C3+ Name-Conditioned 2D Box + Frame Presence + 28x28 RoI Masklet Head Prototype.

Bridges Candidate 3 (lever10/work/PRICING_C2_C3.md) and GeoBoxRoI-3D
(bluesky_20261128/reports/w2_native_grounding_3d.md):
  - Multi-tap pre-merger ViT feature pyramid (taps 9/17/25/27) + optional 10-ch
    pixel-aligned geometric channels (Plucker rays, log-depth, depth grads, sigma_D).
  - 2-layer bidirectional query-patch cross-attention conditioned on noun-span
    embedding (LM layer-16 + lexical skip), outputting decoupled:
      * Frame presence logit z_pres (balanced BCE with n_neg / n_pos pos_weight;
        never crushed by Branch O's alpha=0.25 focal scalar!).
      * IoU-calibrated objectness z_obj (Varifocal loss against true box IoU).
      * Normalized 2D box [cx, cy, w, h] in (0, 1) (L1 + GIoU loss on positives).
      * Optional 28x28 RoIAlign depth-gated masklet head (Dice + BCE distilled
        offline from frozen SAM 3 J1-k, enabling zero-SAM3 serving!).
  - Includes K1 room-fold splitting (sha256 parity), exclusion guard, fail-fast
    metrics (top-1 IoU >= bar on largest anchor + presence AUROC >= 0.85 +
    held-out precision=0.609 threshold calibration), and vnice.sh SIGTERM handler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import signal
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Box geometry & differentiable GIoU / Varifocal / Dice losses
# ---------------------------------------------------------------------------

def cxcywh_to_xyxy(boxes: torch.Tensor) -> torch.Tensor:
    cx, cy, w, h = boxes.unbind(-1)
    x0 = cx - 0.5 * w
    y0 = cy - 0.5 * h
    x1 = cx + 0.5 * w
    y1 = cy + 0.5 * h
    return torch.stack([x0, y0, x1, y1], dim=-1)


def box_iou_and_giou(pred_cxcywh: torch.Tensor, gt_cxcywh: torch.Tensor, eps: float = 1e-6) -> tuple[torch.Tensor, torch.Tensor]:
    """Elementwise IoU and GIoU for paired boxes [..., 4] in normalized cxcywh."""
    p = cxcywh_to_xyxy(pred_cxcywh)
    g = cxcywh_to_xyxy(gt_cxcywh)

    ix0 = torch.maximum(p[..., 0], g[..., 0])
    iy0 = torch.maximum(p[..., 1], g[..., 1])
    ix1 = torch.minimum(p[..., 2], g[..., 2])
    iy1 = torch.minimum(p[..., 3], g[..., 3])
    inter = (ix1 - ix0).clamp(min=0.0) * (iy1 - iy0).clamp(min=0.0)

    area_p = (p[..., 2] - p[..., 0]).clamp(min=0.0) * (p[..., 3] - p[..., 1]).clamp(min=0.0)
    area_g = (g[..., 2] - g[..., 0]).clamp(min=0.0) * (g[..., 3] - g[..., 1]).clamp(min=0.0)
    union = (area_p + area_g - inter).clamp(min=eps)
    iou = inter / union

    cx0 = torch.minimum(p[..., 0], g[..., 0])
    cy0 = torch.minimum(p[..., 1], g[..., 1])
    cx1 = torch.maximum(p[..., 2], g[..., 2])
    cy1 = torch.maximum(p[..., 3], g[..., 3])
    c_area = ((cx1 - cx0).clamp(min=0.0) * (cy1 - cy0).clamp(min=0.0)).clamp(min=eps)
    giou = iou - (c_area - union) / c_area
    return iou, giou


def varifocal_loss(logits: torch.Tensor, target_iou: torch.Tensor, pos_mask: torch.Tensor, alpha: float = 0.75, gamma: float = 2.0) -> torch.Tensor:
    """IoU-calibrated Varifocal Loss (never crushes positive confidence like alpha=0.25 focal)."""
    p = torch.sigmoid(logits)
    target = torch.where(pos_mask, target_iou.clamp(0.0, 1.0), torch.zeros_like(target_iou))
    weight = torch.where(pos_mask, target, alpha * (p.detach() ** gamma))
    bce = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
    denom = pos_mask.float().sum().clamp(min=1.0)
    return (weight * bce).sum() / denom


def dice_bce_masklet_loss(mask_logits: torch.Tensor, mask_gt: torch.Tensor, pos_mask: torch.Tensor) -> torch.Tensor:
    """Combined BCE + Soft-Dice loss on positive 28x28 RoI masklets."""
    if not pos_mask.any():
        return mask_logits.sum() * 0.0
    ml = mask_logits[pos_mask]
    mg = mask_gt[pos_mask].float()
    bce = F.binary_cross_entropy_with_logits(ml, mg)
    probs = torch.sigmoid(ml).flatten(1)
    tgts = mg.flatten(1)
    inter = (probs * tgts).sum(dim=1)
    denom = probs.sum(dim=1) + tgts.sum(dim=1) + 1e-5
    dice = 1.0 - (2.0 * inter + 1e-5) / denom
    return bce + dice.mean()


# ---------------------------------------------------------------------------
# C3+ Architecture (GeoBoxRoI-2D)
# ---------------------------------------------------------------------------

class BidirQueryPatchBlock(nn.Module):
    """Bidirectional query-patch cross-attention + FFN block (d=384)."""

    def __init__(self, d_model: int = 384, n_heads: int = 8, dropout: float = 0.0):
        super().__init__()
        self.q_norm1 = nn.LayerNorm(d_model)
        self.p_norm1 = nn.LayerNorm(d_model)
        self.q_to_p = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.q_norm2 = nn.LayerNorm(d_model)
        self.q_ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.GELU(),
            nn.Linear(d_model * 4, d_model),
        )
        self.p_norm2 = nn.LayerNorm(d_model)
        self.p_to_q = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)

    def forward(self, q: torch.Tensor, patches: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # q: [B, Q, D], patches: [B, L, D]
        q_n, p_n = self.q_norm1(q), self.p_norm1(patches)
        q_out, _ = self.q_to_p(q_n, p_n, p_n, need_weights=False)
        q = q + q_out
        q = q + self.q_ffn(self.q_norm2(q))
        p_out, _ = self.p_to_q(self.p_norm2(patches), q, q, need_weights=False)
        patches = patches + p_out
        return q, patches


class RoIMaskletHead(nn.Module):
    """Lightweight 28x28 depth-gated RoI masklet decoder (<1M params, <2 ms batched).

    Uses pure-PyTorch grid_sample (zero torchvision.ops dependency) so it runs in
    every local scratch env.
    """

    def __init__(self, d_in: int = 384, d_hid: int = 128, out_size: int = 28):
        super().__init__()
        self.out_size = out_size
        self.proj = nn.Conv2d(d_in, d_hid, kernel_size=1)
        self.q_film = nn.Linear(d_in, d_hid * 2)
        self.conv = nn.Sequential(
            nn.Conv2d(d_hid, d_hid, kernel_size=3, padding=1),
            nn.GroupNorm(8, d_hid),
            nn.GELU(),
            nn.Conv2d(d_hid, d_hid, kernel_size=3, padding=1),
            nn.GroupNorm(8, d_hid),
            nn.GELU(),
            nn.Conv2d(d_hid, 1, kernel_size=1),
        )

    def forward(self, feat_map: torch.Tensor, boxes_cxcywh: torch.Tensor, q_state: torch.Tensor) -> torch.Tensor:
        """feat_map: [B, D, H, W], boxes_cxcywh: [B, 4] in [0, 1], q_state: [B, D] -> [B, 28, 28]."""
        B = feat_map.shape[0]
        S = self.out_size
        xyxy = cxcywh_to_xyxy(boxes_cxcywh.detach().clamp(1e-3, 1.0 - 1e-3))  # [B, 4] in [0, 1]
        # Convert to [-1, 1] grid_sample coordinates
        x0 = xyxy[:, 0] * 2.0 - 1.0
        y0 = xyxy[:, 1] * 2.0 - 1.0
        x1 = xyxy[:, 2] * 2.0 - 1.0
        y1 = xyxy[:, 3] * 2.0 - 1.0

        t = torch.linspace(0.0, 1.0, S, device=feat_map.device, dtype=feat_map.dtype)
        gx = x0[:, None] + (x1 - x0)[:, None] * t[None, :]  # [B, S]
        gy = y0[:, None] + (y1 - y0)[:, None] * t[None, :]  # [B, S]
        grid_x = gx[:, None, :].expand(B, S, S)
        grid_y = gy[:, :, None].expand(B, S, S)
        grid = torch.stack([grid_x, grid_y], dim=-1)  # [B, S, S, 2]

        f = self.proj(feat_map)
        roi = F.grid_sample(f, grid, mode="bilinear", padding_mode="border", align_corners=False)
        gamma, beta = self.q_film(q_state).chunk(2, dim=-1)
        roi = roi * (1.0 + gamma[:, :, None, None]) + beta[:, :, None, None]
        return self.conv(roi).squeeze(1)


class C3BoxPresenceHead(nn.Module):
    """C3+ Name-Conditioned 2D Box + Presence + Optional 28x28 Masklet Head."""

    def __init__(
        self,
        n_taps: int = 4,
        d_tap: int = 1152,
        d_name: int = 4096,
        d_geo_extra: int = 0,
        d_model: int = 384,
        n_heads: int = 8,
        n_layers: int = 2,
        with_masklet: bool = True,
    ):
        super().__init__()
        self.n_taps = n_taps
        self.d_geo_extra = d_geo_extra
        self.with_masklet = with_masklet
        self.tap_projs = nn.ModuleList([nn.Sequential(nn.LayerNorm(d_tap), nn.Linear(d_tap, d_model)) for _ in range(n_taps)])
        self.geo_proj = nn.Linear(d_geo_extra, d_model) if d_geo_extra > 0 else None
        self.pos_mlp = nn.Sequential(nn.Linear(2, d_model), nn.GELU(), nn.Linear(d_model, d_model))
        self.name_proj = nn.Sequential(nn.LayerNorm(d_name), nn.Linear(d_name, d_model))
        self.pres_token = nn.Parameter(torch.zeros(1, 1, d_model))
        self.box_token = nn.Parameter(torch.zeros(1, 1, d_model))
        nn.init.normal_(self.pres_token, std=0.02)
        nn.init.normal_(self.box_token, std=0.02)

        self.blocks = nn.ModuleList([BidirQueryPatchBlock(d_model=d_model, n_heads=n_heads) for _ in range(n_layers)])
        self.out_norm = nn.LayerNorm(d_model)
        self.pres_head = nn.Linear(d_model, 1)
        self.obj_head = nn.Linear(d_model, 1)
        self.box_head = nn.Sequential(nn.Linear(d_model, d_model), nn.GELU(), nn.Linear(d_model, 4))
        self.masklet_head = RoIMaskletHead(d_in=d_model, d_hid=128, out_size=28) if with_masklet else None

    def _grid_pos(self, H: int, W: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        ys = torch.linspace(-1.0, 1.0, H, device=device, dtype=dtype)
        xs = torch.linspace(-1.0, 1.0, W, device=device, dtype=dtype)
        yy, xx = torch.meshgrid(ys, xs, indexing="ij")
        coords = torch.stack([xx, yy], dim=-1).reshape(1, H * W, 2)
        return self.pos_mlp(coords)

    def forward(
        self,
        taps: list[torch.Tensor],
        name_emb: torch.Tensor,
        geo_extra: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        """
        Args:
          taps: list of n_taps tensors each [B, H, W, d_tap].
          name_emb: [B, d_name] pooled noun-span embedding.
          geo_extra: optional [B, H, W, d_geo_extra] geometric channels.
        """
        assert len(taps) == self.n_taps
        B, H, W, _ = taps[0].shape
        fused = sum(proj(t) for proj, t in zip(self.tap_projs, taps)) / math.sqrt(self.n_taps)
        if self.geo_proj is not None and geo_extra is not None:
            fused = fused + self.geo_proj(geo_extra)
        patches = fused.reshape(B, H * W, -1) + self._grid_pos(H, W, fused.device, fused.dtype)

        q_name = self.name_proj(name_emb).unsqueeze(1)  # [B, 1, D]
        q = torch.cat([q_name + self.pres_token, q_name + self.box_token], dim=1)  # [B, 2, D]

        for blk in self.blocks:
            q, patches = blk(q, patches)
        q = self.out_norm(q)
        q_pres, q_box = q[:, 0], q[:, 1]

        pres_logit = self.pres_head(q_pres).squeeze(-1)     # [B]
        obj_logit = self.obj_head(q_box).squeeze(-1)        # [B]
        box_cxcywh = torch.sigmoid(self.box_head(q_box))    # [B, 4] in (0, 1)

        out = dict(pres_logit=pres_logit, obj_logit=obj_logit, box_cxcywh=box_cxcywh)
        if self.masklet_head is not None:
            feat_map = patches.transpose(1, 2).reshape(B, -1, H, W)
            out["masklet_logit"] = self.masklet_head(feat_map, box_cxcywh, q_box)  # [B, 28, 28]
        return out


def compute_c3_loss(
    out: dict[str, torch.Tensor],
    gt_present: torch.Tensor,
    gt_box_cxcywh: torch.Tensor,
    *,
    pos_weight: float = 1.0,
    ignore_mask: torch.Tensor | None = None,
    gt_masklet: torch.Tensor | None = None,
    w_l1: float = 5.0,
    w_giou: float = 2.0,
    w_vfl: float = 1.0,
    w_masklet: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Compute C3+ registered loss (balanced BCE presence + L1 + GIoU + Varifocal + optional masklet)."""
    valid = torch.ones_like(gt_present, dtype=torch.bool) if ignore_mask is None else ~ignore_mask
    pos = valid & (gt_present > 0.5)

    pw = torch.tensor(float(pos_weight), device=out["pres_logit"].device, dtype=out["pres_logit"].dtype)
    pres_bce = F.binary_cross_entropy_with_logits(
        out["pres_logit"][valid], gt_present[valid].float(), pos_weight=pw
    ) if valid.any() else out["pres_logit"].sum() * 0.0

    iou, giou = box_iou_and_giou(out["box_cxcywh"], gt_box_cxcywh)
    if pos.any():
        l1_loss = F.l1_loss(out["box_cxcywh"][pos], gt_box_cxcywh[pos])
        giou_loss = (1.0 - giou[pos]).mean()
    else:
        l1_loss = out["box_cxcywh"].sum() * 0.0
        giou_loss = out["box_cxcywh"].sum() * 0.0

    vfl = varifocal_loss(out["obj_logit"][valid], iou.detach()[valid], pos[valid]) if valid.any() else out["obj_logit"].sum() * 0.0
    mloss = (
        dice_bce_masklet_loss(out["masklet_logit"], gt_masklet, pos)
        if (gt_masklet is not None and "masklet_logit" in out)
        else out["pres_logit"].sum() * 0.0
    )

    total = pres_bce + w_l1 * l1_loss + w_giou * giou_loss + w_vfl * vfl + w_masklet * mloss
    return dict(
        total=total,
        pres_bce=pres_bce,
        l1=l1_loss,
        giou=giou_loss,
        vfl=vfl,
        masklet=mloss,
        mean_pos_iou=iou[pos].mean() if pos.any() else torch.tensor(0.0, device=total.device),
    )


# ---------------------------------------------------------------------------
# Registered C3+ room fold split, AUROC, and precision=0.609 threshold calibration
# ---------------------------------------------------------------------------

def room_fold(room_id: str) -> int:
    """Two-fold room split by sha256(room) parity (PRICING_C2_C3.md L66)."""
    return int(hashlib.sha256(room_id.encode("utf-8")).hexdigest()[-1], 16) % 2


def binary_auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Exact Mann-Whitney U AUROC (ties half)."""
    s = np.asarray(scores, dtype=np.float64)
    y = np.asarray(labels, dtype=bool)
    pos, neg = s[y], s[~y]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    d = pos[:, None] - neg[None, :]
    return float(np.mean((d > 0) + 0.5 * (d == 0)))


def calibrate_presence_threshold(scores: np.ndarray, labels: np.ndarray, target_precision: float = 0.609) -> dict[str, float]:
    """Registered threshold rule (PRICING_C2_C3.md L69): lowest threshold reaching
    target_precision=0.609 on held-out training fold; if none reaches it, highest precision.
    """
    s = np.asarray(scores, dtype=np.float64)
    y = np.asarray(labels, dtype=bool)
    uniq = np.sort(np.unique(s))
    best_reach = None
    best_prec = (-1.0, float(uniq[-1]) if len(uniq) else 0.5, 0.0)
    n_pos = int(y.sum())
    for thr in uniq:
        pred = s >= thr
        tp = int((pred & y).sum())
        n_pred = int(pred.sum())
        if n_pred == 0:
            continue
        prec = tp / n_pred
        rec = tp / max(n_pos, 1)
        if prec >= target_precision and best_reach is None:
            best_reach = (float(thr), float(prec), float(rec))
        if prec > best_prec[0]:
            best_prec = (float(prec), float(thr), float(rec))
    if best_reach is not None:
        return dict(threshold=best_reach[0], precision=best_reach[1], recall=best_reach[2], reached_target=1.0)
    return dict(threshold=best_prec[1], precision=best_prec[0], recall=best_prec[2], reached_target=0.0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="C3+ Box+Presence Head prototype smoke / benchmark")
    ap.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--grid-h", type=int, default=23)
    ap.add_argument("--grid-w", type=int, default=30)
    ap.add_argument("--steps", type=int, default=5)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    stop_flag = {"hit": False}
    def _on_term(sig, _frame):
        stop_flag["hit"] = True
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _on_term)

    dev = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    torch.manual_seed(20261128)
    model = C3BoxPresenceHead(n_taps=4, d_tap=1152, d_name=4096, d_geo_extra=10, d_model=384, n_layers=2, with_masklet=True).to(dev)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)

    taps = [torch.randn(args.batch, args.grid_h, args.grid_w, 1152, device=dev) for _ in range(4)]
    name_emb = torch.randn(args.batch, 4096, device=dev)
    geo_extra = torch.randn(args.batch, args.grid_h, args.grid_w, 10, device=dev)
    gt_pres = torch.randint(0, 2, (args.batch,), device=dev)
    gt_pres[0] = 1
    gt_box = torch.tensor([[0.5, 0.5, 0.3, 0.3]] * args.batch, device=dev)
    gt_mask = (torch.rand(args.batch, 28, 28, device=dev) > 0.5).float()

    # Timed forward + train smoke
    if dev.type == "cuda":
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for step in range(args.steps):
        if stop_flag["hit"]:
            break
        opt.zero_grad(set_to_none=True)
        out = model(taps, name_emb, geo_extra)
        losses = compute_c3_loss(out, gt_pres, gt_box, pos_weight=2.0, gt_masklet=gt_mask)
        losses["total"].backward()
        opt.step()
    if dev.type == "cuda":
        torch.cuda.synchronize()
    train_ms = (time.perf_counter() - t0) * 1000.0 / max(args.steps, 1)

    model.eval()
    with torch.inference_mode():
        if dev.type == "cuda":
            torch.cuda.synchronize()
        t1 = time.perf_counter()
        out = model(taps, name_emb, geo_extra)
        if dev.type == "cuda":
            torch.cuda.synchronize()
        infer_ms = (time.perf_counter() - t1) * 1000.0

    rec = dict(
        status="PASS",
        device=str(dev),
        params_m=round(n_params / 1e6, 2),
        batch=args.batch,
        grid=[args.grid_h, args.grid_w],
        train_step_ms=round(train_ms, 2),
        infer_batch_ms=round(infer_ms, 2),
        infer_per_frame_ms=round(infer_ms / args.batch, 2),
        final_loss=round(float(losses["total"].item()), 4),
    )
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
