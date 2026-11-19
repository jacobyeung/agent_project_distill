#!/usr/bin/env python3
"""Extract and seal G3T camera-token and camera-head sidecars (`<key>.cam.npz`) for an existing G3T patch-grid store.

For each 32-frame selection in `sets.jsonl` / `<store>/manifest.jsonl`:
  1. Preprocess the 32 frames identically to `tools/g3t_patch_grid_store.py` (`load_and_preprocess_images_square(1024)`
     then bilinear resize to `518x518`, `align_corners=False`).
  2. Run `model.aggregator` under `bfloat16` autocast and `model.local_camera_head` + `model.global_camera_head` under
     fp32 (`torch.amp.autocast('cuda', enabled=False)`), matching `G3T.forward` bit-for-bit without running
     `depth_head` or `point_head`. On the first selection of each shard, verify bit-identity (`torch.equal`) against
     `model(inputs[None])`.
  3. Extract layer-23 camera tokens `tokens[23][0, :, 0, :]` as `float16 [32, 2048]`, `local_pose_enc [32, 6]`,
     `global_pose_enc [32, 5]`, and `coords_1024 [32, 4]`.
  4. Convert G3T's extrinsics and intrinsics into PDG's 16 anchor-group relative camera encodings (`g3t_pose_9d [16, 9]`,
     `g3t_gravity_up [3]`, `g3t_step_scale [1]`) via `student_pilot.camera_targets.{encode_cameras,encode_gravity}`.
  5. Write `<store>/c/<key[:2]>/<key>.cam.npz`, `<store>/camera_manifest.jsonl`, and `<store>/CAMERA_RECEIPT.json`.

Subcommands:
  extract SOURCE SETS_JSONL STORE_DIR SHARD NSHARDS [LIMIT]
  seal    SETS_JSONL STORE_DIR
  build   SOURCE SETS_JSONL STORE_DIR [LIMIT]
"""
import argparse
import concurrent.futures as cf
import json
import math
import os
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from student_pilot.camera_targets import GROUPS, encode_cameras, encode_gravity
from tools.g3t_patch_grid_store import (
    ENCODER,
    FEATURE_DIM,
    FRAMES,
    INPUT_SIDE,
    LAYER,
    REPOSITORY,
    REVISION,
    key,
    load,
    read_lines,
    sha,
)

COORD_SCALE = 1024
PATCH_START = 5
SIDECAR_SCHEMA = "g3t-camera-sidecar-v1"
SIDECAR_KEYS = (
    "cam_token_l23",
    "local_pose_enc",
    "global_pose_enc",
    "coords_1024",
    "g3t_pose_9d",
    "g3t_gravity_up",
    "g3t_step_scale",
)
SIDECAR_ROW_KEYS = {
    "schema",
    "key",
    "frames",
    "sidecar",
    "file",
    "sha256",
    "bytes",
    "groups",
    "layer",
    "feature_dim",
    "encoder",
    "cam_token_shape",
    "cam_token_dtype",
    "pose_shape",
    "gravity_shape",
    "step_scale",
}


def make_4x4(extri):
    import torch

    b, s, _, _ = extri.shape
    bottom = (
        torch.tensor([0.0, 0.0, 0.0, 1.0], device=extri.device, dtype=extri.dtype)
        .view(1, 1, 1, 4)
        .expand(b, s, 1, 4)
    )
    return torch.cat([extri, bottom], dim=-2)


