"""R0 scene ground truth, frame layout and frame-tied visibility (ScanNet++ iphone + laser-scan annotations).

World frame: the laser scan (mesh_aligned_0.05.ply), z up, metres. Cameras: pose_intrinsic_imu.json `aligned_pose`
(camera-to-world in the scan frame; the axis convention is resolved per scene against iphone/colmap/images.txt).
Frame index i of the decoded rgb.mkv is key frame_%06d in the pose file (60 fps, like the VSI-590K mp4 the student
trained on). Layout: indices = floor(linspace(0, total-1, n)), n in {32, 64} (the D0 rows' rule).
"""
import json, os
import numpy as np

STRUCT = {'wall', 'floor', 'ceiling', 'doorframe', 'window frame', 'remove', 'split', 'object', 'objects', 'unknown',
          'pipe', 'beam', 'pillar', 'column', 'stairs', 'staircase', 'ceiling light', 'ceiling lamp', 'light', 'cable',
          'wire', 'electrical duct', 'ceiling beam', 'ventilation', 'air duct', 'duct', 'rail', 'skirting board',
          'baseboard', 'power socket', 'socket', 'light switch', 'switch', 'reflection', 'mirror reflection', 'floor mat'}
VIS_RES = (160, 120)       # visibility raster (w, h): 1/12 of the 1920x1440 iphone frame, 1/4 of the 640x480 student frame
VIS_MIN_PX = 8             # an instance is visible in a frame with >= 8 raster pixels (~128 px at 640x480)


def layout(total, n):
    return [int(x) for x in np.floor(np.linspace(0, total - 1, n))]


def read_ply(path):
    """Binary little-endian PLY: returns vertices (N,3) float64 and faces (M,3) int64."""
    with open(path, 'rb') as f:
        hdr = []
        while True:
            line = f.readline().decode('ascii', 'replace').strip()
            hdr.append(line)
            if line == 'end_header':
                break
        assert 'format binary_little_endian 1.0' in hdr, hdr[:3]
        elems, cur = [], None
        tmap = {'float': 'f4', 'float32': 'f4', 'double': 'f8', 'uchar': 'u1', 'uint8': 'u1', 'char': 'i1', 'int8': 'i1',
                'short': 'i2', 'int16': 'i2', 'ushort': 'u2', 'uint16': 'u2', 'int': 'i4', 'int32': 'i4', 'uint': 'u4', 'uint32': 'u4'}
        for line in hdr:
            t = line.split()
            if t[:1] == ['element']:
                cur = dict(name=t[1], n=int(t[2]), props=[]); elems.append(cur)
            elif t[:1] == ['property']:
                cur['props'].append(('list', tmap[t[2]], tmap[t[3]], t[4]) if t[1] == 'list' else (t[2], tmap[t[1]]))
        V = F = None
        for e in elems:
            if e['name'] == 'vertex':
                dt = np.dtype([(p[0], '<' + p[1]) for p in e['props']])
                a = np.frombuffer(f.read(dt.itemsize * e['n']), dtype=dt, count=e['n'])
                V = np.stack([a['x'], a['y'], a['z']], 1).astype(np.float64)
            elif e['name'] == 'face':
                p = e['props'][0]
                assert p[0] == 'list' and len(e['props']) == 1
                dt = np.dtype([('c', '<' + p[1]), ('i', '<' + p[2], (3,))])
                a = np.frombuffer(f.read(dt.itemsize * e['n']), dtype=dt, count=e['n'])
                assert (a['c'] == 3).all()
                F = a['i'].astype(np.int64)
            else:
                raise ValueError('unexpected element ' + e['name'])
    return V, F


def norm_label(s):
    return ' '.join(s.lower().replace('_', ' ').split())


def load_scene(sdir):
    V, F = read_ply(os.path.join(sdir, 'scans', 'mesh_aligned_0.05.ply'))
    seg = np.asarray(json.load(open(os.path.join(sdir, 'scans', 'segments.json')))['segIndices'], dtype=np.int64)
    assert len(seg) == len(V), (len(seg), len(V))
    anno = json.load(open(os.path.join(sdir, 'scans', 'segments_anno.json')))
    seg2v = {}
    order = np.argsort(seg, kind='stable'); ss = seg[order]
    cut = np.flatnonzero(np.diff(ss)) + 1
    for grp in np.split(order, cut):
        seg2v[int(seg[grp[0]])] = grp
    inst = []
    vlab = np.full(len(V), -1, dtype=np.int64)
    for g in anno['segGroups']:
        idx = [seg2v[s] for s in g['segments'] if s in seg2v]
        if not idx:
            continue
        vi = np.unique(np.concatenate(idx))
        k = len(inst)
        inst.append(dict(id=int(g['id']), label=norm_label(g['label']), v=vi))
        vlab[vi] = k
    return dict(V=V, F=F, inst=inst, vlab=vlab)


