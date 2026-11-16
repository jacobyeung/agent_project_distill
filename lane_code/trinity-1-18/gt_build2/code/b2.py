"""gt_build2 parametric variant of build_arkit_cr_r180.py; options in env B2OPT (JSON): dt=le|us, floor=global|A|B|C, band, pose64, f32.
VARIANT r180 of build_arkit_cr.py (gt_build lane): also rotates upside-down landscape captures 180 deg.
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

OPT = json.loads(os.environ.get('B2OPT', '{}'))
LABEL_MAP = {'tv_monitor': 'tv'}
SH, SW = 192, 256
ROT = {-1: np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.]]),
       1: np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.]]),
       2: np.diag([-1., -1., 1., 1.])}  # VARIANT r180: upside-down landscape


def ts(s):
    return float(os.path.basename(s).split('_')[1].rsplit('.', 1)[0])


def lift(d, K, M):
    fx, fy, cx, cy = K
    if OPT.get('f32'): d = d.astype(np.float32).astype(np.float64)
    v, u = np.mgrid[0:d.shape[0], 0:d.shape[1]].astype(np.float64)
    ray = OPT.get('ray', 'div'); xf = OPT.get('xf', 'hom')
    if ray == 'div': X, Y = (u + .5 - cx) / fx * d, (v + .5 - cy) / fy * d
    elif ray == 'mulfirst': X, Y = (u + .5 - cx) * d / fx, (v + .5 - cy) * d / fy
    else:
        Ki = np.linalg.inv(np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1.]]))
        c = np.stack([u + .5, v + .5, np.ones_like(u)], -1) @ Ki.T * d[..., None]; X, Y = c[..., 0], c[..., 1]
    if xf == 'hom': return (np.stack([X, Y, d, np.ones_like(d)], -1).reshape(-1, 4) @ M.T)[:, :3]
    if xf == 'rt': return np.stack([X, Y, d], -1).reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    if xf == 'f32h': return (np.stack([X, Y, d, np.ones_like(d)], -1).reshape(-1, 4).astype(np.float32) @ M.astype(np.float32).T)[:, :3].astype(np.float64)
    if xf == 'ein': return np.einsum('ij,nj->ni', M[:3, :3], np.stack([X, Y, d], -1).reshape(-1, 3)) + M[:3, 3]


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
        poses.append(np.linalg.inv(w2c) if OPT.get('inv', 'linalg') == 'linalg' else np.block([[w2c[:3, :3].T, -(w2c[:3, :3].T @ w2c[:3, 3])[:, None]], [np.zeros((1, 3)), np.ones((1, 1))]])); near.append(abs(rows[i, 0] - t) <= pose_dt if OPT.get('dt', 'le') == 'le' else round(abs(rows[i, 0] - t) * 1e6) <= 500)
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
        _, _, fx, fy, cx, cy = np.loadtxt(pc[round(t, 3)]); K0 = (fx, fy, cx, cy)
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
        if rot and OPT.get('prerot'):
            P = lift(np.array(Image.open(p)).astype(np.float64) / 1000.0, K0, poses[f] if pose64 else poses[f].astype(np.float32).astype(np.float64))
            P = np.rot90(P.reshape(SH, SW, 3), rot).reshape(-1, 3)
        else:
            P = lift(d, (fx, fy, cx, cy), M)
        pts.append((P, d.reshape(-1) > 0))
    cut = np.percentile(np.concatenate([P[ok, 2] for x in pts if x is not None for P, ok in [x]]), floor_pct, method=OPT.get('pct', 'linear')) + floor_off
    if OPT.get('dump'):
        np.save(OPT['dump'] + '_dbg.npy', dict(pts=pts, cut=cut, cen=cen, L=L, A=A, vol=vol, rot=rot, yi=yi, xi=xi, SHr=SHr, SWr=SWr), allow_pickle=True)
    o = OPT.get('order', 'vol')
    ORDER = {'vol': lambda: np.argsort(vol)[::-1], 'volm': lambda: np.argsort(np.prod(L + 2 * margin, 1))[::-1],
             'stable': lambda: np.argsort(-vol, kind='stable'), 'rstable': lambda: np.argsort(vol, kind='stable')[::-1],
             'maxlen': lambda: np.argsort(L.max(1))[::-1], 'sum': lambda: np.argsort(L.sum(1))[::-1]}[o]()
    inst = np.full((32, H, W), -1, np.int32)
    for f, x in enumerate(pts):
        if x is None: continue
        P, ok = x
        out = np.full(len(P), -1, np.int32)
        fl = OPT.get('floor', 'global'); ex = (cen[:, 2] - L[:, 2] / 2) >= cut
        below = P[:, 2] <= cut if OPT.get('le') else P[:, 2] < cut
        if 'nex' in OPT: ex[OPT['nex']] = False
        if OPT.get('band'): below &= P[:, 2] >= cut - 2 * floor_off
        inex = np.zeros(len(P), bool)
        for k in ORDER:
            m = (np.abs((P - cen[k]) @ A[k].T) <= L[k] / 2 + margin).all(1)
            if ex[k]: inex |= m
            if fl == 'A' and not ex[k]: m &= ~below
            out[m] = k
        if fl == 'global': out[below] = -1
        elif fl == 'B': out[below & (out >= 0) & ~ex[np.maximum(out, 0)]] = -1
        elif fl == 'C': out[below & ~inex] = -1
        out[~ok] = -1
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
    print(*build(cid, src, fi, out, pose64=bool(OPT.get('pose64'))))
