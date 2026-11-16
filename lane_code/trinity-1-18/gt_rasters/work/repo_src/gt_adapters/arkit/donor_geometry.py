from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any
import numpy as np
from scipy.ndimage import minimum_filter

MIN_DEPTH_M = 0.05

_PLY_DTYPES = {
    "float": "<f4", "float32": "<f4", "float64": "<f8", "double": "<f8",
    "int": "<i4", "int32": "<i4", "uint": "<u4", "uint32": "<u4",
    "short": "<i2", "ushort": "<u2", "uchar": "u1", "char": "i1",
}


class GTProviderError(RuntimeError):
    """A pinned r804 GT-geometry invariant was violated."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_file(spec: dict[str, Any], label: str) -> Path:
    path = Path(spec["path"])
    if not path.is_file() or path.is_symlink() or path.stat().st_size != int(spec["bytes"]):
        raise GTProviderError(f"missing or size-drifted {label}: {path}")
    if sha256_file(path) != spec["sha256"]:
        raise GTProviderError(f"SHA-256 drift in {label}: {path}")
    return path


def _load_vertices(path: Path) -> np.ndarray:
    with path.open("rb") as handle:
        count = None
        props: list[tuple[str, str]] = []
        in_vertices = False
        while True:
            raw = handle.readline()
            if not raw:
                raise GTProviderError(f"unterminated PLY header: {path}")
            line = raw.decode("ascii", errors="strict").strip()
            if line == "end_header":
                break
            if line.startswith("format ") and line != "format binary_little_endian 1.0":
                raise GTProviderError(f"unsupported PLY format: {path}: {line}")
            if line.startswith("element vertex "):
                count = int(line.split()[-1])
                in_vertices = True
            elif line.startswith("element "):
                in_vertices = False
            elif in_vertices and line.startswith("property "):
                fields = line.split()
                if len(fields) == 3 and fields[1] != "list":
                    if fields[1] not in _PLY_DTYPES:
                        raise GTProviderError(f"unsupported PLY property: {fields[1]}")
                    props.append((fields[2], _PLY_DTYPES[fields[1]]))
        if count is None or not props:
            raise GTProviderError(f"invalid PLY vertex header: {path}")
        dtype = np.dtype(props)
        rows = np.frombuffer(handle.read(dtype.itemsize * count), dtype=dtype)
    if len(rows) != count or any(axis not in rows.dtype.names for axis in ("x", "y", "z")):
        raise GTProviderError(f"invalid PLY vertex payload: {path}")
    points = np.stack([rows["x"], rows["y"], rows["z"]], axis=1).astype(np.float32)
    if not np.isfinite(points).all():
        raise GTProviderError(f"non-finite mesh vertices: {path}")
    return points


class Renderer:
    @staticmethod
    def _pose(frame: dict[str, Any]) -> np.ndarray:
        rotation = np.load(frame["pose_R"]["path"]).astype(np.float64).reshape(3, 3)
        translation = np.load(frame["pose_t"]["path"]).astype(np.float64).reshape(3)
        if not np.isfinite(rotation).all() or not np.isfinite(translation).all():
            raise GTProviderError("non-finite GT pose")
        if np.max(np.abs(rotation.T @ rotation - np.eye(3))) > 1e-3:
            raise GTProviderError("non-orthonormal GT pose")
        if abs(np.linalg.det(rotation) - 1.0) > 1e-3:
            raise GTProviderError("improper GT pose")
        pose = np.eye(4, dtype=np.float64)
        pose[:3, :3], pose[:3, 3] = rotation, translation
        return pose

    @staticmethod
    def _render(vertices: np.ndarray, pose: np.ndarray, intrinsics: np.ndarray,
                height: int, width: int) -> tuple[np.ndarray, np.ndarray]:
        rotation, translation = pose[:3, :3], pose[:3, 3]
        camera = (vertices.astype(np.float64) - translation) @ rotation
        depth = camera[:, 2]
        keep = np.isfinite(depth) & (depth > MIN_DEPTH_M)
        camera, depth = camera[keep], depth[keep]
        u = intrinsics[0, 0] * camera[:, 0] / depth + intrinsics[0, 2]
        v = intrinsics[1, 1] * camera[:, 1] / depth + intrinsics[1, 2]
        keep = (u >= 0) & (u < width) & (v >= 0) & (v < height)
        x, y, z = u[keep].astype(np.int32), v[keep].astype(np.int32), depth[keep].astype(np.float32)
        rendered = np.full((height, width), np.inf, dtype=np.float32)
        np.minimum.at(rendered, (y, x), z)
        for _ in range(3):
            holes = ~np.isfinite(rendered)
            rendered = np.where(holes, minimum_filter(rendered, size=3), rendered)
        mask = np.isfinite(rendered)
        return np.where(mask, rendered, 0).astype(np.float32), mask

