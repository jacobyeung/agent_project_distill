"""REQ-113 GT grounding backend over the sealed r804 REQ-01 scene closure.

The provider knows only a scene id and a tool-supplied category string.  It
never receives a question, qid, answer, or category-specific target instance.
Name matching is delegated byte-for-byte to the matcher used by the sealed
REQ-07/REQ-16 packet builder.  Every matched GT instance is projected; no
question-relevance filter exists in this module.
"""


from __future__ import annotations


import hashlib


from gt_errors import UnmappedGroundingLabel


import json


import math


import os


import re


import threading


from collections import OrderedDict


import pathlib


from pathlib import Path


from typing import Any, Callable


import cv2


import numpy as np
from mesh_membership import SPARSE_KEYS, instance_faces, validate_memberships


from donor_geometry import GTProviderError, _require_file, sha256_file


from gt_label_matcher_r1313 import match_label as _LOCAL_MATCH_LABEL


HERE = Path(__file__).resolve().parent


MIN_DEPTH_M = 0.05


OCCLUSION_TOLERANCE_M = 0.15


_BOX_SIGNS = np.asarray([
    [-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1],
    [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1],
], dtype=np.float64)


_BOX_TRIANGLES = np.asarray([
    [0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5],
    [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6],
    [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3],
], dtype=np.int64)


_MAX_INSTANCE_FACES = 30_000


class GTGroundingError(RuntimeError):
    """A sealed mapping, asset, projection, or output-boundary invariant failed."""


_SEALED_MATCH_LABEL: Callable[[str, dict[str, list[int]]], list[int]] = _LOCAL_MATCH_LABEL


def _load_instance_mesh(asset: dict[str, Any]) -> dict[str, np.ndarray]:
    mesh_path = _require_file(asset["mesh"], "REQ-113 grounding instance mesh")
    annotations_path = _require_file(
        asset["annotations"], "REQ-113 grounding instance annotations")
    with np.load(mesh_path, allow_pickle=False) as stored:
        legacy = {"vertices_world", "faces", "face_instance_ids"}
        sparse = {"vertices_world", "faces"} | SPARSE_KEYS
        if set(stored.files) not in (legacy, sparse):
            raise GTGroundingError(f"unexpected grounding mesh schema: {mesh_path}")
        mesh = {
            "vertices": stored["vertices_world"].astype(np.float32),
            "faces": stored["faces"].astype(np.int64),
        }
        if set(stored.files) == legacy:
            mesh["instance_ids"] = stored["face_instance_ids"].astype(np.int32)
        else:
            if stored["faces"].dtype.kind not in "iu":
                raise GTGroundingError(f"noninteger sparse grounding faces: {mesh_path}")
            mesh.update({key: stored[key] for key in SPARSE_KEYS})
    if mesh["faces"].ndim != 2 or mesh["faces"].shape[1] != 3:
        raise GTGroundingError(f"non-triangular grounding mesh: {mesh_path}")
    if "instance_ids" in mesh and len(mesh["faces"]) != len(mesh["instance_ids"]):
        raise GTGroundingError(f"grounding face/id length mismatch: {mesh_path}")
    annotations = json.loads(annotations_path.read_text())
    annotation_ids = {int(row["instance_id"]) for row in annotations.get("instances", [])}
    if "membership_instance_ids" in mesh:
        vertices, faces = mesh["vertices"], mesh["faces"]
        if (vertices.ndim != 2 or vertices.shape[1] != 3
                or not np.isfinite(vertices).all()
                or np.any(faces < 0) or np.any(faces >= len(vertices))):
            raise GTGroundingError(f"invalid sparse grounding geometry: {mesh_path}")
        try:
            validate_memberships(mesh, annotation_ids)
        except ValueError as error:
            raise GTGroundingError(f"invalid sparse grounding membership: {error}") from error
        return mesh
    mesh_ids = {int(value) for value in np.unique(mesh["instance_ids"]) if int(value) >= 0}
    # Some authenticated instances have an OBB annotation but no triangle faces.
    # Those IDs intentionally reach _render_instance's OBB fallback below.  Mesh
    # IDs must still be a non-empty subset of the authenticated annotations.
    if not annotation_ids or not mesh_ids or not mesh_ids.issubset(annotation_ids):
        raise GTGroundingError(f"grounding annotation/id mismatch: {mesh_path}")
    return mesh


