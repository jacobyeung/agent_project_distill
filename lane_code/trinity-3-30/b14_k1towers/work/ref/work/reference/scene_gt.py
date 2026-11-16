"""Per-scene ScanNet GT: 32-frame poses and instance rasters (toolprog npz), objects.json boxes, and minimal oriented
boxes of each instance's mesh vertices (the VLM-3R box rule), cached under out/mobb/."""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, '/scratch/jjyeung/orch_cd/gt_ceiling/work/gl')
import common as C  # noqa: E402

RAW = '/scratch/jjyeung/orch_cd/toolprog/data/scannet_gt/raw'
MOBB = f'{C.W}/out/mobb'


def box_corners(b):
    h = np.asarray(b['axesLengths'], float) / 2
    R = np.asarray(b['normalizedAxes'], float).reshape(3, 3)
    s = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float) * h
    return s @ R + np.asarray(b['centroid'], float)


def min_rect(xy):
    """Minimum-area rectangle of 2D points: (area, angle, lo, hi)."""
    from scipy.spatial import ConvexHull
    try:
        h = xy[ConvexHull(xy).vertices]
    except Exception:
        h = xy
    best = None
    for i in range(len(h)):
        e = h[(i + 1) % len(h)] - h[i]
        if np.hypot(*e) < 1e-9:
            continue
        a = math.atan2(e[1], e[0])
        R2 = np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]])
        q = xy @ R2.T
        lo, hi = q.min(0), q.max(0)
        ar = float(np.prod(hi - lo))
        if best is None or ar < best[0]:
            best = (ar, a, lo, hi)
    return best


def minimal_obb(P):
    """Minimal-volume oriented box with one face flush to a convex-hull face (standard approximation of
    Open3D get_minimal_oriented_bounding_box). Returns the meta_info box format."""
    from scipy.spatial import ConvexHull
    P = np.asarray(P, float)
    if len(P) < 5:
        lo, hi = P.min(0), P.max(0)
        return {'centroid': ((lo + hi) / 2).tolist(), 'axesLengths': np.maximum(hi - lo, 1e-3).tolist(), 'normalizedAxes': np.eye(3).ravel().tolist()}
    try:
        hull = ConvexHull(P)
        H = P[hull.vertices]
        normals = np.unique(np.round(hull.equations[:, :3], 6), axis=0)
    except Exception:
        H, normals = P, np.eye(3)
    best = None
    for n in normals:
        n = n / np.linalg.norm(n)
        u = np.cross(n, [1, 0, 0] if abs(n[0]) < 0.9 else [0, 1, 0]); u /= np.linalg.norm(u)
        v = np.cross(n, u)
        r = min_rect(np.stack([H @ u, H @ v], 1))
        if r is None:
            continue
        ar, a, lo, hi = r
        hn = H @ n
        vol = ar * (hn.max() - hn.min())
        if best is None or vol < best[0]:
            e1 = math.cos(a) * u + math.sin(a) * v
            e2 = -math.sin(a) * u + math.cos(a) * v
            c2 = (lo + hi) / 2
            centre = c2[0] * e1 + c2[1] * e2 + (hn.max() + hn.min()) / 2 * n
            best = (vol, {'centroid': centre.tolist(), 'axesLengths': [float(hi[0] - lo[0]), float(hi[1] - lo[1]), float(hn.max() - hn.min())],
                          'normalizedAxes': np.stack([e1, e2, n]).ravel().tolist()})
    return best[1]


def read_ply_xyz(path):
    with open(path, 'rb') as fh:
        nv, props, cur = 0, [], None
        while True:
            line = fh.readline().decode('ascii').strip()
            p = line.split()
            if p[:2] == ['element', 'vertex']:
                nv, cur = int(p[2]), 'v'
            elif p[:1] == ['element']:
                cur = 'o'
            elif p[:1] == ['property'] and cur == 'v':
                props.append((p[2], {'float': 'f4', 'uchar': 'u1', 'int': 'i4', 'double': 'f8', 'ushort': 'u2'}[p[1]]))
            if line == 'end_header':
                break
        dt = np.dtype([(n, '<' + t) for n, t in props])
        v = np.frombuffer(fh.read(nv * dt.itemsize), dtype=dt, count=nv)
    return np.stack([v['x'], v['y'], v['z']], 1).astype(np.float64)


def instance_vertices(scene):
    xyz = read_ply_xyz(f'{RAW}/{scene}/{scene}_vh_clean_2.ply')
    seg = np.asarray(json.load(open(f'{RAW}/{scene}/{scene}_vh_clean_2.0.010000.segs.json'))['segIndices'])
    agg = json.load(open(f'{RAW}/{scene}/{scene}.aggregation.json'))['segGroups']
    out = {}
    for g in agg:
        m = np.isin(seg, g['segments'])
        out[int(g.get('objectId', g['id']))] = xyz[m]
    return out


def mobb_for_scene(scene):
    os.makedirs(MOBB, exist_ok=True)
    p = f'{MOBB}/{scene}.json'
    if os.path.exists(p):
        return {int(k): v for k, v in json.load(open(p)).items()}
    out = {i: minimal_obb(P) for i, P in instance_vertices(scene).items() if len(P)}
    json.dump(out, open(p, 'w'))
    return out


class SceneGT:
    def __init__(self, scene):
        z = np.load(C.GTNPZ % scene)
        self.scene = scene
        self.inst, self.c2w, self.valid = z['inst'], z['c2w'], z['valid']
        self.ids = [int(i) for i in z['ids']]
        self.labels = [str(x) for x in z['labels']]
        self.npzbox = {i: {'centroid': c, 'axesLengths': l, 'normalizedAxes': a}
                       for i, c, l, a in zip(self.ids, z['obb_centroid'], z['obb_lengths'], z['obb_axes'])}
        self.lab_of = dict(zip(self.ids, self.labels))
        self._mobb = None
        self._vis = {}

    def ids_for(self, name):
        labs = set(C.T.match_labels(name, sorted(set(self.labels))))
        return [i for i in self.ids if self.lab_of[i] in labs]

    def visible(self, k, minpx=1):
        if (k, minpx) not in self._vis:
            u, n = np.unique(self.inst[k], return_counts=True)
            self._vis[(k, minpx)] = {int(a): int(b) for a, b in zip(u, n) if a >= 0 and b >= minpx}
        return self._vis[(k, minpx)]

    def box(self, i, src='npz'):
        if src == 'npz':
            return self.npzbox[i]
        if self._mobb is None:
            self._mobb = mobb_for_scene(self.scene)
        return self._mobb.get(i, self.npzbox[i])