def prior_from_g3t_extri_intri(w2c, intr_518, coords_1024):
    """Convert G3T [32, 4, 4] w2c, [32, 3, 3] 518x518 intrinsics, and [32, 4] 1024-space crop boxes to PDG priors."""
    w2c = np.asarray(w2c, dtype=np.float64)
    intr_crop = np.asarray(intr_518, dtype=np.float64).copy()
    coords_1024 = np.asarray(coords_1024, dtype=np.float64)
    if (
        w2c.shape != (FRAMES, 4, 4)
        or intr_crop.shape != (FRAMES, 3, 3)
        or coords_1024.ndim != 2
        or coords_1024.shape[0] != FRAMES
        or coords_1024.shape[1] < 4
    ):
        raise ValueError(
            f"Unexpected G3T shapes: w2c={w2c.shape}, intr={intr_crop.shape}, coords={coords_1024.shape}"
        )
    c2w_g3t = np.linalg.inv(w2c)
    box = coords_1024[:, :4] * (float(INPUT_SIDE) / float(COORD_SCALE))
    intr_crop[:, 0, 2] -= box[:, 0]
    intr_crop[:, 1, 2] -= box[:, 1]
    crop_hw = np.stack([box[:, 3] - box[:, 1], box[:, 2] - box[:, 0]], axis=-1)
    g3t_pose_9d, mask, d_bar_g3t = encode_cameras(c2w_g3t, intr_crop, crop_hw)
    g3t_gravity_up, grav_ok = encode_gravity(c2w_g3t, world_up=(0.0, -1.0, 0.0))
    if not bool(np.all(mask)) or not bool(grav_ok) or not (math.isfinite(float(d_bar_g3t)) and float(d_bar_g3t) >= 0.0):
        raise ValueError(
            f"Invalid G3T prior encoding: mask_all={bool(np.all(mask))}, grav_ok={grav_ok}, d_bar={d_bar_g3t}"
        )
    pose_9d = np.ascontiguousarray(g3t_pose_9d, dtype=np.float32)
    gravity_up = np.ascontiguousarray(g3t_gravity_up, dtype=np.float32)
    step_scale = np.asarray([float(d_bar_g3t)], dtype=np.float32)
    if not (np.isfinite(pose_9d).all() and np.isfinite(gravity_up).all() and np.isfinite(step_scale).all()):
        raise ValueError("Non-finite values in G3T camera prior")
    return pose_9d, gravity_up, step_scale


def g3t_camera_forward(model, inputs, layer=LAYER, verify_full=False):
    """Run G3T aggregator + camera heads on 518x518 `inputs [32, 3, 518, 518]`."""
    import torch

    use_cuda = inputs.device.type == "cuda"
    with torch.inference_mode():
        if use_cuda:
            with torch.autocast("cuda", dtype=torch.bfloat16):
                tokens, patch_start = model.aggregator(inputs[None])
            with torch.amp.autocast("cuda", enabled=False):
                local_pose_enc = model.local_camera_head(tokens)[-1]
                global_pose_enc = model.global_camera_head(tokens)[-1]
        else:
            tokens, patch_start = model.aggregator(inputs[None])
            local_pose_enc = model.local_camera_head(tokens)[-1]
            global_pose_enc = model.global_camera_head(tokens)[-1]

        if verify_full:
            if use_cuda:
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    full_out = model(inputs[None])
            else:
                full_out = model(inputs[None])
            if not (
                torch.equal(local_pose_enc, full_out["local_pose_enc"])
                and torch.equal(global_pose_enc, full_out["global_pose_enc"])
            ):
                raise ValueError("Camera-only G3T forward diverged from full G3T.forward")

    if int(patch_start) != PATCH_START:
        raise ValueError(f"Expected G3T patch_start_idx={PATCH_START}, got {int(patch_start)}")
    if not (0 <= layer < len(tokens)):
        raise ValueError(f"Requested G3T layer {layer}, model produced {len(tokens)} layers")
    block = tokens[layer]
    if block.ndim != 4 or block.shape[0] != 1 or block.shape[1] != FRAMES or block.shape[3] != FEATURE_DIM:
        raise ValueError(f"Unexpected G3T token block shape {tuple(block.shape)}")
    cam_token = np.ascontiguousarray(block[0, :, 0, :].detach().to(dtype=torch.float16).cpu().numpy())
    local_np = np.ascontiguousarray(local_pose_enc[0].detach().to(dtype=torch.float32).cpu().numpy())
    global_np = np.ascontiguousarray(global_pose_enc[0].detach().to(dtype=torch.float32).cpu().numpy())
    if not (np.isfinite(cam_token).all() and np.isfinite(local_np).all() and np.isfinite(global_np).all()):
        raise ValueError("G3T produced non-finite camera tokens or pose encodings")
    return cam_token, local_np, global_np, local_pose_enc, global_pose_enc


