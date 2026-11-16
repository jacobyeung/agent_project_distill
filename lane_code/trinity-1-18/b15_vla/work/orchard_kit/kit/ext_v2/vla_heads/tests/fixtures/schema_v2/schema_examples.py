#!/usr/bin/env python3
"""Worked examples of VLA_SCHEMA.md (vla_schema_v2), recomputed from deterministic inputs.

Pure numpy plus the standard library (hashlib, json, math). Run:  python3 schema_examples.py
It prints every example's inputs and outputs and asserts the values the schema states, within the
schema's tolerances (T-1: 1e-6 on vectors; text byte for byte). Lanes import the input generators
(`scene_inputs`, `fast_fixture_chunks`, `floor_depth_g3t`) so that their conformance tests read
exactly these arrays.

Conventions (schema 0): OpenCV camera axes; continuous pixels (column i covers [i, i+1), centre
i + 0.5); depth is optical-axis z; T_a_b maps points in frame b to frame a; erosion and dilation by
k px use a 3 x 3 square element applied k times with zero border; np.median, np.percentile
(linear interpolation) and SVD principal axes.
"""
import hashlib
import json
import math

import numpy as np

SCHEMA = 'vla_schema_v2'
TOL = 1e-6           # T-1 tolerance on record vectors
S_TRUE = 2.0         # metres per G3T unit in the synthetic G3T stub
W = H = 256          # LIBERO raster
# LIBERO dataset orientation (raw[::-1, ::-1] of the MuJoCo render) mirrors the view left-right, so the true OpenCV
# camera frame projects with fx < 0. G3T sees an ordinary image and reconstructs the mirrored scene with fx > 0;
# MIRROR maps G3T camera-frame points to the true OpenCV camera frame.
K_TRUE = np.array([[-128.0, 0.0, 128.0], [0.0, 128.0, 128.0], [0.0, 0.0, 1.0]])
K_G3T = np.array([[128.0, 0.0, 128.0], [0.0, 128.0, 128.0], [0.0, 0.0, 1.0]])
MIRROR = np.diag([-1.0, 1.0, 1.0])
TAU = 0.80
INSTRUCTION = 'pick up the black bowl between the plate and the ramekin and place it on the plate'
PHRASES = {0: ('black bowl between the plate and the ramekin', 'black bowl'), 1: ('plate', 'plate')}
R_HE, T_HE = np.eye(3), np.array([0.0, 0.0, -0.10])
GRIP = (0.039, -0.039)
AA = (3.141593, 0.0, 0.0)
P_EEF = {s: (0.40, 0.00, 1.30) for s in range(0, 25)}
P_EEF.update({32: (0.45, 0.00, 1.25), 40: (0.50, 0.00, 1.20)})
TABLE_Z = 0.90
# Axis-aligned boxes [xmin, xmax, ymin, ymax, zmin, zmax] in the base frame (x forward, y left, z up).
BOXES = {1: ('bowl (target)', (0.53, 0.67, -0.165, -0.035, 0.90, 0.95)),
         2: ('plate (place)', (0.61, 0.79, 0.015, 0.185, 0.90, 0.92)),
         3: ('bowl (distractor)', (0.38, 0.52, 0.135, 0.265, 0.90, 0.95))}
