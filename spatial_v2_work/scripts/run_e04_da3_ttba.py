"""E04 Zero-Training DA3-Nested + Separate Paired 5-Step TT-BA (+ Optional Geo-Maj@K).

Strictly separates paired arms per cross-family review:
  1. G3T          (banked served/tower cameras from CAMERA_SPLIT.json or K1 tower.npz)
  2. DA3-only     (raw DA3-Nested Giant-Large native metric depth + extrinsics; NO TT-BA)
  3. DA3 + TT-BA  (paired refinement via 5-step Levenberg-Marquardt TT-BA + safe commit guard)
  4. Geo-Maj@K    (optional bonus: zero-training consensus across canonical, mirror_x, reverse_t)

Modes:
  --mode devs1      Runs live DA3-Nested on local dev-S1 anchor PNGs (lever8/j1/frames),
                    evaluates G3T vs DA3-only vs DA3+TT-BA against GT.json (38 GT captures;
                    28 landscape captures already unpacked in lever8/j1/frames).
  --mode k1_cached  CPU-only evaluation on cached K1 DA3 predictions at
                    /scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3 vs G3T towers.

Usage (local scratch PyTorch env, 0 NFS reads, vnice-safe):
  CUDA_VISIBLE_DEVICES=4 /data3/shared/scripts/vnice/vnice.sh \
    /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B run_e04_da3_ttba.py \
    --mode devs1 --captures arkitscenes/41069053 --out /scratch/jjyeung/orch_home_distill/work_e03_e04/out_e04_smoke
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import sys
import time
import types
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ttba_lm as T

DA3_SRC = Path("/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src")
DA3_SITE = Path("/scratch/jjyeung/geo_bakeoff_kit/runtime/site")
DA3_WEIGHTS = Path("/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors")

J1_ROOT = Path("/scratch/jjyeung/orch_n30/lever8/j1")
FRAMES_J1 = J1_ROOT / "out/FRAMES_J1.json"
CAMERA_SPLIT = Path("/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/CAMERA_SPLIT.json")
DEVS1_GT = Path("/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/out2/GT.json")

K1_MANIFEST = Path("/scratch/jjyeung/orch_n30/geo_k1/stage/K1_MANIFEST.arkit_timing.json")
K1_DA3_PRED = Path("/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3")
K1_TOWERS = Path("/scratch/jjyeung/k1/run_tower_sam_2")


def load_da3_model(device: str = "cuda"):
    """Load local DA3-Nested Giant-Large from /scratch safetensors with zero NFS/hub calls."""
    # Lightweight stub avoids moviepy/export dependency in sam3_capretry_native_v1
    if "depth_anything_3.utils.export" not in sys.modules:
        sys.modules["depth_anything_3.utils.export"] = types.SimpleNamespace(export=None)
    for p in (str(DA3_SRC), str(DA3_SITE)):
        if p not in sys.path:
            sys.path.insert(0, p)

    import torch
    import safetensors.torch as st
    from depth_anything_3.api import DepthAnything3

    t0 = time.perf_counter()
    model = DepthAnything3(model_name="da3nested-giant-large")
    state = st.load_file(str(DA3_WEIGHTS), device="cpu")
    shared_aux = {
        f"model.da3.head.scratch.output_conv2_aux.{i}.2.{wb}"
        for i in (1, 2, 3) for wb in ("weight", "bias")
    }
    missing, unexpected = model.load_state_dict(state, strict=False)
    if (set(missing) - shared_aux) or unexpected:
        raise RuntimeError(f"DA3 state dict mismatch: missing={missing}, unexpected={unexpected}")
    model = model.to(device).eval()
    load_s = time.perf_counter() - t0
    return model, load_s


def _extrinsics_to_c2w(ext: np.ndarray) -> np.ndarray:
    """Convert DA3 extrinsics (N, 3, 4) or (N, 4, 4) w2c -> OpenCV c2w (N, 4, 4)."""
    ext = np.asarray(ext, dtype=np.float64)
    N = ext.shape[0]
    w2c = np.broadcast_to(np.eye(4, dtype=np.float64), (N, 4, 4)).copy()
    w2c[:, :3, :4] = ext[:, :3, :4]
    return T.invert_se3(w2c)


def _sample_depth_grid(depth: np.ndarray, size: int = 51) -> tuple[np.ndarray, np.ndarray]:
    """Sample (N, H, W) depth onto a (N, size, size) regular grid."""
    N, H, W = depth.shape
    rr = np.linspace(0, H - 1, size).round().astype(int)
    cc = np.linspace(0, W - 1, size).round().astype(int)
    grid = depth[:, rr][:, :, cc].astype(np.float64)
    uv = np.linspace(0.0, 1000.0, size)
    return grid, uv


def run_da3_on_images(model, images: list, process_res: int = 504) -> dict[str, Any]:
    """Run DA3-Nested inference on PIL images; returns c2w, K, depth, conf, wall_s."""
    import torch

    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    pred = model.inference(images, process_res=process_res)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    wall_s = time.perf_counter() - t0
    peak_gib = (torch.cuda.max_memory_reserved() / (2 ** 30)) if torch.cuda.is_available() else 0.0

    c2w = _extrinsics_to_c2w(pred.extrinsics)
    K = np.asarray(pred.intrinsics, dtype=np.float64)
    depth = np.asarray(pred.depth, dtype=np.float32)
    conf = np.asarray(pred.conf, dtype=np.float32) if getattr(pred, "conf", None) is not None else None
    return dict(c2w=c2w, K=K, depth=depth, conf=conf, wall_s=wall_s, peak_gib=peak_gib)


def run_ttba_on_prediction(
    c2w: np.ndarray,
    K: np.ndarray,
    depth: np.ndarray,
    conf: np.ndarray | None = None,
    *,
    max_iters: int = 5,
    stride: int = 3,
    min_rel_drop: float = 0.35,
    k5s_gate_c2w: np.ndarray | None = None,
    k5s_tau_rot_deg: float = 0.25,
) -> tuple[T.TTBAResult, dict[str, Any]]:
    """Run 5-step LM TT-BA on a tower prediction (DA3 or G3T), optionally gated by K5-S."""
    d_grid, grid_uv = _sample_depth_grid(depth, size=51)
    c_grid = _sample_depth_grid(conf, size=51)[0] if conf is not None else None
    # Normalize conf to [0, 1] if present
    if c_grid is not None and np.isfinite(c_grid).any():
        p95 = float(np.percentile(c_grid[np.isfinite(c_grid)], 95))
        c_grid = np.clip(c_grid / max(p95, 1e-6), 0.0, 1.0)

    k5s_info: dict[str, Any] = dict(used_gate=False, triggered=True)
    if k5s_gate_c2w is not None:
        k5s = T.k5s_pose_disagreement(c2w, k5s_gate_c2w, tau_rot_deg=k5s_tau_rot_deg)
        k5s_info = dict(used_gate=True, triggered=k5s["trigger_ttba"], **k5s)
        if not k5s["trigger_ttba"]:
            return T.TTBAResult(
                c2w=c2w.copy(), scale=1.0, committed=False,
                initial_cost=0.0, final_cost=0.0, rel_cost_drop=0.0,
                iterations=0, wall_ms=0.0, inlier_ratio=1.0, cost_history=[],
            ), k5s_info

    corr = T.build_depth_correspondences(
        c2w, K, d_grid, grid_uv,
        frame_offsets=(1, 2, 4), stride=stride, conf_grid=c_grid,
    )
    if len(corr.src_idx) < 20:
        return T.TTBAResult(
            c2w=c2w.copy(), scale=1.0, committed=False,
            initial_cost=0.0, final_cost=0.0, rel_cost_drop=0.0,
            iterations=0, wall_ms=0.0, inlier_ratio=0.0, cost_history=[],
        ), dict(k5s_info, edges=len(corr.src_idx), note="too_few_edges")

    res = T.run_ttba_lm(
        c2w, K, corr,
        max_iters=max_iters, w_reproj=1.0, w_depth=2.0,
        huber_px=4.0, huber_logz=0.08, min_rel_drop=min_rel_drop,
        optimize_scale=False,
    )
    return res, dict(k5s_info, edges=len(corr.src_idx))


def _summary_metrics(rows: list[dict[str, Any]], arm_key: str) -> dict[str, Any]:
    if not rows:
        return {}
    rot_max = [r[arm_key]["rotation_max_deg"] for r in rows]
    rot_rms = [r[arm_key]["rotation_rms_deg"] for r in rows]
    t_rms = [r[arm_key]["translation_rms_m"] for r in rows]
    classes = [r[arm_key]["cls"] for r in rows]
    gt15 = sum(x > 15.0 for x in rot_max)
    return dict(
        n=len(rows),
        pass_n=sum(c == "pass" for c in classes),
        moderate_n=sum(c == "moderate" for c in classes),
        gross_n=sum(c == "gross" for c in classes),
        rot_gt15_n=gt15,
        rot_gt15_rate=round(gt15 / len(rows), 4),
        median_rot_max_deg=round(float(np.median(rot_max)), 3),
        median_rot_rms_deg=round(float(np.median(rot_rms)), 3),
        median_trans_rms_m=round(float(np.median(t_rms)), 4),
    )


def run_devs1(args) -> int:
    from PIL import Image, ImageOps

    split = json.loads(CAMERA_SPLIT.read_text())
    split_by_cap = {c["capture"]: c for c in split["captures"]}
    gt_all = json.loads(DEVS1_GT.read_text())
    frames_j1 = {c["capture"]: c for c in json.loads(FRAMES_J1.read_text())["captures"]}

    # Eligible dev-S1 captures that have both GT.json and local frames in lever8/j1/frames
    avail_caps = sorted(set(split_by_cap) & set(gt_all) & set(frames_j1))
    if args.captures:
        want = [x.strip() for x in args.captures.split(",") if x.strip()]
        missing = [c for c in want if c not in avail_caps]
        if missing:
            raise SystemExit(f"Captures missing local frames/GT: {missing} (available={len(avail_caps)})")
        caps = want
    else:
        caps = avail_caps
    if args.limit:
        caps = caps[: args.limit]

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cap_dir = out / "captures"
    cap_dir.mkdir(exist_ok=True)

    stop_flag = {"hit": False}
    def _on_term(sig, _frame):
        stop_flag["hit"] = True
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _on_term)

    model, load_s = load_da3_model(device=args.device)
    print(json.dumps(dict(event="LOADED", model="da3nested-giant-large", device=args.device, load_seconds=round(load_s, 2), captures=len(caps))), flush=True)

    rows = []
    for idx, cap in enumerate(caps, 1):
        if stop_flag["hit"]:
            print(json.dumps(dict(event="SIGTERM_STOP", completed=idx - 1, total=len(caps))), flush=True)
            break
        stub = cap.replace("/", "__")
        rec_path = cap_dir / f"{stub}.json"
        if rec_path.is_file() and not args.overwrite:
            rows.append(json.loads(rec_path.read_text()))
            continue

        fmeta = frames_j1[cap]["frames"]
        imgs = [Image.open(J1_ROOT / f["file"]).convert("RGB") for f in fmeta]
        gt_c2w = np.asarray(gt_all[cap]["c2w"], dtype=np.float64)

        # Arm 1: Banked G3T from CAMERA_SPLIT.json (exact audit numbers)
        g3t_rf = split_by_cap[cap]["rigid_fit"]
        g3t_cls = "gross" if g3t_rf["rotation_max_deg"] > 60 else ("pass" if g3t_rf["accepted"] else "moderate")
        g3t_eval = dict(
            translation_rms_m=float(g3t_rf["translation_rms_m"]),
            rotation_rms_deg=float(g3t_rf["rotation_rms_deg"]),
            rotation_max_deg=float(g3t_rf["rotation_max_deg"]),
            accepted=bool(g3t_rf["accepted"]),
            cls=g3t_cls,
        )

        # Arm 2: DA3-only (strictly separated from TT-BA!)
        da3 = run_da3_on_images(model, imgs, process_res=args.process_res)
        da3_fit = T.align_trajectory_rigid(da3["c2w"], gt_c2w, with_scale=False)
        da3_fit_sim3 = T.align_trajectory_rigid(da3["c2w"], gt_c2w, with_scale=True)
        da3_only_eval = dict(
            translation_rms_m=round(da3_fit["translation_rms_m"], 4),
            rotation_rms_deg=round(da3_fit["rotation_rms_deg"], 3),
            rotation_max_deg=round(da3_fit["rotation_max_deg"], 3),
            sim3_scale=round(da3_fit_sim3["scale"], 4),
            accepted=bool(da3_fit["accepted"]),
            cls=da3_fit["cls"],
            wall_s=round(da3["wall_s"], 2),
            peak_gib=round(da3["peak_gib"], 2),
        )

        # Arm 3: DA3 + 5-Step TT-BA (paired on the exact same DA3 output)
        ttba_res, ttba_meta = run_ttba_on_prediction(
            da3["c2w"], da3["K"], da3["depth"], da3["conf"],
            max_iters=args.ttba_iters, min_rel_drop=args.min_rel_drop,
        )
        ttba_fit = T.align_trajectory_rigid(ttba_res.c2w, gt_c2w, with_scale=False)
        da3_ttba_eval = dict(
            translation_rms_m=round(ttba_fit["translation_rms_m"], 4),
            rotation_rms_deg=round(ttba_fit["rotation_rms_deg"], 3),
            rotation_max_deg=round(ttba_fit["rotation_max_deg"], 3),
            accepted=bool(ttba_fit["accepted"]),
            cls=ttba_fit["cls"],
            committed=bool(ttba_res.committed),
            rel_cost_drop=round(ttba_res.rel_cost_drop, 4),
            ttba_wall_ms=round(ttba_res.wall_ms, 2),
            edges=ttba_meta.get("edges", 0),
        )

        row: dict[str, Any] = dict(
            capture=cap,
            dataset=split_by_cap[cap]["dataset"],
            g3t=g3t_eval,
            da3_only=da3_only_eval,
            da3_ttba=da3_ttba_eval,
        )

        # Optional Arm 4: Geo-Maj@K (canonical + horizontal mirror + time reversal)
        if args.with_geomaj:
            imgs_mir = [ImageOps.mirror(im) for im in imgs]
            imgs_rev = list(reversed(imgs))
            pred_mir = run_da3_on_images(model, imgs_mir, process_res=args.process_res)
            pred_rev = run_da3_on_images(model, imgs_rev, process_res=args.process_res)
            c2w_mir = T.unmirror_c2w_x(pred_mir["c2w"])
            c2w_rev = T.unreverse_c2w_t(pred_rev["c2w"])
            k5s_mir = T.k5s_pose_disagreement(da3["c2w"], c2w_mir)
            k5s_rev = T.k5s_pose_disagreement(da3["c2w"], c2w_rev)
            fused = T.geo_maj_k_fuse([da3["c2w"], c2w_mir, c2w_rev])
            gm_fit = T.align_trajectory_rigid(fused["fused_c2w"], gt_c2w, with_scale=False)
            row["geomaj3"] = dict(
                translation_rms_m=round(gm_fit["translation_rms_m"], 4),
                rotation_rms_deg=round(gm_fit["rotation_rms_deg"], 3),
                rotation_max_deg=round(gm_fit["rotation_max_deg"], 3),
                accepted=bool(gm_fit["accepted"]),
                cls=gm_fit["cls"],
                weights=[round(float(w), 3) for w in fused["weights"]],
                k5s_mir_max_rot_deg=round(k5s_mir["max_rot_deg"], 3),
                k5s_rev_max_rot_deg=round(k5s_rev["max_rot_deg"], 3),
            )

        # Save pose arrays for downstream relift
        np.savez_compressed(
            cap_dir / f"{stub}.npz",
            da3_c2w=da3["c2w"],
            da3_ttba_c2w=ttba_res.c2w,
            da3_K=da3["K"],
            da3_depth_grid=_sample_depth_grid(da3["depth"], 51)[0].astype(np.float32),
        )
        rec_path.write_text(json.dumps(row, indent=1) + "\n")
        rows.append(row)
        print(json.dumps(dict(event="CAPTURE", idx=idx, total=len(caps), **row)), flush=True)

    summary = dict(
        mode="devs1",
        total_captures=len(rows),
        all={arm: _summary_metrics(rows, arm) for arm in ("g3t", "da3_only", "da3_ttba") + (("geomaj3",) if args.with_geomaj else ())},
        arkit={arm: _summary_metrics([r for r in rows if r["dataset"] == "arkitscenes"], arm)
               for arm in ("g3t", "da3_only", "da3_ttba") + (("geomaj3",) if args.with_geomaj else ())},
        scannet_family={arm: _summary_metrics([r for r in rows if r["dataset"] != "arkitscenes"], arm)
                        for arm in ("g3t", "da3_only", "da3_ttba") + (("geomaj3",) if args.with_geomaj else ())},
    )
    (out / "SUMMARY_E04.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(dict(event="SUMMARY", **summary), indent=1), flush=True)
    return 0


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def run_k1_cached(args) -> int:
    """CPU-only paired comparison of cached K1 DA3-only vs DA3+TT-BA on local pred_gpu/da3."""
    manifest = json.loads(K1_MANIFEST.read_text())
    caps = manifest["captures"]
    if args.limit:
        caps = caps[: args.limit]
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for c in caps:
        key = _digest(c)
        pfile = K1_DA3_PRED / key[:16] / "pred.npz"
        gt_info = c.get("gt")
        if not pfile.is_file() or not gt_info or not Path(gt_info["path"]).is_file():
            continue
        with np.load(pfile, allow_pickle=False) as z:
            slots = z["anchor_slots"].astype(int)
            c2w = z["c2w"][slots].astype(np.float64)
            K = z["intrinsics"][slots].astype(np.float64)
            dgrid = z["depth_grid64"][slots].astype(np.float64)
        with np.load(gt_info["path"], allow_pickle=False) as g:
            valid = g["valid"].astype(bool)
            gt_c2w = g["c2w"].astype(np.float64)
        if valid.sum() < 4:
            continue
        da3_fit = T.align_trajectory_rigid(c2w[valid], gt_c2w[valid], with_scale=False)
        corr = T.build_depth_correspondences(c2w, K, dgrid, np.linspace(0, 1000, 51), frame_offsets=(1, 2, 4), stride=4)
        ttba = T.run_ttba_lm(c2w, K, corr, max_iters=args.ttba_iters, min_rel_drop=args.min_rel_drop) if len(corr.src_idx) >= 20 else T.TTBAResult(
            c2w=c2w, scale=1.0, committed=False, initial_cost=0.0, final_cost=0.0, rel_cost_drop=0.0, iterations=0, wall_ms=0.0, inlier_ratio=0.0, cost_history=[]
        )
        ttba_fit = T.align_trajectory_rigid(ttba.c2w[valid], gt_c2w[valid], with_scale=False)
        rows.append(dict(
            capture=c["canonical"],
            dataset=c["canonical"].split("/")[0],
            da3_only=dict(translation_rms_m=round(da3_fit["translation_rms_m"], 4), rotation_rms_deg=round(da3_fit["rotation_rms_deg"], 3),
                          rotation_max_deg=round(da3_fit["rotation_max_deg"], 3), cls=da3_fit["cls"]),
            da3_ttba=dict(translation_rms_m=round(ttba_fit["translation_rms_m"], 4), rotation_rms_deg=round(ttba_fit["rotation_rms_deg"], 3),
                          rotation_max_deg=round(ttba_fit["rotation_max_deg"], 3), cls=ttba_fit["cls"],
                          committed=bool(ttba.committed), ttba_wall_ms=round(ttba.wall_ms, 2)),
        ))

    summary = dict(
        mode="k1_cached",
        total_captures=len(rows),
        all={arm: _summary_metrics(rows, arm) for arm in ("da3_only", "da3_ttba")},
        arkit={arm: _summary_metrics([r for r in rows if r["dataset"] == "arkitscenes"], arm) for arm in ("da3_only", "da3_ttba")},
    )
    (out / "SUMMARY_E04_K1.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1), flush=True)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="E04: DA3-only vs G3T + separate paired DA3+TT-BA arm")
    ap.add_argument("--mode", choices=("devs1", "k1_cached"), default="devs1")
    ap.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    ap.add_argument("--captures", default=None, help="Comma-separated capture names (devs1 mode)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--process-res", type=int, default=504)
    ap.add_argument("--ttba-iters", type=int, default=5)
    ap.add_argument("--min-rel-drop", type=float, default=0.35)
    ap.add_argument("--with-geomaj", action="store_true", help="Also run Geo-Maj@3 (canonical + mirror + reverse)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--out", default=str(HERE / "out_e04"))
    args = ap.parse_args(argv)
    return run_devs1(args) if args.mode == "devs1" else run_k1_cached(args)


if __name__ == "__main__":
    sys.exit(main())
