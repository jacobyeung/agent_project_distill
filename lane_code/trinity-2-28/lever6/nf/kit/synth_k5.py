"""Synthetic K5 returns in K5's exact record format (kit 2.py records, 0.py group result and
receipt), built from the banked read's own geometry exports. Tests and dry runs only."""
import hashlib
import json
from pathlib import Path

import numpy as np

import replay_nf as R


def array_sha(a):
    a = np.ascontiguousarray(np.asarray(a))
    return dict(sha256=hashlib.sha256(a.tobytes()).hexdigest(), dtype=str(a.dtype), shape=list(a.shape))


def banked_cameras(reference=R.DEFAULTS['k5_reference'], banked=R.DEFAULTS['banked'], tasks=R.DEFAULTS['tasks'],
                   geometry=R.DEFAULTS['geometry']):
    """{K5 key: (K, cu, s)} from the banked geometry export of each K5 capture."""
    ref = json.loads(Path(reference).read_text())['captures']
    t = R.load_tasks(tasks)
    data = json.loads(Path(banked).read_text())
    clip = {}
    for x in data['arms']['unflagged']:
        clip.setdefault(t[x['key']]['scene'], x['perception']['clip'])
    out = {}
    for c in sorted(ref, key=lambda c: c['position']):
        z = np.load(Path(geometry)/(clip[c['capture']]+'.npz'))
        out[c['k']] = (np.array(z['K'], float), np.array(z['camera_to_world'], float), float(z['scale']))
    return out


def world(C, deg=17.0, shift=(0.3, -0.2, 0.1)):
    """Left-multiply every camera by one rigid world transform (a different reference frame)."""
    a = np.radians(deg)
    W = np.eye(4)
    W[:3, :3] = [[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]]
    W[:3, 3] = shift
    return W@C


def perturb(C, deg=25.0, shift=0.4):
    """Right-multiply every frame but the first by a camera-local yaw and a forward shift."""
    a = np.radians(deg)
    D = np.eye(4)
    D[:3, :3] = [[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]]
    D[:3, 3] = [shift/4, 0.0, shift]
    out = C.copy()
    for k in range(1, len(C)):
        D_k = D.copy()
        D_k[:3, 3] *= k/len(C)
        out[k] = C[k]@D_k
    return out


def record(key, n, K, cu, s, position, index):
    cm = np.array(cu, float).copy()
    cm[:, :3, 3] *= s
    tag = np.concatenate([np.ravel(cu), [s]])
    shas = {name: array_sha(tag+i) for i, name in enumerate(('p9', 'd', 'dc', 'pt'))}
    shas.update(K=array_sha(K), cm=array_sha(cm), cu=array_sha(cu), s=array_sha(np.float64(s)))
    return dict(status='ok', k=key, n=n, seconds=1.0, bind_seconds=0.1, rebuilt=position == 0, K=np.asarray(K).tolist(),
                cm=cm.tolist(), cu=np.asarray(cu).tolist(), s=float(s), sha=shas, peak_bytes=0, reserved_bytes=0,
                rss_kib=0, position=position, index=index)


def arm_result(arm, cams, frames, reverse):
    keys = list(cams)
    order = list(range(len(keys)))
    if reverse:
        order.reverse()
    order.append(0)
    recs = [record(keys[x], frames[keys[x]], *cams[keys[x]], position=pos, index=x) for pos, x in enumerate(order)]
    return dict(schema=1, token='synthetic', arm=arm, mode='g', det=arm >= 2, reverse=bool(reverse), pid=1000+arm,
                warn_only=False, status='ok', complete=True, records=recs, error=None, ops=[], warned_ops=[],
                order=order, switches={}, load_seconds=1.0, warned_count=0, seconds=10.0, exit_code=0, wall_seconds=10.0)


def write_group(directory, group, arms):
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=False)
    result = dict(schema=1, token='synthetic', group=group, complete=True, arms=arms, error=None,
                  staging_seconds=1.0, frames_verified=0, job='0', write_test=None)
    raw = json.dumps(result, separators=(',', ':'), allow_nan=False).encode()
    (d/('5%d.json' % group)).write_bytes(raw)
    (d/('5%d.1.json' % group)).write_text(json.dumps(dict(schema=1, token='synthetic', group=group, input_sha256='0'*64,
        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), complete=True, job='0')))
    return d


def make_returns(root, a1_cams, a2_cams, reference=R.DEFAULTS['k5_reference']):
    """g0 holds D1 then A1, g1 holds D2 then A2 (kit xq); D arms copy the A arms."""
    ref = json.loads(Path(reference).read_text())['captures']
    frames = {c['k']: c['frames'] for c in ref}
    root = Path(root)
    g0 = write_group(root/'g0', 0, [arm_result(2, a1_cams, frames, 0), arm_result(0, a1_cams, frames, 0)])
    g1 = write_group(root/'g1', 1, [arm_result(3, a2_cams, frames, 1), arm_result(1, a2_cams, frames, 1)])
    return [g0, g1]