def colmap_c2w(sdir):
    out = {}
    for line in open(os.path.join(sdir, 'iphone', 'colmap', 'images.txt')):
        t = line.split()
        if len(t) == 10 and t[9].endswith('.jpg') and not line.startswith('#'):
            qw, qx, qy, qz, tx, ty, tz = map(float, t[1:8])
            R = np.array([[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
                          [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
                          [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]])
            M = np.eye(4); M[:3, :3] = R.T; M[:3, 3] = -R.T @ np.array([tx, ty, tz])
            out[int(t[9][6:12])] = M
    return out


GL2CV = np.diag([1.0, -1.0, -1.0, 1.0])


def load_cameras(sdir):
    """Returns (total_frames, {frame: (c2w_opencv 4x4, K 3x3)}, convention record)."""
    P = json.load(open(os.path.join(sdir, 'iphone', 'pose_intrinsic_imu.json')))
    keys = sorted(P)
    assert keys[0] == 'frame_000000' and keys[-1] == 'frame_%06d' % (len(keys) - 1), (keys[0], keys[-1], len(keys))
    cm = colmap_c2w(sdir)
    common = [i for i in sorted(cm) if i < len(keys)][:200]
    err = {}
    for name, flip in (('opencv', np.eye(4)), ('opengl', GL2CV)):
        e = [np.abs(np.asarray(P['frame_%06d' % i]['aligned_pose']) @ flip - cm[i])[:3].max() for i in common]
        err[name] = float(np.median(e))
    conv = min(err, key=err.get)
    assert np.isfinite(err[conv]) and err[conv] < 0.05, ('aligned_pose disagrees with colmap', err)
    flip = np.eye(4) if conv == 'opencv' else GL2CV
    cams = {i: (np.asarray(P['frame_%06d' % i]['aligned_pose'], dtype=np.float64) @ flip,
                np.asarray(P['frame_%06d' % i]['intrinsic'], dtype=np.float64)) for i in range(len(keys))}
    return len(keys), cams, dict(convention=conv, median_abs_err_vs_colmap=err, colmap_frames_compared=len(common))


def render_ids(V, vlab, c2w, K, src_wh=(1920, 1440), res=VIS_RES, spacing=0.05):
    """Point-splat z-buffer of mesh vertices; returns (h, w) int array of instance index (-1 none / unlabeled)."""
    w, h = res
    s = w / src_wh[0]
    w2c = np.linalg.inv(c2w)
    Pc = V @ w2c[:3, :3].T + w2c[:3, 3]
    z = Pc[:, 2]
    ok = z > 0.05
    Pc, z, lab = Pc[ok], z[ok], vlab[ok]
    u = (K[0, 0] * Pc[:, 0] / z + K[0, 2]) * s
    v = (K[1, 1] * Pc[:, 1] / z + K[1, 2]) * s
    rad = np.clip(np.ceil(K[0, 0] * s * spacing / z / 2).astype(int), 0, 4)
    zb = np.full(h * w, np.inf); ib = np.full(h * w, -1, dtype=np.int64)
    for r in range(int(rad.max()) + 1 if len(rad) else 0):
        sel = rad >= r
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                uu = np.floor(u[sel]).astype(int) + dx; vv = np.floor(v[sel]).astype(int) + dy
                m = (uu >= 0) & (uu < w) & (vv >= 0) & (vv < h)
                pix = vv[m] * w + uu[m]; zz = z[sel][m]; ll = lab[sel][m]
                o = np.lexsort((zz, pix))
                pix, zz, ll = pix[o], zz[o], ll[o]
                first = np.ones(len(pix), bool); first[1:] = pix[1:] != pix[:-1]
                pix, zz, ll = pix[first], zz[first], ll[first]
                better = zz < zb[pix]
                zb[pix[better]] = zz[better]; ib[pix[better]] = ll[better]
    return ib.reshape(h, w)


def visible_counts(scene, cams, frames):
    """{frame: {instance index: raster pixel count}} for the given frame indices."""
    out = {}
    for fi in frames:
        c2w, K = cams[fi]
        ids = render_ids(scene['V'], scene['vlab'], c2w, K)
        u, c = np.unique(ids[ids >= 0], return_counts=True)
        out[fi] = {int(a): int(b) for a, b in zip(u, c)}
    return out
