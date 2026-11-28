"""KT-6 Stage-1A Real-Data Correspondence Trainer: Arm A (epi_vit) vs Arm B (corresp_stem).

Tests Codex Astra's #1 representation hypothesis on local cached K1 indoor captures (0 NFS IO):
  - Arm A (`epi_vit`):      Unfrozen Qwen3.5-9B ViT taps (9,17,25) -> EpiAdapter (65M) -> GeoHeads
  - Arm B (`corresp_stem`): Correspondence-native DA3 DINOv2-L/14 taps (7,15,23) -> EpiAdapter -> GeoHeads
Under the exact same clean room-disjoint K1 split (233 train / 53 val, 0 room overlap),
frozen DA3-Giant SpatialForcing^2 teacher, DecoupledDepthLoss, PoseAnd4DLoss, and optimizer.
Metric3DRoPE and DeltaGeoBias are strictly OFF in Stage-1A.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler

from .data_k1_local import (
    DEFAULT_EXCL_DIR,
    DEFAULT_FRAMES_ROOT,
    DEFAULT_MANIFEST_PATH,
    LocalK1CaptureDataset,
    collate_k1_batch,
)
from .eval_stage1a import evaluate_stage1a_model, format_eval_summary
from .stage1a_model import (
    DEFAULT_DA3_CKPT,
    DEFAULT_QWEN_VISUAL_CKPT,
    ArmType,
    DA3GiantTeacher,
    Stage1ACorrespondenceModel,
)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def init_distributed() -> Tuple[bool, int, int, int]:
    """Initialize DDP if launched via torchrun; otherwise return single-process settings."""
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


def save_checkpoint(
    path: Path,
    model: Stage1ACorrespondenceModel,
    optimizer: torch.optim.Optimizer,
    step: int,
    args: argparse.Namespace,
    split_summary: Dict[str, object],
    metrics: Optional[Dict[str, float]] = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".pt.tmp")
    payload = {
        "step": step,
        "arm": model.arm,
        "teacher_dim": model.cfg.sf2.teacher_dim,
        "tiny": model.tiny,
        "use_metric_3d_rope": model.use_metric_3d_rope,
        "use_delta_geo_bias": model.use_delta_geo_bias,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "args": vars(args),
        "split_summary": split_summary,
        "metrics": metrics or {},
    }
    torch.save(payload, tmp)
    os.replace(tmp, path)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train KT-6 Stage-1A correspondence arm (epi_vit vs corresp_stem).")
    ap.add_argument("--arm", type=str, choices=("epi_vit", "corresp_stem"), required=True)
    ap.add_argument("--out-dir", type=str, required=True)
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--batch-size", type=int, default=1, help="Per-GPU clip batch size")
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--num-views", type=int, default=8)
    ap.add_argument("--grid-h", type=int, default=20)
    ap.add_argument("--grid-w", type=int, default=20)
    ap.add_argument("--backbone-lr", type=float, default=2e-5)
    ap.add_argument("--head-lr", type=float, default=2e-4)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--warmup-steps", type=int, default=50)
    ap.add_argument("--max-grad-norm", type=float, default=1.0)
    ap.add_argument("--freeze-backbone", action="store_true")
    ap.add_argument("--no-grad-ckpt", action="store_true")
    ap.add_argument("--random-subsample", action="store_true")
    ap.add_argument("--seed", type=int, default=20261128)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--log-every", type=int, default=1)
    ap.add_argument("--eval-every", type=int, default=250)
    ap.add_argument("--save-every", type=int, default=500)
    ap.add_argument("--eval-max-samples", type=int, default=None)
    ap.add_argument("--skip-final-eval", action="store_true")
    ap.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST_PATH)
    ap.add_argument("--frames-root", type=str, default=DEFAULT_FRAMES_ROOT)
    ap.add_argument("--excl-dir", type=str, default=DEFAULT_EXCL_DIR)
    ap.add_argument("--qwen-ckpt", type=str, default=DEFAULT_QWEN_VISUAL_CKPT)
    ap.add_argument("--da3-ckpt", type=str, default=DEFAULT_DA3_CKPT)
    ap.add_argument("--tiny", action="store_true", help="Tiny architecture for fast CPU/unit tests")
    ap.add_argument("--resume", type=str, default=None)
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

    # 1. Leakage-verified clean K1 datasets (Arm A needs both Qwen + DA3 RGB for DA3 teacher; Arm B needs DA3 RGB)
    need_qwen = args.arm == "epi_vit"
    train_ds = LocalK1CaptureDataset(
        split="train",
        num_views=args.num_views,
        grid_h=args.grid_h,
        grid_w=args.grid_w,
        manifest_path=args.manifest,
        frames_root=args.frames_root,
        excl_dir=args.excl_dir,
        random_subsample=args.random_subsample,
        seed=args.seed + rank,
        load_qwen_rgb=need_qwen,
        load_da3_rgb=True,
    )
    val_ds = LocalK1CaptureDataset(
        split="val",
        num_views=args.num_views,
        grid_h=args.grid_h,
        grid_w=args.grid_w,
        manifest_path=args.manifest,
        frames_root=args.frames_root,
        excl_dir=args.excl_dir,
        random_subsample=False,
        seed=args.seed,
        load_qwen_rgb=need_qwen,
        load_da3_rgb=(not need_qwen),
        max_captures=args.eval_max_samples,
    )

    train_sampler = (
        DistributedSampler(train_ds, num_replicas=world_size, rank=rank, shuffle=True, seed=args.seed)
        if is_dist
        else None
    )
    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=(train_sampler is None),
        sampler=train_sampler,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
        drop_last=True,
        collate_fn=collate_k1_batch,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=1,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
        collate_fn=collate_k1_batch,
    )

    # 2. Frozen DA3-Giant teacher (SpatialForcing^2 targets) + Student Stage-1A model
    teacher = DA3GiantTeacher(ckpt_path=None if args.tiny else args.da3_ckpt, tiny=args.tiny)
    teacher = teacher.to(device=device, dtype=amp_dtype if use_amp else torch.float32).eval()

    model = Stage1ACorrespondenceModel(
        arm=args.arm,
        teacher_dim=teacher.teacher_dim,
        qwen_ckpt=None if args.tiny else args.qwen_ckpt,
        da3_ckpt=None if args.tiny else args.da3_ckpt,
        freeze_backbone=args.freeze_backbone,
        gradient_checkpointing=(not args.no_grad_ckpt),
        tiny=args.tiny,
    ).to(device)

    assert not model.use_metric_3d_rope and not model.use_delta_geo_bias, "Stage-1A isolation violated"
    param_counts = model.parameter_counts()

    param_groups = model.build_param_groups(
        backbone_lr=args.backbone_lr, head_lr=args.head_lr, weight_decay=args.weight_decay
    )
    optimizer = torch.optim.AdamW(param_groups, betas=(0.9, 0.95), eps=1e-8)

    start_step = 0
    if args.resume:
        ckpt = torch.load(args.resume, map_location="cpu", weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"], strict=True)
        if "optimizer_state_dict" in ckpt:
            optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        start_step = int(ckpt.get("step", 0))

    ddp_model: torch.nn.Module = (
        DDP(model, device_ids=[local_rank] if device.type == "cuda" else None, find_unused_parameters=False)
        if is_dist
        else model
    )

    if is_main:
        header = {
            "arm": args.arm,
            "world_size": world_size,
            "device": str(device),
            "metric_3d_rope": False,
            "delta_geo_bias": False,
            "split_summary": train_ds.split_summary,
            "param_counts": param_counts,
            "num_views": args.num_views,
            "grid_hw": [args.grid_h, args.grid_w],
            "steps": args.steps,
            "batch_size_per_gpu": args.batch_size,
            "grad_accum": args.grad_accum,
            "effective_batch_size": args.batch_size * args.grad_accum * world_size,
        }
        print(f"[Stage-1A Startup] {json.dumps(header)}", flush=True)
        (out_dir / "config_summary.json").write_text(json.dumps(header, indent=2) + "\n")

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    log_f = (out_dir / "train_log.jsonl").open("a") if is_main else None
    rgb_key = model.rgb_key()

    epoch = 0
    data_iter = iter(train_loader)
    step_times: List[float] = []
    loss_curve: List[Dict[str, float]] = []

    ddp_model.train()
    for step in range(start_step + 1, args.steps + 1):
        t_step0 = time.monotonic()
        lr_mult = cosine_lr_multiplier(step - 1, args.steps, args.warmup_steps)
        for pg in optimizer.param_groups:
            base = args.backbone_lr if str(pg.get("name", "")).startswith("backbone") else args.head_lr
            pg["lr"] = base * lr_mult

        optimizer.zero_grad(set_to_none=True)
        accum_metrics: Dict[str, float] = {}

        for micro in range(args.grad_accum):
            try:
                batch = next(data_iter)
            except StopIteration:
                epoch += 1
                if train_sampler is not None:
                    train_sampler.set_epoch(epoch)
                data_iter = iter(train_loader)
                batch = next(data_iter)

            gpu_batch: Dict[str, torch.Tensor] = {}
            for k, v in batch.items():
                if torch.is_tensor(v):
                    gpu_batch[k] = v.to(device, non_blocking=True)

            # Frozen DA3-Giant teacher features [B, N, Hm*Wm, D_tea]
            with torch.no_grad(), torch.amp.autocast(device_type=device.type, dtype=amp_dtype, enabled=use_amp):
                teacher_feats = teacher(gpu_batch["rgb_da3"])

            sync_ctx = (
                ddp_model.no_sync() if (is_dist and micro < args.grad_accum - 1) else torch.enable_grad()
            )
            with sync_ctx:
                with torch.amp.autocast(device_type=device.type, dtype=amp_dtype, enabled=use_amp):
                    _, loss, loss_dict = ddp_model(
                        gpu_batch[rgb_key],
                        timestamps=gpu_batch["timestamps"],
                        view_mask=gpu_batch["view_mask"],
                        batch=gpu_batch,
                        teacher_feats=teacher_feats,
                    )
                    scaled_loss = loss / float(args.grad_accum)
                scaled_loss.backward()

            for mk, mv in loss_dict.items():
                accum_metrics[mk] = accum_metrics.get(mk, 0.0) + float(mv.item()) / float(args.grad_accum)

        grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm).item())
        optimizer.step()

        if device.type == "cuda":
            torch.cuda.synchronize(device)
        dt = time.monotonic() - t_step0
        step_times.append(dt)
        peak_gib = (
            float(torch.cuda.max_memory_allocated(device)) / (1024.0**3) if device.type == "cuda" else 0.0
        )

        rec = {
            "step": step,
            "arm": args.arm,
            "loss": round(accum_metrics.get("total_loss", 0.0), 5),
            "sf2_feat": round(accum_metrics.get("sf2_feat_l16", 0.0), 5),
            "sf2_gram": round(accum_metrics.get("sf2_gram_l16", 0.0), 5),
            "depth": round(accum_metrics.get("depth_total", 0.0), 5),
            "pose": round(accum_metrics.get("pose", 0.0), 5),
            "ray": round(accum_metrics.get("ray", 0.0), 5),
            "pmap": round(accum_metrics.get("pmap", 0.0), 5),
            "gravity": round(accum_metrics.get("gravity", 0.0), 5),
            "fov": round(accum_metrics.get("fov", 0.0), 5),
            "grad_norm": round(grad_norm, 4),
            "lr_head": round(args.head_lr * lr_mult, 7),
            "lr_backbone": round(args.backbone_lr * lr_mult, 7),
            "step_time_s": round(dt, 4),
            "steps_per_sec": round(1.0 / max(dt, 1e-6), 4),
            "peak_vram_gib": round(peak_gib, 3),
        }
        loss_curve.append(rec)

        if is_main and (step % args.log_every == 0 or step == 1 or step == args.steps):
            print(
                f"[step {step:05d}/{args.steps}] arm={args.arm} loss={rec['loss']:.4f} "
                f"(sf2={rec['sf2_feat']:.3f}/{rec['sf2_gram']:.3f} depth={rec['depth']:.3f} "
                f"pose={rec['pose']:.3f} pmap={rec['pmap']:.3f}) "
                f"gnorm={rec['grad_norm']:.2f} {rec['steps_per_sec']:.2f} it/s peak={rec['peak_vram_gib']:.2f} GiB",
                flush=True,
            )
            assert log_f is not None
            log_f.write(json.dumps(rec) + "\n")
            log_f.flush()

        if is_main and args.save_every > 0 and step % args.save_every == 0:
            save_checkpoint(
                out_dir / f"step_{step:06d}.pt", model, optimizer, step, args, train_ds.split_summary, rec
            )

        if args.eval_every > 0 and step % args.eval_every == 0 and step < args.steps:
            if is_main:
                ev = evaluate_stage1a_model(
                    model, val_loader, device=device, amp_dtype=amp_dtype, max_samples=args.eval_max_samples
                )
                print(format_eval_summary(ev), flush=True)
                (out_dir / f"eval_step_{step:06d}.json").write_text(json.dumps(ev, indent=2) + "\n")
            if is_dist:
                dist.barrier()

    # Final checkpoint & held-out evaluation on rank 0
    if is_main:
        if log_f is not None:
            log_f.close()
        last_rec = loss_curve[-1] if loss_curve else {}
        ckpt_path = out_dir / "latest.pt"
        save_checkpoint(ckpt_path, model, optimizer, args.steps, args, train_ds.split_summary, last_rec)

        eval_res: Optional[Dict[str, object]] = None
        if not args.skip_final_eval:
            eval_res = evaluate_stage1a_model(
                model, val_loader, device=device, amp_dtype=amp_dtype, max_samples=args.eval_max_samples
            )
            print(format_eval_summary(eval_res), flush=True)
            (out_dir / "eval_final.json").write_text(json.dumps(eval_res, indent=2) + "\n")

        # Steady-state speed (exclude step 1 compilation/warmup if >2 steps)
        steady = step_times[1:] if len(step_times) > 2 else step_times
        mean_step_s = float(np.mean(steady)) if steady else 0.0
        summary = {
            "arm": args.arm,
            "steps": args.steps,
            "world_size": world_size,
            "peak_vram_gib": round(
                float(torch.cuda.max_memory_allocated(device)) / (1024.0**3) if device.type == "cuda" else 0.0,
                3,
            ),
            "peak_reserved_gib": round(
                float(torch.cuda.max_memory_reserved(device)) / (1024.0**3) if device.type == "cuda" else 0.0,
                3,
            ),
            "mean_step_time_s": round(mean_step_s, 4),
            "mean_steps_per_sec": round(1.0 / max(mean_step_s, 1e-6), 4),
            "loss_step1": loss_curve[0]["loss"] if loss_curve else None,
            "loss_final": loss_curve[-1]["loss"] if loss_curve else None,
            "loss_curve": loss_curve,
            "eval_overall": eval_res["overall"] if eval_res else None,
            "eval_by_dataset": eval_res["by_dataset"] if eval_res else None,
            "split_summary": train_ds.split_summary,
            "param_counts": param_counts,
            "checkpoint": str(ckpt_path),
        }
        (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(
            f"[Stage-1A DONE] arm={args.arm} peak_vram={summary['peak_vram_gib']:.2f} GiB "
            f"steady={summary['mean_steps_per_sec']:.2f} step/s "
            f"loss {summary['loss_step1']} -> {summary['loss_final']}",
            flush=True,
        )

    if is_dist:
        dist.barrier()
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
