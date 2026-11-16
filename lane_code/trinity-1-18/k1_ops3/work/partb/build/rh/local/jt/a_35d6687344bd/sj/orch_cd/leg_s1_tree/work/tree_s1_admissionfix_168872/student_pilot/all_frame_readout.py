"""head_acc pose protocol on all 32 frames and the original even-frame subset.

Matches head_acc/work/analyze.py: origin-frame metric cameras, no alignment;
all unordered pairs; 0.25 m baseline; centimetre rounding before strict MRA
thresholds 0.50..0.95; direction in each source camera's gravity-level frame.
"""
from collections import defaultdict
import math

import numpy as np

from .camera_targets import rotation_from_xyzw, trajectory_scale
from .gate_eval import evaluate as gate, geodesic_deg
from .readout_geometry import validation_summary


def stats(values):
    v = np.asarray(values, dtype=float)
    if not len(v):
        return {'n': 0}
    if not np.isfinite(v).all():
        raise ValueError('Nonfinite head_acc measurement')
    return dict(n=len(v), median=float(np.median(v)), p25=float(np.percentile(v, 25)),
                p75=float(np.percentile(v, 75)), p90=float(np.percentile(v, 90)), mean=float(v.mean()))


def decode(camera):
    camera = np.asarray(camera, dtype=float)
    if not np.isfinite(camera).all() or np.any(np.linalg.norm(camera[:, 3:7], axis=-1) < 1e-8):
        raise ValueError('Invalid camera prediction')
    r = np.array([rotation_from_xyzw(q).T for q in camera[:, 3:7]])
    c = -np.einsum('nij,nj->ni', r, camera[:, :3])
    return r, c


def level(rotation, up):
    up = np.asarray(up, dtype=float)
    if not np.isfinite(up).all() or np.linalg.norm(up) < 1e-8:
        raise ValueError('Invalid gravity')
    up = up / np.linalg.norm(up)
    f = rotation[:, 2]
    h = f - (f @ up) * up
    if np.linalg.norm(h) < 1e-8:
        return None
    z = h / np.linalg.norm(h)
    y = -up
    x = np.cross(y, z)
    return np.stack((x / np.linalg.norm(x), y, z))


def direction(v):
    scores = {'forward': v[2], 'backward': -v[2], 'right': v[0], 'left': -v[0]}
    return max(scores, key=scores.get)


def pose_metrics(records, slots, *, gravity=True):
    pooled = defaultdict(lambda: defaultdict(list))
    scenes = defaultdict(int)
    for record in records:
        gt, pred = record['gt'], record['pred']
        selected = [i for i in slots if gt['camera_mask'][i]]
        rg, cg = decode(np.asarray(gt['camera'])[selected])
        rp, cp = decode(np.asarray(pred['camera'])[selected])
        values = defaultdict(list)
        for a, b, c, d in zip(rg, rp, cg, cp):
            values['rot_deg'].append(float(geodesic_deg(b, a)))
            values['centre_err_m'].append(float(np.linalg.norm(d - c)))
        lg, lp = [None]*len(rg), [None]*len(rp)
        if gravity:
            lg, lp = [level(r, gt['gravity']) for r in rg], [level(r, pred['gravity']) for r in rp]
        for i in range(len(selected)):
            for j in range(i + 1, len(selected)):
                dg, dp = cg[j] - cg[i], cp[j] - cp[i]
                mg, mp = float(np.linalg.norm(dg)), float(np.linalg.norm(dp))
                values['pair_rot_deg'].append(float(geodesic_deg(rp[j].T @ rp[i], rg[j].T @ rg[i])))
                if mg >= .25:
                    rounded_gt, rounded_pr = round(mg, 2), round(mp, 2)
                    err = abs(rounded_pr - rounded_gt) / rounded_gt
                    values['pair_disp_mra'].append(sum(err < 1 - (.50 + .05 * k) for k in range(10)) / 10.)
                if lg[i] is not None:
                    vg = lg[i] @ dg
                    if math.hypot(vg[0], vg[2]) >= .25:
                        # An undefined predicted heading counts as a miss.
                        values['pair_dir4_agree'].append(float(lp[i] is not None and direction(lp[i] @ dp) == direction(vg)))
        for subset in ('all', record['dataset']):
            scenes[subset] += 1
            for key, value in values.items():
                pooled[subset][key].extend(value)
    return {subset: dict(scenes=scenes[subset], **{k: stats(v) for k, v in metrics.items()})
            for subset, metrics in pooled.items()}


def even_records(records):
    result = []
    for record in records:
        gt, pred = dict(record['gt']), dict(record['pred'])
        gt['camera'], gt['camera_mask'] = np.asarray(gt['camera'])[1::2], np.asarray(gt['camera_mask'])[1::2]
        gt['trajectory_scale'] = trajectory_scale(gt['camera'], gt['camera_mask'])
        gt['depth_anchor_frames'] = list(range(16))
        pred['camera'] = np.asarray(pred['camera'])[1::2]
        result.append({**record, 'gt': gt, 'pred': pred})
    return result


def evaluate(records, heads, heldout, training):
    heads = set(heads)
    result = dict(protocol='head_acc_origin_metric_v1',
                geometry_validation=validation_summary(record['pred'] for record in records),
                all_frames=pose_metrics(records, range(32), gravity='gravity' in heads),
                even_frames=pose_metrics(records, range(1, 32, 2), gravity='gravity' in heads),
                even_gate=gate(even_records(records), heads - {'scale'}, heldout, training),
                scale_comparison='32-frame step target only; even-frame scale-head comparison omitted',
                pair_rule='all unordered pairs; GT baseline >=0.25m; round metres to 2 decimals for strict MRA')
    if 'gravity' not in heads:
        result['unavailable_metrics'] = ['pair_dir4_agree']
    return result
