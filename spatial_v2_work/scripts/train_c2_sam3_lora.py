"""KT-4 Grounding Breaker: C2 SAM 3 Native-Res (1008x1008) Detector/Presence LoRA Pilot.

Trains and evaluates a rank-16 LoRA adapter on SAM 3's vision-text fusion encoder and
query decoder attention projections plus trainable presence and dot-product scoring heads,
keeping the vision backbone (1008x1008 ViT + FPN), text backbone (VETextEncoder),
geometry encoder, and mask decoder (UniversalSegmentationHead) 100% frozen.

Hard guarantees:
  1. Zero room leakage enforced at startup via RoomExclusionGuard from
     /scratch/jjyeung/orch_home_distill/spatial_v2/data_k1_local.py (233 clean K1 train
     captures / 214 physical rooms; 0 overlap with DEV-MASK 117 [46 captures / 35 rooms],
     K1-heldout [53 captures / 50 rooms], dev-S1, R0-dev, BENCH v2, withheld-80).
  2. Evaluated at Step 0 (frozen SAM 3 baseline), Step 250, Step 500, and Step 1000 on:
     - K1-heldout (53 captures / 50 rooms): frame-level presence AUROC, <1% small-object
       box recall (IoU >= 0.50 / 0.70), overall box IoU >= 0.70 recall, empty-frame FP rate.
     - Paired DEV-MASK 117 (117 items / 46 captures / 35 rooms, 10,000-draw room bootstrap,
       seed 20261120):
         * C2-h1 (registered FT-h1 rule: top-1 proposal per frame with joint >= 0.05, score >= 0.30)
         * C2-h1-cal (calibrated presence/joint threshold selected strictly on K1-heldout)
         * C2-h0 (per-frame pool oracle at mask IoU >= 0.50 against GT mask e)
         * C2-box-k (C2 predicted tight box fed into frozen SAM 3 box_detect k path)
       all paired against baseline a (55.81), frozen h1 (43.85), frozen h0 (43.50),
       J1-k (66.84, +11.03), and GT ceiling e (69.57, +13.76).
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils import parametrize
from PIL import Image

# Ensure local scipy and SAM 3 source are on sys.path (100% local /scratch, 0 NFS IO)
PYEXTRA = Path("/scratch/jjyeung/orch_n30/lever8/j1/pyextra")
SAM3_SRC = Path("/scratch/jjyeung/b01ec87a6f29b/d/s/sam3")
ORCH_HOME = Path("/scratch/jjyeung/orch_home_distill")
J1_KIT = Path("/scratch/jjyeung/orch_n30/lever8/j1/kit")

for p in (PYEXTRA, SAM3_SRC, ORCH_HOME, J1_KIT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from spatial_v2.data_k1_local import RoomExclusionGuard, build_clean_k1_splits, canonical_room_keys
import j1_common as G
import select_j1 as S
import detect as D

import types
_tm = types.ModuleType("torchmetrics")
_tm.functional = types.SimpleNamespace(f1_score=lambda preds, target, **kw: torch.tensor(0.0, device=preds.device))
sys.modules.setdefault("torchmetrics", _tm)

from sam3.model_builder import build_sam3_image_model
from sam3.model.data_misc import FindStage, BatchedFindTarget, BatchedInferenceMetadata
from sam3.model.box_ops import box_cxcywh_to_xyxy, box_xyxy_to_cxcywh, box_iou
from sam3.train.loss.sam3_loss import Sam3LossWrapper
from sam3.train.loss.loss_fns import IABCEMdetr, Boxes
from sam3.train.matcher import BinaryHungarianMatcherV2, BinaryOneToManyMatcher

GRID_H, GRID_W = 240, 320
GRID_PIXELS = GRID_H * GRID_W  # 76,800
MIN_POS_PIXELS = 48            # ~0.0625% of frame; includes <1% small objects (48..767 px)
SMALL_OBJ_MAX_PIXELS = 768     # 1.0% of 240x320 frame

# Standard indoor synonym table used strictly on K1 training rooms so ScanNet++ / ScanNet
# canonical labels (e.g. "radiator", "refrigerator", "sofa") align with natural queries ("heater", "fridge", "couch").
INDOOR_SYNONYMS: dict[str, list[str]] = {
    "radiator": ["heater", "wall heater", "heating radiator"],
    "heater": ["radiator"],
    "refrigerator": ["fridge", "mini fridge"],
    "fridge": ["refrigerator"],
    "sofa": ["couch"],
    "couch": ["sofa"],
    "tv": ["television", "tv monitor"],
    "television": ["tv"],
    "trash can": ["trash bin", "garbage can", "waste bin", "bin"],
    "trash bin": ["trash can"],
    "washbasin": ["sink", "bathroom sink"],
    "sink": ["washbasin"],
    "office chair": ["chair", "desk chair", "swivel chair"],
    "armchair": ["chair", "lounge chair"],
    "nightstand": ["bedside table", "side table"],
    "wardrobe": ["closet", "cabinet"],
}

COMMON_INDOOR_NEGATIVES: list[str] = [
    "heater", "radiator", "microwave", "refrigerator", "oven", "stove", "dishwasher",
    "washer", "dryer", "Kettle", "coffee maker", "toaster", "sink", "toilet", "bathtub",
    "shower", "mirror", "towel", "cabinet", "shelf", "bookshelf", "desk", "table",
    "coffee table", "dining table", "chair", "office chair", "armchair", "stool",
    "sofa", "couch", "bed", "pillow", "blanket", "nightstand", "wardrobe", "dresser",
    "tv", "monitor", "laptop", "keyboard", "printer", "lamp", "ceiling light", "fan",
    "plant", "flower pot", "picture", "painting", "clock", "curtain", "blinds",
    "window", "door", "trash can", "box", "backpack", "bag", " suitcase", "shoe",
    "clothes", "bicycle", "fireplace", "stairs",
]


# ---------------------------------------------------------------------------
# 1. LoRA Parametrization for PyTorch / SAM 3 MultiheadAttention
# ---------------------------------------------------------------------------

class LoRAWeight(nn.Module):
    """Low-rank weight adapter W + (alpha / r) * (B @ A) for register_parametrization."""
    def __init__(self, out_features: int, in_features: int, r: int = 16, alpha: float = 32.0):
        super().__init__()
        self.r = r
        self.scale = alpha / float(r)
        self.lora_A = nn.Parameter(torch.empty(r, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, W: torch.Tensor) -> torch.Tensor:
        delta = (self.lora_B @ self.lora_A).to(dtype=W.dtype) * self.scale
        return W + delta


def attach_c2_lora_and_heads(
    model: nn.Module,
    *,
    lora_rank: int = 16,
    lora_alpha: float = 32.0,
    train_bbox_head: bool = True,
) -> dict[str, Any]:
    """Freeze vision/text backbones and mask decoder; attach r=16 LoRA to fusion encoder &
    query decoder attention projections, and unfreeze presence + dot_prod_scoring (+ optional bbox_embed).
    """
    for p in model.parameters():
        p.requires_grad_(False)
    dev = next(model.parameters()).device

    lora_modules = []
    # Fusion encoder layers (self_attn, cross_attn_image)
    for idx, layer in enumerate(model.transformer.encoder.layers):
        for aname in ("self_attn", "cross_attn_image"):
            attn = getattr(layer, aname)
            parametrize.register_parametrization(
                attn, "in_proj_weight",
                LoRAWeight(attn.in_proj_weight.shape[0], attn.in_proj_weight.shape[1], r=lora_rank, alpha=lora_alpha).to(dev),
            )
            parametrize.register_parametrization(
                attn.out_proj, "weight",
                LoRAWeight(attn.out_proj.weight.shape[0], attn.out_proj.weight.shape[1], r=lora_rank, alpha=lora_alpha).to(dev),
            )
            lora_modules.append(f"encoder.layers.{idx}.{aname}")

    # Query decoder layers (self_attn, ca_text, cross_attn)
    for idx, layer in enumerate(model.transformer.decoder.layers):
        for aname in ("self_attn", "ca_text", "cross_attn"):
            attn = getattr(layer, aname)
            parametrize.register_parametrization(
                attn, "in_proj_weight",
                LoRAWeight(attn.in_proj_weight.shape[0], attn.in_proj_weight.shape[1], r=lora_rank, alpha=lora_alpha).to(dev),
            )
            parametrize.register_parametrization(
                attn.out_proj, "weight",
                LoRAWeight(attn.out_proj.weight.shape[0], attn.out_proj.weight.shape[1], r=lora_rank, alpha=lora_alpha).to(dev),
            )
            lora_modules.append(f"decoder.layers.{idx}.{aname}")

    # Unfreeze presence head and dot-product scoring head
    head_modules = [
        model.transformer.decoder.presence_token,
        model.transformer.decoder.presence_token_head,
        model.transformer.decoder.presence_token_out_norm,
        model.dot_prod_scoring,
    ]
    if train_bbox_head:
        head_modules.append(model.transformer.decoder.bbox_embed)

    for m in head_modules:
        for p in m.parameters():
            p.requires_grad_(True)

    # Ensure parametrizations are on the same device as model
    dev = next(model.parameters()).device
    model.to(dev)

    trainable_params = [p for p in model.parameters() if p.requires_grad]
    total_params = sum(p.numel() for p in model.parameters())
    n_trainable = sum(p.numel() for p in trainable_params)

    # Verify frozen components have 0 trainable params
    assert sum(p.numel() for p in model.backbone.parameters() if p.requires_grad) == 0, "Backbone must be 100% frozen!"
    assert sum(p.numel() for p in model.segmentation_head.parameters() if p.requires_grad) == 0, "Mask head must be 100% frozen!"
    assert sum(p.numel() for p in model.geometry_encoder.parameters() if p.requires_grad) == 0, "Geometry encoder must be 100% frozen!"

    return {
        "lora_rank": lora_rank,
        "lora_alpha": lora_alpha,
        "lora_attn_modules": len(lora_modules),
        "train_bbox_head": train_bbox_head,
        "trainable_params": n_trainable,
        "total_params": total_params,
        "trainable_pct": round(100.0 * n_trainable / total_params, 4),
    }


def extract_trainable_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    """Save only trainable parameters (LoRA A/B weights + presence/scoring/bbox heads)."""
    return {
        k: v.detach().cpu().clone()
        for k, v in model.state_dict().items()
        if any(
            sub in k
            for sub in (
                "parametrizations",
                "presence_token",
                "dot_prod_scoring",
                "decoder.bbox_embed",
            )
        )
    }


# ---------------------------------------------------------------------------
# 2. Zero-Leakage K1 Split Verification & Query Indexing
# ---------------------------------------------------------------------------

def mask_to_box_cxcywh_and_xyxy(mask: np.ndarray) -> tuple[list[float], list[float], int] | None:
    """Compute tight normalized [cx, cy, w, h] and [x0, y0, x1, y1] from a 2D boolean mask."""
    ys, xs = np.nonzero(mask)
    n_pix = int(len(ys))
    if n_pix == 0:
        return None
    H, W = mask.shape
    x0 = float(xs.min()) / float(W)
    x1 = float(xs.max() + 1) / float(W)
    y0 = float(ys.min()) / float(H)
    y1 = float(ys.max() + 1) / float(H)
    cx = 0.5 * (x0 + x1)
    cy = 0.5 * (y0 + y1)
    bw = max(1e-4, x1 - x0)
    bh = max(1e-4, y1 - y0)
    return [cx, cy, bw, bh], [x0, y0, x1, y1], n_pix


def index_k1_captures(records: list[Any], is_train: bool = True) -> dict[str, Any]:
    """Index all valid frames and per-label GT boxes/areas from K1 captures on local /scratch."""
    t0 = time.perf_counter()
    frames_index: list[dict[str, Any]] = []
    small_frame_indices: list[int] = []
    all_vocab: set[str] = set(x.strip().lower() for x in COMMON_INDOOR_NEGATIVES)

    total_pos_pairs = 0
    total_small_pos_pairs = 0
    total_hard_neg_pairs = 0

    for rec in records:
        with np.load(rec.gt_path, allow_pickle=False) as z:
            inst = z["inst"]       # (32, H, W)
            ids = z["ids"]         # (M,)
            labels = z["labels"]   # (M,)
            valid = z["valid"]     # (32,)

        # Group instance IDs by clean lowercase label
        label_to_iids: dict[str, list[int]] = {}
        for iid_val, lbl_val in zip(ids, labels):
            clean_lbl = str(lbl_val).strip().lower()
            if not clean_lbl or clean_lbl in ("invalid", "none", "unknown", "unlabeled"):
                continue
            label_to_iids.setdefault(clean_lbl, []).append(int(iid_val))
            all_vocab.add(clean_lbl)

        if not label_to_iids:
            continue

        # Capture-level vocabulary including synonyms (so we never sample a synonym of a present label as a negative!)
        cap_forbidden_neg: set[str] = set(label_to_iids.keys())
        for lbl in list(label_to_iids.keys()):
            for syn in INDOOR_SYNONYMS.get(lbl, []):
                cap_forbidden_neg.add(syn.strip().lower())

        for slot in range(32):
            if not bool(valid[slot]):
                continue
            fpath = rec.anchor_frame_paths[slot]
            if not Path(fpath).is_file():
                continue

            frame_inst = inst[slot]
            pos_by_label: dict[str, list[dict[str, Any]]] = {}
            hard_neg_labels: list[str] = []
            has_small_obj = False

            for lbl, iids in label_to_iids.items():
                boxes_cxcywh = []
                boxes_xyxy = []
                areas_px = []
                any_fragment = False

                for iid_val in iids:
                    m = (frame_inst == iid_val)
                    res = mask_to_box_cxcywh_and_xyxy(m)
                    if res is None:
                        continue
                    any_fragment = True
                    b_cx, b_xy, n_px = res
                    if n_px >= MIN_POS_PIXELS:
                        boxes_cxcywh.append(b_cx)
                        boxes_xyxy.append(b_xy)
                        areas_px.append(n_px)
                        if n_px < SMALL_OBJ_MAX_PIXELS:
                            has_small_obj = True

                if boxes_cxcywh:
                    entry = {
                        "boxes_cxcywh": boxes_cxcywh,
                        "boxes_xyxy": boxes_xyxy,
                        "areas_px": areas_px,
                        "min_area_px": min(areas_px),
                        "max_area_px": max(areas_px),
                        "has_small": any(a < SMALL_OBJ_MAX_PIXELS for a in areas_px),
                        "is_synonym": False,
                    }
                    pos_by_label[lbl] = entry
                    total_pos_pairs += 1
                    if entry["has_small"]:
                        total_small_pos_pairs += 1

                    # During training, also add indoor synonyms (e.g. radiator -> heater) with 0 leakage
                    if is_train:
                        for syn in INDOOR_SYNONYMS.get(lbl, []):
                            syn_clean = syn.strip().lower()
                            if syn_clean not in pos_by_label and syn_clean not in label_to_iids:
                                syn_entry = dict(entry, is_synonym=True)
                                pos_by_label[syn_clean] = syn_entry
                elif not any_fragment:
                    # Strictly 0 pixels in this frame, but object exists in this capture!
                    hard_neg_labels.append(lbl)
                    if is_train:
                        for syn in INDOOR_SYNONYMS.get(lbl, []):
                            syn_clean = syn.strip().lower()
                            if syn_clean not in hard_neg_labels:
                                hard_neg_labels.append(syn_clean)
                    total_hard_neg_pairs += 1

            if not pos_by_label:
                continue

            f_idx = len(frames_index)
            frames_index.append({
                "capture_id": rec.canonical,
                "dataset": rec.dataset,
                "room_id": rec.room,
                "slot": slot,
                "frame_path": fpath,
                "pos_by_label": pos_by_label,
                "hard_neg_labels": hard_neg_labels,
                "forbidden_neg": cap_forbidden_neg,
                "has_small": has_small_obj,
            })
            if has_small_obj:
                small_frame_indices.append(f_idx)

    return {
        "frames": frames_index,
        "small_frame_indices": small_frame_indices,
        "vocab": sorted(all_vocab),
        "stats": {
            "num_captures": len(records),
            "indexed_frames": len(frames_index),
            "frames_with_small_lt1pct": len(small_frame_indices),
            "total_pos_frame_label_pairs": total_pos_pairs,
            "total_small_pos_pairs": total_small_pos_pairs,
            "total_in_capture_hard_neg_pairs": total_hard_neg_pairs,
            "index_seconds": round(time.perf_counter() - t0, 2),
        },
    }


# ---------------------------------------------------------------------------
# 3. Fast Image Preprocessing & SAM 3 Forward Helpers
# ---------------------------------------------------------------------------

def preprocess_pil_for_sam3(images: list[Image.Image], device: torch.device, resolution: int = 1008) -> torch.Tensor:
    """ExactSam3Processor tensor transform: RGB -> float [0,1] -> resize (1008, 1008) -> Normalize(0.5, 0.5)."""
    tensors = []
    for im in images:
        arr = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
        t = torch.from_numpy(arr).permute(2, 0, 1)  # (3, H, W)
        tensors.append(t)
    # Stack per-size or interpolate individually if aspect ratios differ (e.g. rotated ARKit portrait vs landscape)
    resized = []
    for t in tensors:
        r = F.interpolate(t.unsqueeze(0).to(device), size=(resolution, resolution), mode="bilinear", align_corners=False)[0]
        r = (r - 0.5) / 0.5
        resized.append(r)
    return torch.stack(resized, dim=0)


def build_sam3_loss_wrapper(device: torch.device) -> Sam3LossWrapper:
    """Build SAM 3's official detector + presence loss wrapper (roboflow_v100_full_ft_100_images config)."""
    matcher = BinaryHungarianMatcherV2(
        cost_class=2.0,
        cost_bbox=5.0,
        cost_giou=2.0,
        focal=True,
        alpha=0.25,
        gamma=2.0,
        stable=False,
    )
    o2m_matcher = BinaryOneToManyMatcher(
        alpha=0.3,
        threshold=0.4,
        topk=4,
    )
    loss_fns = [
        Boxes(weight_dict={"loss_bbox": 5.0, "loss_giou": 2.0}),
        IABCEMdetr(
            weak_loss=False,
            weight_dict={
                "loss_ce": 20.0,
                "presence_loss": 20.0,
            },
            pos_weight=10.0,
            alpha=0.25,
            gamma=2.0,
            use_presence=True,
            pos_focal=False,
            pad_n_queries=200,
        ),
    ]
    wrapper = Sam3LossWrapper(
        loss_fns_find=loss_fns,
        matcher=matcher,
        o2m_matcher=o2m_matcher,
        o2m_weight=2.0,
        use_o2m_matcher_on_o2m_aux=False,
        normalization="local",
        normalize_by_valid_object_num=False,
    )
    return wrapper.to(device)