def build_sidecar_arrays(model, inputs, coords, pose_encoding_to_extri_intri, layer=LAYER, verify_full=False):
    import torch

    cam_token, local_np, global_np, local_pose_enc, global_pose_enc = g3t_camera_forward(
        model, inputs, layer=layer, verify_full=verify_full
    )
    with torch.inference_mode():
        g2c, intr = pose_encoding_to_extri_intri(
            local_pose_enc, (INPUT_SIDE, INPUT_SIDE), pose_encoding_type="noT_quaR_FoV"
        )
        w2g, _ = pose_encoding_to_extri_intri(
            global_pose_enc,
            (INPUT_SIDE, INPUT_SIDE),
            pose_encoding_type="absT_quaRy_noFoV",
            build_intrinsics=False,
        )
        w2c = torch.matmul(make_4x4(g2c), make_4x4(w2g))[0].double().cpu().numpy()
        intr_518 = intr[0].double().cpu().numpy()
    coords_np = np.ascontiguousarray(coords.detach().to(dtype=torch.float32).cpu().numpy()[:, :4])
    pose_9d, gravity_up, step_scale = prior_from_g3t_extri_intri(w2c, intr_518, coords_np)
    return {
        "cam_token_l23": cam_token,
        "local_pose_enc": local_np,
        "global_pose_enc": global_np,
        "coords_1024": coords_np,
        "g3t_pose_9d": pose_9d,
        "g3t_gravity_up": gravity_up,
        "g3t_step_scale": step_scale,
    }


def verify_sidecar_npz(path):
    with np.load(path, allow_pickle=False) as data:
        if set(data.files) != set(SIDECAR_KEYS):
            raise ValueError(f"{path} keys {sorted(data.files)} != {sorted(SIDECAR_KEYS)}")
        cam_token = data["cam_token_l23"]
        local_pose = data["local_pose_enc"]
        global_pose = data["global_pose_enc"]
        coords = data["coords_1024"]
        pose_9d = data["g3t_pose_9d"]
        gravity_up = data["g3t_gravity_up"]
        step_scale = data["g3t_step_scale"]
        if cam_token.dtype != np.float16 or cam_token.shape != (FRAMES, FEATURE_DIM):
            raise ValueError(f"{path} cam_token_l23 invalid: {cam_token.dtype} {cam_token.shape}")
        if local_pose.dtype != np.float32 or local_pose.shape != (FRAMES, 6):
            raise ValueError(f"{path} local_pose_enc invalid: {local_pose.dtype} {local_pose.shape}")
        if global_pose.dtype != np.float32 or global_pose.shape != (FRAMES, 5):
            raise ValueError(f"{path} global_pose_enc invalid: {global_pose.dtype} {global_pose.shape}")
        if coords.dtype != np.float32 or coords.shape != (FRAMES, 4):
            raise ValueError(f"{path} coords_1024 invalid: {coords.dtype} {coords.shape}")
        if pose_9d.dtype != np.float32 or pose_9d.shape != (GROUPS, 9):
            raise ValueError(f"{path} g3t_pose_9d invalid: {pose_9d.dtype} {pose_9d.shape}")
        if gravity_up.dtype != np.float32 or gravity_up.shape != (3,):
            raise ValueError(f"{path} g3t_gravity_up invalid: {gravity_up.dtype} {gravity_up.shape}")
        if step_scale.dtype != np.float32 or step_scale.shape != (1,) or float(step_scale[0]) < 0.0:
            raise ValueError(f"{path} g3t_step_scale invalid: {step_scale.dtype} {step_scale.shape} {step_scale}")
        for name in SIDECAR_KEYS:
            if not np.isfinite(data[name]).all():
                raise ValueError(f"{path} {name} contains non-finite values")
        return float(step_scale[0])


