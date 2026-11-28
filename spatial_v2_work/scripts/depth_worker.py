"""Persistent GPU coprocess worker for closed-loop R2R-CE navigation in `sam3_capretry_native_v1`.

Reads 1..4 (512, 512, 3) uint8 RGB frames from `/dev/shm/jjyeung_nav_e0_rgb_ipc.dat` memmap,
runs StandaloneVCDepth (`m400/vc_depth_only.pt`) and StandaloneDA3Depth (`da3nested-giant-large`),
caches predictions per deterministic frame hash within the episode, and returns the metric depth
at the clicked waypoint `(u, v)` plus scale diagnostics over stdin/stdout JSON lines prefixed with `IPC_JSON:`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List
import numpy as np
import torch

SHM_RGB_PATH = Path("/dev/shm/jjyeung_nav_e0_rgb_ipc.dat")
MAX_CLIP = 4
H, W = 512, 512


def sample_click_depth(d_map: np.ndarray, u: float, v: float) -> float:
    Hd, Wd = d_map.shape
    px_x = min(max(int(u * Wd), 0), Wd - 1)
    px_y = min(max(int(v * Hd), 0), Hd - 1)
    y0, y1 = max(0, px_y - 1), min(Hd, px_y + 2)
    x0, x1 = max(0, px_x - 1), min(Wd, px_x + 2)
    patch = d_map[y0:y1, x0:x1]
    valid = patch[np.isfinite(patch) & (patch > 0.05)]
    return float(np.median(valid)) if valid.size > 0 else float(d_map[px_y, px_x])


def main():
    ipc_out = sys.stdout
    # Redirect standard print/logging from third-party libraries (e.g. DA3 [INFO]) to stderr
    sys.stdout = sys.stderr

    from depth_models import StandaloneVCDepth, StandaloneDA3Depth

    need_vc = "--vc" in sys.argv
    need_da3 = "--da3" in sys.argv

    vc_model = StandaloneVCDepth(device="cuda") if need_vc else None
    da3_model = StandaloneDA3Depth(device="cuda") if need_da3 else None

    rgb_mmap = np.memmap(str(SHM_RGB_PATH), dtype=np.uint8, mode="r", shape=(MAX_CLIP, H, W, 3))

    vc_cache: Dict[str, dict] = {}
    da3_cache: Dict[str, dict] = {}
    ep_vc_scales: Dict[str, List[float]] = {}
    ep_da3_scales: Dict[str, List[float]] = {}

    ipc_out.write("IPC_JSON:" + json.dumps({"ready": True, "vc": need_vc, "da3": need_da3}) + "\n")
    ipc_out.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        cmd = req.get("cmd")
        if cmd == "quit":
            break
        if cmd == "reset_ep":
            ep_key = f"{req.get('arm')}:{req.get('ep_id')}"
            ep_vc_scales.pop(ep_key, None)
            ep_da3_scales.pop(ep_key, None)
            if len(vc_cache) > 2500:
                vc_cache.clear()
            if len(da3_cache) > 2500:
                da3_cache.clear()
            ipc_out.write("IPC_JSON:" + json.dumps({"ok": True}) + "\n")
            ipc_out.flush()
            continue

        if cmd == "query":
            arm = req["arm"]
            k = int(req["k"])
            u = float(req["u"])
            v = float(req["v"])
            ep_id = str(req["ep_id"])
            ep_key = f"{arm}:{ep_id}"

            frames = [rgb_mmap[i].copy() for i in range(k)]
            h_hash = hashlib.md5(b"".join(f.tobytes() for f in frames)).hexdigest()

            if arm.startswith("vc_"):
                if h_hash not in vc_cache:
                    out = vc_model.infer_single_or_clip(frames, query_grid_size=64, hab_hfov_deg=90.0)
                    vc_cache[h_hash] = {
                        "vc_raw": out["vc_raw"],
                        "s_fov_58deg": float(out["s_fov_58deg"]),
                        "s_fov_e0_194": float(out["s_fov_e0_194"]),
                        "s_anchor": float(out["s_anchor"]),
                        "svd_valid": bool(out["anchor_info"].get("svd_valid", False)),
                        "pred_fov_x_deg": float(out["pred_fov_x_deg"]),
                    }
                entry = vc_cache[h_hash]
                if entry["svd_valid"]:
                    ep_vc_scales.setdefault(ep_key, []).append(entry["s_anchor"])
                s_ep = float(np.median(ep_vc_scales[ep_key])) if ep_vc_scales.get(ep_key) else entry["s_anchor"]

                d_raw_click = sample_click_depth(entry["vc_raw"], u, v)
                if arm == "vc_raw":
                    scale = 1.0
                elif arm in ("vc_fovfix", "vc_fovfix_58deg"):
                    scale = entry["s_fov_58deg"]
                elif arm == "vc_fovfix_e0":
                    scale = entry["s_fov_e0_194"]
                elif arm == "vc_scale_anchor":
                    scale = s_ep
                else:
                    raise ValueError(f"Unknown V-C arm: {arm}")

                d_val = d_raw_click * scale
                resp = {
                    "ok": True,
                    "d_click": d_val,
                    "d_raw_click": d_raw_click,
                    "scale": scale,
                    "pred_fov_x_deg": entry["pred_fov_x_deg"],
                }
                ipc_out.write("IPC_JSON:" + json.dumps(resp) + "\n")
                ipc_out.flush()

            elif arm.startswith("da3_"):
                last_hash = hashlib.md5(frames[-1].tobytes()).hexdigest()
                if last_hash not in da3_cache:
                    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                        out = da3_model.infer_single_or_window([frames[-1]], process_res=336, hab_hfov_deg=90.0)
                    da3_cache[last_hash] = {
                        "da3_raw": out["da3_raw"],
                        "s_fov_da3": float(out["s_fov_da3"]),
                        "s_anchor": float(out["s_anchor"]),
                        "svd_valid": bool(out["anchor_info"].get("svd_valid", False)),
                        "pred_hfov_deg": float(out["pred_hfov_deg"]),
                    }
                entry = da3_cache[last_hash]
                if entry["svd_valid"]:
                    ep_da3_scales.setdefault(ep_key, []).append(entry["s_anchor"])
                s_ep = float(np.median(ep_da3_scales[ep_key])) if ep_da3_scales.get(ep_key) else entry["s_fov_da3"]

                d_raw_click = sample_click_depth(entry["da3_raw"], u, v)
                if arm == "da3_raw":
                    scale = 1.0
                elif arm == "da3_fovfix":
                    scale = entry["s_fov_da3"]
                elif arm == "da3_scale_anchor":
                    scale = s_ep
                else:
                    raise ValueError(f"Unknown DA3 arm: {arm}")

                d_val = d_raw_click * scale
                resp = {
                    "ok": True,
                    "d_click": d_val,
                    "d_raw_click": d_raw_click,
                    "scale": scale,
                    "pred_hfov_deg": entry["pred_hfov_deg"],
                }
                ipc_out.write("IPC_JSON:" + json.dumps(resp) + "\n")
                ipc_out.flush()


if __name__ == "__main__":
    main()
