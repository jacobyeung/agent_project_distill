import fcntl
import json
import socket
from pathlib import Path
from uuid import uuid4

import numpy as np
from scipy.ndimage import map_coordinates

from .contract import camera_arrays, load_export, raster_depth
from .io import ROOT, check_space, footprint, sha256, utc
from .selectors import TowerGeometry
from .provenance import verify_export_receipt


NATIVE_LIMIT = 30_000_000_000
NATIVE_FREE = 150 * 1024 ** 3


def resample(array, hw, order=1):
    h, w = hw
    ih, iw = array.shape[-2:]
    yy, xx = np.meshgrid((np.arange(h)+.5)/h*ih-.5, (np.arange(w)+.5)/w*iw-.5, indexing="ij")
    return np.stack([map_coordinates(d, [yy, xx], order=order, mode="nearest", prefilter=False) for d in array])


def native_preflight(root, scene_count, device, run_host=None):
    root = Path(root).resolve()
    if not root.is_relative_to("/scratch"):
        raise ValueError("Native depth must stay on node-local scratch")
    if device == "cpu":
        if scene_count != 1 or not root.is_relative_to(ROOT):
            raise PermissionError("CPU native export is limited to one clip inside this lane")
        check_space(64 * 1024 ** 2)
    else:
        if not run_host or socket.gethostname().split(".")[0] != run_host or root.is_relative_to(ROOT):
            raise PermissionError("Native GPU output requires the declared run host and a separate scratch root")
        used = footprint(root) if root.exists() else 0
        if used >= NATIVE_LIMIT:
            raise RuntimeError("The 30 GB native-depth budget is exhausted")
        if check_space() - (NATIVE_LIMIT-used) < NATIVE_FREE:
            raise RuntimeError("The full native export must leave 150 GiB free")
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_native(root, model, scene, prediction, frames, slots, device, run_id=None):
    root = Path(root)
    directory = root / run_id / model if run_id else root / model
    if not directory.resolve().is_relative_to(root.resolve()):
        raise ValueError("Native namespace escapes its storage root")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"scannet__{scene}_{uuid4().hex}.npz"
    source = prediction.depth[slots]
    if np.max(source) > np.finfo(np.float16).max:
        raise ValueError("Native depth cannot be represented in float16")
    depth = source.astype(np.float16)
    with (root / "manifest.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        expected = depth.nbytes + 128 * 1024
        if footprint(root) + expected > NATIVE_LIMIT:
            raise RuntimeError("The next native file would exceed the 30 GB total cap")
        free = check_space(expected)
        if device != "cpu" and free - expected < NATIVE_FREE:
            raise RuntimeError("Native export would cross the 150 GiB free-space floor")
        with path.open("xb") as f:
            np.savez_compressed(f, depth=depth, intrinsics=prediction.intrinsics[slots],
                                source_hw=np.array(prediction.source_hw), anchor_frame_indices=frames[slots],
                                quantization_max_abs_m=np.array(float(np.max(np.abs(source-depth.astype(np.float32))))))
        row = {"file": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha256(path),
               "scene": scene, "model": model, "anchors": len(slots), "dtype": "float16",
               "shape": list(depth.shape), "created_at": utc(), "run_id": run_id}
        with (root / "MANIFEST.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
    return row


def load_native(path, frames):
    with np.load(path, allow_pickle=False) as z:
        data = {k: z[k] for k in z.files}
    np.testing.assert_array_equal(data["anchor_frame_indices"], frames)
    if data["depth"].ndim != 3 or len(data["depth"]) != len(frames) or data["intrinsics"].shape != (len(frames), 3, 3):
        raise ValueError("Native depth/calibration has the wrong shape")
    if not np.isfinite(data["depth"]).all() or np.any(data["depth"] < 0):
        raise ValueError("Invalid native depth")
    return data


def verified_native(root, receipt, frames):
    root = Path(root).resolve()
    if not receipt:
        raise ValueError("The producing arm has no native-depth receipt")
    path = (root / receipt["file"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Native receipt escapes its storage root")
    rows = [json.loads(line) for line in (root / "MANIFEST.jsonl").read_text().splitlines() if line.strip()]
    matches = [row for row in rows if row["file"] == receipt["file"]]
    if len(matches) != 1 or any(matches[0].get(key) != receipt.get(key) for key in ("sha256", "bytes", "scene", "model")):
        raise ValueError("Native file does not match the producing arm and manifest")
    if path.stat().st_size != receipt["bytes"] or sha256(path) != receipt["sha256"]:
        raise ValueError("Native file bytes differ from the producing arm's receipt")
    return load_native(path, frames)


class NativeGeometry(TowerGeometry):
    def __init__(self, exports, scene, native_root, full_intrinsics=True):
        exports, native_root = Path(exports), Path(native_root)
        path = exports / f"scannet__{scene}.npz"
        producer = verify_export_receipt(exports, scene)
        super().__init__(path)
        self.native_rays = {}
        baseline = load_export(path)
        frames = baseline["anchor_frame_indices"]
        _, self.intrinsics = camera_arrays(baseline, (240, 320))
        recipe_path = exports / "native_recipes" / f"{scene}.json"
        if recipe_path.is_file():
            recipe = json.loads(recipe_path.read_text())
            kind = recipe["kind"]
            if kind in ("clip_scale", "clip_scale_depth_only", "frame_affine"):
                self.raster = raster_depth(baseline["depth_grid"])
                self.representation = "transformed_51_grid; no native G3T raster"
                return
            data = verified_native(native_root, recipe.get("candidate_native"), frames)
            depth = data["depth"].astype(np.float32)
            if kind == "consensus":
                depth *= np.asarray(recipe["scales"], np.float32)[:, None, None]
            if kind == "average":
                other = verified_native(native_root, recipe.get("second_native"), frames)
                second = resample(other["depth"].astype(np.float32), depth.shape[-2:])
                valid = (depth > 0) & (second > 0)
                depth = np.where(valid, .5 * (depth + second), 0)
            retain_intrinsics = kind in ("consensus", "pose_g3t")
        else:
            data = verified_native(native_root, producer.get("native_depth"), frames)
            depth = data["depth"].astype(np.float32)
            retain_intrinsics = True
        self.raster = resample(depth, (240, 320)).astype(np.float32)
        if retain_intrinsics and full_intrinsics:
            self.intrinsics = data["intrinsics"].astype(np.float64)
            h, w = data["source_hw"]
            self.intrinsics[:, 0] *= 320 / w
            self.intrinsics[:, 1] *= 240 / h
        self.representation = "native_float16_half_pixel"

    def depth(self, k):
        return self.raster[k-1]

    def rays(self, k):
        if k not in self.native_rays:
            yy, xx = np.mgrid[:240, :320]
            self.native_rays[k] = np.stack([xx+.5, yy+.5, np.ones_like(xx)], -1) @ np.linalg.inv(self.intrinsics[k-1]).T
        return self.native_rays[k]