def extract(source, sets_path, store, shard, nshards, limit=None):
    import torch
    import torch.nn.functional as F

    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    from vggt.models.g3t import G3T
    from vggt.utils.load_fn import load_and_preprocess_images_square
    from vggt.utils.pose_enc import pose_encoding_to_extri_intri

    store = Path(store)
    sets = [json.loads(line) for line in read_lines(sets_path)]
    sets = sorted(sets, key=lambda entry: entry["key"])[shard::nshards]
    if limit:
        sets = sets[:limit]
    out_rows, out_times = store / f"cm_{shard}.jsonl", store / f"ct_{shard}.jsonl"
    store.mkdir(parents=True, exist_ok=True)
    done = {json.loads(line)["key"] for line in read_lines(out_rows)} if out_rows.exists() else set()
    todo = [entry for entry in sets if entry["key"] not in done]
    print(f"sidecar shard {shard}/{nshards}: {len(sets)} sets, {len(done)} done, {len(todo)} to do", flush=True)
    if not todo:
        return
    torch.manual_seed(0)
    started = time.time()
    model = G3T.from_pretrained(REPOSITORY, revision=REVISION).eval().to("cuda")
    print(f"model load {time.time() - started:.1f}s", flush=True)
    pool = cf.ThreadPoolExecutor(2)
    futures = [pool.submit(load, entry, load_and_preprocess_images_square) for entry in todo[:2]]
    following = 2
    for idx in range(len(todo)):
        entry, images, coords, load_seconds = futures.pop(0).result()
        if following < len(todo):
            futures.append(pool.submit(load, todo[following], load_and_preprocess_images_square))
            following += 1
        item_started = time.time()
        with torch.inference_mode():
            inputs = F.interpolate(
                images.to("cuda", non_blocking=True),
                size=(INPUT_SIDE, INPUT_SIDE),
                mode="bilinear",
                align_corners=False,
            )
            arrays = build_sidecar_arrays(
                model,
                inputs,
                coords,
                pose_encoding_to_extri_intri,
                layer=LAYER,
                verify_full=(idx == 0),
            )
        gpu_seconds = time.time() - item_started
        relative = Path("c") / entry["key"][:2] / f"{entry['key']}.cam.npz"
        target = store / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f".tmp{os.getpid()}.npz")
        np.savez(temporary, **arrays)
        os.replace(temporary, target)
        step_scale_val = verify_sidecar_npz(target)
        row = {
            "schema": SIDECAR_SCHEMA,
            "key": entry["key"],
            "frames": entry["frames"],
            "sidecar": str(relative),
            "file": str(relative),
            "sha256": sha(target),
            "bytes": target.stat().st_size,
            "groups": GROUPS,
            "layer": LAYER,
            "feature_dim": FEATURE_DIM,
            "encoder": ENCODER,
            "cam_token_shape": [FRAMES, FEATURE_DIM],
            "cam_token_dtype": "float16",
            "pose_shape": [GROUPS, 9],
            "gravity_shape": [3],
            "step_scale": step_scale_val,
        }
        with out_rows.open("a") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
        with out_times.open("a") as stream:
            stream.write(
                json.dumps(
                    {
                        "key": entry["key"],
                        "load_s": round(load_seconds, 3),
                        "gpu_s": round(gpu_seconds, 3),
                        "total_s": round(time.time() - item_started + load_seconds, 3),
                        "bytes": target.stat().st_size,
                        "peak_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2),
                    }
                )
                + "\n"
            )
        if (idx + 1) % 25 == 0 or (idx + 1) == len(todo):
            elapsed = max(time.time() - started, 1e-6)
            print(
                f"  [{idx + 1}/{len(todo)}] rate={(idx + 1) / elapsed:.2f} sel/s "
                f"gpu={gpu_seconds:.2f}s load={load_seconds:.2f}s last={entry['key'][:12]}",
                flush=True,
            )
    pool.shutdown(wait=True)
    print(f"sidecar shard {shard} done in {time.time() - started:.0f}s", flush=True)


