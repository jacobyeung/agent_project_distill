"""VARIANT r180 of build_arkit_cr.py (gt_build lane): also rotates upside-down landscape captures 180 deg.
Clean-room ARKit raster rebuild: raw ARKitScenes 3dod capture -> dose_pool arkit_gt npz.

Rules fitted on 41069053 and 42899922 (see GT_RASTER_REBUILD_SCOPE.md):
frames = timestamp-sorted lowres_depth at the stored 32 indices; pose = inverse of the
nearest lowres_wide.traj row; a frame whose nearest pose is more than 0.5 ms away is
written as missing (depth 0, inst -1, pose kept); depth = PNG mm / 1000 at 256x192,
nearest-resized to 320x240 with index floor(i * 0.8); K = pincam x 1.25; inst = smallest
annotated obbAligned box (+0.03 m on every side) containing the lifted source pixel
(pixel centre +0.5), with points below (2nd percentile of all lifted z) + 0.05 m set to -1.
Portrait captures (sensor x axis along gravity in the 32 poses) are rotated 90 deg so image +y
points down: source PNG rotated before the resize, K swapped, c2w right-multiplied by ROT.
"""
import ctypes
ctypes.CDLL(None).prctl(41, 1, 0, 0, 0)  # PR_SET_THP_DISABLE: THP compaction stalls on this node
import glob, hashlib, json, os, sys
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

LABEL_MAP = {'tv_monitor': 'tv'}
SH, SW = 192, 256
ROT = {-1: np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.]]),
       1: np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.]]),
       2: np.diag([-1., -1., 1., 1.])}  # VARIANT r180: upside-down landscape


def ts(s):
    return float(os.path.basename(s).split('_')[1].rsplit('.', 1)[0])


def build(cid, src, frame_indices, out_path, pose_dt=0.0005, margin=0.03, floor_pct=2.0, floor_off=0.05,
          pose64=False):
    listing = f'{src}/../depth_list.txt'  # full directory listing when src holds only the 32 selected frames
    names = open(listing).read().split() if os.path.exists(listing) else [os.path.basename(x) for x in glob.glob(f'{src}/{cid}_frames/lowres_depth/*.png')]
    ds = [f'{src}/{cid}_frames/lowres_depth/{n}' for n in sorted(names, key=ts)]
    pc = {round(ts(p), 3): p for p in glob.glob(f'{src}/{cid}_frames/lowres_wide_intrinsics/*.pincam')}
    rows = np.loadtxt(f'{src}/{cid}_frames/lowres_wide.traj')
    ann = json.load(open(f'{src}/{cid}_3dod_annotation.json'))['data']
    box = [o['segments']['obbAligned'] for o in ann]
    cen = np.array([b['centroid'] for b in box]); L = np.array([b['axesLengths'] for b in box])
    A = np.array([b['normalizedAxes'] for b in box], float).reshape(-1, 3, 3)
    vol = np.prod(L, 1)
    poses, near = [], []
    for idx in frame_indices:
        t = ts(ds[idx]); i = int(np.argmin(np.abs(rows[:, 0] - t)))
        w2c = np.eye(4); w2c[:3, :3] = Rotation.from_rotvec(rows[i, 1:4]).as_matrix(); w2c[:3, 3] = rows[i, 4:7]
        poses.append(np.linalg.inv(w2c)); near.append(abs(rows[i, 0] - t) <= pose_dt)
    xz = np.mean([q[2, 0] for q in poses]); yz = np.mean([q[2, 1] for q in poses])
    rot = (2 if yz > 0 else 0) if abs(yz) >= abs(xz) else (-1 if xz < 0 else 1)   # VARIANT r180: image +y up -> rotate 180
    SHr, SWr = (SW, SH) if rot in (-1, 1) else (SH, SW)
    H, W = (320, 240) if rot in (-1, 1) else (240, 320)
    yi = np.floor(np.arange(H) * SHr / H).astype(int); xi = np.floor(np.arange(W) * SWr / W).astype(int)
    c2w = np.zeros((32, 4, 4), np.float32); Kf = np.zeros((32, 3, 3)); depth = np.zeros((32, H, W), np.float32)
    pts, missing = [], []
    for f, idx in enumerate(frame_indices):
        p = ds[idx]; t = ts(p)
        pose = poses[f] @ ROT[rot] if rot else poses[f]
        c2w[f] = pose.astype(np.float32)
        _, _, fx, fy, cx, cy = np.loadtxt(pc[round(t, 3)])
        if rot == -1: fx, fy, cx, cy = fy, fx, SH - cy, cx
        elif rot == 1: fx, fy, cx, cy = fy, fx, cy, SW - cx
        elif rot == 2: cx, cy = SW - cx, SH - cy
        Kf[f] = np.diag([W / SWr, H / SHr, 1]) @ np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        if not near[f]:
            missing.append(f); pts.append(None); continue
        png = np.array(Image.open(p))
        if rot: png = np.rot90(png, rot)
        depth[f] = (png[np.ix_(yi, xi)] / 1000.0).astype(np.float32)
        d = png.astype(np.float64) / 1000.0
        v, u = np.mgrid[0:SHr, 0:SWr].astype(np.float64)
        M = pose if pose64 else c2w[f].astype(np.float64)
        P = (np.stack([(u + .5 - cx) / fx * d, (v + .5 - cy) / fy * d, d, np.ones_like(d)], -1).reshape(-1, 4) @ M.T)[:, :3]
        pts.append((P, d.reshape(-1) > 0))
    cut = np.percentile(np.concatenate([P[ok, 2] for x in pts if x is not None for P, ok in [x]]), floor_pct) + floor_off
    inst = np.full((32, H, W), -1, np.int32)
    for f, x in enumerate(pts):
        if x is None: continue
        P, ok = x
        out = np.full(len(P), -1, np.int32)
        for k in np.argsort(vol)[::-1]:
            out[(np.abs((P - cen[k]) @ A[k].T) <= L[k] / 2 + margin).all(1)] = k
        out[P[:, 2] < cut] = -1; out[~ok] = -1
        inst[f] = out.reshape(SHr, SWr)[np.ix_(yi, xi)]
    ids = np.arange(len(ann), dtype=np.int32)
    with open(out_path, 'xb') as fh:
        np.savez_compressed(fh, depth=depth, inst=inst, K=Kf[0], K_frames=Kf, c2w=c2w, valid=np.ones(32, dtype=bool),
                            ids=ids, labels=np.array([LABEL_MAP.get(o['label'], o['label']) for o in ann]),
                            obb_centroid=cen, obb_lengths=L, obb_axes=A.reshape(-1, 9),
                            frame_indices=np.asarray(frame_indices, np.int64))
    return hashlib.sha256(open(out_path, 'rb').read()).hexdigest(), missing, rot


if __name__ == '__main__':
    cid, src, out = sys.argv[1:4]
    fi = json.loads(sys.argv[4])
    print(*build(cid, src, fi, out, pose64=len(sys.argv) > 5))
