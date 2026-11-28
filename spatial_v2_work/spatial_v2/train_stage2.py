"""Spatial-V2 Stage-2 Full 9B Trainer (FSDP2 / DDP / 1-GPU BF16 + Liger/Chunked CE + GCS Sync).

Supports:
  - `--frontend {corresp_stem, da3_nested}` (Arm B correspondence side-stem vs Arm C DA3-Nested trunk)
  - `--init-ckpt <path|synthetic>` (`step-544` or base `Qwen3.5-9B`, or `synthetic` for zero-disk
    exact-9B-architecture VRAM benchmarking)
  - `--stage1a-ckpt <path>` (loads winning KT-6 Stage-1A front-end weights with `fusion_gate=0`)
  - `--sharding {fsdp2, ddp, none}` (composable PyTorch FSDP2 `fully_shard` for Orchard 4x H100 80GB)
  - `--use-vla-aux` (optional Stage-2b FlowExpert continuous VLA action head at taps 12, 16, 24)
  - Exact VRAM decomposition (`weights_vram_gib`, `post_forward_vram_gib`, `activation_vram_gib`,
    `peak_vram_gib`), throughput (`steps/s`, `tokens/s`), and 4x H100 80GB FSDP2 VRAM projection.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import subprocess
import time
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional, Tuple

import numpy as np
import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler

from .data_k1_local import DEFAULT_EXCL_DIR, DEFAULT_FRAMES_ROOT, DEFAULT_MANIFEST_PATH
from .stage1a_model import DEFAULT_DA3_CKPT, DEFAULT_QWEN_VISUAL_CKPT, DA3GiantTeacher
from .stage2_data import (
    DEFAULT_E05_JSONL,
    Stage2SpatialDataset,
    build_synthetic_stage2_batch,
    collate_stage2_batch,
)
from .stage2_model import HAS_LIGER_FLCE, FrontendType, SpatialV2Stage2Model


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def init_distributed() -> Tuple[bool, int, int, int]:
    if "RANK" in os.environ and "WORLD_SIZE" in os.environ:
        rank = int(os.environ["RANK"])
        world_size = int(os.environ["WORLD_SIZE"])
        local_rank = int(os.environ.get("LOCAL_RANK", 0))
        backend = "nccl" if torch.cuda.is_available() else "gloo"
        dist.init_process_group(backend=backend)
        if torch.cuda.is_available():
            torch.cuda.set_device(local_rank)
        return True, rank, world_size, local_rank
    return False, 0, 1, 0


def cosine_lr_multiplier(step: int, total_steps: int, warmup_steps: int, min_ratio: float = 0.05) -> float:
    if step < warmup_steps:
        return float(step + 1) / float(max(1, warmup_steps))
    denom = max(1, total_steps - warmup_steps)
    progress = min(1.0, float(step - warmup_steps) / float(denom))
    return min_ratio + 0.5 * (1.0 - min_ratio) * (1.0 + math.cos(math.pi * progress))


class StatelessLowMemAdamW(torch.optim.Optimizer):
    """Zero-extra-VRAM decoupled weight-decay + RMS-normalized update for 1-GPU 49GB 9B smoke runs.

    When testing a full 9.5B-trainable model in BF16 on a single 49 GB GPU, weights (18.4 GiB) +
    BF16 gradients (17.8 GiB) + checkpointed activations (~3.5 GiB) consume ~39.7 GiB. Allocating
    71 GiB of FP32 AdamW state tensors on that single GPU would exceed 49 GB (whereas on 4x H100 80GB
    FSDP2 shards them to 17.8 GiB/GPU). This optimizer performs decoupled weight decay + per-tensor
    RMS-normalized gradient updates in-place with 0 B of persistent GPU state overhead.
    """

    def __init__(
        self,
        params: Iterable[Dict[str, object]],
        lr: float = 1e-5,
        weight_decay: float = 0.01,
        eps: float = 1e-8,
    ) -> None:
        defaults = dict(lr=lr, weight_decay=weight_decay, eps=eps)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None):  # type: ignore[override]
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for group in self.param_groups:
            lr = float(group["lr"])
            wd = float(group.get("weight_decay", 0.0))
            eps = float(group.get("eps", 1e-8))
            for p in group["params"]:
                if p.grad is None:
                    continue
                g = p.grad
                if wd != 0.0:
                    p.mul_(1.0 - lr * wd)
                rms = g.float().pow(2).mean().sqrt().clamp_min(eps).to(p.dtype)
                p.add_(g / rms, alpha=-lr)
        return loss


def apply_fsdp2_sharding(model: SpatialV2Stage2Model) -> None:
    """Apply PyTorch composable FSDP2 (`fully_shard`) across Qwen3.5 vision, decoder layers, and front-end."""
    from torch.distributed.fsdp import MixedPrecisionPolicy, fully_shard

    mp_policy = MixedPrecisionPolicy(param_dtype=torch.bfloat16, reduce_dtype=torch.float32)
    for blk in model.lm.model.visual.blocks:
        fully_shard(blk, mp_policy=mp_policy)
    fully_shard(model.lm.model.visual, mp_policy=mp_policy)
    for layer in model.lm.model.language_model.layers:
        fully_shard(layer, mp_policy=mp_policy)
    fully_shard(model.frontend, mp_policy=mp_policy)
    fully_shard(model, mp_policy=mp_policy)


def project_4xh100_fsdp2_vram(
    total_params: int,
    trainable_params: int,
    measured_activation_gib: float,
    world_size: int = 4,
) -> Dict[str, float]:
    """Compute exact 4x H100 80GB FSDP2 (`fully_shard`) per-GPU VRAM breakdown from measured components."""
    gib = 1024.0**3
    sharded_params_bf16_gib = (total_params * 2.0) / (world_size * gib)
    sharded_grads_bf16_gib = (trainable_params * 2.0) / (world_size * gib)
    # FP32 master weight shard (4B) + exp_avg (4B) + exp_avg_sq (4B) = 12 bytes / trainable param / world_size
    sharded_adamw_fp32_gib = (trainable_params * 12.0) / (world_size * gib)
    # 2x all-gather prefetch buffer for a single Qwen3_5DecoderLayer (~0.25B params * 2B * 2 = ~0.95 GiB)
    allgather_buffer_gib = 1.10
    cuda_nccl_context_gib = 2.40
    projected_peak_gib = (
        sharded_params_bf16_gib
        + sharded_grads_bf16_gib
        + sharded_adamw_fp32_gib
        + allgather_buffer_gib
        + measured_activation_gib
        + cuda_nccl_context_gib
    )
    return {
        "world_size": world_size,
        "sharded_params_bf16_gib": round(sharded_params_bf16_gib, 3),
        "sharded_grads_bf16_gib": round(sharded_grads_bf16_gib, 3),
        "sharded_adamw_fp32_gib": round(sharded_adamw_fp32_gib, 3),
        "allgather_buffer_gib": round(allgather_buffer_gib, 3),
        "measured_activation_gib": round(measured_activation_gib, 3),
        "cuda_nccl_context_gib": round(cuda_nccl_context_gib, 3),
        "projected_per_h100_peak_gib": round(projected_peak_gib, 3),
        "h100_80gb_headroom_gib": round(79.18 - projected_peak_gib, 3),
    }


def sync_checkpoint_to_gcs(local_path: Path, gcs_uri_prefix: str) -> bool:
    """Sync checkpoint from node-local `/tmp` directly to `gs://cmu-gpucloud-jjyeung/spatial_v2/...`."""
    if not gcs_uri_prefix:
        return False
    dst = gcs_uri_prefix.rstrip("/") + "/" + local_path.name
    cmd = ["gcloud", "storage", "cp", str(local_path), dst]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        print(f"[GCS Sync Warning] Failed to upload {local_path} -> {dst}: {res.stderr.strip()}", flush=True)
        return False
    print(f"[GCS Sync OK] Uploaded {local_path} -> {dst}", flush=True)
    return True


def save_stage2_checkpoint(
    path: Path,
    model: SpatialV2Stage2Model,
    optimizer: torch.optim.Optimizer,
    step: int,
    args: argparse.Namespace,
    metrics: Dict[str, object],
    gcs_sync_uri: Optional[str] = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".pt.tmp")
    payload = {
        "step": step,
        "frontend": model.frontend_type,
        "tap_layers": model.tap_layers,
        "freeze_scale_donor": model.freeze_scale_donor,
        "use_vla_aux": model.use_vla_aux,
        "tiny": model.tiny,
        "args": vars(args),
        "metrics": metrics,
        "frontend_state_dict": model.frontend.state_dict(),
        "front_pose_head": model.front_pose_head.state_dict(),
        "front_depth_head": model.front_depth_head.state_dict(),
        "tap_pose_heads": model.tap_pose_heads.state_dict(),
        "tap_depth_heads": model.tap_depth_heads.state_dict(),
        "tap_cam_projs": model.tap_cam_projs.state_dict(),
        "sf2_loss": model.sf2_loss.state_dict(),
        "front_sf2_probe": model.front_sf2_probe.state_dict(),
        "scale_donor": model.scale_donor.state_dict(),
    }
    if model.flow_expert is not None:
        payload["flow_expert"] = model.flow_expert.state_dict()
    if args.save_full_lm or model.tiny:
        payload["lm_state_dict"] = model.lm.state_dict()
        payload["optimizer_state_dict"] = optimizer.state_dict()
    torch.save(payload, tmp)
    os.replace(tmp, path)
    if gcs_sync_uri:
        sync_checkpoint_to_gcs(path, gcs_sync_uri)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train Spatial-V2 Stage-2 Full 9B Model.")
    ap.add_argument("--frontend", type=str, choices=("corresp_stem", "da3_nested"), required=True)
    ap.add_argument("--out-dir", type=str, required=True)
    ap.add_argument(
        "--init-ckpt",
        type=str,
        default="synthetic",
        help="Path to Qwen3.5-9B / step-544 checkpoint directory or safetensors, or 'synthetic' for 0-disk init",
    )
    ap.add_argument("--qwen-visual-ckpt", type=str, default=DEFAULT_QWEN_VISUAL_CKPT)
    ap.add_argument("--da3-ckpt", type=str, default=DEFAULT_DA3_CKPT)
    ap.add_argument("--stage1a-ckpt", type=str, default=None, help="Winning KT-6 Stage-1A front-end checkpoint")
    ap.add_argument("--sharding", type=str, choices=("fsdp2", "ddp", "none"), default="none")
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--num-views", type=int, default=8)
    ap.add_argument("--grid-h", type=int, default=20)
    ap.add_argument("--grid-w", type=int, default=20)
    ap.add_argument("--seq-len", type=int, default=128)
    ap.add_argument("--teacher-dim", type=int, default=3072)
    ap.add_argument("--lm-lr", type=float, default=1e-5)
    ap.add_argument("--frontend-lr", type=float, default=5e-5)
    ap.add_argument("--head-lr", type=float, default=2e-4)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--warmup-steps", type=int, default=50)
    ap.add_argument("--max-grad-norm", type=float, default=1.0)
    ap.add_argument("--lora-rank", type=int, default=16)
    ap.add_argument("--lora-alpha", type=float, default=32.0)
    ap.add_argument("--unfreeze-last-k", type=int, default=2)
    ap.add_argument("--no-freeze-scale-donor", action="store_true")
    ap.add_argument("--freeze-qwen-vision", action="store_true")
    ap.add_argument("--use-vla-aux", action="store_true")
    ap.add_argument("--no-grad-ckpt", action="store_true")
    ap.add_argument("--synthetic-data", action="store_true", help="Zero-disk synthetic data for VRAM smoke tests")
    ap.add_argument("--has-4d-teacher", action="store_true", help="Enable 4D dynamic teacher targets in synthetic mode")
    ap.add_argument("--tiny", action="store_true", help="Tiny 32-layer Qwen3.5 config for fast CPU unit tests")
    ap.add_argument("--single-gpu-opt", type=str, choices=("auto", "adamw", "stateless"), default="auto")
    ap.add_argument("--save-every", type=int, default=250)
    ap.add_argument("--save-full-lm", action="store_true")
    ap.add_argument("--skip-final-save", action="store_true")
    ap.add_argument("--gcs-sync-uri", type=str, default="")
    ap.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST_PATH)
    ap.add_argument("--frames-root", type=str, default=DEFAULT_FRAMES_ROOT)
    ap.add_argument("--excl-dir", type=str, default=DEFAULT_EXCL_DIR)
    ap.add_argument("--e05-jsonl", type=str, default=DEFAULT_E05_JSONL)
    ap.add_argument("--random-subsample", action="store_true")
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--log-every", type=int, default=1)
    ap.add_argument("--seed", type=int, default=20261128)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    is_dist, rank, world_size, local_rank = init_distributed()
    is_main = rank == 0
    seed_everything(args.seed + rank)

    device = torch.device(f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu")
    amp_dtype = torch.bfloat16 if device.type == "cuda" else torch.float32
    use_amp = device.type == "cuda"

    out_dir = Path(args.out_dir)
    if is_main:
        out_dir.mkdir(parents=True, exist_ok=True)

    if device.type == "cuda":
        torch.cuda.set_device(device)
        _ = torch.empty(1, device=device)
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)

    # 1. Build Stage-2 Model (construct directly in bf16 on GPU when CUDA is available to avoid 36GB fp32 CPU spike)
    t_init0 = time.monotonic()
    use_synth_ckpt = args.tiny or args.synthetic_data or str(args.init_ckpt).lower() in ("", "none", "synthetic")
    model = SpatialV2Stage2Model(
        frontend=args.frontend,
        init_ckpt=None if use_synth_ckpt else args.init_ckpt,
        qwen_visual_ckpt=None if use_synth_ckpt else args.qwen_visual_ckpt,
        da3_ckpt=None if use_synth_ckpt else args.da3_ckpt,
        stage1a_ckpt=args.stage1a_ckpt,
        teacher_dim=64 if args.tiny else args.teacher_dim,
        tap_layers=(16, 24),
        freeze_scale_donor=(not args.no_freeze_scale_donor),
        freeze_qwen_vision=args.freeze_qwen_vision,
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
        unfreeze_last_k=args.unfreeze_last_k,
        use_vla_aux=args.use_vla_aux,
        gradient_checkpointing=(not args.no_grad_ckpt),
        tiny=args.tiny,
        param_dtype=amp_dtype if device.type == "cuda" else torch.float32,
    ).to(device=device, dtype=amp_dtype if device.type == "cuda" else torch.float32)

    param_counts = model.parameter_counts()
    init_time_s = time.monotonic() - t_init0

    weights_vram_gib = (
        float(torch.cuda.memory_allocated(device)) / (1024.0**3) if device.type == "cuda" else 0.0
    )

    # 2. Apply FSDP2 (`fully_shard`) or DDP if running multi-GPU
    train_engine: nn.Module = model
    if is_dist and args.sharding == "fsdp2":
        apply_fsdp2_sharding(model)
        train_engine = model
    elif is_dist and args.sharding == "ddp":
        train_engine = DDP(
            model,
            device_ids=[local_rank] if device.type == "cuda" else None,
            find_unused_parameters=False,
        )

    # 3. Optimizer selection (auto-selects StatelessLowMemAdamW on single <=49GB GPU with >3B trainable params)
    param_groups = model.build_param_groups(
        lm_lr=args.lm_lr,
        frontend_lr=args.frontend_lr,
        head_lr=args.head_lr,
        weight_decay=args.weight_decay,
    )
    use_stateless_opt = args.single_gpu_opt == "stateless" or (
        args.single_gpu_opt == "auto"
        and world_size == 1
        and param_counts["total_trainable"] > 3_000_000_000
    )
    if use_stateless_opt:
        optimizer: torch.optim.Optimizer = StatelessLowMemAdamW(
            param_groups, lr=args.lm_lr, weight_decay=args.weight_decay
        )
        opt_name = "StatelessLowMemAdamW (1-GPU 49GB full-9B mode)"
    else:
        optimizer = torch.optim.AdamW(param_groups, betas=(0.9, 0.95), eps=1e-8)
        opt_name = "torch.optim.AdamW"

    # 4. Data pipeline (real leakage-verified K1+E05 dataset or zero-disk synthetic batch stream)
    train_loader: Optional[DataLoader] = None
    train_sampler: Optional[DistributedSampler] = None
    teacher: Optional[DA3GiantTeacher] = None
    split_summary: Dict[str, object] = {"mode": "synthetic_zero_disk"}

    if not args.synthetic_data:
        train_ds = Stage2SpatialDataset(
            split="train",
            num_views=args.num_views,
            grid_h=args.grid_h,
            grid_w=args.grid_w,
            max_seq_len=args.seq_len,
            vocab_size=model.lm.config.text_config.vocab_size,
            manifest_path=args.manifest,
            frames_root=args.frames_root,
            excl_dir=args.excl_dir,
            e05_jsonl=args.e05_jsonl,
            random_subsample=args.random_subsample,
            seed=args.seed,
        )
        split_summary = getattr(train_ds, "split_summary", {"train_captures": len(train_ds)})
        train_sampler = (
            DistributedSampler(train_ds, num_replicas=world_size, rank=rank, shuffle=True, seed=args.seed)
            if is_dist
            else None
        )
        # Dedicated seeded DataLoader generator (fixes Codex Stage-1A item #2)
        dl_gen = torch.Generator().manual_seed(args.seed)
        train_loader = DataLoader(
            train_ds,
            batch_size=args.batch_size,
            shuffle=(train_sampler is None),
            sampler=train_sampler,
            num_workers=args.num_workers,
            pin_memory=(device.type == "cuda"),
            drop_last=True,
            collate_fn=collate_stage2_batch,
            generator=dl_gen,
        )
        teacher = DA3GiantTeacher(
            ckpt_path=None if args.tiny else args.da3_ckpt,
            tiny=args.tiny,
            tiny_dim=64 if args.tiny else args.teacher_dim,
        ).to(device=device, dtype=amp_dtype).eval()

    hm, wm = args.grid_h // 2, args.grid_w // 2
    tokens_per_sample = args.num_views * hm * wm + args.seq_len
    tokens_per_step = tokens_per_sample * args.batch_size * args.grad_accum * world_size

    if is_main:
        header = {
            "frontend": args.frontend,
            "world_size": world_size,
            "sharding": args.sharding,
            "device": str(device),
            "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu",
            "optimizer": opt_name,
            "liger_flce_available": HAS_LIGER_FLCE,
            "gradient_checkpointing": not args.no_grad_ckpt,
            "freeze_scale_donor": not args.no_freeze_scale_donor,
            "use_vla_aux": args.use_vla_aux,
            "tap_layers": list(model.tap_layers),
            "num_views": args.num_views,
            "grid_hw": [args.grid_h, args.grid_w],
            "seq_len": args.seq_len,
            "tokens_per_sample": tokens_per_sample,
            "tokens_per_step": tokens_per_step,
            "weights_vram_gib": round(weights_vram_gib, 3),
            "init_time_s": round(init_time_s, 3),
            "param_counts": param_counts,
            "split_summary": split_summary,
        }
        print(f"[Stage-2 Startup] {json.dumps(header)}", flush=True)
        (out_dir / "config_summary.json").write_text(json.dumps(header, indent=2) + "\n")

    log_f = (out_dir / "train_log.jsonl").open("a") if is_main else None
    data_iter = iter(train_loader) if train_loader is not None else None
    epoch = 0
    step_times: List[float] = []
    loss_curve: List[Dict[str, object]] = []
    max_activation_vram_gib = 0.0

    train_engine.train()
    for step in range(1, args.steps + 1):
        t_step0 = time.monotonic()
        lr_mult = cosine_lr_multiplier(step - 1, args.steps, args.warmup_steps)
        for pg in optimizer.param_groups:
            pg["lr"] = float(pg["base_lr"]) * lr_mult

        optimizer.zero_grad(set_to_none=True)
        accum_metrics: Dict[str, float] = {}
        post_fwd_vram_gib = 0.0

        for micro in range(args.grad_accum):
            if args.synthetic_data:
                gpu_batch, teacher_feats = build_synthetic_stage2_batch(
                    batch_size=args.batch_size,
                    num_views=args.num_views,
                    grid_h=args.grid_h,
                    grid_w=args.grid_w,
                    seq_len=args.seq_len,
                    vocab_size=model.lm.config.text_config.vocab_size,
                    teacher_dim=64 if args.tiny else args.teacher_dim,
                    has_4d_teacher=args.has_4d_teacher,
                    include_vla=args.use_vla_aux,
                    device=device,
                    dtype=amp_dtype,
                    seed=args.seed + step * 100 + micro + rank * 10000,
                )
            else:
                assert data_iter is not None and train_loader is not None and teacher is not None
                try:
                    raw_batch = next(data_iter)
                except StopIteration:
                    epoch += 1
                    if hasattr(train_loader.dataset, "set_epoch"):
                        train_loader.dataset.set_epoch(epoch)  # type: ignore[union-attr]
                    if train_sampler is not None:
                        train_sampler.set_epoch(epoch)
                    data_iter = iter(train_loader)
                    raw_batch = next(data_iter)
                gpu_batch = {
                    k: v.to(device, non_blocking=True) for k, v in raw_batch.items() if torch.is_tensor(v)
                }
                with torch.no_grad(), torch.amp.autocast(device_type=device.type, dtype=amp_dtype, enabled=use_amp):
                    teacher_feats = teacher(gpu_batch["rgb_da3"])

            sync_ctx = (
                train_engine.no_sync()  # type: ignore[operator]
                if (is_dist and args.sharding == "ddp" and micro < args.grad_accum - 1)
                else torch.enable_grad()
            )
            with sync_ctx:
                with torch.amp.autocast(device_type=device.type, dtype=amp_dtype, enabled=use_amp):
                    _, loss, loss_dict = train_engine(
                        rgb_qwen=gpu_batch["rgb_qwen"],
                        rgb_da3=gpu_batch["rgb_da3"],
                        input_ids=gpu_batch["input_ids"],
                        attention_mask=gpu_batch["attention_mask"],
                        labels=gpu_batch["labels"],
                        timestamps=gpu_batch["timestamps"],
                        view_mask=gpu_batch["view_mask"],
                        batch=gpu_batch,
                        teacher_feats=teacher_feats,
                        return_logits=False,
                    )
                    scaled_loss = loss / float(args.grad_accum)

                if device.type == "cuda":
                    post_fwd_vram_gib = max(
                        post_fwd_vram_gib, float(torch.cuda.memory_allocated(device)) / (1024.0**3)
                    )

                scaled_loss.backward()

            for mk, mv in loss_dict.items():
                val = float(mv.item()) if torch.is_tensor(mv) else float(mv)
                accum_metrics[mk] = accum_metrics.get(mk, 0.0) + val / float(args.grad_accum)

        grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm).item())
        if not math.isfinite(grad_norm):
            raise RuntimeError(f"Non-finite gradient norm detected at step {step}: grad_norm={grad_norm}")
        optimizer.step()

        if device.type == "cuda":
            torch.cuda.synchronize(device)
        dt = time.monotonic() - t_step0
        step_times.append(dt)

        peak_vram_gib = (
            float(torch.cuda.max_memory_allocated(device)) / (1024.0**3) if device.type == "cuda" else 0.0
        )
        peak_reserved_gib = (
            float(torch.cuda.max_memory_reserved(device)) / (1024.0**3) if device.type == "cuda" else 0.0
        )
        act_vram_gib = max(0.0, post_fwd_vram_gib - weights_vram_gib)
        max_activation_vram_gib = max(max_activation_vram_gib, act_vram_gib)

        steps_per_sec = 1.0 / max(dt, 1e-6)
        toks_per_sec = float(tokens_per_step) / max(dt, 1e-6)

        rec: Dict[str, object] = {
            "step": step,
            "frontend": args.frontend,
            "loss": round(accum_metrics.get("total_loss", 0.0), 5),
            "l_lm": round(accum_metrics.get("l_lm", 0.0), 5),
            "l_geo": round(accum_metrics.get("l_geo", 0.0), 5),
            "l_sf2": round(accum_metrics.get("l_sf2", 0.0), 5),
            "l_vla_aux": round(accum_metrics.get("l_vla_aux", 0.0), 5),
            "geo_16_depth": round(accum_metrics.get("geo_16_depth", 0.0), 5),
            "geo_24_depth": round(accum_metrics.get("geo_24_depth", 0.0), 5),
            "geo_16_pose": round(accum_metrics.get("geo_16_pose", 0.0), 5),
            "geo_24_pose": round(accum_metrics.get("geo_24_pose", 0.0), 5),
            "sf2_feat_l16": round(accum_metrics.get("sf2_feat_l16", 0.0), 5),
            "sf2_feat_l24": round(accum_metrics.get("sf2_feat_l24", 0.0), 5),
            "fusion_gate": round(accum_metrics.get("fusion_gate", 0.0), 6),
            "grad_norm": round(grad_norm, 4),
            "step_time_s": round(dt, 4),
            "steps_per_sec": round(steps_per_sec, 4),
            "tokens_per_sec": round(toks_per_sec, 2),
            "weights_vram_gib": round(weights_vram_gib, 3),
            "post_fwd_vram_gib": round(post_fwd_vram_gib, 3),
            "activation_vram_gib": round(act_vram_gib, 3),
            "peak_vram_gib": round(peak_vram_gib, 3),
            "peak_reserved_gib": round(peak_reserved_gib, 3),
        }
        loss_curve.append(rec)

        if is_main and (step % args.log_every == 0 or step == 1 or step == args.steps):
            print(
                f"[step {step:04d}/{args.steps}] front={args.frontend} "
                f"loss={rec['loss']:.4f} (lm={rec['l_lm']:.3f} geo={rec['l_geo']:.3f} sf2={rec['l_sf2']:.3f}) "
                f"gate={rec['fusion_gate']:+.5f} gnorm={rec['grad_norm']:.2f} "
                f"{rec['steps_per_sec']:.3f} step/s ({rec['tokens_per_sec']:.1f} tok/s) "
                f"act={rec['activation_vram_gib']:.2f} GiB peak={rec['peak_vram_gib']:.2f} GiB",
                flush=True,
            )
            assert log_f is not None
            log_f.write(json.dumps(rec) + "\n")
            log_f.flush()

        if is_main and args.save_every > 0 and step % args.save_every == 0:
            save_stage2_checkpoint(
                out_dir / f"step_{step:06d}.pt",
                model,
                optimizer,
                step,
                args,
                rec,
                gcs_sync_uri=args.gcs_sync_uri,
            )

    if is_main:
        if log_f is not None:
            log_f.close()
        steady = step_times[1:] if len(step_times) > 2 else step_times
        mean_step_s = float(np.mean(steady)) if steady else 0.0
        mean_steps_per_sec = 1.0 / max(mean_step_s, 1e-6)
        mean_tokens_per_sec = float(tokens_per_step) / max(mean_step_s, 1e-6)

        h100_projection = project_4xh100_fsdp2_vram(
            total_params=param_counts["total_params"],
            trainable_params=param_counts["total_trainable"],
            measured_activation_gib=max_activation_vram_gib,
            world_size=4,
        )

        ckpt_path = out_dir / "latest.pt"
        if not args.skip_final_save:
            save_stage2_checkpoint(
                ckpt_path,
                model,
                optimizer,
                args.steps,
                args,
                loss_curve[-1] if loss_curve else {},
                gcs_sync_uri=args.gcs_sync_uri,
            )

        summary = {
            "frontend": args.frontend,
            "steps": args.steps,
            "world_size": world_size,
            "sharding": args.sharding,
            "device": str(device),
            "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu",
            "optimizer": opt_name,
            "weights_vram_gib": round(weights_vram_gib, 3),
            "max_activation_vram_gib": round(max_activation_vram_gib, 3),
            "peak_vram_gib": round(
                float(torch.cuda.max_memory_allocated(device)) / (1024.0**3) if device.type == "cuda" else 0.0,
                3,
            ),
            "peak_reserved_gib": round(
                float(torch.cuda.max_memory_reserved(device)) / (1024.0**3) if device.type == "cuda" else 0.0,
                3,
            ),
            "mean_step_time_s": round(mean_step_s, 4),
            "mean_steps_per_sec": round(mean_steps_per_sec, 4),
            "mean_tokens_per_sec": round(mean_tokens_per_sec, 2),
            "loss_step1": loss_curve[0]["loss"] if loss_curve else None,
            "loss_final": loss_curve[-1]["loss"] if loss_curve else None,
            "loss_curve": loss_curve,
            "param_counts": param_counts,
            "orchard_4xh100_fsdp2_projection": h100_projection,
            "checkpoint": str(ckpt_path) if not args.skip_final_save else None,
        }
        (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(
            f"[Stage-2 DONE] frontend={args.frontend} peak_vram={summary['peak_vram_gib']:.2f} GiB "
            f"(weights={summary['weights_vram_gib']:.2f} GiB, act={summary['max_activation_vram_gib']:.2f} GiB) "
            f"steady={summary['mean_steps_per_sec']:.3f} step/s ({summary['mean_tokens_per_sec']:.1f} tok/s) "
            f"4xH100_FSDP2_proj={h100_projection['projected_per_h100_peak_gib']:.2f} GiB/GPU",
            flush=True,
        )

    if is_dist:
        dist.barrier()
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