AGENT_C = np.array([1.40, 0.00, 1.20])
AGENT_R = np.column_stack(([0.0, 1.0, 0.0], [0.0, 0.0, -1.0], [-1.0, 0.0, 0.0]))  # columns x_A, y_A, z_A (world)
SAM3_SCORES = {1: 0.91, 2: 0.95, 3: 0.88}
TOP_CENTRES = {oid: np.array([(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, b[5]]) for oid, (_, b) in BOXES.items()}
NOUN_IDS = {'black bowl': (1, 3), 'plate': (2,)}


# ----------------------------------------------------------------------------------------- math
def rodrigues(aa):
    aa = np.asarray(aa, dtype=np.float64)
    th = float(np.linalg.norm(aa))
    if th < 1e-12:
        return np.eye(3)
    k = aa / th
    Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * Kx + (1 - math.cos(th)) * Kx @ Kx


def rigid(R, t):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, t
    return T


def inv(T):
    R, t = T[:3, :3], T[:3, 3]
    return rigid(R.T, -R.T @ t)


def apply(T, X):
    return T[:3, :3] @ np.asarray(X, dtype=np.float64) + T[:3, 3]


def proprio(step):
    return np.array(list(P_EEF[step]) + list(AA) + list(GRIP), dtype=np.float64)


def wrist_pose(step):
    """T_base<-wrist = T_base<-eef T_eef<-wrist (camera axes OpenCV)."""
    p = proprio(step)
    return rigid(rodrigues(p[3:6]), p[0:3]) @ rigid(R_HE, T_HE)


def centre(step):
    p = proprio(step)
    return p[0:3] + rodrigues(p[3:6]) @ T_HE


def erode(mask, k):
    m = np.asarray(mask, dtype=bool)
    for _ in range(k):
        p = np.pad(m, 1, constant_values=False)
        out = np.ones_like(m)
        for dr in (0, 1, 2):
            for dc in (0, 1, 2):
                out &= p[dr:dr + m.shape[0], dc:dc + m.shape[1]]
        m = out
    return m


def dilate(mask, k):
    m = np.asarray(mask, dtype=bool)
    for _ in range(k):
        p = np.pad(m, 1, constant_values=False)
        out = np.zeros_like(m)
        for dr in (0, 1, 2):
            for dc in (0, 1, 2):
                out |= p[dr:dr + m.shape[0], dc:dc + m.shape[1]]
        m = out
    return m


# ------------------------------------------------------------------------------------ rendering
def render(T_world_cam, K=K_TRUE, h=H, w=W):
    """Ray-cast the boxes and the table plane z = TABLE_Z: optical-axis depth [h, w] (nan = no hit) and ids
    (0 = table, -1 = nothing)."""
    rows, cols = np.mgrid[0:h, 0:w]
    d_cam = np.stack([((cols + 0.5) - K[0, 2]) / K[0, 0], ((rows + 0.5) - K[1, 2]) / K[1, 1],
                      np.ones((h, w))], -1)                       # z = 1, so ray parameter = depth
    R, o = T_world_cam[:3, :3], T_world_cam[:3, 3]
    d = d_cam @ R.T
    depth = np.full((h, w), np.inf)
    ids = np.full((h, w), -1, dtype=np.int64)
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (TABLE_Z - o[2]) / d[..., 2]
    hit = (d[..., 2] < 0) & (t > 0)
    depth[hit], ids[hit] = t[hit], 0
    for oid, (_, b) in sorted(BOXES.items()):
        lo, hi = np.array(b[0::2]), np.array(b[1::2])
        with np.errstate(divide='ignore', invalid='ignore'):
            t1, t2 = (lo - o) / d, (hi - o) / d
        tn = np.nanmax(np.minimum(t1, t2), -1)
        tf = np.nanmin(np.maximum(t1, t2), -1)
        box_hit = (tn <= tf) & (tf > 0) & (tn > 0) & (tn < depth)
        depth[box_hit], ids[box_hit] = tn[box_hit], oid
    depth[~np.isfinite(depth)] = np.nan
    return depth, ids


def confidence(h=H, w=W):
    rows, cols = np.mgrid[0:h, 0:w]
    return 1.0 + ((7 * rows + 13 * cols) % 17) / 16.0


def scene_inputs(t):
    """Stub perception for examples 1-3 at step t: views [wrist_t, agent_t, wrist history newest first],
    each with T_view0<-view (G3T units), K, and for wrist_t and agent_t the G3T depth (metres / S_TRUE),
    confidence and the SAM 3 proposals {noun: [(mask, score, object id)]}."""
    hist = []
    for off in (8, 16, 32):
        h = max(t - off, 0)
        if h != t and h not in hist:
            hist.append(h)
    poses = [('wrist', t, wrist_pose(t)), ('agent', t, rigid(AGENT_R, AGENT_C))]
    poses += [('wrist', h, wrist_pose(h)) for h in hist]
    T0w = inv(poses[0][2])
    views = []
    for i, (role, step, Twc) in enumerate(poses):
        rel = T0w @ Twc                                          # metric T_view0<-view, true frames
        Tg = rigid(MIRROR @ rel[:3, :3] @ MIRROR, MIRROR @ rel[:3, 3] / S_TRUE)   # G3T: mirrored frames, G3T units
        v = dict(role=role, step=step, T0=Tg, K=K_G3T.copy(), T_world_cam=Twc)
        if i < 2:
            depth, ids = render(Twc)
            v.update(depth=depth / S_TRUE, conf=confidence(), ids=ids,
                     proposals={noun: [(ids == oid, SAM3_SCORES[oid], oid) for oid in oids if (ids == oid).any()]
                                for noun, oids in NOUN_IDS.items()})
        views.append(v)
    return views


# ------------------------------------------------------------------------------------- provider
def unproject(rows, cols, z, K):
    x = ((cols + 0.5) - K[0, 2]) / K[0, 0]
    y = ((rows + 0.5) - K[1, 2]) / K[1, 1]
    return np.column_stack((x * z, y * z, z))


def principal_extents(P):
    Q = P - P.mean(0)
    _, _, Vt = np.linalg.svd(Q, full_matrices=False)
    proj = Q @ Vt.T
    return np.sort(np.percentile(proj, 98, axis=0) - np.percentile(proj, 2, axis=0))[::-1]


def lift(mask, depth, conf, K, erode_px=2, min_pixels=20):
    keep = erode(mask, erode_px) & np.isfinite(depth) & (depth > 0)
    c = conf[np.isfinite(conf)]
    keep &= np.isfinite(conf) & (conf > np.median(c))
    rows, cols = np.nonzero(keep)
    if len(rows) < min_pixels:
        return None
    P = unproject(rows, cols, depth[rows, cols], K)
    return dict(X=np.median(P, axis=0), ext=principal_extents(P), n=len(rows))


def project01(X, K, w=W, h=H):
    return np.array([(K[0, 0] * X[0] / X[2] + K[0, 2]) / w, (K[1, 1] * X[1] / X[2] + K[1, 2]) / h])


def in_frame(uv):
    return bool(np.isfinite(uv).all() and 0 <= uv[0] < 1 and 0 <= uv[1] < 1)


def record_uv(X, K, behind=0.01):
    if X[2] <= behind:
        return np.array([-1.0, -1.0])
    return np.clip(project01(X, K), -1.0, 2.0)


def code1000(u01):
    """uv01 (float64, in frame) -> integer code 0..999."""
    return min(int(math.floor(1000.0 * u01 + 1e-9)), 999)


def student_point(oid, Twc):
    """The stub student's pointing answer: the code of the object's top-face centre projected into the dataset-
    orientation image (K_TRUE)."""
    X = apply(inv(Twc), TOP_CENTRES[oid])
    uv = np.array([(K_TRUE[0, 0] * X[0] / X[2] + K_TRUE[0, 2]) / W, (K_TRUE[1, 1] * X[1] / X[2] + K_TRUE[1, 2]) / H])
    return code1000(uv[0]), code1000(uv[1])


def points_for(t, wrist_ids, agent_ids):
    """{entity: (wrist code or None, agent code or None)} from the objects each view's student points at."""
    tw, ta = wrist_pose(t), rigid(AGENT_R, AGENT_C)
    return {e: (None if wrist_ids[e] is None else student_point(wrist_ids[e], tw),
                None if agent_ids[e] is None else student_point(agent_ids[e], ta)) for e in (0, 1)}


def point_pixel(code):
    """Student point code 0..1000 -> pixel (row, col); 1000 clamps to 999."""
    u, v = (min(int(c), 999) for c in code)
    return int(math.floor((v + 0.5) / 1000 * H)), int(math.floor((u + 0.5) / 1000 * W))


def mask_has(mask, uv):
    if not in_frame(uv):
        return False
    return bool(mask[int(math.floor(uv[1] * H)), int(math.floor(uv[0] * W))])


def scale_proprio(t, views, min_motion=0.02, max_spread=0.2):
    ratios = {}
    for v in views[2:]:
        metric = float(np.linalg.norm(centre(t) - centre(v['step'])))
        model = float(np.linalg.norm(v['T0'][:3, 3]))
        if not math.isfinite(metric) or metric < min_motion or not math.isfinite(model) or model <= 1e-12:
            continue
        ratios[v['step']] = metric / model
    if not ratios:
        return None, ratios
    r = np.array(list(ratios.values()))
    if r.max() / r.min() - 1 > max_spread:
        return None, ratios
    return float(np.median(r)), ratios


def provider(t, presence, points):
    """presence[e] = (P_wrist, P_agent); points[e] = (code_wrist or None, code_agent or None).
    Returns (where [2, 18] float64, reasons, info)."""
    views = scene_inputs(t)
    s, ratios = scale_proprio(t, views)
    vw, va = views[0], views[1]
    T_a0 = inv(va['T0'])                                          # T_agent<-view0
    p = proprio(t)
    R_eef = rodrigues(p[3:6])
    where, reasons, info = np.zeros((2, 18)), [], dict(scale=s, ratios=ratios, entities=[])
    for e in (0, 1):
        _, noun = PHRASES[e]
        ent = dict()
        grounded, lifts, masks = {}, {}, {}
        for name, v, P_yes, code in (('wrist', vw, presence[e][0], points[e][0]),
                                     ('agent', va, presence[e][1], points[e][1])):
            if P_yes < TAU:
                ent[name] = 'low_presence'
                continue
            if code is None:
                ent[name] = 'no_point'
                continue
            r, c = point_pixel(code)
            hits = [(score, oid, m) for (m, score, oid) in v['proposals'][noun] if m[r, c]]
            if not hits:
                ent[name] = 'no_lift'
                continue
            score, oid, m = max(hits, key=lambda z: z[0])
            L = lift(m, v['depth'], v['conf'], v['K'])
            if L is None:
                ent[name] = 'no_lift'
                continue
            grounded[name], lifts[name], masks[name] = oid, L, m
            ent[name] = f'grounded object {oid}, {L["n"]} lifted px'
        ent['P'] = max(presence[e])
        if not grounded:
            views = (ent.get('wrist'), ent.get('agent'))
            why = 'no_lift' if 'no_lift' in views else ('no_point' if 'no_point' in views else 'low_presence')
            reasons.append(why)
            info['entities'].append(ent)
            continue
        if 'wrist' in grounded and 'agent' in grounded:
            Xw_in_agent = apply(T_a0, lifts['wrist']['X'])
            uv1 = project01(Xw_in_agent, va['K']) if Xw_in_agent[2] > 0 else np.array([np.nan, np.nan])
            ok1 = mask_has(dilate(masks['agent'], 3), uv1)
            Xa_in_0 = apply(va['T0'], lifts['agent']['X'])
            uv2 = project01(Xa_in_0, vw['K']) if Xa_in_0[2] > 0 else np.array([np.nan, np.nan])
            ok2 = (not in_frame(uv2)) or mask_has(dilate(masks['wrist'], 3), uv2)
            ent['cross'] = dict(wrist_to_agent_px=(uv1 * [W, H]).tolist(), ok1=ok1,
                                agent_to_wrist_px=(uv2 * [W, H]).tolist(), ok2=ok2)
            if not (ok1 and ok2):
                reasons.append('cross_view')
                info['entities'].append(ent)
                continue
        src = 'wrist' if 'wrist' in grounded else 'agent'
        X0 = lifts['wrist']['X'] if src == 'wrist' else apply(va['T0'], lifts['agent']['X'])
        ext = lifts[src]['ext']
        uv_a, uv_w = record_uv(apply(T_a0, X0), va['K']), record_uv(X0, vw['K'])
        row = np.zeros(18)
        row[0], row[1], row[2:4], row[4:6] = ent['P'], 1.0, uv_a, uv_w
        reason = 'ok'
        if X0[2] <= 0.01:
            reason = 'behind_wrist'
        elif s is not None and float(np.linalg.norm(s * X0)) <= 2.0:
            Xm = s * (MIRROR @ X0)                               # metres, true OpenCV wrist frame
            row[6:9] = Xm
            row[9:12] = R_eef @ (R_HE @ Xm + T_HE)
            row[12:15] = np.maximum(s * ext, 0.02)
            row[15:18] = (1, 0, 0)
        else:
            reason = 'no_scale'
        if reason == 'behind_wrist':
            reasons.append(reason)
            info['entities'].append(ent)
            continue
        where[e] = row
        reasons.append(reason)
        ent.update(source=src, X_g3t=X0.tolist())
        info['entities'].append(ent)
    return where, reasons, info


# ------------------------------------------------------------------------------------------ text
def f2(x):
    s = f'{x:.2f}'
    return '0.00' if s == '-0.00' else s


def view_text(uv):
    return f'[{code1000(uv[0])},{code1000(uv[1])}]' if in_frame(uv) else 'out of view'


def where_line(where, reasons, withheld=False):
    parts = []
    for e in (0, 1):
        phrase = PHRASES[e][0]
        role = ('target', 'place')[e]
        row, why = where[e], reasons[e]
        if withheld:
            body = 'withheld'
        elif why in ('low_presence', 'no_point'):
            body = 'not seen'
        elif why in ('no_lift', 'cross_view', 'behind_wrist'):
            body = 'unsure'
        else:
            body = f'p {f2(row[0])} agent {view_text(row[2:4])} wrist {view_text(row[4:6])}'
            if row[15:18].any():
                body += (f' cam ({", ".join(f2(x) for x in row[6:9])}) m reach ({", ".join(f2(x) for x in row[9:12])})'
                         f' m size {" x ".join(f2(x) for x in row[12:15])} m')
            else:
                body += ' scale unknown'
        parts.append(f'{role} "{phrase}" {body}')
    return 'where: ' + '; '.join(parts) + '.'


# -------------------------------------------------------------------------------------- checking
FAILS = []
COUNT = [0]


def check(name, got, want, tol=TOL):
    COUNT[0] += 1
    if want is None:
        FAILS.append(name + ' (no stated value)')
        return False
    got, want = np.asarray(got, dtype=np.float64), np.asarray(want, dtype=np.float64)
    ok = got.shape == want.shape and bool(np.all(np.abs(got - want) <= tol))
    if not ok:
        FAILS.append(name)
        print(f'  FAIL {name}: got {np.array2string(got, precision=8)} want {want}')
    return ok


def check_eq(name, got, want):
    COUNT[0] += 1
    if want is None:
        FAILS.append(name + ' (no stated value)')
        return
    if got != want:
        FAILS.append(name)
        print(f'  FAIL {name}:\n    got  {got!r}\n    want {want!r}')


def show(name, arr, nd=6):
    print(f'  {name} = [' + ', '.join(f'{x:.{nd}f}' for x in np.asarray(arr).ravel()) + ']')


# ------------------------------------------------------------------------------- the examples
# Stated values (schema section 11). Vectors to 1e-6; lines byte for byte.
EX1_WHERE = [[0.97, 1, 0.560551, 0.655945, 0.359375, 0.638672, 0.098437, 0.097070, 0.350000, 0.098437, -0.097070, -0.250000, 0.125927, 0.117893, 0.020000, 1, 0, 0],
             [0.99, 1, 0.429223, 0.699266, 0.240234, 0.369141, 0.197422, -0.099453, 0.380000, 0.197422, 0.099453, -0.280000, 0.166268, 0.148466, 0.020000, 1, 0, 0]]
EX1_LINE = ('where: target "black bowl between the plate and the ramekin" p 0.97 agent [560,655] wrist [359,638] '
            'cam (0.10, 0.10, 0.35) m reach (0.10, -0.10, -0.25) m size 0.13 x 0.12 x 0.02 m; place "plate" p 0.99 '
            'agent [429,699] wrist [240,369] cam (0.20, -0.10, 0.38) m reach (0.20, 0.10, -0.28) m size 0.17 x 0.15 x 0.02 m.')
EX2_LINE = ('where: target "black bowl between the plate and the ramekin" unsure; place "plate" p 0.99 agent [429,699] '
            'wrist [240,369] cam (0.20, -0.10, 0.38) m reach (0.20, 0.10, -0.28) m size 0.17 x 0.15 x 0.02 m.')
EX3_WHERE = [[0.95, 1, 0.565534, 0.677734, 0.206197, 0.604114] + [0] * 12,
             [0.99, 1, 0.429396, 0.698934, 0.191406, 0.396484] + [0] * 12]
EX3_LINE = ('where: target "black bowl between the plate and the ramekin" p 0.95 agent [565,677] wrist [206,604] scale '
            'unknown; place "plate" p 0.99 agent [429,698] wrist [191,396] scale unknown.')
EX_POINTS = {40: {0: ((357, 642), (562, 656)), 1: ((236, 368), (428, 700))},
             '40d': {0: ((571, 214), (562, 656)), 1: ((236, 368), (428, 700))},
             0: {0: ((277, 611), (562, 656)), 1: ((187, 395), (428, 700))}}


def example_1_2_3():
    global EX1_LINE
    print('Examples 1-3: synthetic LIBERO scene (stub perception from scene_inputs)')
    for oid, (name, b) in BOXES.items():
        print(f'  box {oid} {name}: x {b[0]:.3f}..{b[1]:.3f}, y {b[2]:.3f}..{b[3]:.3f}, z {b[4]:.3f}..{b[5]:.3f}')
    print(f'  table plane z = {TABLE_Z}; G3T stub: depth = metric depth / {S_TRUE}, T translations / {S_TRUE};'
          ' confidence = 1 + ((7 row + 13 col) mod 17) / 16')
    out = {}
    # ---- example 1
    t = 40
    views = scene_inputs(t)
    print(f'Example 1 (t = {t}): views {[(v["role"], v["step"]) for v in views]}')
    for v in views[2:]:
        dm = float(np.linalg.norm(centre(t) - centre(v['step'])))
        print(f'  wrist_{v["step"]}: metric displacement {dm:.10f} m, G3T displacement '
              f'{np.linalg.norm(v["T0"][:3, 3]):.10f}')
    presence = {0: (0.93, 0.97), 1: (0.96, 0.99)}
    points = points_for(t, {0: 1, 1: 2}, {0: 1, 1: 2})
    print(f'  student points (wrist, agent) uv1000: {points}')
    where, reasons, info = provider(t, presence, points)
    print(f'  scale s = {info["scale"]!r}; ratios {info["ratios"]}')
    for e, ent in enumerate(info['entities']):
        print(f'  entity {e}: {ent}')
    for e in (0, 1):
        show(f'where[{e}]', where[e])
    print('  reasons', reasons)
    check('ex1 scale', info['scale'], 2.0, 1e-12)
    check('ex1 where', where, EX1_WHERE, 5e-7)
    line = where_line(where, reasons)
    print('  line:', line)
    check_eq('ex1 points', points, EX_POINTS[40])
    check_eq('ex1 reasons', reasons, ['ok', 'ok'])
    check_eq('ex1 line', line, EX1_LINE)
    out['ex1'] = (where, reasons, line)
    # dropout draw
    h8 = hashlib.sha256(f'17:libero_spatial/task03/demo_007:{t}'.encode()).hexdigest()[:8]
    u = int(h8, 16) / 16 ** 8
    print(f'  dropout draw sha256("17:libero_spatial/task03/demo_007:40")[:8] = {h8} -> {u:.4f}')
    check_eq('ex1 dropout hex', h8, '9c6b2b8d')
    check('ex1 dropout u', round(u, 4), 0.6110, 1e-12)
    # proprio normalisation
    pmin = np.array([-0.30, -0.40, 0.85, 2.80, -0.60, -0.60, 0.00, -0.04])
    pmax = np.array([0.70, 0.40, 1.45, 3.30, 0.60, 0.60, 0.04, 0.00])
    pn = 2 * (proprio(t) - pmin) / (pmax - pmin) - 1
    show('normalised proprio', pn)
    check('ex1 proprio', pn, [0.6, 0.0, 0.166667, 0.366372, 0.0, 0.0, 0.95, -0.95], 5e-7)
    # ---- example 2
    print('Example 2 (t = 40): the wrist point lands on the distractor bowl')
    points2 = points_for(t, {0: 3, 1: 2}, {0: 1, 1: 2})
    print(f'  student points (wrist, agent) uv1000: {points2}')
    where2, reasons2, info2 = provider(t, presence, points2)
    print(f'  entity 0: {info2["entities"][0]}')
    print('  reasons', reasons2)
    for e in (0, 1):
        show(f'where[{e}]', where2[e])
    line2 = where_line(where2, reasons2)
    print('  line:', line2)
    check_eq('ex2 points', points2, EX_POINTS['40d'])
    check_eq('ex2 line', line2, EX2_LINE)
    check_eq('ex2 reasons', reasons2, ['cross_view', 'ok'])
    check('ex2 where0', where2[0], np.zeros(18), 0)
    check('ex2 where1', where2[1], where[1], 0)
    out['ex2'] = (where2, reasons2, line2, info2)
    # ---- example 3
    print('Example 3 (t = 0): scale unknown')
    views3 = scene_inputs(0)
    print(f'  views {[(v["role"], v["step"]) for v in views3]}')
    presence3 = {0: (0.30, 0.95), 1: (0.96, 0.99)}
    points3 = points_for(0, {0: 1, 1: 2}, {0: 1, 1: 2})
    print(f'  student points (wrist, agent) uv1000: {points3}')
    where3, reasons3, info3 = provider(0, presence3, points3)
    for e, ent in enumerate(info3['entities']):
        print(f'  entity {e}: {ent}')
    for e in (0, 1):
        show(f'where[{e}]', where3[e])
    print('  reasons', reasons3)
    line3 = where_line(where3, reasons3)
    print('  line:', line3)
    check_eq('ex3 points', points3, EX_POINTS[0])
    check_eq('ex3 reasons', reasons3, ['no_scale', 'no_scale'])
    check('ex3 where', where3, EX3_WHERE, 5e-7)
    check_eq('ex3 line', line3, EX3_LINE)
    out['ex3'] = (where3, reasons3, line3)
    # withheld line
    print('  withheld line:', where_line(where, reasons, withheld=True))
    return out


def example_4():
    print('Example 4: navigation waypoint (512 x 512, HFOV 90, h = 1.25 m)')
    Wn, h = 512, 1.25
    f = (Wn / 2) / math.tan(math.radians(90) / 2)

    def lift_click(x, y, z_override=None):
        dy = y * Wn - Wn / 2
        if z_override is not None:
            z = z_override
        elif dy > 0:
            z = h * f / dy
        else:
            z = None
        if z is None:
            px = (x * Wn - Wn / 2) / f
            beta, r = math.degrees(math.atan2(-px, 1.0)), None
        else:
            px = z * (x * Wn - Wn / 2) / f
            beta, r = math.degrees(math.atan2(-px, z)), math.hypot(px, z)
        L = 0.5 if r is None else min(max(r - 0.5, 0.0), 2.0)
        turns = int(round(abs(beta) / 15))
        fwd = int(round(L / 0.25))
        prims = (['turn_left' if beta > 0 else 'turn_right'] * turns) + ['forward'] * fwd
        return dict(z=z, px=px, beta=beta, r=r, L=L, prims=prims)

    a = lift_click(0.62, 0.81)
    print(f'  <goal frame=32 x=0.62 y=0.81>: pixel ({0.62 * Wn:.2f}, {0.81 * Wn:.2f}); z = {a["z"]:.6f}; '
          f'P_x = {a["px"]:.6f}; beta = {a["beta"]:.4f}; r = {a["r"]:.6f}; L = {a["L"]:.6f}; {a["prims"]}')
    check('ex4 z', a['z'], 2.016129, 5e-7)
    check('ex4 px', a['px'], 0.483871, 5e-7)
    check('ex4 beta', a['beta'], -13.4957, 5e-5)
    check('ex4 r', a['r'], 2.073381, 5e-7)
    check('ex4 L', a['L'], 1.573381, 5e-7)
    check_eq('ex4 prims', a['prims'], ['turn_right'] + ['forward'] * 6)
    b = lift_click(0.50, 0.99)
    print(f'  bottom clamp y = 0.99: z = {b["z"]:.6f}; beta = {b["beta"]:.4f}; L = {b["L"]:.6f}; {b["prims"]}')
    check('ex4b z', b['z'], 1.275510, 5e-7)
    check_eq('ex4b prims', b['prims'], ['forward'] * 3)
    c = lift_click(0.30, 0.55)
    print(f'  far click: z = {c["z"]:.6f}; beta = {c["beta"]:.4f}; r = {c["r"]:.6f}; L = {c["L"]:.6f}; {c["prims"]}')
    check('ex4c beta', c['beta'], 21.8014, 5e-5)
    check_eq('ex4c prims', c['prims'], ['turn_left'] + ['forward'] * 8)
    d = lift_click(0.70, 0.40)
    print(f'  above the horizon y = 0.40: range undefined; beta = {d["beta"]:.4f}; L = {d["L"]}; {d["prims"]}')
    check_eq('ex4d prims', d['prims'], ['turn_right'] + ['forward'] * 2)
    # g3t_depth check on a synthetic G3T depth map of a level camera 0.625 G3T units above a flat floor
    depth, up = floor_depth_g3t()
    fit = floor_fit(depth, np.array([[256.0, 0, 256.0], [0, 256.0, 256.0], [0, 0, 1]]), up)
    s = h / fit['h']
    row, col = min(int(0.81 * 512), 511), min(int(0.62 * 512), 511)
    dz = depth[row, col]
    g = lift_click(0.62, 0.81, z_override=s * dz)
    print(f'  g3t_depth: plane fit inliers {fit["inliers"]}, h_G3T = {fit["h"]:.12f}, median residual '
          f'{fit["resid"]:.3e}, s = {s:.12f}; depth[{row}, {col}] = {dz:.12f}; z = {g["z"]:.6f}; '
          f'beta = {g["beta"]:.4f}; r = {g["r"]:.6f}; L = {g["L"]:.6f}; {g["prims"]}')
    check('ex4g h', fit['h'], 0.625, 1e-12)
    check('ex4g inliers', fit['inliers'], 129540, 0)
    check('ex4g z', g['z'], 2.018927, 5e-7)
    check_eq('ex4g prims', g['prims'], a['prims'])
    zc = h * f / (0.81 * Wn - Wn / 2) / 2
    print(f'  the floor_plane z at the continuous click equals S_TRUE x {zc:.12f}; the pixel-centre depth differs by the '
          'half-pixel row offset (158.5 vs 158.72 px below the horizon)')


def floor_depth_g3t(h_g3t=0.625, n=512):
    """G3T depth [n, n] of a level camera (f = n/2, principal point n/2) h_g3t above a flat floor; nan above the
    horizon. Gravity up in the camera frame is (0, -1, 0)."""
    rows = np.arange(n)[:, None] + 0.5
    dy = rows - n / 2
    with np.errstate(divide='ignore'):
        z = np.where(dy > 0, h_g3t * (n / 2) / dy, np.nan)
    return np.broadcast_to(z, (n, n)).copy(), np.array([0.0, -1.0, 0.0])


def floor_fit(depth, K, up, max_normal_deg=10.0, min_inliers=500, max_residual=0.02):
    """Deterministic floor fit (schema 8.2): finite-difference normals, inliers in the lower image half with
    normals within max_normal_deg of `up`, height = -(P . up), h_G3T = median height."""
    Hd, Wd = depth.shape
    rows, cols = np.mgrid[0:Hd, 0:Wd]
    P = np.stack([((cols + 0.5) - K[0, 2]) / K[0, 0] * depth, ((rows + 0.5) - K[1, 2]) / K[1, 1] * depth, depth], -1)
    dx, dy = P[1:-1, 2:] - P[1:-1, :-2], P[2:, 1:-1] - P[:-2, 1:-1]
    nrm = np.cross(dy, dx)
    with np.errstate(invalid='ignore', divide='ignore'):
        nrm = nrm / np.linalg.norm(nrm, axis=-1, keepdims=True)
        cos = np.abs(nrm @ (up / np.linalg.norm(up)))
    inner = P[1:-1, 1:-1]
    lower = (rows[1:-1, 1:-1] + 0.5) > Hd / 2
    with np.errstate(invalid='ignore'):
        ok = lower & np.isfinite(cos) & (cos >= math.cos(math.radians(max_normal_deg))) & \
            np.isfinite(inner).all(-1) & (inner[..., 2] > 0)
    heights = -(inner[ok] @ up)
    if heights.size < min_inliers:
        return dict(h=None, inliers=int(heights.size), resid=None)
    hh = float(np.median(heights))
    resid = float(np.median(np.abs(heights - hh)))
    ok_fit = hh > 0 and resid <= max_residual * hh
    return dict(h=hh if ok_fit else None, inliers=int(heights.size), resid=resid)


def example_5():
    print('Example 5: action normalisation and gripper')
    mx = np.array([0.9375, 0.9375, 0.9375, 0.1875, 0.1875, 0.375])
    mn = -mx
    raw = np.array([0.30, -0.15, -0.60, 0.0375, 0.0, -0.075])
    y = 2 * (raw - mn) / (mx - mn) - 1
    show('normalised', y, 2)
    check('ex5 y', y, [0.32, -0.16, -0.64, 0.20, 0.00, -0.20], 1e-12)
    a6 = 0.0
    g = 1 - 2 * a6
    check('ex5 g', g, 1.0, 0)
    pred = np.array([1.30, -0.16, -0.64, 0.20, 0.00, -0.20])
    x = (np.clip(pred, -1, 1) + 1) / 2 * (mx - mn) + mn
    show('de-normalised', x, 4)
    check('ex5 x', x, [0.9375, -0.15, -0.60, 0.0375, 0.0, -0.075], 1e-12)

    def cmd(gp):
        return 1 if gp >= 0 else -1

    def starvla(gp):
        a = (1 - gp) / 2
        return 1 - 2 * int(a > 0.5)
    for gp in (-0.83, 0.0, 0.4):
        print(f'  predicted g = {gp:+.2f}: command {cmd(gp):+d}; StarVLA client {starvla(gp):+d}')
        check(f'ex5 gripper {gp}', cmd(gp), starvla(gp), 0)
    check('ex5 a6=1', 1 - 2 * 1.0, -1.0, 0)


def example_6():
    print('Example 6: cache key')
    obj = {
        'episode': 'libero_spatial/task03/demo_007',
        'g3t': {'config': '5aeb2acd008d41a1cac52e10216fbf35e8dfeb2ce26b89bb24e7ccc4ee0817d7',
                'source': 'df1ea59a73b0ad08b51670bfa37da84eace99b9d0c45c8d270f7052b42e98701',
                'weights': 'd460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702'},
        'hand_eye_sha256': '3' * 64,
        'instruction': INSTRUCTION,
        'orientation': 'dataset',
        'phrase_table_sha256': '4' * 64,
        'proprio': {str(s): [float(x) for x in proprio(s)] for s in (40, 32, 24, 8)},
        'provider_code_sha': '0' * 40,
        'provider_config_sha256': '1' * 64,
        'sam3_checkpoint_sha256': '9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e',
        'schema': f'{SCHEMA}/where_cache_key',
        'student_export_sha256': '2' * 64,
        't': 40,
        'views': [{'image_sha256': c * 64, 'role': r, 'step': s}
                  for c, r, s in (('5', 'wrist', 40), ('6', 'agent', 40), ('7', 'wrist', 32), ('8', 'wrist', 24),
                                  ('9', 'wrist', 8))],
    }
    text = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    key = hashlib.sha256(text.encode('utf-8')).hexdigest()
    print('  ' + text)
    print('  key =', key)
    check_eq('ex6 key', key, '8e2cc39e657d6476ad6a15f254c8f1a9dc7f9e43c08c98a068ee0e184e43b2a6')
    z = np.zeros((2, 2, 3), dtype=np.uint8)
    dig = hashlib.sha256(b'2,2,3;' + z.tobytes()).hexdigest()
    print('  image digest of a 2 x 2 x 3 zero array =', dig)
    check_eq('ex6 digest', dig, '0e828bc8f1402ce29e34308138a96956732294f18d5cfbf62dbbfe2b04cafdce')
    return text, key


# ------------------------------------------------------------------------------------- tokens
RESERVED_FIRST, RESERVED_N = 247019, 1025      # the reserved list is the contiguous ids 247019..248043


def dct_matrix(n):
    k = np.arange(n, dtype=np.float64)[:, None]
    i = np.arange(n, dtype=np.float64)[None]
    m = np.cos(math.pi / n * (i + 0.5) * k) * math.sqrt(2.0 / n)
    m[0] /= math.sqrt(2.0)
    return m


def example_chunk():
    """[8, 7] normalised chunk: dims 0-5 = example 5's normalised action times (10 - k) / 10; gripper g = +1 for
    k < 4, -1 after."""
    base = np.array([0.32, -0.16, -0.64, 0.20, 0.00, -0.20])
    y = np.zeros((8, 7))
    for k in range(8):
        y[k, :6] = base * (10 - k) / 10
        y[k, 6] = 1.0 if k < 4 else -1.0
    return y


def fast_fixture_chunks(n=512, seed=20261111):
    """The FAST fixture's fitting set: example_chunk() plus n deterministic chunks (numpy RandomState, stable across
    versions): dims 0-5 = clip(a + b k / 7, -1, 1) with a, b ~ U(-0.5, 0.5); gripper +1 or -1 switching once at
    a uniform step."""
    rng = np.random.RandomState(seed)
    out = [example_chunk()]
    for _ in range(n):
        a, b = rng.uniform(-0.5, 0.5, size=6), rng.uniform(-0.5, 0.5, size=6)
        k = np.arange(8)[:, None]
        y = np.zeros((8, 7))
        y[:, :6] = np.clip(a + b * k / 7, -1, 1)
        first, switch = (1.0 if rng.uniform() < 0.5 else -1.0), rng.randint(0, 9)
        y[:, 6] = np.where(np.arange(8) < switch, first, -first)
        out.append(y)
    return np.stack(out)


def example_7():
    print('Example 7: action tokens for the example chunk')
    y = example_chunk()
    for k in range(8):
        print('  y[%d] = [%s]' % (k, ', '.join(f'{v:+.2f}' for v in y[k])))
    # bins
    v = (y + 1) / 2 * 256
    bins = np.minimum(np.floor(v), 255).astype(int).ravel()
    frac_b = np.abs(v - np.round(v))
    exact_b = frac_b == 0                      # y in {-1, 0, +1}: exact in fp32 as well
    margin_b = float(np.min(frac_b[~exact_b]))
    print('  bins (time-major, 56):', bins.tolist())
    print(f'  bins LM ids = 247019 + code: first 7 {(RESERVED_FIRST + bins[:7]).tolist()}; nearest bin edge '
          f'{margin_b:.4f} code units')
    check_eq('ex7 bins', bins.tolist(), [168, 107, 46, 153, 128, 102, 255, 164, 109, 54, 151, 128, 104, 255, 160, 111, 62,
                                         148, 128, 107, 255, 156, 113, 70, 145, 128, 110, 255, 152, 115, 78, 143, 128,
                                         112, 0, 148, 117, 87, 140, 128, 115, 0, 144, 119, 95, 138, 128, 117, 0, 140,
                                         121, 103, 135, 128, 120, 0])
    assert margin_b > 1e-3
    # digits
    q = (y + 1) / 2 * 1000
    digits = np.round(q).astype(int).ravel()
    margin_d = float(np.min(np.abs(np.abs(q - np.floor(q)) - 0.5)))   # distance from a rounding tie
    text = ' '.join(str(d) for d in digits)
    print(f'  digits text: "{text[:60]} ..." ({len(digits)} numbers); nearest rounding tie {margin_d:.4f}')
    print('  digits (56):', digits.tolist())
    check_eq('ex7 digits', digits[:14].tolist(), [660, 420, 180, 600, 500, 400, 1000, 644, 428, 212, 590, 500, 410, 1000])
    assert margin_d > 1e-3
    # FAST integer stage
    M = dct_matrix(8)
    coeff = M @ y
    ints = np.round(coeff * 10)
    margin_f = float(np.min(np.abs(np.abs(coeff * 10 - np.floor(coeff * 10)) - 0.5)))
    ints = ints.astype(int).ravel()
    print('  FAST integers round(10 DCT) (frequency-major, 56):', ints.tolist())
    print(f'  nearest rounding tie {margin_f:.4f}')
    assert margin_f > 1e-3
    fit = np.round(np.stack([(M @ c).ravel() for c in fast_fixture_chunks()]) * 10)
    lo, hi = int(fit.min()), int(fit.max())
    print(f'  fixture fit set: {len(fast_fixture_chunks())} chunks, min_token {lo}, max_token {hi}, alphabet '
          f'{hi - lo + 1} symbols; BPE characters of the example = chr(int - min_token): first 7 '
          f'{[int(c) - lo for c in ints[:7]]}')
    want = [0] * 56
    for i, v in {0: 6, 1: -3, 2: -12, 3: 4, 5: -4, 7: 2, 8: -1, 9: -4, 10: 1, 12: -1, 13: 26, 27: -9, 41: 6, 55: -5}.items():
        want[i] = v
    check_eq('ex7 fast ints', ints.tolist(), want)
    check_eq('ex7 fast range', (lo, hi), (-28, 28))
    rec = M.T @ (ints.reshape(8, 7) / 10)
    err = float(np.abs(rec - y).max())
    print(f'  integer-stage round trip max |error| = {err:.4f} (bound sqrt(8) * 0.5 / 10 = {math.sqrt(8) * 0.05:.4f})')
    assert err <= math.sqrt(8) * 0.05
    print(f'  FAST symbol s -> LM id 247019 + s (s = 0..1023); end symbol 1024 -> LM id 248043')
    return bins, digits, ints, (lo, hi)


def example_quantisation():
    print('Quantisation before the fp32 cast')
    u = 179.2 / 256
    print(f'  float64 u = {u!r} -> code {code1000(u)}; the same value after an fp32 cast '
          f'{float(np.float32(u))!r} -> floor(1000 u) = {int(math.floor(1000 * float(np.float32(u))))}')
    check_eq('quant f64', code1000(u), 700)
    check_eq('quant f32', int(math.floor(1000 * float(np.float32(u)))), 699)
    check_eq('quant 1000', point_pixel((1000, 1000)), (255, 255))
    for i in (0, 1, 127, 128, 255):
        c = code1000((i + 0.5) / W)
        back = int(math.floor((c + 0.5) / 1000 * W))
        check_eq(f'roundtrip {i}', back, i)


def main():
    print(f'{SCHEMA} worked examples (numpy {np.__version__})')
    out = example_1_2_3()
    example_4()
    example_5()
    example_6()
    example_7()
    example_quantisation()
    if FAILS:
        print(f'FAILED {len(FAILS)}: {FAILS}')
        raise SystemExit(1)
    print(f'ALL {COUNT[0]} CHECKS PASSED (examples 1-7 and the quantisation rules)')


if __name__ == '__main__':
    main()