def _safe_component(value: str, label: str) -> str:
    text = str(value)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", text) or text in {".", ".."}:
        raise GTGroundingError(f"unsafe {label}: {value!r}")
    return text


def _output_dir(path: Path) -> Path:
    runtime_raw = str(os.environ.get("REQ73_RUN_OUTPUT_ROOT", "")).strip()
    if not runtime_raw:
        raise GTGroundingError("REQ73_RUN_OUTPUT_ROOT is required for mask materialization")
    runtime = Path(runtime_raw).resolve()
    resolved = path.resolve()
    if resolved == runtime or runtime not in resolved.parents:
        raise GTGroundingError(f"mask directory escapes the admitted runtime root: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _canonical_label(value: str) -> str:
    # This is the sealed matcher's own first operation, not a new match tier.
    return str(value).lower().strip()


class REQ113GTGroundingProvider:
    def _inventory(self, scene_id: str) -> dict[str, Any]:
        scene_id = _safe_component(scene_id, "scene id")
        with self._lock:
            cached = self._inventories.get(scene_id)
            if cached is not None:
                return cached
        row = self.geometry._verify_scene(scene_id)
        groups = json.loads(Path(row["instances"]["path"]).read_text()).get("segGroups")
        if not isinstance(groups, list) or not groups:
            raise GTGroundingError(f"empty GT instance inventory: {scene_id}")
        labels_to_ids: dict[str, list[int]] = {}
        obbs: dict[int, dict[str, Any]] = {}
        labels: dict[int, str] = {}
        for group in groups:
            try:
                instance_id = int(group.get("objectId", group.get("id")))
                label = str(group["label"]).lower().strip()
                obb = group["obb"]
                centroid = np.asarray(obb["centroid"], dtype=np.float64).reshape(3)
                lengths = np.asarray(obb["axesLengths"], dtype=np.float64).reshape(3)
                axes = np.asarray(obb["normalizedAxes"], dtype=np.float64).reshape(3, 3)
            except (KeyError, TypeError, ValueError) as exc:
                raise GTGroundingError(f"malformed GT instance in {scene_id}") from exc
            if (
                instance_id < 0 or not label or not np.isfinite(centroid).all()
                or not np.isfinite(lengths).all() or not np.isfinite(axes).all()
                or (lengths <= 0).any()
            ):
                raise GTGroundingError(f"invalid GT instance in {scene_id}: {instance_id}")
            if instance_id in obbs:
                raise GTGroundingError(f"duplicate GT instance id in {scene_id}: {instance_id}")
            labels_to_ids.setdefault(label, []).append(instance_id)
            labels[instance_id] = label
            obbs[instance_id] = {
                "axes": axes,
                "centroid": centroid,
                "lengths": lengths,
            }
        result = {"labels": labels, "labels_to_ids": labels_to_ids, "obbs": obbs, "row": row}
        with self._lock:
            self._inventories[scene_id] = result
        return result

    def _instance_mesh(self, scene_id: str) -> dict[str, np.ndarray] | None:
        with self._lock:
            if scene_id in self._meshes:
                self._meshes.move_to_end(scene_id)
                return self._meshes[scene_id]
        row = self._inventory(scene_id)["row"]
        asset = self.grounding_assets.get(scene_id)
        if row["dataset"] == "scannetpp" and asset is None:
            raise GTGroundingError(f"missing ScanNet++ grounding asset: {scene_id}")
        mesh = None if asset is None else _load_instance_mesh(asset)
        with self._lock:
            self._meshes[scene_id] = mesh
            while len(self._meshes) > 2:
                self._meshes.popitem(last=False)
        return mesh

    def match_instances(self, scene_id: str, object_label: str) -> list[int]:
        inventory = self._inventory(scene_id)
        matched = _SEALED_MATCH_LABEL(object_label, inventory["labels_to_ids"])
        return sorted({int(value) for value in matched})

    @staticmethod
    def _project(points: np.ndarray, pose: np.ndarray, intrinsics: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        camera = (points - pose[:3, 3]) @ pose[:3, :3]
        depth = camera[:, 2]
        safe = np.where(depth > MIN_DEPTH_M, depth, 1.0)
        u = intrinsics[0, 0] * camera[:, 0] / safe + intrinsics[0, 2]
        v = intrinsics[1, 1] * camera[:, 1] / safe + intrinsics[1, 2]
        return u, v, depth

    def _obb_corners(self, scene_id: str, instance_id: int) -> np.ndarray:
        obb = self._inventory(scene_id)["obbs"].get(int(instance_id))
        if obb is None:
            raise GTGroundingError(f"mapped GT instance lacks an OBB: {scene_id}/{instance_id}")
        # The sealed ScanNet/ScanNet++ packet-builder convention stores axesLengths
        # as half-extents (grid_common._obb_corners); do not divide them again.
        return obb["centroid"] + (_BOX_SIGNS * obb["lengths"]) @ obb["axes"]

    def _scene_zbuffer(
        self, scene_id: str, frame_index: int, pose: np.ndarray,
        intrinsics: np.ndarray, height: int, width: int,
    ) -> np.ndarray:
        key = (scene_id, int(frame_index))
        with self._lock:
            cached = self._zbuffers.get(key)
            if cached is not None:
                self._zbuffers.move_to_end(key)
                return cached
        mesh = self._instance_mesh(scene_id)
        if mesh is None:
            scene_frame = self.geometry._frame(scene_id, frame_index)
            camera = (
                scene_frame["points"].astype(np.float64) - pose[:3, 3]
            ) @ pose[:3, :3]
            zbuffer = np.where(scene_frame["mask"], camera[:, :, 2], np.inf).astype(np.float32)
        else:
            u, v, depth = self._project(mesh["vertices"], pose, intrinsics)
            valid = (
                (depth > MIN_DEPTH_M) & (u >= 0) & (u < width)
                & (v >= 0) & (v < height)
            )
            zbuffer = np.full((height, width), np.inf, dtype=np.float32)
            if valid.any():
                np.minimum.at(
                    zbuffer,
                    (v[valid].astype(np.int32), u[valid].astype(np.int32)),
                    depth[valid].astype(np.float32),
                )
            # The authenticated meshes are vertex splats at canvas scale;
            # fill only small holes, matching the sealed packet-builder family.
            for _ in range(3):
                holes = ~np.isfinite(zbuffer)
                if not holes.any():
                    break
                zbuffer = np.where(holes, cv2.erode(zbuffer, np.ones((3, 3), np.uint8)), zbuffer)
        with self._lock:
            self._zbuffers[key] = zbuffer
            while len(self._zbuffers) > 40:
                self._zbuffers.popitem(last=False)
        return zbuffer

    def _render_instance(self, scene_id: str, frame_index: int, instance_id: int) -> dict[str, Any] | None:
        key = (scene_id, int(frame_index), int(instance_id))
        with self._lock:
            if key in self._masks:
                self._masks.move_to_end(key)
                cached = self._masks[key]
                if cached is None:
                    return None
                return {**cached, "mask": cached["mask"].copy()}
        pose, intrinsics, height, width = self._camera(scene_id, frame_index)
        mesh = self._instance_mesh(scene_id)
        if mesh is None:
            triangle_world = self._obb_corners(scene_id, instance_id)[_BOX_TRIANGLES]
        else:
            selected = instance_faces(mesh, int(instance_id))
            if len(selected) == 0:
                # The sealed instance channel is a closure over packet-mapped
                # instances.  A category outside that closure still gets a
                # GT OBB primitive rather than a question-conditioned miss.
                triangle_world = self._obb_corners(scene_id, instance_id)[_BOX_TRIANGLES]
            else:
                if len(selected) > _MAX_INSTANCE_FACES:
                    slots = np.linspace(0, len(selected) - 1, _MAX_INSTANCE_FACES).astype(np.int64)
                    selected = selected[slots]
                triangle_world = mesh["vertices"][mesh["faces"][selected]]
        flattened = triangle_world.reshape(-1, 3)
        u, v, depth = self._project(flattened, pose, intrinsics)
        u, v, depth = u.reshape(-1, 3), v.reshape(-1, 3), depth.reshape(-1, 3)
        object_depth = np.full((height, width), np.inf, dtype=np.float32)
        object_mask = np.zeros((height, width), dtype=bool)
        for tri_index in range(len(triangle_world)):
            if not (depth[tri_index] > MIN_DEPTH_M).all():
                continue
            points = np.stack([u[tri_index], v[tri_index]], axis=1)
            x0 = max(0, int(math.floor(float(points[:, 0].min()))))
            x1 = min(width, int(math.ceil(float(points[:, 0].max()))) + 1)
            y0 = max(0, int(math.floor(float(points[:, 1].min()))))
            y1 = min(height, int(math.ceil(float(points[:, 1].max()))) + 1)
            if x1 <= x0 or y1 <= y0:
                continue
            local = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
            polygon = np.rint(points - np.asarray([x0, y0])).astype(np.int32)
            cv2.fillConvexPoly(local, polygon, 1)
            selected = local.astype(bool)
            if not selected.any():
                continue
            # Perspective-correct camera-Z interpolation.  A triangle-mean
            # depth incorrectly rejects slanted instance faces at the GT
            # scene z-buffer and can erase otherwise visible instances.
            yy, xx = np.indices(selected.shape, dtype=np.float64)
            px, py = xx + x0 + 0.5, yy + y0 + 0.5
            x_a, y_a = points[0]
            x_b, y_b = points[1]
            x_c, y_c = points[2]
            denominator = (y_b - y_c) * (x_a - x_c) + (x_c - x_b) * (y_a - y_c)
            if abs(float(denominator)) < 1e-12:
                continue
            w_a = ((y_b - y_c) * (px - x_c) + (x_c - x_b) * (py - y_c)) / denominator
            w_b = ((y_c - y_a) * (px - x_c) + (x_a - x_c) * (py - y_c)) / denominator
            w_c = 1.0 - w_a - w_b
            reciprocal_depth = (
                w_a / depth[tri_index, 0]
                + w_b / depth[tri_index, 1]
                + w_c / depth[tri_index, 2]
            )
            tri_depth = np.where(reciprocal_depth > 0, 1.0 / reciprocal_depth, np.inf)
            region_depth = object_depth[y0:y1, x0:x1]
            take = selected & (tri_depth < region_depth)
            region_depth[take] = tri_depth[take]
            object_depth[y0:y1, x0:x1] = region_depth
            object_mask[y0:y1, x0:x1] |= selected
        if not object_mask.any():
            result = None
        else:
            scene_zbuffer = self._scene_zbuffer(
                scene_id, frame_index, pose, intrinsics, height, width)
            visible = object_mask & np.isfinite(scene_zbuffer) & (
                object_depth <= scene_zbuffer + OCCLUSION_TOLERANCE_M)
            if not visible.any():
                result = None
            else:
                ys, xs = np.where(visible)
                result = {
                    "area_norm": float(len(xs) / float(width * height)),
                    "bbox_pixels": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                    "frame_size": [width, height],
                    "mask": visible,
                    "mask_pixel_count": int(len(xs)),
                }
        with self._lock:
            stored = None if result is None else {**result, "mask": result["mask"].copy()}
            self._masks[key] = stored
            while len(self._masks) > self._cache_masks:
                self._masks.popitem(last=False)
        return result

    def visible_instances(self, scene_id: str, frame_index: int, object_label: str) -> list[dict[str, Any]]:
        instance_ids = self.match_instances(scene_id, object_label)
        if not instance_ids:
            raise UnmappedGroundingLabel(
                _canonical_label(object_label), self._inventory(scene_id)["labels_to_ids"])
        rows = []
        for instance_id in instance_ids:
            rendered = self._render_instance(scene_id, frame_index, instance_id)
            if rendered is not None:
                rows.append({"instance_id": instance_id, **rendered})
        return rows

    def visible_frames(self, scene_id: str, object_label: str) -> list[tuple[int, float]]:
        if not self.match_instances(scene_id, object_label):
            raise UnmappedGroundingLabel(
                _canonical_label(object_label), self._inventory(scene_id)["labels_to_ids"])
        visible = []
        for frame_index in range(1, 33):
            try:
                rows = self.visible_instances(scene_id, frame_index, object_label)
            except GTGroundingError as exc:
                if "dataset-official GT pose missing" in str(exc):
                    continue
                raise
            if rows:
                visible.append((frame_index, float(sum(row["area_norm"] for row in rows))))
        return visible

    def find_frames(self, scene_id: str, object_label: str, num_frames: str = "5") -> list[int]:
        visible = self.visible_frames(scene_id, object_label)
        frame_indices = [frame_index for frame_index, _ in visible]
        if not frame_indices:
            return []
        if str(num_frames) == "1":
            # first_and_last_visible_forced dominates the requested count
            # (REQ113_CONTRACT.json grounding_contract): both endpoints return
            # whenever they differ.
            return sorted({min(frame_indices), max(frame_indices)})
        if str(num_frames).lower() == "all":
            return sorted(frame_indices)
        try:
            count = max(1, int(num_frames))
        except (TypeError, ValueError):
            count = 5
        if len(frame_indices) <= count:
            return sorted(frame_indices)
        ranked = sorted(visible, key=lambda row: (-row[1], row[0]))
        selected = {frame_index for frame_index, _ in ranked[:count]}
        first, last = min(frame_indices), max(frame_indices)
        for forced in (first, last):
            if forced in selected:
                continue
            removable = [row for row in reversed(ranked) if row[0] in selected and row[0] not in {first, last}]
            if len(selected) >= count and removable:
                selected.remove(removable[0][0])
            selected.add(forced)
        return sorted(selected)

    def boxes(self, scene_id: str, frame_index: int, object_label: str) -> list[list[float]]:
        rows = self.visible_instances(scene_id, frame_index, object_label)
        boxes = []
        for row in rows:
            width, height = row["frame_size"]
            x0, y0, x1, y1 = row["bbox_pixels"]
            boxes.append([
                round(x0 / width, 3), round(y0 / height, 3),
                round(x1 / width, 3), round(y1 / height, 3),
            ])
        return boxes

    def points(self, scene_id: str, frame_index: int, object_label: str) -> list[dict[str, Any]]:
        rows = self.visible_instances(scene_id, frame_index, object_label)
        points = []
        labels = self._inventory(scene_id)["labels"]
        for row in rows:
            width, height = row["frame_size"]
            x0, y0, x1, y1 = row["bbox_pixels"]
            points.append({
                "instance_id": int(row["instance_id"]),
                "label": labels[int(row["instance_id"])],
                "pixel_norm": [
                    round((x0 + x1) / (2.0 * width), 4),
                    round((y0 + y1) / (2.0 * height), 4),
                ],
            })
        return points

    def segment_frame(self, scene_id: str, frame_index: int, object_label: str, mask_dir: Path) -> dict[str, Any]:
        output = _output_dir(mask_dir)
        rows = self.visible_instances(scene_id, frame_index, object_label)
        instances = []
        for row in rows:
            instance_id = int(row["instance_id"])
            path = output / f"gt_instance_{instance_id}.npy"
            if path.exists():
                existing = np.load(path, allow_pickle=False)
                if not np.array_equal(existing, row["mask"]):
                    raise GTGroundingError(f"immutable GT mask drift: {path}")
            else:
                with path.open("xb") as handle:
                    np.save(handle, row["mask"])
            width, height = row["frame_size"]
            x0, y0, x1, y1 = row["bbox_pixels"]
            instances.append({
                "area_norm": row["area_norm"],
                "bbox_norm": [x0 / width, y0 / height, x1 / width, y1 / height],
                "bbox_pixels": [x0, y0, x1, y1],
                "instance_id": instance_id,
                "mask_handle": str(path),
                "mask_pixel_count": row["mask_pixel_count"],
                "score": 1.0,
            })
        frame_size = list(rows[0]["frame_size"]) if rows else list(self._camera(scene_id, frame_index)[2:][::-1])
        return {
            "frame_size": frame_size,
            "instances": instances,
            "n_raw": len(instances),
            "score_thresh": 1.0,
        }

    def segment_video(self, scene_id: str, object_label: str, frame_indices: list[int], mask_dir: Path) -> dict[str, Any]:
        output = _output_dir(mask_dir)
        frames: dict[int, list[dict[str, Any]]] = {}
        frame_size = None
        for frame_index in [int(value) for value in frame_indices]:
            payload = self.segment_frame(
                scene_id, frame_index, object_label, output / f"frame_{frame_index:02d}")
            frames[frame_index] = payload["instances"]
            frame_size = payload["frame_size"]
        return {
            "_req113_primitives_only": True,
            "frame_size": frame_size or [0, 0],
            "frames": frames,
            "score_thresh": 1.0,
        }
