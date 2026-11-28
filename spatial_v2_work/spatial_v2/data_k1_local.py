"""Local K1 real indoor capture dataset with strict room-level exclusion guard.

Zero NFS IO: reads only node-local /scratch assets:
  - Manifest:    /scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json
  - Frames:      /scratch/jjyeung/k1_frames/<sha[:2]>/<sha>.png
  - GT npz:      per-capture paths under /scratch/jjyeung/orch_cd/dose_pool/out/...
  - Exclusions:  /scratch/jjyeung/orch_n30/nvkey1/work/excl/{R0_ROOMS.txt,
                 dev_scene_exclusions.json, benchmark_scene_exclusions.json,
                 WITHHELD_ROOMS_80.json, K1_SPLIT.json}
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional, Sequence, Set, Tuple

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from .geo_heads import (
    compute_gravity_leveled_poses,
    compute_plucker_rays,
    unproject_depth,
)

DEFAULT_MANIFEST_PATH = "/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json"
DEFAULT_FRAMES_ROOT = "/scratch/jjyeung/k1_frames"
DEFAULT_EXCL_DIR = "/scratch/jjyeung/orch_n30/nvkey1/work/excl"
DEFAULT_DA3_PRED_ROOT = "/scratch/jjyeung/orch_n30/geo_k1/pred_gpu/da3"

_SCANNET_RESCAN_RE = re.compile(r"^scene(\d{4})_\d{2}$")

QWEN_MEAN = (0.5, 0.5, 0.5)
QWEN_STD = (0.5, 0.5, 0.5)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def canonical_room_keys(canonical: str, room: Optional[str] = None) -> Set[str]:
    """Expand a capture/room identity into canonical room & rescan-stripped keys."""
    keys: Set[str] = set()
    for raw in (canonical, room):
        if not raw:
            continue
        norm = raw.strip().replace("::", "/")
        keys.add(norm)
        keys.add(norm.replace("/", "::"))
        if "/" in norm:
            ds, sc = norm.split("/", 1)
            keys.add(sc)
            if ds == "scannet":
                m = _SCANNET_RESCAN_RE.match(sc)
                if m:
                    base = f"scene{m.group(1)}"
                    keys.add(f"scannet/{base}")
                    keys.add(f"scannet::{base}")
                    keys.add(base)
                elif sc.startswith("scene") and "_" in sc:
                    base = sc.rsplit("_", 1)[0]
                    keys.add(f"scannet/{base}")
                    keys.add(f"scannet::{base}")
                    keys.add(base)
    return keys


class RoomExclusionGuard:
    """Enforces zero room-level leakage against all 5 canonical lab blocklists."""

    def __init__(self, excl_dir: str | Path = DEFAULT_EXCL_DIR) -> None:
        self.excl_dir = Path(excl_dir)
        self.blocklists: Dict[str, Set[str]] = {
            "R0": set(),
            "dev-S1": set(),
            "BENCH_v2": set(),
            "withheld-80": set(),
            "K1-heldout": set(),
        }
        self._load_all()
        self.verify_canaries()

    def _add_many(self, bucket: str, items: Iterable[str]) -> None:
        target = self.blocklists[bucket]
        for item in items:
            if isinstance(item, str) and item.strip():
                target.update(canonical_room_keys(item))

    def _load_all(self) -> None:
        r0_path = self.excl_dir / "R0_ROOMS.txt"
        dev_path = self.excl_dir / "dev_scene_exclusions.json"
        bm_path = self.excl_dir / "benchmark_scene_exclusions.json"
        w80_path = self.excl_dir / "WITHHELD_ROOMS_80.json"
        k1_path = self.excl_dir / "K1_SPLIT.json"

        for p in (r0_path, dev_path, bm_path, w80_path, k1_path):
            if not p.is_file():
                raise FileNotFoundError(f"Required exclusion list missing: {p}")

        # 1. R0 (372 rooms: R0-rl + R0-dev)
        self._add_many("R0", (l.strip() for l in r0_path.read_text().splitlines() if l.strip()))

        # 2. dev-S1 (100 physical groups + 224 aliases/natives)
        dev_ex = json.loads(dev_path.read_text())
        self._add_many("dev-S1", dev_ex.get("rooms", []))
        self._add_many("dev-S1", dev_ex.get("physical_groups", []))
        self._add_many("dev-S1", dev_ex.get("natives", []))
        aliases = dev_ex.get("aliases", {})
        if isinstance(aliases, dict):
            self._add_many("dev-S1", aliases.keys())
            for v in aliases.values():
                if isinstance(v, str):
                    self._add_many("dev-S1", [v])
                elif isinstance(v, list):
                    self._add_many("dev-S1", v)

        # 3. BENCH v2 (VSI-Bench, ReVSI, VSTI, STI-Bench/ReSTI, DSI, MindCube, OSI)
        bm_ex = json.loads(bm_path.read_text())
        self._add_many("BENCH_v2", bm_ex.get("physical_groups", []))
        self._add_many("BENCH_v2", bm_ex.get("scenes", []))
        self._add_many("BENCH_v2", bm_ex.get("rung1_tokens", []))

        # 4. Withheld-80
        w80 = json.loads(w80_path.read_text())
        self._add_many("withheld-80", w80.get("rooms", []))
        w80_aliases = w80.get("aliases", {})
        if isinstance(w80_aliases, dict):
            self._add_many("withheld-80", w80_aliases.keys())
            for v in w80_aliases.values():
                if isinstance(v, list):
                    self._add_many("withheld-80", v)
                elif isinstance(v, str):
                    self._add_many("withheld-80", [v])

        # 5. K1-heldout (58 heldout captures / rooms)
        k1s = json.loads(k1_path.read_text())
        for entry in k1s.get("heldout", []):
            if isinstance(entry, str):
                self._add_many("K1-heldout", [entry])
            elif isinstance(entry, dict):
                self._add_many(
                    "K1-heldout",
                    [entry.get("canonical", ""), entry.get("room", ""), entry.get("scene", "")],
                )

    def hits_for_capture(
        self, canonical: str, room: Optional[str] = None, k1_split: Optional[str] = None
    ) -> List[str]:
        keys = canonical_room_keys(canonical, room)
        hits = [name for name, bset in self.blocklists.items() if keys & bset]
        if k1_split is not None and k1_split != "train" and "K1-heldout" not in hits:
            hits.append("K1-heldout")
        return sorted(hits)

    def is_forbidden_for_train(
        self, canonical: str, room: Optional[str] = None, k1_split: Optional[str] = None
    ) -> bool:
        return len(self.hits_for_capture(canonical, room, k1_split=k1_split)) > 0

    def verify_canaries(self) -> Dict[str, List[str]]:
        """Assert that planted rooms from every blocklist (incl. ScanNet rescan alias) are blocked."""
        results: Dict[str, List[str]] = {}
        for name, bset in self.blocklists.items():
            # Pick a deterministic scannet room if present, else first entry with '/'
            scannet_rooms = sorted(k for k in bset if k.startswith("scannet/scene") and "_" not in k)
            if scannet_rooms:
                probe_room = scannet_rooms[0]
                probe_canonical = f"{probe_room}_99"  # synthetic rescan suffix
            else:
                slash_rooms = sorted(k for k in bset if "/" in k)
                if not slash_rooms:
                    raise RuntimeError(f"Exclusion blocklist {name} is empty!")
                probe_room = slash_rooms[0]
                probe_canonical = probe_room
            hits = self.hits_for_capture(probe_canonical, probe_room)
            if name not in hits:
                raise RuntimeError(
                    f"Canary leakage check FAILED for {name}: probe={probe_canonical}, hits={hits}"
                )
            results[name] = hits
        return results

    def assert_clean_split(
        self,
        train_records: Sequence["CaptureRecord"],
        val_records: Sequence["CaptureRecord"],
    ) -> None:
        train_rooms = {r.room for r in train_records}
        val_rooms = {r.room for r in val_records}
        overlap = train_rooms & val_rooms
        if overlap:
            raise RuntimeError(f"Room overlap between train and val: {sorted(overlap)[:5]}")
        for r in train_records:
            hits = self.hits_for_capture(r.canonical, r.room, k1_split=r.k1_split)
            if hits:
                raise RuntimeError(f"Forbidden room leaked into train: {r.canonical} ({r.room}) hits={hits}")
        for r in val_records:
            hits = [h for h in self.hits_for_capture(r.canonical, r.room) if h != "K1-heldout"]
            if hits:
                raise RuntimeError(f"Forbidden non-K1-heldout room in val: {r.canonical} ({r.room}) hits={hits}")


@dataclass(frozen=True)
class CaptureRecord:
    canonical: str
    room: str
    dataset: str
    k1_split: str
    gt_path: str
    anchor_frame_paths: Tuple[str, ...]
    anchor_timestamps: Tuple[float, ...]
    da3_pred_path: Optional[str] = None


def build_clean_k1_splits(
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    frames_root: str | Path = DEFAULT_FRAMES_ROOT,
    excl_dir: str | Path = DEFAULT_EXCL_DIR,
    da3_pred_root: Optional[str | Path] = DEFAULT_DA3_PRED_ROOT,
) -> Tuple[List[CaptureRecord], List[CaptureRecord], RoomExclusionGuard, Dict[str, object]]:
    """Build strictly disjoint, leakage-verified K1 train & held-out val splits."""
    guard = RoomExclusionGuard(excl_dir)
    manifest = json.loads(Path(manifest_path).read_text())
    frames_root_p = Path(frames_root)

    # Optional DA3 precomputed index
    da3_by_cap: Dict[str, str] = {}
    if da3_pred_root and Path(da3_pred_root).is_dir():
        for entry in sorted(Path(da3_pred_root).iterdir()):
            dj = entry / "DONE.json"
            pz = entry / "pred.npz"
            if dj.is_file() and pz.is_file():
                meta = json.loads(dj.read_text())
                if "capture" in meta:
                    da3_by_cap[meta["capture"]] = str(pz)

    train_records: List[CaptureRecord] = []
    val_records: List[CaptureRecord] = []
    skipped_missing = 0
    excluded_non_k1 = 0

    for cap in manifest["captures"]:
        canonical = cap["canonical"]
        room = cap["room"]
        dataset = canonical.split("/", 1)[0]
        k1_split = cap.get("k1_split", cap.get("split", "unknown"))
        gt_info = cap.get("gt")
        if not gt_info or not os.path.isfile(gt_info.get("path", "")):
            skipped_missing += 1
            continue

        dense_frames = cap.get("dense_frames", [])
        anchor_slots = cap.get("anchor_slots", [])
        if len(anchor_slots) != 32 or len(dense_frames) < 32:
            skipped_missing += 1
            continue

        anchor_paths: List[str] = []
        missing_frame = False
        for slot in anchor_slots:
            h = dense_frames[int(slot)]["sha256"]
            fp = frames_root_p / h[:2] / f"{h}.png"
            if not fp.is_file():
                missing_frame = True
                break
            anchor_paths.append(str(fp))
        if missing_frame:
            skipped_missing += 1
            continue

        # Timestamps from model_row if available, else normalized index
        ts_raw = (
            cap.get("model_row", {}).get("student_input", {}).get("timestamps")
            or [float(i) for i in range(len(anchor_paths))]
        )
        if len(ts_raw) != len(anchor_paths):
            ts_raw = [float(i) for i in range(len(anchor_paths))]
        t_min, t_max = min(ts_raw), max(ts_raw)
        denom = max(t_max - t_min, 1e-6)
        ts_norm = tuple((float(t) - t_min) / denom for t in ts_raw)

        rec = CaptureRecord(
            canonical=canonical,
            room=room,
            dataset=dataset,
            k1_split=k1_split,
            gt_path=gt_info["path"],
            anchor_frame_paths=tuple(anchor_paths),
            anchor_timestamps=ts_norm,
            da3_pred_path=da3_by_cap.get(canonical),
        )

        hits = guard.hits_for_capture(canonical, room, k1_split=k1_split)
        if not hits:
            train_records.append(rec)
        elif set(hits) == {"K1-heldout"}:
            val_records.append(rec)
        else:
            excluded_non_k1 += 1

    guard.assert_clean_split(train_records, val_records)
    split_sig = hashlib.sha256(
        json.dumps(
            {
                "train": [r.canonical for r in train_records],
                "val": [r.canonical for r in val_records],
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()

    summary = {
        "train_captures": len(train_records),
        "train_rooms": len({r.room for r in train_records}),
        "val_captures": len(val_records),
        "val_rooms": len({r.room for r in val_records}),
        "room_overlap": 0,
        "skipped_missing_local": skipped_missing,
        "excluded_blocked_rooms": excluded_non_k1,
        "split_sha256": split_sig,
    }
    return train_records, val_records, guard, summary


def _masked_downsample_depth(
    depth: np.ndarray, out_h: int, out_w: int, min_depth: float = 0.05, max_depth: float = 25.0
) -> Tuple[np.ndarray, np.ndarray]:
    """Masked area-average downsample of metric depth [N, H, W] -> ([N, out_h, out_w], valid_mask)."""
    d = torch.from_numpy(depth.astype(np.float32))  # [N, H, W]
    valid = torch.isfinite(d) & (d > min_depth) & (d < max_depth)
    d_zero = torch.where(valid, d, torch.zeros_like(d))
    num = torch.nn.functional.adaptive_avg_pool2d(d_zero.unsqueeze(1), (out_h, out_w)).squeeze(1)
    den = torch.nn.functional.adaptive_avg_pool2d(valid.float().unsqueeze(1), (out_h, out_w)).squeeze(1)
    out_valid = den > 0.25
    out_depth = torch.where(out_valid, num / den.clamp_min(1e-6), torch.zeros_like(num))
    return out_depth.numpy().astype(np.float32), out_valid.numpy().astype(bool)


def _scale_intrinsics(K: np.ndarray, src_h: int, src_w: int, dst_h: int, dst_w: int) -> np.ndarray:
    K_out = K.astype(np.float64).copy()
    sx = float(dst_w) / float(src_w)
    sy = float(dst_h) / float(src_h)
    K_out[..., 0, 0] *= sx
    K_out[..., 0, 2] *= sx
    K_out[..., 1, 1] *= sy
    K_out[..., 1, 2] *= sy
    return K_out.astype(np.float32)


def _load_rgb_tensor(
    paths: Sequence[str],
    height: int,
    width: int,
    mean: Tuple[float, float, float],
    std: Tuple[float, float, float],
) -> torch.Tensor:
    imgs: List[np.ndarray] = []
    for p in paths:
        with Image.open(p) as im:
            im_rgb = im.convert("RGB").resize((width, height), resample=Image.BILINEAR)
            imgs.append(np.asarray(im_rgb, dtype=np.float32) / 255.0)
    arr = np.stack(imgs, axis=0)  # [N, H, W, 3]
    t = torch.from_numpy(arr).permute(0, 3, 1, 2).contiguous()  # [N, 3, H, W]
    m = torch.tensor(mean, dtype=torch.float32).view(1, 3, 1, 1)
    s = torch.tensor(std, dtype=torch.float32).view(1, 3, 1, 1)
    return (t - m) / s


class LocalK1CaptureDataset(Dataset):
    """Real cached indoor K1 dataset returning paired dual-grid RGB + exact metric 3D GT.

    Produces aligned spatial patch grids `(grid_h, grid_w)` for both:
      - Qwen3.5 ViT (patch=16 -> RGB size `grid_h*16 x grid_w*16`)
      - DA3 / DINOv2 (patch=14 -> RGB size `grid_h*14 x grid_w*14`)
    """

    def __init__(
        self,
        split: Literal["train", "val"],
        num_views: int = 8,
        grid_h: int = 20,
        grid_w: int = 20,
        manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
        frames_root: str | Path = DEFAULT_FRAMES_ROOT,
        excl_dir: str | Path = DEFAULT_EXCL_DIR,
        random_subsample: bool = False,
        seed: int = 42,
        load_qwen_rgb: bool = True,
        load_da3_rgb: bool = True,
        max_captures: Optional[int] = None,
    ) -> None:
        super().__init__()
        if grid_h % 2 != 0 or grid_w % 2 != 0:
            raise ValueError(f"grid_h and grid_w must be even (spatial_merge=2), got {(grid_h, grid_w)}")
        if num_views < 2 or num_views > 32:
            raise ValueError(f"num_views must be in [2, 32], got {num_views}")

        train_recs, val_recs, guard, summary = build_clean_k1_splits(
            manifest_path=manifest_path, frames_root=frames_root, excl_dir=excl_dir
        )
        self.guard = guard
        self.split_summary = summary
        self.split = split
        recs = train_recs if split == "train" else val_recs
        if max_captures is not None:
            recs = recs[:max_captures]
        self.records: List[CaptureRecord] = list(recs)
        self.num_views = num_views
        self.grid_h = grid_h
        self.grid_w = grid_w
        self.hm = grid_h // 2
        self.wm = grid_w // 2
        self.random_subsample = random_subsample and (split == "train")
        self.rng = np.random.default_rng(seed)
        self.load_qwen_rgb = load_qwen_rgb
        self.load_da3_rgb = load_da3_rgb

    def __len__(self) -> int:
        return len(self.records)

    def _select_indices(self, valid_flags: np.ndarray) -> np.ndarray:
        n_total = len(valid_flags)
        valid_idx = np.where(valid_flags)[0]
        pool = valid_idx if len(valid_idx) >= self.num_views else np.arange(n_total)
        if len(pool) == self.num_views:
            return pool.astype(np.int64)
        if self.random_subsample and len(pool) > self.num_views:
            # Stratified jittered sampling preserving monotonic temporal order
            edges = np.linspace(0, len(pool), self.num_views + 1)
            chosen = []
            for i in range(self.num_views):
                lo = int(math.floor(edges[i]))
                hi = max(lo + 1, int(math.floor(edges[i + 1])))
                hi = min(hi, len(pool))
                chosen.append(pool[int(self.rng.integers(lo, hi))])
            return np.asarray(chosen, dtype=np.int64)
        pos = np.linspace(0, len(pool) - 1, self.num_views).round().astype(np.int64)
        return pool[pos].astype(np.int64)

    def __getitem__(self, idx: int) -> Dict[str, object]:
        rec = self.records[idx]
        with np.load(rec.gt_path, allow_pickle=False) as z:
            depth_all = z["depth"]  # [32, H_d, W_d]
            K_all = z["K_frames"] if "K_frames" in z.files else np.broadcast_to(z["K"], (32, 3, 3)).copy()
            c2w_all = z["c2w"]  # [32, 4, 4]
            valid_all = z["valid"].astype(bool)

        # Ensure finite poses
        finite_pose = np.isfinite(c2w_all).all(axis=(1, 2)) & np.isfinite(K_all).all(axis=(1, 2))
        sel = self._select_indices(valid_all & finite_pose)

        depth_sel = depth_all[sel]  # [N, H_d, W_d]
        K_sel = K_all[sel]  # [N, 3, 3]
        c2w_sel = c2w_all[sel].astype(np.float64)  # [N, 4, 4]
        vm_sel = (valid_all & finite_pose)[sel]
        src_h, src_w = depth_sel.shape[1], depth_sel.shape[2]

        # OpenCV w2c from c2w: R_w2c = R_c2w^T, t_w2c = -R_w2c @ t_c2w
        R_c2w = c2w_sel[:, :3, :3]
        t_c2w = c2w_sel[:, :3, 3]
        R_w2c = np.swapaxes(R_c2w, -1, -2)
        t_w2c = -np.einsum("nij,nj->ni", R_w2c, t_c2w)

        # World +Z up expressed in each OpenCV camera frame: R_w2c @ [0, 0, 1]
        z_world = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        grav_cam = np.einsum("nij,j->ni", R_w2c, z_world)
        grav_cam = grav_cam / np.linalg.norm(grav_cam, axis=-1, keepdims=True).clip(min=1e-7)

        # Canonicalize into SE(3)-invariant View-0 +Z-up world frame
        rot_t = torch.from_numpy(R_w2c.astype(np.float32)).unsqueeze(0)
        trans_t = torch.from_numpy(t_w2c.astype(np.float32)).unsqueeze(0)
        grav_t = torch.from_numpy(grav_cam.astype(np.float32)).unsqueeze(0)
        rot_canon, trans_canon = compute_gravity_leveled_poses(rot_t, trans_t, grav_t[:, 0])
        rot_gt = rot_canon.squeeze(0)  # [N, 3, 3]
        trans_gt = trans_canon.squeeze(0)  # [N, 3]
        gravity_gt = grav_t.squeeze(0)  # [N, 3]

        # Resolution-invariant focal ratios
        fx_w = np.clip(np.abs(K_sel[:, 0, 0]) / float(src_w), 0.1, 10.0)
        fy_h = np.clip(np.abs(K_sel[:, 1, 1]) / float(src_h), 0.1, 10.0)
        log_fx_w_gt = torch.from_numpy(np.log(fx_w).astype(np.float32))
        log_fy_h_gt = torch.from_numpy(np.log(fy_h).astype(np.float32))

        # Downsample depth & scale intrinsics to fine (grid_h, grid_w) and merged (hm, wm)
        depth_fine, depth_valid = _masked_downsample_depth(depth_sel, self.grid_h, self.grid_w)
        depth_gt = torch.from_numpy(depth_fine)  # [N, H2, W2]
        depth_valid_t = torch.from_numpy(depth_valid) & torch.from_numpy(vm_sel)[:, None, None]

        K_fine = torch.from_numpy(_scale_intrinsics(K_sel, src_h, src_w, self.grid_h, self.grid_w))
        K_merged = torch.from_numpy(_scale_intrinsics(K_sel, src_h, src_w, self.hm, self.wm))

        plucker_gt = compute_plucker_rays(K_merged, rot_gt, trans_gt, self.hm, self.wm)  # [N, Hm, Wm, 6]
        pmap_gt = unproject_depth(depth_gt, K_fine, rot_gt, trans_gt)  # [N, H2, W2, 3]
        pmap_gt = torch.where(depth_valid_t.unsqueeze(-1), pmap_gt, torch.zeros_like(pmap_gt))

        frame_paths = [rec.anchor_frame_paths[int(i)] for i in sel]
        timestamps = torch.tensor([rec.anchor_timestamps[int(i)] for i in sel], dtype=torch.float32)

        sample: Dict[str, object] = {
            "depth_gt": depth_gt,
            "depth_valid": depth_valid_t,
            "rot_gt": rot_gt,
            "trans_gt": trans_gt,
            "gravity_gt": gravity_gt,
            "log_fx_w_gt": log_fx_w_gt,
            "log_fy_h_gt": log_fy_h_gt,
            "K_fine": K_fine,
            "K_merged": K_merged,
            "plucker_gt": plucker_gt,
            "pmap_gt": pmap_gt,
            "metric_scale_locked": torch.tensor(1.0, dtype=torch.float32),
            "view_mask": torch.from_numpy(vm_sel.astype(bool)),
            "timestamps": timestamps,
            "capture_id": rec.canonical,
            "room_id": rec.room,
            "dataset": rec.dataset,
        }
        if self.load_qwen_rgb:
            sample["rgb_qwen"] = _load_rgb_tensor(
                frame_paths, self.grid_h * 16, self.grid_w * 16, QWEN_MEAN, QWEN_STD
            )
        if self.load_da3_rgb:
            sample["rgb_da3"] = _load_rgb_tensor(
                frame_paths, self.grid_h * 14, self.grid_w * 14, IMAGENET_MEAN, IMAGENET_STD
            )
        return sample


def collate_k1_batch(items: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Collate list of LocalK1CaptureDataset items into batched tensors + metadata lists."""
    out: Dict[str, object] = {}
    keys = items[0].keys()
    for k in keys:
        v0 = items[0][k]
        if torch.is_tensor(v0):
            out[k] = torch.stack([it[k] for it in items], dim=0)
        else:
            out[k] = [it[k] for it in items]
    return out