def seal(sets_path, store, overwrite=False):
    """camera_manifest.jsonl over every selection of SETS_JSONL and <store>/manifest.jsonl, verified."""
    store = Path(store)
    sets = {entry["key"]: entry for entry in (json.loads(line) for line in read_lines(sets_path))}
    store_manifest = store / "manifest.jsonl"
    if store_manifest.is_file():
        store_keys = {json.loads(line)["key"] for line in read_lines(store_manifest)}
        if store_keys != set(sets):
            raise ValueError(
                f"sets ({len(sets)}) and store manifest.jsonl ({len(store_keys)}) differ by "
                f"{len(store_keys ^ set(sets))} keys"
            )
    rows = {}
    for path in sorted(store.glob("cm_*.jsonl")):
        for line in read_lines(path):
            row = json.loads(line)
            if row["key"] in rows:
                raise ValueError(f"selection {row['key']} has more than one sidecar row")
            rows[row["key"]] = row
    if set(rows) != set(sets):
        raise ValueError(
            f"sidecar rows cover {len(set(rows) & set(sets))} of {len(sets)} selections "
            f"and {len(set(rows) - set(sets))} foreign keys"
        )
    total = 0
    for selection, row in rows.items():
        relative = Path(row["sidecar"])
        if (
            set(row) != SIDECAR_ROW_KEYS
            or row["schema"] != SIDECAR_SCHEMA
            or row["frames"] != sets[selection]["frames"]
            or key(row["frames"]) != selection
            or row["file"] != row["sidecar"]
            or row["groups"] != GROUPS
            or row["layer"] != LAYER
            or row["feature_dim"] != FEATURE_DIM
            or row["encoder"] != ENCODER
            or row["cam_token_shape"] != [FRAMES, FEATURE_DIM]
            or row["cam_token_dtype"] != "float16"
            or row["pose_shape"] != [GROUPS, 9]
            or row["gravity_shape"] != [3]
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            raise ValueError(f"sidecar row {selection} differs from its selection or schema")
        target = store / relative
        if sha(target) != row["sha256"]:
            raise ValueError(f"sidecar file {row['sidecar']} differs from its row sha256")
        verify_sidecar_npz(target)
        size = target.stat().st_size
        if row["bytes"] != size:
            raise ValueError(f"sidecar file {row['sidecar']} size {size} != {row['bytes']}")
        total += size
    manifest = store / "camera_manifest.jsonl"
    if manifest.exists() and not overwrite:
        raise FileExistsError(f"{manifest} already exists (pass --overwrite to replace)")
    tmp_manifest = store / f"camera_manifest.jsonl.tmp{os.getpid()}"
    with tmp_manifest.open("w") as stream:
        for selection in sorted(rows):
            stream.write(json.dumps(rows[selection], sort_keys=True) + "\n")
    os.replace(tmp_manifest, manifest)
    receipt = {
        "schema": SIDECAR_SCHEMA,
        "selections": len(rows),
        "bytes": total,
        "encoder": ENCODER,
        "layer": LAYER,
        "feature_dim": FEATURE_DIM,
        "groups": GROUPS,
        "sets": {"path": str(sets_path), "sha256": sha(sets_path)},
        "store_manifest": (
            {"path": str(store_manifest), "sha256": sha(store_manifest)} if store_manifest.is_file() else None
        ),
        "camera_manifest": {"path": str(manifest), "sha256": sha(manifest)},
        "tool_sha256": sha(Path(__file__)),
    }
    receipt_path = store / "CAMERA_RECEIPT.json"
    if receipt_path.exists() and not overwrite:
        raise FileExistsError(f"{receipt_path} already exists (pass --overwrite to replace)")
    tmp_receipt = store / f"CAMERA_RECEIPT.json.tmp{os.getpid()}"
    with tmp_receipt.open("w") as stream:
        stream.write(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    os.replace(tmp_receipt, receipt_path)
    return receipt


def build(source, sets_path, store, limit=None, overwrite=False):
    extract(source, sets_path, store, 0, 1, limit=limit)
    return seal(sets_path, store, overwrite=overwrite)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("extract")
    for name in ("source", "sets", "store"):
        run.add_argument(name)
    run.add_argument("shard", type=int)
    run.add_argument("nshards", type=int)
    run.add_argument("limit", type=int, nargs="?")
    sealing = sub.add_parser("seal")
    sealing.add_argument("sets")
    sealing.add_argument("store")
    sealing.add_argument("--overwrite", action="store_true")
    building = sub.add_parser("build")
    for name in ("source", "sets", "store"):
        building.add_argument(name)
    building.add_argument("--limit", type=int, default=None)
    building.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "extract":
        result = extract(args.source, args.sets, args.store, args.shard, args.nshards, args.limit)
    elif args.command == "seal":
        result = seal(args.sets, args.store, overwrite=args.overwrite)
    else:
        result = build(args.source, args.sets, args.store, limit=args.limit, overwrite=args.overwrite)
    if result is not None:
        print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