def sample_training_step_batch(
    train_data: dict[str, Any],
    rng: random.Random,
    *,
    num_images: int = 2,
    queries_per_image: int = 4,
) -> tuple[list[Image.Image], list[str], list[list[list[float]]], list[list[list[float]]], list[int]]:
    """Sample `num_images` frames (forcing >=1 frame with a <1% small object) and `queries_per_image`
    balanced text prompts per image (50% positive with small-object oversampling, 50% hard negative).
    """
    frames = train_data["frames"]
    small_indices = train_data["small_frame_indices"]
    vocab = train_data["vocab"]

    chosen_frames = []
    for i in range(num_images):
        if i == 0 and small_indices and rng.random() < 0.75:
            chosen_frames.append(frames[rng.choice(small_indices)])
        else:
            chosen_frames.append(frames[rng.randrange(len(frames))])

    pil_images: list[Image.Image] = []
    captions: list[str] = []
    gt_boxes_cxcywh: list[list[list[float]]] = []
    gt_boxes_xyxy: list[list[list[float]]] = []
    is_pos_flags: list[int] = []

    n_pos_per_img = max(1, queries_per_image // 2)
    n_neg_per_img = queries_per_image - n_pos_per_img

    for fmeta in chosen_frames:
        with Image.open(fmeta["frame_path"]) as im:
            pil_images.append(im.convert("RGB"))

        pos_items = list(fmeta["pos_by_label"].items())
        # Prioritize small-object positive queries 60% of the time when available
        small_pos = [(k, v) for k, v in pos_items if v["has_small"]]
        chosen_pos = []
        if small_pos and rng.random() < 0.65:
            chosen_pos.append(rng.choice(small_pos))
        while len(chosen_pos) < n_pos_per_img:
            chosen_pos.append(rng.choice(pos_items))

        for lbl, entry in chosen_pos:
            captions.append(lbl)
            gt_boxes_cxcywh.append(entry["boxes_cxcywh"])
            gt_boxes_xyxy.append(entry["boxes_xyxy"])
            is_pos_flags.append(1)

        # Sample hard negatives (50% in-capture frame-absent, 50% cross-capture indoor vocab)
        hard_negs = fmeta["hard_neg_labels"]
        forbidden = fmeta["forbidden_neg"]
        for j in range(n_neg_per_img):
            if hard_negs and (j % 2 == 0 or rng.random() < 0.6):
                neg_lbl = rng.choice(hard_negs)
            else:
                # Sample from indoor vocab outside capture's forbidden set
                neg_lbl = rng.choice(vocab)
                for _ in range(15):
                    if neg_lbl not in forbidden:
                        break
                    neg_lbl = rng.choice(vocab)
            captions.append(neg_lbl)
            gt_boxes_cxcywh.append([])
            gt_boxes_xyxy.append([])
            is_pos_flags.append(0)

    return pil_images, captions, gt_boxes_cxcywh, gt_boxes_xyxy, is_pos_flags


def forward_and_compute_loss(
    model: nn.Module,
    loss_wrapper: Sam3LossWrapper,
    pil_images: list[Image.Image],
    captions: list[str],
    gt_boxes_cxcywh: list[list[list[float]]],
    gt_boxes_xyxy: list[list[list[float]]],
    is_pos_flags: list[int],
    device: torch.device,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Run frozen image/text backbones under torch.no_grad(), tile top FPN level across queries,
    run trainable fusion encoder + query decoder + heads, and compute Sam3LossWrapper + presence margin loss.
    """
    num_images = len(pil_images)
    total_q = len(captions)
    q_per_img = total_q // num_images
    assert total_q == num_images * q_per_img

    # 1. Frozen vision backbone on unique images only (huge speedup & VRAM savings)
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.bfloat16):
        img_tensor = preprocess_pil_for_sam3(pil_images, device=device, resolution=1008)
        vis_out = model.backbone.forward_image(img_tensor)
        # We only need the top FPN level [-1] for _encode_prompt + transformer.encoder + decoder
        top_fpn = vis_out["backbone_fpn"][-1].detach()      # (num_images, 256, 72, 72)
        top_pos = vis_out["vision_pos_enc"][-1].detach()    # (num_images, 256, 72, 72)
        del vis_out, img_tensor

        # Tile each image's FPN features q_per_img times -> (total_q, 256, 72, 72)
        tiled_fpn = top_fpn.repeat_interleave(q_per_img, dim=0)
        tiled_pos = top_pos.repeat_interleave(q_per_img, dim=0)

        # Frozen text backbone on all total_q captions
        text_out = model.backbone.forward_text(captions, device=device)
        backbone_out = {
            "vision_features": tiled_fpn,
            "backbone_fpn": [tiled_fpn],
            "vision_pos_enc": [tiled_pos],
            "language_features": text_out["language_features"].detach(),
            "language_mask": text_out["language_mask"].detach(),
            "language_embeds": text_out["language_embeds"].detach(),
        }

    # 2. Construct FindStage and BatchedFindTarget for total_q image-text queries
    img_ids = torch.arange(total_q, device=device, dtype=torch.long)
    txt_ids = torch.arange(total_q, device=device, dtype=torch.long)
    find_input = FindStage(
        img_ids=img_ids,
        text_ids=txt_ids,
        input_boxes=torch.empty((0, total_q, 4), device=device, dtype=torch.float32),
        input_boxes_mask=torch.empty((total_q, 0), device=device, dtype=torch.bool),
        input_boxes_label=torch.empty((0, total_q), device=device, dtype=torch.long),
        input_points=torch.empty((0, total_q, 2), device=device, dtype=torch.float32),
        input_points_mask=torch.empty((total_q, 0), device=device, dtype=torch.bool),
        object_ids=None,
    )

    num_boxes_list = []
    all_cxcywh = []
    all_xyxy = []
    obj_ids_padded = []
    max_b = max((len(b) for b in gt_boxes_cxcywh), default=0)

    for q_idx, (b_cx, b_xy) in enumerate(zip(gt_boxes_cxcywh, gt_boxes_xyxy)):
        nb = len(b_cx)
        num_boxes_list.append(nb)
        for k in range(nb):
            all_cxcywh.append(b_cx[k])
            all_xyxy.append(b_xy[k])

    num_boxes_t = torch.tensor(num_boxes_list, device=device, dtype=torch.long)
    total_gt_boxes = sum(num_boxes_list)
    if total_gt_boxes > 0:
        boxes_cx_t = torch.tensor(all_cxcywh, device=device, dtype=torch.float32)
        boxes_xy_t = torch.tensor(all_xyxy, device=device, dtype=torch.float32)
    else:
        boxes_cx_t = torch.zeros((0, 4), device=device, dtype=torch.float32)
        boxes_xy_t = torch.zeros((0, 4), device=device, dtype=torch.float32)

    # Build padded boxes (total_q, max_b, 4) and object_ids_packed
    boxes_padded = torch.zeros((total_q, max_b, 4), device=device, dtype=torch.float32)
    obj_padded = torch.full((total_q, max_b), -1, device=device, dtype=torch.long)
    cursor = 0
    for q_idx, nb in enumerate(num_boxes_list):
        if nb > 0:
            boxes_padded[q_idx, :nb] = boxes_cx_t[cursor : cursor + nb]
            obj_padded[q_idx, :nb] = torch.arange(cursor, cursor + nb, device=device, dtype=torch.long)
            cursor += nb

    find_target = BatchedFindTarget(
        num_boxes=num_boxes_t,
        boxes=boxes_cx_t,
        boxes_padded=boxes_padded,
        repeated_boxes=boxes_xy_t.clone(),
        segments=None,
        semantic_segments=None,
        is_valid_segment=None,
        is_exhaustive=torch.ones(total_q, device=device, dtype=torch.bool),
        object_ids=torch.arange(total_gt_boxes, device=device, dtype=torch.long),
        object_ids_padded=obj_padded,
    )

    # 3. Trainable forward through fusion encoder + query decoder + heads (skip segmentation_head during training)
    # Temporarily disable segmentation_head in forward_grounding so we don't compute 200x288x288 masks per training query
    orig_seg_head = model.segmentation_head
    model.segmentation_head = None
    try:
        with torch.amp.autocast("cuda", dtype=torch.bfloat16):
            geo_prompt = model._get_dummy_prompt(num_prompts=total_q)
            out = model.forward_grounding(
                backbone_out=backbone_out,
                find_input=find_input,
                find_target=find_target,
                geometric_prompt=geo_prompt,
            )
            loss_dict = loss_wrapper.compute_loss(out, model.back_convert(find_target))
            core_loss = loss_dict["core_loss"]

            # Additional explicit presence & empty-frame false-positive suppression loss:
            # On negative queries (num_boxes == 0), penalize max(pred_logits) > -2.0 and presence_logit_dec > -2.0
            # On positive queries (num_boxes > 0), encourage presence_logit_dec > +2.0
            pres_logits = out["presence_logit_dec"].squeeze(-1).float()  # (total_q,)
            target_pres = torch.tensor(is_pos_flags, device=device, dtype=torch.float32)
            bce_pres = F.binary_cross_entropy_with_logits(pres_logits, target_pres)

            pred_logits = out["pred_logits"].squeeze(-1).float()  # (total_q, 200)
            max_query_logit = pred_logits.max(dim=-1).values      # (total_q,)
            neg_mask = (target_pres < 0.5)
            if neg_mask.any():
                # Suppress false-positive query spikes on empty frames
                neg_query_suppress = F.softplus(max_query_logit[neg_mask] + 1.0).mean()
            else:
                neg_query_suppress = torch.tensor(0.0, device=device)

            total_loss = core_loss + 2.0 * bce_pres + 0.5 * neg_query_suppress
    finally:
        model.segmentation_head = orig_seg_head

    with torch.no_grad():
        pres_prob = pres_logits.sigmoid()
        pos_mask = (target_pres > 0.5)
        pos_pres_mean = float(pres_prob[pos_mask].mean().item()) if pos_mask.any() else 0.0
        neg_pres_mean = float(pres_prob[neg_mask].mean().item()) if neg_mask.any() else 0.0

    metrics = {
        "total_loss": float(total_loss.detach().item()),
        "core_loss": float(core_loss.detach().item()),
        "bce_pres": float(bce_pres.detach().item()),
        "neg_suppress": float(neg_query_suppress.detach().item()),
        "pos_pres_prob": round(pos_pres_mean, 4),
        "neg_pres_prob": round(neg_pres_mean, 4),
    }
    return total_loss, metrics


# ---------------------------------------------------------------------------
# 4. K1-Heldout Fast Evaluator (53 captures / 50 rooms, Cached FPN Top Level)
# ---------------------------------------------------------------------------

def compute_auroc(labels: list[int], scores: list[float]) -> float:
    """Exact Wilcoxon-Mann-Whitney AUROC without external sklearn dependency."""
    y = np.asarray(labels, dtype=np.int32)
    s = np.asarray(scores, dtype=np.float64)
    pos = s[y == 1]
    neg = s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.0
    # Pairwise comparison via broadcasting or rank sum
    diff = pos[:, None] - neg[None, :]
    wins = np.sum(diff > 0) + 0.5 * np.sum(diff == 0)
    return float(wins / (len(pos) * len(neg)))


def build_k1_heldout_eval_cache(
    model: nn.Module,
    val_data: dict[str, Any],
    device: torch.device,
    *,
    frames_per_capture: int = 2,
    seed: int = 20261128,
) -> list[dict[str, Any]]:
    """Pre-extract top FPN level (backbone_fpn[-1], vision_pos_enc[-1]) in bf16 on CPU for
    2 representative frames per capture across all 53 K1-heldout captures (~106 frames, ~275 MB RAM).
    Prioritizes frames containing <1% small objects so small-object recall has high statistical power.
    """
    rng = random.Random(seed)
    by_cap: dict[str, list[dict[str, Any]]] = {}
    for f in val_data["frames"]:
        by_cap.setdefault(f["capture_id"], []).append(f)

    vocab = val_data["vocab"]
    selected_frames: list[dict[str, Any]] = []
    for cap_id in sorted(by_cap.keys()):
        flist = by_cap[cap_id]
        small_f = [f for f in flist if f["has_small"]]
        other_f = [f for f in flist if not f["has_small"]]
        picks = []
        if small_f:
            picks.append(small_f[0])
            if len(small_f) > 1 and len(picks) < frames_per_capture:
                picks.append(small_f[-1])
        for f in other_f:
            if len(picks) >= frames_per_capture:
                break
            picks.append(f)
        selected_frames.extend(picks[:frames_per_capture])

    cached_items: list[dict[str, Any]] = []
    model.eval()
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.bfloat16):
        for fmeta in selected_frames:
            with Image.open(fmeta["frame_path"]) as im:
                pil_im = im.convert("RGB")
            img_t = preprocess_pil_for_sam3([pil_im], device=device, resolution=1008)
            vis_out = model.backbone.forward_image(img_t)
            top_fpn_cpu = vis_out["backbone_fpn"][-1].detach().to("cpu", dtype=torch.bfloat16)
            top_pos_cpu = vis_out["vision_pos_enc"][-1].detach().to("cpu", dtype=torch.bfloat16)
            del vis_out, img_t

            # Build evaluation queries for this frame: all positive labels + up to 3 hard negatives
            queries = []
            for lbl, entry in sorted(fmeta["pos_by_label"].items()):
                if entry.get("is_synonym", False):
                    continue
                queries.append({
                    "prompt": lbl,
                    "is_pos": 1,
                    "boxes_xyxy": entry["boxes_xyxy"],
                    "areas_px": entry["areas_px"],
                    "neg_type": "none",
                })
            # In-capture frame-absent hard negatives
            for lbl in fmeta["hard_neg_labels"][:2]:
                queries.append({
                    "prompt": lbl,
                    "is_pos": 0,
                    "boxes_xyxy": [],
                    "areas_px": [],
                    "neg_type": "in_capture_absent",
                })
            # Cross-capture indoor negative
            for _ in range(20):
                neg_lbl = rng.choice(vocab)
                if neg_lbl not in fmeta["forbidden_neg"]:
                    queries.append({
                        "prompt": neg_lbl,
                        "is_pos": 0,
                        "boxes_xyxy": [],
                        "areas_px": [],
                        "neg_type": "cross_capture_absent",
                    })
                    break

            cached_items.append({
                "capture_id": fmeta["capture_id"],
                "room_id": fmeta["room_id"],
                "slot": fmeta["slot"],
                "top_fpn_cpu": top_fpn_cpu,
                "top_pos_cpu": top_pos_cpu,
                "queries": queries,
            })

    return cached_items


@torch.no_grad()
def evaluate_k1_heldout(
    model: nn.Module,
    eval_cache: list[dict[str, Any]],
    device: torch.device,
) -> dict[str, Any]:
    """Run fast K1-heldout evaluation across all 53 captures / 50 rooms."""
    t0 = time.perf_counter()
    model.eval()
    orig_seg_head = model.segmentation_head
    model.segmentation_head = None

    y_true: list[int] = []
    pres_scores: list[float] = []
    joint_scores: list[float] = []
    top_q_scores: list[float] = []
    neg_types: list[str] = []

    # Per-GT-instance box IoU tracking
    all_top1_ious: list[float] = []
    all_top5_ious: list[float] = []
    all_h1_active_ious: list[float] = []

    small_top1_ious: list[float] = []
    small_top5_ious: list[float] = []
    small_h1_active_ious: list[float] = []

    large_top1_ious: list[float] = []
    large_h1_active_ious: list[float] = []

    try:
        with torch.amp.autocast("cuda", dtype=torch.bfloat16):
            for item in eval_cache:
                queries = item["queries"]
                nq = len(queries)
                if nq == 0:
                    continue
                prompts = [q["prompt"] for q in queries]
                tiled_fpn = item["top_fpn_cpu"].to(device).expand(nq, -1, -1, -1)
                tiled_pos = item["top_pos_cpu"].to(device).expand(nq, -1, -1, -1)

                text_out = model.backbone.forward_text(prompts, device=device)
                backbone_out = {
                    "vision_features": tiled_fpn,
                    "backbone_fpn": [tiled_fpn],
                    "vision_pos_enc": [tiled_pos],
                    "language_features": text_out["language_features"],
                    "language_mask": text_out["language_mask"],
                    "language_embeds": text_out["language_embeds"],
                }
                find_input = FindStage(
                    img_ids=torch.arange(nq, device=device, dtype=torch.long),
                    text_ids=torch.arange(nq, device=device, dtype=torch.long),
                    input_boxes=torch.empty((0, nq, 4), device=device, dtype=torch.float32),
                    input_boxes_mask=torch.empty((nq, 0), device=device, dtype=torch.bool),
                    input_boxes_label=torch.empty((0, nq), device=device, dtype=torch.long),
                    input_points=torch.empty((0, nq, 2), device=device, dtype=torch.float32),
                    input_points_mask=torch.empty((nq, 0), device=device, dtype=torch.bool),
                    object_ids=None,
                )
                out = model.forward_grounding(
                    backbone_out=backbone_out,
                    find_input=find_input,
                    find_target=None,
                    geometric_prompt=model._get_dummy_prompt(num_prompts=nq),
                )

                p_probs = out["presence_logit_dec"].sigmoid().squeeze(-1).float().cpu().numpy()   # (nq,)
                q_probs = out["pred_logits"].sigmoid().squeeze(-1).float().cpu().numpy()          # (nq, 200)
                p_boxes = out["pred_boxes_xyxy"].float().cpu().numpy()                            # (nq, 200, 4)

                for q_idx, q in enumerate(queries):
                    pres = float(p_probs[q_idx])
                    scores = q_probs[q_idx]
                    joints = scores * pres
                    order = np.argsort(-joints)
                    best_i = int(order[0])
                    best_score = float(scores[best_i])
                    best_joint = float(joints[best_i])

                    y_true.append(int(q["is_pos"]))
                    pres_scores.append(pres)
                    joint_scores.append(best_joint)
                    top_q_scores.append(best_score)
                    neg_types.append(q["neg_type"])

                    if q["is_pos"] == 1:
                        top1_box = p_boxes[q_idx, best_i]
                        top5_boxes = p_boxes[q_idx, order[:5]]
                        h1_fires = (best_joint >= 0.05 and best_score >= 0.30)

                        for gt_xyxy, area_px in zip(q["boxes_xyxy"], q["areas_px"]):
                            # Compute 2D box IoU against top-1 and top-5 predicted boxes
                            iou1 = _box_iou_xyxy_np(top1_box, gt_xyxy)
                            iou5 = max(_box_iou_xyxy_np(tb, gt_xyxy) for tb in top5_boxes)
                            iou_h1 = iou1 if h1_fires else 0.0

                            all_top1_ious.append(iou1)
                            all_top5_ious.append(iou5)
                            all_h1_active_ious.append(iou_h1)

                            if area_px < SMALL_OBJ_MAX_PIXELS:
                                small_top1_ious.append(iou1)
                                small_top5_ious.append(iou5)
                                small_h1_active_ious.append(iou_h1)
                            else:
                                large_top1_ious.append(iou1)
                                large_h1_active_ious.append(iou_h1)
    finally:
        model.segmentation_head = orig_seg_head

    y_arr = np.asarray(y_true, dtype=np.int32)
    j_arr = np.asarray(joint_scores, dtype=np.float64)
    s_arr = np.asarray(top_q_scores, dtype=np.float64)
    neg_mask = (y_arr == 0)
    pos_mask = (y_arr == 1)

    # Empty-frame FP rate under registered h1 gate (joint >= 0.05 & score >= 0.30)
    h1_active = (j_arr >= 0.05) & (s_arr >= 0.30)
    fp_rate_h1 = float(np.mean(h1_active[neg_mask])) if np.any(neg_mask) else 0.0
    tp_rate_h1 = float(np.mean(h1_active[pos_mask])) if np.any(pos_mask) else 0.0
    frame_prec_h1 = float(np.sum(h1_active & pos_mask) / max(1, np.sum(h1_active)))

    # Calibrate joint threshold tau_cal strictly on K1-heldout to reach target frame precision >= 0.75
    # (or maximize F1 with precision >= 0.65)
    best_tau = 0.05
    best_f1 = -1.0
    for tau in np.linspace(0.05, 0.65, 61):
        act = (j_arr >= tau) & (s_arr >= 0.30)
        tp = int(np.sum(act & pos_mask))
        fp = int(np.sum(act & neg_mask))
        fn = int(np.sum((~act) & pos_mask))
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        if prec >= 0.65 and f1 > best_f1:
            best_f1 = f1
            best_tau = float(round(tau, 3))

    act_cal = (j_arr >= best_tau) & (s_arr >= 0.30)
    fp_rate_cal = float(np.mean(act_cal[neg_mask])) if np.any(neg_mask) else 0.0
    tp_rate_cal = float(np.mean(act_cal[pos_mask])) if np.any(pos_mask) else 0.0
    frame_prec_cal = float(np.sum(act_cal & pos_mask) / max(1, np.sum(act_cal)))

    def _rate(arr: list[float], thr: float) -> float:
        return round(100.0 * float(np.mean(np.asarray(arr) >= thr)), 2) if arr else 0.0

    return {
        "num_queries": len(y_true),
        "num_pos_queries": int(np.sum(pos_mask)),
        "num_neg_queries": int(np.sum(neg_mask)),
        "num_gt_instances": len(all_top1_ious),
        "num_small_lt1pct_instances": len(small_top1_ious),
        "presence_auroc": round(compute_auroc(y_true, pres_scores) * 100.0, 2),
        "joint_auroc": round(compute_auroc(y_true, joint_scores) * 100.0, 2),
        "h1_frame_tp_rate_pct": round(100.0 * tp_rate_h1, 2),
        "h1_empty_frame_fp_rate_pct": round(100.0 * fp_rate_h1, 2),
        "h1_frame_precision_pct": round(100.0 * frame_prec_h1, 2),
        "cal_tau": best_tau,
        "cal_frame_tp_rate_pct": round(100.0 * tp_rate_cal, 2),
        "cal_empty_frame_fp_rate_pct": round(100.0 * fp_rate_cal, 2),
        "cal_frame_precision_pct": round(100.0 * frame_prec_cal, 2),
        "all_box_iou70_top1_pct": _rate(all_top1_ious, 0.70),
        "all_box_iou70_top5_pct": _rate(all_top5_ious, 0.70),
        "all_box_iou70_h1_active_pct": _rate(all_h1_active_ious, 0.70),
        "all_box_iou50_top1_pct": _rate(all_top1_ious, 0.50),
        "all_box_iou50_top5_pct": _rate(all_top5_ious, 0.50),
        "all_box_iou50_h1_active_pct": _rate(all_h1_active_ious, 0.50),
        "small_lt1pct_box_iou70_top1_pct": _rate(small_top1_ious, 0.70),
        "small_lt1pct_box_iou70_top5_pct": _rate(small_top5_ious, 0.70),
        "small_lt1pct_box_iou70_h1_active_pct": _rate(small_h1_active_ious, 0.70),
        "small_lt1pct_box_iou50_top1_pct": _rate(small_top1_ious, 0.50),
        "small_lt1pct_box_iou50_top5_pct": _rate(small_top5_ious, 0.50),
        "small_lt1pct_box_iou50_h1_active_pct": _rate(small_h1_active_ious, 0.50),
        "eval_seconds": round(time.perf_counter() - t0, 2),
    }


def _box_iou_xyxy_np(a: np.ndarray | list[float], b: np.ndarray | list[float]) -> float:
    ix0 = max(float(a[0]), float(b[0]))
    iy0 = max(float(a[1]), float(b[1]))
    ix1 = min(float(a[2]), float(b[2]))
    iy1 = min(float(a[3]), float(b[3]))
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    area_a = max(0.0, float(a[2]) - float(a[0])) * max(0.0, float(a[3]) - float(a[1]))
    area_b = max(0.0, float(b[2]) - float(b[0])) * max(0.0, float(b[3]) - float(b[1]))
    u = area_a + area_b - inter
    return float(inter / u) if u > 0.0 else 0.0


def _oracle_h0_idx(props: list[dict[str, Any]], gt_mask: np.ndarray, floor: float = 0.50) -> int | None:
    """Return index of proposal with highest 2D mask IoU >= floor against gt_mask, or None."""
    if not props or not gt_mask.any():
        return None
    best_i = None
    best_val = floor
    for idx, p in enumerate(props):
        val = float(S.iou(p["mask"], gt_mask))
        if val >= best_val:
            best_val = val
            best_i = idx
    return best_i


def _box_iou_cxcywh(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    ax0, ay0 = float(a[0]) - 0.5 * float(a[2]), float(a[1]) - 0.5 * float(a[3])
    ax1, ay1 = float(a[0]) + 0.5 * float(a[2]), float(a[1]) + 0.5 * float(a[3])
    bx0, by0 = float(b[0]) - 0.5 * float(b[2]), float(b[1]) - 0.5 * float(b[3])
    bx1, by1 = float(b[0]) + 0.5 * float(b[2]), float(b[1]) + 0.5 * float(b[3])
    return _box_iou_xyxy_np([ax0, ay0, ax1, ay1], [bx0, by0, bx1, by1])


# ---------------------------------------------------------------------------
# 5. Paired DEV-MASK 117 Evaluator (117 items, 46 captures, 35 rooms)
# ---------------------------------------------------------------------------

def _relift_args(R, out: Path):
    return SimpleNamespace(
        capture=R.BASE / "cap/t1.gz",
        depth=G.DEPTH,
        receipt=G.RECEIPT,
        join=R.BASE / "cap/score_t1/JOIN_T1.jsonl",
        funnel=R.BASE / "cap/score_t1/FUNNEL_T1.json",
        gt_dirs=[R.BASE / "gt/t1_gt/gt", R.BASE / "gt/arkit_gt/gt"] + R.NOGT_DIRS,
        out=Path(out),
        half_only=False,
    )


def _fresh_relift(R) -> dict[str, Any]:
    captured: dict[str, Any] = {}
    original = R.dump
    R.dump = lambda path, value: captured.__setitem__("result", value)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            R.run(_relift_args(R, G.OUT / "unused_relift_dump.json"))
    finally:
        R.dump = original
    return captured["result"]


_DEV117_STATIC_OPERAND_CACHE: dict[tuple[str, str], dict[str, tuple[Any, int, list[dict[str, Any]], bytes]]] = {}


@torch.no_grad()
def evaluate_dev_mask_117(
    model: nn.Module,
    device: torch.device,
    *,
    cal_tau: float = 0.25,
) -> dict[str, Any]:
    """Run paired DEV-MASK 117 evaluation across all 117 items (46 captures, 35 physical rooms).

    Evaluates:
      - a          : served StageOne baseline (55.81)
      - e          : bound GT instance mask ceiling (69.57)
      - k          : frozen SAM 3 GT-box oracle from J1 (66.84)
      - j1_h1      : banked frozen SAM 3 h1 from J1 (43.85)
      - j1_h0      : banked frozen SAM 3 h0 pool oracle from J1 (43.50)
      - c2_h1      : C2 model under registered h1 rule (joint >= 0.05, score >= 0.30)
      - c2_h1_cal  : C2 model under K1-heldout calibrated threshold (joint >= cal_tau, score >= 0.30)
      - c2_h0      : C2 model under h0 per-frame pool oracle (IoU >= 0.50 against GT mask e)
    """
    t0 = time.perf_counter()
    model.eval()

    import resource
    orig_setrlimit = resource.setrlimit
    orig_cuda_vis = os.environ.get("CUDA_VISIBLE_DEVICES")
    resource.setrlimit = lambda *a, **kw: None
    try:
        R = G.load_relift()
        R.dependencies()
    finally:
        resource.setrlimit = orig_setrlimit
        if orig_cuda_vis is not None:
            os.environ["CUDA_VISIBLE_DEVICES"] = orig_cuda_vis
        if hasattr(json, "_a0_dumps"):
            json.dumps = json._a0_dumps
            json.loads = json._a0_loads

    preloaded_path = Path("/scratch/jjyeung/orch_home_distill/work_c2_sam3/dev117_preloaded.pt")
    preloaded = torch.load(preloaded_path, weights_only=False)
    refs = preloaded["refs"]
    items = preloaded["items"]
    objects = preloaded["objects"]
    rows = preloaded["rows"]
    depths = preloaded["depths"]

    prompts_j1 = G.read_json(G.PROMPTS_J1)
    prompts_by_cap = {c["capture"]: c for c in prompts_j1["captures"]}
    frames_by_cap = {c["capture"]: c for c in G.read_json(G.FRAMES_J1)["captures"]}

    by_item: dict[str, list[dict[str, Any]]] = {}
    for o in objects:
        by_item.setdefault(o["item_id"], []).append(o)

    # Group items by capture so we encode each capture's 32 frames at most once
    items_by_cap: dict[str, list[dict[str, Any]]] = {}
    for it in items:
        items_by_cap.setdefault(it["capture"], []).append(it)

    cells = ("a", "e", "k", "j1_h1", "j1_h0", "c2_h1", "c2_h1_cal", "c2_h1_hi", "c2_h0", "a_c2_rescue")
    out_rows: list[dict[str, Any]] = []
    empty_operands: dict[str, int] = {c: 0 for c in cells}
    pr_records: dict[str, list[dict[str, Any]]] = {c: [] for c in cells}

    # Track 2D box IoU on the 1,064 GT anchors of DEV-MASK 117
    dev117_top1_box_ious: list[float] = []
    dev117_top5_box_ious: list[float] = []
    dev117_small_top1_box_ious: list[float] = []
    dev117_small_top5_box_ious: list[float] = []
    dev117_heater_top1_box_ious: list[float] = []

    # Process capture by capture (46 captures)
    for cap_idx, (cap, cap_items) in enumerate(sorted(items_by_cap.items()), 1):
        p_cap = prompts_by_cap[cap]
        f_cap = frames_by_cap[cap]

        # Load GT instance array & depth geometry for this capture once
        with np.load(cap_items[0]["gt_path"], allow_pickle=False) as z:
            inst_arr = z["inst"].copy()
        g = R.restore(depths[cap])

        # Load banked J1 detect file for k, j1_h1, j1_h0 reference
        j1_det = G.read_json(G.DETECT / (G.stub(cap) + ".json.gz"))
        j1_text = j1_det["text"]
        j1_k_raw = j1_det["k"]
        k_masks_by_iid: dict[int, np.ndarray] = {}
        for u in p_cap["k_units"]:
            iid_u = int(u["instance_id"])
            rec_k = j1_k_raw[str(iid_u)]
            m_k = np.zeros((32, GRID_H, GRID_W), dtype=bool)
            for a_rec in rec_k["anchors"]:
                m_k[int(a_rec["slot"]) - 1] = S.to_grid(G.unpack(a_rec["mask"]))
            k_masks_by_iid[iid_u] = m_k

        # Identify unique text prompts needed for this capture
        unique_prompts = list(p_cap.get("text_prompts") or sorted({op["prompt"] for op in p_cap["operands"]}))

        # Run frozen vision backbone on the 32 frames of this capture in chunks of 8
        pil_frames = D.load_images(f_cap["frames"], 32)
        c2_proposals_by_prompt: dict[str, list[list[dict[str, Any]]]] = {pr: [] for pr in unique_prompts}

        with torch.amp.autocast("cuda", dtype=torch.bfloat16):
            # Pre-encode all unique prompts for this capture
            text_By_prompt = {
                pr: model.backbone.forward_text([pr], device=device)
                for pr in unique_prompts
            }

            chunk_size = 8
            for start_f in range(0, 32, chunk_size):
                end_f = min(32, start_f + chunk_size)
                B_f = end_f - start_f
                img_t = preprocess_pil_for_sam3(pil_frames[start_f:end_f], device=device, resolution=1008)
                vis_out = model.backbone.forward_image(img_t)

                find_input = FindStage(
                    img_ids=torch.arange(B_f, device=device, dtype=torch.long),
                    text_ids=torch.zeros(B_f, device=device, dtype=torch.long),
                    input_boxes=torch.empty((0, B_f, 4), device=device, dtype=torch.float32),
                    input_boxes_mask=torch.empty((B_f, 0), device=device, dtype=torch.bool),
                    input_boxes_label=torch.empty((0, B_f), device=device, dtype=torch.long),
                    input_points=torch.empty((0, B_f, 2), device=device, dtype=torch.float32),
                    input_points_mask=torch.empty((B_f, 0), device=device, dtype=torch.bool),
                    object_ids=None,
                )
                geo_prompt = model._get_dummy_prompt(num_prompts=B_f)

                for pr in unique_prompts:
                    t_out = text_By_prompt[pr]
                    backbone_out = {
                        "vision_features": vis_out["backbone_fpn"][-1],
                        "backbone_fpn": list(vis_out["backbone_fpn"]),
                        "vision_pos_enc": list(vis_out["vision_pos_enc"]),
                        "language_features": t_out["language_features"],
                        "language_mask": t_out["language_mask"],
                        "language_embeds": t_out["language_embeds"],
                    }
                    raw = model.forward_grounding(
                        backbone_out=backbone_out,
                        find_input=find_input,
                        find_target=None,
                        geometric_prompt=geo_prompt,
                    )
                    scores_b = raw["pred_logits"].sigmoid().squeeze(-1).float()          # (B_f, 200)
                    pres_b = raw["presence_logit_dec"].sigmoid().squeeze(-1).float()     # (B_f,)
                    boxes_b = raw["pred_boxes"].float().cpu().numpy()                    # (B_f, 200, 4) cxcywh
                    masks_b = raw["pred_masks"]                                          # (B_f, 200, 288, 288)
                    if masks_b.dim() == 5:
                        masks_b = masks_b.squeeze(2)

                    for b_i in range(B_f):
                        sc = scores_b[b_i]
                        pr_val = float(pres_b[b_i].item())
                        jt = sc * pr_val
                        order = torch.argsort(sc, descending=True, stable=True)
                        top5_idx = order[:5].tolist()
                        top5_boxes_cxcywh = [boxes_b[b_i, q_i].tolist() for q_i in top5_idx]
                        keep = order[jt[order] >= 0.05][:30]
                        frame_props = []
                        if len(keep) > 0:
                            kept_native = masks_b[b_i, keep].unsqueeze(1).float()  # (K, 1, 288, 288)
                            m480 = (F.interpolate(kept_native, size=(480, 640), mode="bilinear", align_corners=False)[:, 0] > 0).cpu().numpy()
                            for k_i, q_idx in enumerate(keep.tolist()):
                                m_grid = S.to_grid(m480[k_i])
                                if not m_grid.any():
                                    continue
                                s_val = float(sc[q_idx].item())
                                frame_props.append({
                                    "score": s_val,
                                    "presence": pr_val,
                                    "joint": s_val * pr_val,
                                    "box_cxcywh": boxes_b[b_i, q_idx].tolist(),
                                    "mask_grid": m_grid,
                                })
                        c2_proposals_by_prompt[pr].append({
                            "props": frame_props,
                            "top5_boxes_cxcywh": top5_boxes_cxcywh,
                            "presence": pr_val,
                            "top1_score": float(sc[top5_idx[0]].item()) if top5_idx else 0.0,
                        })

                del vis_out, img_t

        # Score 2D box IoU across this capture's k_units (1,064 GT anchors total across 46 captures)
        iid_to_prompt: dict[int, str] = {}
        for op in p_cap["operands"]:
            iid_to_prompt.setdefault(int(op["instance_id"]), op["prompt"])
        for u in p_cap["k_units"]:
            iid_u = int(u["instance_id"])
            pr_u = iid_to_prompt.get(iid_u)
            if not pr_u or pr_u not in c2_proposals_by_prompt:
                continue
            for b_gt in u["boxes"]:
                slot_idx = int(b_gt["slot"]) - 1
                gt_cx = b_gt["box"]
                gt_px = int(b_gt["gt_pixels"])
                f_info = c2_proposals_by_prompt[pr_u][slot_idx]
                t5_boxes = f_info["top5_boxes_cxcywh"]
                iou1 = _box_iou_cxcywh(t5_boxes[0], gt_cx) if t5_boxes else 0.0
                iou5 = max((_box_iou_cxcywh(tb, gt_cx) for tb in t5_boxes), default=0.0)
                dev117_top1_box_ious.append(iou1)
                dev117_top5_box_ious.append(iou5)
                if gt_px < SMALL_OBJ_MAX_PIXELS:
                    dev117_small_top1_box_ious.append(iou1)
                    dev117_small_top5_box_ious.append(iou5)
                if pr_u == "heater":
                    dev117_heater_top1_box_ious.append(iou1)

        # Score all items in this capture
        for it in cap_items:
            iid = it["item_id"]
            ref = refs[iid]
            row = rows[iid]
            served = {o["name"].strip().lower(): o for o in row["objects"]}
            pair_lifts: dict[str, list[Any]] = {c: [] for c in cells}

            for o in by_item[iid]:
                name = o["name"]
                prompt = name.strip().lower()
                target = (inst_arr == o["instance_id"])
                obj_a = served.get(prompt)

                op_cache_key = (iid, prompt)
                static_op = _DEV117_STATIC_OPERAND_CACHE.get(op_cache_key)
                if static_op is None:
                    # 1. Baseline a, GT e, Oracle k
                    m_a = R.masks_array(obj_a["selected_masks"]) if obj_a else np.zeros((32, GRID_H, GRID_W), dtype=bool)
                    m_e = target
                    m_k = k_masks_by_iid[int(o["instance_id"])]

                    # 2. Banked J1 h1 and h0
                    j1_frames = j1_text[prompt]
                    m_j1_h1 = np.zeros((32, GRID_H, GRID_W), dtype=bool)
                    m_j1_h0 = np.zeros((32, GRID_H, GRID_W), dtype=bool)
                    for f_i in range(32):
                        j1_p_grid = [
                            dict(score=p["score"], presence=p["presence"], mask=S.to_grid(G.unpack(p["mask"])))
                            for p in j1_frames[f_i]
                        ]
                        i_h1 = S.top1(j1_p_grid)
                        if i_h1 is not None:
                            m_j1_h1[f_i] = j1_p_grid[i_h1]["mask"]
                        i_h0 = _oracle_h0_idx(j1_p_grid, target[f_i])
                        if i_h0 is not None:
                            m_j1_h0[f_i] = j1_p_grid[i_h0]["mask"]

                    static_op = {}
                    for sc_name, sm_arr in (("a", m_a), ("e", m_e), ("k", m_k), ("j1_h1", m_j1_h1), ("j1_h0", m_j1_h0)):
                        s_val, _ = R.fit_lift(name, sm_arr, g)
                        s_empty = 0 if sm_arr.any() else 1
                        s_fr = G.precision_recall(sm_arr, target)
                        static_op[sc_name] = (s_val, s_empty, s_fr, sm_arr.tobytes())
                    static_op["_m_a"] = m_a
                    _DEV117_STATIC_OPERAND_CACHE[op_cache_key] = static_op
                else:
                    m_a = static_op["_m_a"]

                # 3. C2 LoRA arms: c2_h1, c2_h1_cal, c2_h1_hi, c2_h0, and a_c2_rescue
                c2_frames = c2_proposals_by_prompt[prompt]
                m_c2_h1 = np.zeros((32, GRID_H, GRID_W), dtype=bool)
                m_c2_h1_cal = np.zeros((32, GRID_H, GRID_W), dtype=bool)
                m_c2_h1_hi = np.zeros((32, GRID_H, GRID_W), dtype=bool)
                m_c2_h0 = np.zeros((32, GRID_H, GRID_W), dtype=bool)

                for f_i in range(32):
                    c2_p = [
                        dict(score=p["score"], presence=p["presence"], mask=p["mask_grid"])
                        for p in c2_frames[f_i]["props"]
                    ]
                    i_c2_h1 = S.top1(c2_p)
                    if i_c2_h1 is not None:
                        m_c2_h1[f_i] = c2_p[i_c2_h1]["mask"]
                        jt_val = c2_p[i_c2_h1]["score"] * c2_p[i_c2_h1]["presence"]
                        if jt_val >= cal_tau:
                            m_c2_h1_cal[f_i] = c2_p[i_c2_h1]["mask"]
                        if jt_val >= 0.25 and c2_p[i_c2_h1]["score"] >= 0.40:
                            m_c2_h1_hi[f_i] = c2_p[i_c2_h1]["mask"]
                    i_c2_h0 = _oracle_h0_idx(c2_p, target[f_i])
                    if i_c2_h0 is not None:
                        m_c2_h0[f_i] = c2_p[i_c2_h0]["mask"]

                # a_c2_rescue: use StageOne's 3D-linked selected masks when non-empty; rescue empty operands with c2_h1_hi (or c2_h1_cal)
                m_a_rescue = m_a if m_a.any() else (m_c2_h1_hi if m_c2_h1_hi.any() else m_c2_h1_cal)

                for sc_name in ("a", "e", "k", "j1_h1", "j1_h0"):
                    s_val, s_empty, s_fr, _ = static_op[sc_name]
                    pair_lifts[sc_name].append(s_val)
                    empty_operands[sc_name] += s_empty
                    pr_records[sc_name] += s_fr

                dyn_seen: dict[bytes, tuple[Any, int, list[dict[str, Any]]]] = {
                    static_op["a"][3]: (static_op["a"][0], static_op["a"][1], static_op["a"][2])
                }
                dyn_masks = {
                    "c2_h1": m_c2_h1,
                    "c2_h1_cal": m_c2_h1_cal,
                    "c2_h1_hi": m_c2_h1_hi,
                    "c2_h0": m_c2_h0,
                    "a_c2_rescue": m_a_rescue,
                }
                for c, mc in dyn_masks.items():
                    mb = mc.tobytes()
                    if mb in dyn_seen:
                        d_val, d_empty, d_fr = dyn_seen[mb]
                    else:
                        d_val, _ = R.fit_lift(name, mc, g)
                        d_empty = 0 if mc.any() else 1
                        d_fr = G.precision_recall(mc, target)
                        dyn_seen[mb] = (d_val, d_empty, d_fr)
                    pair_lifts[c].append(d_val)
                    empty_operands[c] += d_empty
                    pr_records[c] += d_fr

            truth = float(ref["task"]["ground_truth"])
            factor = R.unit_factor(ref["task"]["question"])
            item_rec: dict[str, Any] = dict(
                item_id=iid,
                capture=cap,
                room=ref["task"]["room"],
                dataset=G.dataset(cap),
                dataset3=G.fine(cap),
                gaps={},
            )
            for c in cells:
                lifted = R.gap_value(pair_lifts[c])
                gap = R.round_gap(lifted)
                item_rec["gaps"][c] = gap
                item_rec[c] = 100.0 * R.official_mra(None if gap is None else gap * factor, truth)
            out_rows.append(item_rec)

    # Sort out_rows by item_id and verify baseline a = 55.81 and ceiling e = 69.57
    out_rows.sort(key=lambda r: r["item_id"])
    mean_a = round(float(np.mean([r["a"] for r in out_rows])), 2)
    mean_e = round(float(np.mean([r["e"] for r in out_rows])), 2)
    assert abs(mean_a - 55.81) <= 0.02, f"Baseline a mean mismatch: {mean_a} != 55.81"
    assert abs(mean_e - 69.57) <= 0.02, f"Ceiling e mean mismatch: {mean_e} != 69.57"

    boot = R.Bootstrap(refs)
    summary_cells = {}
    for c in cells:
        m_abs = boot.metric(out_rows, c)
        m_vs_a = boot.metric([dict(r, delta=r[c] - r["a"]) for r in out_rows], "delta")
        m_vs_h1 = boot.metric([dict(r, delta=r[c] - r["j1_h1"]) for r in out_rows], "delta")
        m_vs_k = boot.metric([dict(r, delta=r[c] - r["k"]) for r in out_rows], "delta")
        pr_agg = G.summarize_pr(pr_records[c])
        summary_cells[c] = {
            "mra": round(float(m_abs["mean"]), 2),
            "ci95": [round(float(m_abs["ci95"][0]), 2), round(float(m_abs["ci95"][1]), 2)],
            "delta_vs_a": round(float(m_vs_a["mean"]), 2),
            "delta_vs_a_ci95": [round(float(m_vs_a["ci95"][0]), 2), round(float(m_vs_a["ci95"][1]), 2)],
            "delta_vs_j1_h1": round(float(m_vs_h1["mean"]), 2),
            "delta_vs_j1_h1_ci95": [round(float(m_vs_h1["ci95"][0]), 2), round(float(m_vs_h1["ci95"][1]), 2)],
            "delta_vs_k": round(float(m_vs_k["mean"]), 2),
            "delta_vs_k_ci95": [round(float(m_vs_k["ci95"][0]), 2), round(float(m_vs_k["ci95"][1]), 2)],
            "frame_precision": round(float(pr_agg["precision"]) * 100.0, 2) if pr_agg["precision"] is not None else 0.0,
            "frame_recall": round(float(pr_agg["recall"]) * 100.0, 2) if pr_agg["recall"] is not None else 0.0,
            "empty_gt_fp_anchors": int(pr_agg["pred_on_empty_gt"]),
            "empty_operands_of_234": int(empty_operands[c]),
        }

    # Per-dataset breakdown
    by_ds = {}
    for ds in G.DATASETS3:
        sub = [r for r in out_rows if r["dataset3"] == ds]
        by_ds[ds] = {
            "items": len(sub),
            "rooms": len({(r["dataset"], r["room"]) for r in sub}),
            "mra": {c: round(float(np.mean([r[c] for r in sub])), 2) for c in cells},
        }

    def _pct(arr: list[float], thr: float) -> float:
        return round(100.0 * float(np.mean(np.asarray(arr) >= thr)), 2) if arr else 0.0

    box_stats = {
        "num_k_anchors": len(dev117_top1_box_ious),
        "num_small_lt1pct_anchors": len(dev117_small_top1_box_ious),
        "num_heater_anchors": len(dev117_heater_top1_box_ious),
        "all_box_iou70_top1_pct": _pct(dev117_top1_box_ious, 0.70),
        "all_box_iou70_top5_pct": _pct(dev117_top5_box_ious, 0.70),
        "all_box_iou50_top1_pct": _pct(dev117_top1_box_ious, 0.50),
        "all_box_iou50_top5_pct": _pct(dev117_top5_box_ious, 0.50),
        "small_lt1pct_box_iou70_top1_pct": _pct(dev117_small_top1_box_ious, 0.70),
        "small_lt1pct_box_iou70_top5_pct": _pct(dev117_small_top5_box_ious, 0.70),
        "small_lt1pct_box_iou50_top1_pct": _pct(dev117_small_top1_box_ious, 0.50),
        "small_lt1pct_box_iou50_top5_pct": _pct(dev117_small_top5_box_ious, 0.50),
        "heater_box_iou50_top1_pct": _pct(dev117_heater_top1_box_ious, 0.50),
    }

    return {
        "items": len(out_rows),
        "captures": len(items_by_cap),
        "rooms": len({(r["dataset"], r["room"]) for r in out_rows}),
        "cal_tau": cal_tau,
        "box_iou_on_k_anchors": box_stats,
        "cells": summary_cells,
        "by_dataset": by_ds,
        "eval_seconds": round(time.perf_counter() - t0, 2),
    }


# ---------------------------------------------------------------------------
# 6. Main Training & Evaluation Loop
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="KT-4 C2 SAM 3 Native-Res Detector/Presence LoRA Pilot")
    ap.add_argument("--steps", type=int, default=1000, help="Total training steps")
    ap.add_argument("--eval-every", type=int, default=250, help="Evaluate K1-heldout every N steps")
    ap.add_argument("--dev117-steps", default="0,500,1000", help="Comma-separated steps to run full 46-capture DEV-MASK 117 eval")
    ap.add_argument("--lr-lora", type=float, default=1e-4, help="Learning rate for LoRA attention weights")
    ap.add_argument("--lr-heads", type=float, default=1e-4, help="Learning rate for presence and scoring heads")
    ap.add_argument("--lr-bbox", type=float, default=2e-5, help="Learning rate for bbox_embed head")
    ap.add_argument("--lora-rank", type=int, default=16)
    ap.add_argument("--lora-alpha", type=float, default=32.0)
    ap.add_argument("--num-images-per-step", type=int, default=2)
    ap.add_argument("--queries-per-image", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20261128)
    ap.add_argument("--out-dir", default="/scratch/jjyeung/orch_home_distill/work_c2_sam3/run_v1")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    dev117_step_set = {int(x.strip()) for x in args.dev117_steps.split(",") if x.strip()}

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    # 1. STRICT ZERO-LEAKAGE ROOM EXCLUSION GUARD AT STARTUP
    train_recs, val_recs, guard, audit = build_clean_k1_splits()
    guard.verify_canaries()
    assert audit["train_captures"] == 233 and audit["train_rooms"] == 214, f"Unexpected train split: {audit}"
    assert audit["val_captures"] == 53 and audit["val_rooms"] == 50, f"Unexpected val split: {audit}"
    assert audit["room_overlap"] == 0, f"Leakage guard failed: {audit}"

    # Explicitly cross-check against all 46 captures / 35 rooms of DEV-MASK 117 (PROMPTS_J1.json)
    p_j1 = G.read_json(G.PROMPTS_J1)
    dev117_caps = {c["capture"] for c in p_j1["captures"]}
    dev117_room_keys = set()
    for c in p_j1["captures"]:
        dev117_room_keys.update(canonical_room_keys(c["capture"]))
    train_caps = {r.canonical for r in train_recs}
    train_rooms = {r.room for r in train_recs}
    train_room_keys = set()
    for r in train_recs:
        train_room_keys.update(canonical_room_keys(r.canonical, r.room))
    val_caps = {r.canonical for r in val_recs}
    val_rooms = {r.room for r in val_recs}
    val_room_keys = set()
    for r in val_recs:
        val_room_keys.update(canonical_room_keys(r.canonical, r.room))

    assert len(train_caps & dev117_caps) == 0, f"FATAL LEAK: train_caps & dev117_caps = {train_caps & dev117_caps}"
    assert len(train_room_keys & dev117_room_keys) == 0, f"FATAL LEAK: train_room_keys & dev117_room_keys = {train_room_keys & dev117_room_keys}"
    assert len(val_caps & dev117_caps) == 0, f"FATAL LEAK: val_caps & dev117_caps = {val_caps & dev117_caps}"
    assert len(val_room_keys & dev117_room_keys) == 0, f"FATAL LEAK: val_room_keys & dev117_room_keys = {val_room_keys & dev117_room_keys}"

    print(json.dumps({
        "event": "ZERO_LEAKAGE_VERIFIED",
        "train_captures": len(train_recs),
        "train_rooms": len(train_rooms),
        "k1_heldout_captures": len(val_recs),
        "k1_heldout_rooms": len(val_rooms),
        "dev_mask_117_captures": len(dev117_caps),
        "train_vs_dev117_room_overlap": len(train_room_keys & dev117_room_keys),
        "train_vs_k1heldout_room_overlap": len(train_room_keys & val_room_keys),
        "all_canaries_passed": True,
    }), flush=True)

    # 2. Index K1 train (233 captures) and K1-heldout (53 captures), with local /scratch cache
    index_cache_path = out_dir.parent / "k1_index_cache_v1.pt"
    if index_cache_path.is_file():
        cached_idx = torch.load(index_cache_path, weights_only=False)
        train_data, val_data = cached_idx["train_data"], cached_idx["val_data"]
    else:
        train_data = index_k1_captures(train_recs, is_train=True)
        val_data = index_k1_captures(val_recs, is_train=False)
        torch.save({"train_data": train_data, "val_data": val_data}, index_cache_path)
    print(json.dumps({
        "event": "K1_INDEXED",
        "train_stats": train_data["stats"],
        "val_stats": val_data["stats"],
    }), flush=True)

    # 3. Build SAM 3 model & attach C2 LoRA + trainable presence/scoring heads
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t_load = time.perf_counter()
    model = build_sam3_image_model(
        checkpoint_path=str(G.SAM3_CHECKPOINT),
        device=str(device),
        eval_mode=False,
        load_from_HF=False,
        enable_segmentation=True,
    )
    lora_info = attach_c2_lora_and_heads(
        model,
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
        train_bbox_head=True,
    )
    loss_wrapper = build_sam3_loss_wrapper(device)
    model.matcher = loss_wrapper.matcher
    print(json.dumps({
        "event": "MODEL_READY",
        "load_seconds": round(time.perf_counter() - t_load, 2),
        **lora_info,
    }), flush=True)

    # 4. Pre-cache K1-heldout FPN top features once (frozen vision backbone -> ~6s)
    t_cache = time.perf_counter()
    k1_eval_cache = build_k1_heldout_eval_cache(model, val_data, device=device, frames_per_capture=2, seed=args.seed)
    print(json.dumps({
        "event": "K1_HELDOUT_CACHE_READY",
        "cached_frames": len(k1_eval_cache),
        "total_eval_queries": sum(len(x["queries"]) for x in k1_eval_cache),
        "cache_seconds": round(time.perf_counter() - t_cache, 2),
    }), flush=True)

    # 5. Configure AdamW optimizer with parameter groups + cosine LR schedule
    lora_params = []
    head_params = []
    bbox_params = []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if "parametrizations" in name:
            lora_params.append(p)
        elif "bbox_embed" in name:
            bbox_params.append(p)
        else:
            head_params.append(p)

    optimizer = torch.optim.AdamW(
        [
            {"params": lora_params, "lr": args.lr_lora, "weight_decay": 1e-2},
            {"params": head_params, "lr": args.lr_heads, "weight_decay": 1e-2},
            {"params": bbox_params, "lr": args.lr_bbox, "weight_decay": 1e-2},
        ],
        betas=(0.9, 0.95),
    )

    def lr_lambda(step: int) -> float:
        warmup = min(50, max(10, args.steps // 10))
        if step < warmup:
            return float(step + 1) / float(warmup)
        progress = float(step - warmup) / float(max(1, args.steps - warmup))
        return 0.1 + 0.9 * 0.5 * (1.0 + math.cos(math.pi * min(1.0, progress)))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=lr_lambda)

    history: dict[str, Any] = {
        "args": vars(args),
        "zero_leakage_audit": audit,
        "lora_info": lora_info,
        "train_stats": train_data["stats"],
        "val_stats": val_data["stats"],
        "k1_heldout_evals": {},
        "dev_mask_117_evals": {},
        "train_log": [],
    }

    rng = random.Random(args.seed)
    best_k1_score = -1.0
    best_step = 0
    best_state_dict = None

    # Helper to run evaluation at a given step
    def run_eval_at_step(step: int, force_dev117: bool = False):
        nonlocal best_k1_score, best_step, best_state_dict
        k1_res = evaluate_k1_heldout(model, k1_eval_cache, device=device)
        history["k1_heldout_evals"][str(step)] = k1_res
        print(json.dumps({"event": "EVAL_K1_HELDOUT", "step": step, **k1_res}), flush=True)

        # Composite K1-heldout selection score (0 DEV-MASK 117 leakage!):
        # balances joint_auroc + small_lt1pct_box_iou70_h1_active_pct + all_box_iou70_h1_active_pct - 0.5 * h1_empty_frame_fp_rate_pct
        comp_score = (
            k1_res["joint_auroc"]
            + k1_res["small_lt1pct_box_iou70_h1_active_pct"]
            + k1_res["all_box_iou70_h1_active_pct"]
            - 0.5 * k1_res["h1_empty_frame_fp_rate_pct"]
        )
        if step > 0 and comp_score > best_k1_score:
            best_k1_score = comp_score
            best_step = step
            best_state_dict = extract_trainable_state_dict(model)
            torch.save(
                {"step": step, "k1_heldout": k1_res, "state_dict": best_state_dict},
                out_dir / "best_c2_lora.pt",
            )

        if step in dev117_step_set or force_dev117:
            dev_res = evaluate_dev_mask_117(model, device=device, cal_tau=k1_res["cal_tau"])
            history["dev_mask_117_evals"][str(step)] = dev_res
            print(json.dumps({
                "event": "EVAL_DEV_MASK_117",
                "step": step,
                "cal_tau": k1_res["cal_tau"],
                "a": dev_res["cells"]["a"]["mra"],
                "j1_h1": dev_res["cells"]["j1_h1"]["mra"],
                "c2_h1": dev_res["cells"]["c2_h1"]["mra"],
                "c2_h1_vs_a": dev_res["cells"]["c2_h1"]["delta_vs_a"],
                "c2_h1_vs_j1_h1": dev_res["cells"]["c2_h1"]["delta_vs_j1_h1"],
                "c2_h1_cal": dev_res["cells"]["c2_h1_cal"]["mra"],
                "c2_h1_cal_vs_a": dev_res["cells"]["c2_h1_cal"]["delta_vs_a"],
                "c2_h1_hi": dev_res["cells"]["c2_h1_hi"]["mra"],
                "c2_h1_hi_vs_a": dev_res["cells"]["c2_h1_hi"]["delta_vs_a"],
                "a_c2_rescue": dev_res["cells"]["a_c2_rescue"]["mra"],
                "a_c2_rescue_vs_a": dev_res["cells"]["a_c2_rescue"]["delta_vs_a"],
                "c2_h0": dev_res["cells"]["c2_h0"]["mra"],
                "j1_h0": dev_res["cells"]["j1_h0"]["mra"],
                "k": dev_res["cells"]["k"]["mra"],
                "e": dev_res["cells"]["e"]["mra"],
                "c2_h1_empty_gt_fp": dev_res["cells"]["c2_h1"]["empty_gt_fp_anchors"],
                "c2_h1_cal_empty_gt_fp": dev_res["cells"]["c2_h1_cal"]["empty_gt_fp_anchors"],
                "c2_h1_hi_empty_gt_fp": dev_res["cells"]["c2_h1_hi"]["empty_gt_fp_anchors"],
                "c2_h0_empty_operands": dev_res["cells"]["c2_h0"]["empty_operands_of_234"],
                "box_iou": dev_res["box_iou_on_k_anchors"],
                "eval_seconds": dev_res["eval_seconds"],
            }), flush=True)

        (out_dir / "metrics_history.json").write_text(json.dumps(history, indent=2) + "\n")

    # 6. Step 0 Evaluation (Frozen SAM 3 baseline before any weight update; reuse saved Step 0 if present)
    hist_file = out_dir / "metrics_history.json"
    if hist_file.is_file():
        try:
            prev_hist = json.loads(hist_file.read_text())
            if "0" in prev_hist.get("k1_heldout_evals", {}) and "0" in prev_hist.get("dev_mask_117_evals", {}):
                history["k1_heldout_evals"]["0"] = prev_hist["k1_heldout_evals"]["0"]
                history["dev_mask_117_evals"]["0"] = prev_hist["dev_mask_117_evals"]["0"]
                print(json.dumps({"event": "EVAL_K1_HELDOUT", "step": 0, **history["k1_heldout_evals"]["0"], "reused_from_cache": True}), flush=True)
                dev0 = history["dev_mask_117_evals"]["0"]
                print(json.dumps({
                    "event": "EVAL_DEV_MASK_117",
                    "step": 0,
                    "reused_from_cache": True,
                    "cal_tau": dev0["cal_tau"],
                    "a": dev0["cells"]["a"]["mra"],
                    "j1_h1": dev0["cells"]["j1_h1"]["mra"],
                    "c2_h1": dev0["cells"]["c2_h1"]["mra"],
                    "c2_h1_vs_a": dev0["cells"]["c2_h1"]["delta_vs_a"],
                    "c2_h1_vs_j1_h1": dev0["cells"]["c2_h1"]["delta_vs_j1_h1"],
                    "c2_h1_cal": dev0["cells"]["c2_h1_cal"]["mra"],
                    "c2_h1_cal_vs_a": dev0["cells"]["c2_h1_cal"]["delta_vs_a"],
                    "c2_h1_hi": dev0["cells"]["c2_h1_hi"]["mra"],
                    "c2_h1_hi_vs_a": dev0["cells"]["c2_h1_hi"]["delta_vs_a"],
                    "a_c2_rescue": dev0["cells"]["a_c2_rescue"]["mra"],
                    "a_c2_rescue_vs_a": dev0["cells"]["a_c2_rescue"]["delta_vs_a"],
                    "c2_h0": dev0["cells"]["c2_h0"]["mra"],
                    "j1_h0": dev0["cells"]["j1_h0"]["mra"],
                    "k": dev0["cells"]["k"]["mra"],
                    "e": dev0["cells"]["e"]["mra"],
                    "c2_h1_empty_gt_fp": dev0["cells"]["c2_h1"]["empty_gt_fp_anchors"],
                    "c2_h1_cal_empty_gt_fp": dev0["cells"]["c2_h1_cal"]["empty_gt_fp_anchors"],
                    "c2_h1_hi_empty_gt_fp": dev0["cells"]["c2_h1_hi"]["empty_gt_fp_anchors"],
                    "c2_h0_empty_operands": dev0["cells"]["c2_h0"]["empty_operands_of_234"],
                    "box_iou": dev0["box_iou_on_k_anchors"],
                    "eval_seconds": dev0["eval_seconds"],
                }), flush=True)
            else:
                run_eval_at_step(0)
        except Exception:
            run_eval_at_step(0)
    else:
        run_eval_at_step(0)

    # 7. Training loop
    t_train_start = time.perf_counter()
    running_losses: list[dict[str, float]] = []
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    for step in range(1, args.steps + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)

        pil_imgs, caps, b_cx, b_xy, is_pos = sample_training_step_batch(
            train_data,
            rng,
            num_images=args.num_images_per_step,
            queries_per_image=args.queries_per_image,
        )
        loss, step_metrics = forward_and_compute_loss(
            model, loss_wrapper, pil_imgs, caps, b_cx, b_xy, is_pos, device=device
        )
        loss.backward()
        grad_norm = float(torch.nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], max_norm=1.0
        ).item())
        optimizer.step()
        scheduler.step()

        step_metrics["grad_norm"] = round(grad_norm, 4)
        running_losses.append(step_metrics)

        if step % 25 == 0 or step == 1:
            avg_m = {
                k: round(float(np.mean([x[k] for x in running_losses[-25:]])), 4)
                for k in running_losses[-1].keys()
            }
            peak_gib = round(torch.cuda.max_memory_reserved() / (2 ** 30), 2) if torch.cuda.is_available() else 0.0
            elapsed = round(time.perf_counter() - t_train_start, 1)
            log_entry = {
                "event": "TRAIN_STEP",
                "step": step,
                "lr": round(scheduler.get_last_lr()[0], 6),
                "peak_vram_gib": peak_gib,
                "elapsed_s": elapsed,
                **avg_m,
            }
            history["train_log"].append(log_entry)
            print(json.dumps(log_entry), flush=True)

        if step % args.eval_every == 0 or step == args.steps:
            run_eval_at_step(step)

    # Save final checkpoint and evaluate best K1-heldout checkpoint on DEV-MASK 117 if not already evaluated
    final_sd = extract_trainable_state_dict(model)
    torch.save({"step": args.steps, "state_dict": final_sd}, out_dir / "final_c2_lora.pt")
    if 9999 not in dev117_step_set and best_step > 0 and str(best_step) not in history["dev_mask_117_evals"] and best_state_dict is not None:
        model.load_state_dict(best_state_dict, strict=False)
        run_eval_at_step(best_step, force_dev117=True)

    (out_dir / "metrics_history.json").write_text(json.dumps(history, indent=2) + "\n")
    print(json.dumps({
        "event": "TRAINING_COMPLETE",
        "best_k1_step": best_step,
        "total_wall_seconds": round(time.perf_counter() - t_train_start, 2),
        "out_dir": str(out_dir),
    }), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
