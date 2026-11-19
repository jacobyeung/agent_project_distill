"""Phase-1 accuracy gate on held-out training scenes (never benchmark scenes).

Phase 2 starts only from a checkpoint whose heads pass this gate. The thresholds are the agreed
phase-1 gate (phase-2 protocol report, "Phase-1 accuracy gate"):
  pose:  median relative-rotation error <= 5.2 deg, median position error <= 0.25 m,
         median heading error <= 10 deg (position and heading as rendered in the gravity reference);
  depth: AbsRel <= 0.10, delta<1.25 >= 0.90, median absolute error <= 0.20 m;
  decisions: >= 85% agreement with GT on the near/far, left/right and front/back decisions the
         rendered responses support (here on the bank's held-out points; phase 2's row-level
         rendering check is reported separately when its rows are supplied).
Statistics pool every supervised anchor frame (pose) or labelled point (depth) of the held-out scenes.
A criterion with no measurement fails, and a supervised item without a prediction raises.

Datasets appear only as their opaque tokens (d1, d2). G3T reference numbers are copied, with their
definitions, from the measurements cited in G3T_REFERENCE['source']; fields without a measurement are None.
"""
import math

import numpy as np

from .camera_targets import GROUPS, rotation_from_xyzw, to_gravity_reference_frame

SCHEMA = 'student_pilot/gate_eval/v2'
GATE = {
    'rotation_deg_median_max': 5.2,
    'position_m_median_max': 0.25,
    'heading_deg_median_max': 10.0,
    'depth_abs_rel_max': 0.10,
    'depth_delta125_min': 0.90,
    'depth_abs_err_m_median_max': 0.20,
    'decision_agreement_min': 0.85,
}
DECISION_MARGIN_M = 0.20

G3T_REFERENCE = {
    'source': ('lanes/g3t_scale_20261029/RESULT.md, section 1 table "All Evaluated Training Scenes" (G3T on 32-frame '
               'training clips, Sim(3) Umeyama alignment of camera centres to metric GT); '
               'lanes/g3t_scale_20261029/PROBE_RESULT.md, table "By dataset (ridge)" (per-video scale s = GT / G3T '
               'predicted from mean-pooled G3T layer-23 tokens, 5-fold scene-disjoint CV). d1 and d2 are the '
               'opaque dataset tokens of the training rows (d1: 502 videos in the probe, d2: 684).'),
    'definitions': {
        'n_scenes': 'scenes in the RESULT.md measurement',
        'rotation_deg_sim3_mean': 'mean per-camera rotation error after Sim(3) alignment (deg)',
        'rotation_deg_sim3_median': 'median of the same (deg)',
        'rotation_deg_procrustes_mean': 'mean per-camera rotation error after a Procrustes SO(3) fit (deg)',
        'rotation_deg_procrustes_median': 'median of the same (deg)',
        'relative_rotation_deg_pairwise_mean': 'mean pairwise relative-rotation error between cameras (deg)',
        'relative_rotation_deg_pairwise_median': 'median of the same (deg); the closest G3T analogue of this gate\'s '
                                                 'relative-rotation error',
        'ate_rms_m_median_after_sim3': 'median ATE RMS after Sim(3) alignment, scale fitted to GT (m); not a metric '
                                       'translation error',
        'raw_scale_median': 'median s = GT / G3T scale over scenes (G3T is not metric)',
        'raw_scale_sd_ln': 'SD of ln s over scenes',
        'probe_scale_mean_abs_ln_err': 'mean |ln s error| of a ridge probe on G3T tokens (PROBE_RESULT.md)',
        'probe_scale_mra': 'scale mean relative accuracy of that probe (thresholds 0.50..0.95)',
        'metric_translation_m': 'no G3T measurement exists (G3T poses are not metric)',
        'depth_abs_rel': 'no G3T depth measurement exists in the cited files',
        'depth_delta125': 'no G3T depth measurement exists in the cited files',
    },
    'd1': {'n_scenes': 30, 'rotation_deg_sim3_mean': 3.23, 'rotation_deg_sim3_median': 2.75,
           'rotation_deg_procrustes_mean': 2.41, 'rotation_deg_procrustes_median': 2.13,
           'relative_rotation_deg_pairwise_mean': 3.47, 'relative_rotation_deg_pairwise_median': 2.96,
           'ate_rms_m_median_after_sim3': 0.066, 'raw_scale_median': 1.995, 'raw_scale_sd_ln': 0.345,
           'probe_scale_mean_abs_ln_err': 0.052, 'probe_scale_mra': 0.939,
           'metric_translation_m': None, 'depth_abs_rel': None, 'depth_delta125': None},
    'd2': {'n_scenes': 32, 'rotation_deg_sim3_mean': 4.13, 'rotation_deg_sim3_median': 2.29,
           'rotation_deg_procrustes_mean': 3.19, 'rotation_deg_procrustes_median': 1.71,
           'relative_rotation_deg_pairwise_mean': 4.51, 'relative_rotation_deg_pairwise_median': 2.55,
           'ate_rms_m_median_after_sim3': 0.089, 'raw_scale_median': 2.259, 'raw_scale_sd_ln': 0.356,
           'probe_scale_mean_abs_ln_err': 0.070, 'probe_scale_mra': 0.907,
           'metric_translation_m': None, 'depth_abs_rel': None, 'depth_delta125': None},
}


def geodesic_deg(r_a, r_b):
    cos = np.clip(0.5 * (np.trace(np.swapaxes(r_a, -1, -2) @ r_b, axis1=-2, axis2=-1) - 1.0), -1.0, 1.0)
    return np.degrees(np.arccos(cos))


def angle_between_deg(u, v):
    u, v = np.asarray(u, dtype=np.float64), np.asarray(v, dtype=np.float64)
    cos = np.clip(np.sum(u * v, axis=-1) / (np.linalg.norm(u, axis=-1) * np.linalg.norm(v, axis=-1)), -1.0, 1.0)
    return np.degrees(np.arccos(cos))


def heading_and_pitch_deg(r_grav):
    """Heading (azimuth of the optical axis from +Y, left positive) and pitch (elevation) in the gravity reference."""
    forward = np.asarray(r_grav)[..., :, 2]
    heading = np.degrees(np.arctan2(-forward[..., 0], forward[..., 1]))
    pitch = np.degrees(np.arcsin(np.clip(forward[..., 2], -1.0, 1.0)))
    level = np.linalg.norm(forward[..., :2], axis=-1) > 1e-3
    return heading, pitch, level


def wrap_deg(values):
    return np.abs((np.asarray(values) + 180.0) % 360.0 - 180.0)


def unproject(uv, depth, fov_hw, r_grav, t_grav):
    """[K, 2] points on the [0, 1000] grid with optical-axis depth [K] -> [K, 3] in the gravity reference."""
    x = (uv[:, 0] / 500.0 - 1.0) * math.tan(fov_hw[1] / 2) * depth
    y = (uv[:, 1] / 500.0 - 1.0) * math.tan(fov_hw[0] / 2) * depth
    camera = np.stack((x, y, depth), axis=-1)
    return camera @ np.asarray(r_grav).T + np.asarray(t_grav)


def required(mapping, key, scene):
    if key not in mapping or mapping[key] is None:
        raise ValueError(f'Missing prediction or label {key!r} for held-out scene {scene}')
    return np.asarray(mapping[key], dtype=np.float64)


def evaluate_scene(record, heads):
    """Per-item errors of one scene. heads: the set of heads the checkpoint has ({'pose', 'gravity', 'scale', 'depth'})."""
    scene = f"{record['dataset']}/{record['scene']}"
    gt, pred = record['gt'], record['pred']
    mask = np.asarray(gt['camera_mask'], dtype=bool)
    gt_cam, pred_cam = required(gt, 'camera', scene), required(pred, 'camera', scene)
    count = len(gt_cam)
    if count not in (16, 32) or gt_cam.shape != (count, 9) or pred_cam.shape != (count, 9) or mask.shape != (count,):
        raise ValueError(f'Camera arrays of {scene} must have 16 or 32 matching slots')
    if not np.isfinite(pred_cam[mask]).all():
        raise ValueError(f'Non-finite pose prediction for {scene}')
    out = {'dataset': record['dataset'], 'scene': record['scene'], 'rotation_deg': [], 'translation_m': [],
           'position_m': [], 'heading_deg': [], 'pitch_deg': [], 'gravity_deg': None, 'log_scale_err': None,
           'depth_abs_rel': [], 'depth_ratio': [], 'depth_abs_err_m': [], 'decisions': {}}
    groups = np.flatnonzero(mask)
    for g in groups:
        r_gt, r_pred = rotation_from_xyzw(gt_cam[g, 3:7]), rotation_from_xyzw(pred_cam[g, 3:7])
        out['rotation_deg'].append(float(geodesic_deg(r_pred, r_gt)))
        # Camera centres in the origin camera's frame: c = -R^T t for E = [R, t].
        c_gt, c_pred = -r_gt.T @ gt_cam[g, :3], -r_pred.T @ pred_cam[g, :3]
        out['translation_m'].append(float(np.linalg.norm(c_pred - c_gt)))
    gravity_ok = bool(gt.get('gravity_mask', False))
    rendered = 'gravity' in heads and gravity_ok and groups.size
    if 'gravity' in heads and gravity_ok:
        out['gravity_deg'] = float(angle_between_deg(required(pred, 'gravity', scene), required(gt, 'gravity', scene)))
    if rendered:
        r_gt_g, t_gt_g, fov_gt = to_gravity_reference_frame(gt_cam, gt['gravity'])
        r_pr_g, t_pr_g, fov_pr = to_gravity_reference_frame(pred_cam, pred['gravity'])
        out['position_m'] = np.linalg.norm(t_pr_g[groups] - t_gt_g[groups], axis=-1).tolist()
        h_gt, p_gt, level_gt = heading_and_pitch_deg(r_gt_g[groups])
        h_pr, p_pr, level_pr = heading_and_pitch_deg(r_pr_g[groups])
        level = level_gt & level_pr
        out['heading_deg'] = wrap_deg(h_pr - h_gt)[level].tolist()
        out['pitch_deg'] = np.abs(p_pr - p_gt).tolist()
        decide(out['decisions'], 'camera_left_right', t_gt_g[groups, 0], t_pr_g[groups, 0])
        decide(out['decisions'], 'camera_front_back', t_gt_g[groups, 1], t_pr_g[groups, 1])
    scale = float(gt.get('trajectory_scale', 0.0))
    if 'scale' in heads and mask.any() and scale > 0:
        step = float(required(pred, 'trajectory_step_m', scene))
        if not step > 0:
            raise ValueError(f'Non-positive trajectory-step prediction for {scene}')
        out['log_scale_err'] = abs(math.log(step) - math.log(scale))
    if 'depth' in heads:
        depth_mask = np.asarray(gt['point_depth_mask'], dtype=bool)
        if depth_mask.any():
            uv, z_gt = required(gt, 'point_depth_uv', scene), required(gt, 'point_depth_gt', scene)
            z_pr = required(pred, 'point_depth', scene)
            if z_pr.shape != z_gt.shape or not np.isfinite(z_pr[depth_mask]).all() or np.any(z_pr[depth_mask] <= 0):
                raise ValueError(f'Depth predictions of {scene} are missing, non-finite or non-positive')
            anchors = gt.get('depth_anchor_frames', list(range(count)))
            if len(anchors) != len(depth_mask) or any(g < 0 or g >= count for g in anchors):
                raise ValueError('Depth anchor slots differ from pose frames')
            for d, g in enumerate(anchors):
                points = np.flatnonzero(depth_mask[d])
                if not points.size:
                    continue
                zg, zp = z_gt[d, points], z_pr[d, points]
                out['depth_abs_rel'] += (np.abs(zp - zg) / zg).tolist()
                out['depth_ratio'] += np.maximum(zp / zg, zg / zp).tolist()
                out['depth_abs_err_m'] += np.abs(zp - zg).tolist()
                i, j = np.triu_indices(points.size, k=1)
                decide(out['decisions'], 'depth_near_far', zg[i] - zg[j], zp[i] - zp[j])
                if rendered and mask[g]:
                    p_gt = unproject(uv[d, points], zg, fov_gt[g], r_gt_g[g], t_gt_g[g])
                    p_pr = unproject(uv[d, points], zp, fov_pr[g], r_pr_g[g], t_pr_g[g])
                    decide(out['decisions'], 'point_left_right', p_gt[i, 0] - p_gt[j, 0], p_pr[i, 0] - p_pr[j, 0])
                    decide(out['decisions'], 'point_front_back', p_gt[i, 1] - p_gt[j, 1], p_pr[i, 1] - p_pr[j, 1])
    return out


def decide(decisions, name, gt_delta, pred_delta, margin=DECISION_MARGIN_M):
    """Count sign agreement on pairs whose GT difference clears the margin (the cases a response can decide)."""
    gt_delta, pred_delta = np.asarray(gt_delta, dtype=np.float64), np.asarray(pred_delta, dtype=np.float64)
    clear = np.abs(gt_delta) >= margin
    hits, total = decisions.get(name, (0, 0))
    decisions[name] = (hits + int(np.sum(np.sign(gt_delta[clear]) == np.sign(pred_delta[clear]))), total + int(clear.sum()))


def summarize(scenes):
    def stats(values):
        values = np.asarray(values, dtype=np.float64)
        if not values.size:
            return None
        return {'n': int(values.size), 'median': float(np.median(values)), 'p90': float(np.percentile(values, 90)),
                'mean': float(values.mean())}

    pooled = {key: [v for s in scenes for v in s[key]] for key in
              ('rotation_deg', 'translation_m', 'position_m', 'heading_deg', 'pitch_deg', 'depth_abs_rel', 'depth_ratio',
               'depth_abs_err_m')}
    decisions = {}
    for scene in scenes:
        for name, (hits, total) in scene['decisions'].items():
            h, t = decisions.get(name, (0, 0))
            decisions[name] = (h + hits, t + total)
    hits, total = sum(h for h, _ in decisions.values()), sum(t for _, t in decisions.values())
    ratios = np.asarray(pooled['depth_ratio'], dtype=np.float64)
    return {
        'num_scenes': len(scenes),
        'rotation_deg': stats(pooled['rotation_deg']),
        'translation_m': stats(pooled['translation_m']),
        'position_m': stats(pooled['position_m']),
        'heading_deg': stats(pooled['heading_deg']),
        'pitch_deg': stats(pooled['pitch_deg']),
        'gravity_deg': stats([s['gravity_deg'] for s in scenes if s['gravity_deg'] is not None]),
        'log_scale_err': stats([s['log_scale_err'] for s in scenes if s['log_scale_err'] is not None]),
        'depth_abs_rel': float(np.mean(pooled['depth_abs_rel'])) if pooled['depth_abs_rel'] else None,
        'depth_delta125': float(np.mean(ratios < 1.25)) if ratios.size else None,
        'depth_delta125_2': float(np.mean(ratios < 1.25 ** 2)) if ratios.size else None,
        'depth_abs_err_m': stats(pooled['depth_abs_err_m']),
        'depth_points': int(ratios.size),
        'decisions': {name: {'agree': h, 'total': t, 'rate': (h / t if t else None)} for name, (h, t) in sorted(decisions.items())},
        'decision_agreement': (hits / total) if total else None,
    }


def check_gate(summary, heads, gate=GATE):
    """Each criterion of the heads present: True, False, or 'not_measured' (which fails)."""
    def at_most(stat, key, limit):
        value = stat if not isinstance(stat, dict) else stat[key]
        return 'not_measured' if value is None else bool(value <= limit)

    checks = {'rotation_deg_median': at_most(summary['rotation_deg'] and summary['rotation_deg']['median'], None, gate['rotation_deg_median_max'])}
    if 'gravity' in heads:
        checks['position_m_median'] = at_most(summary['position_m'] and summary['position_m']['median'], None, gate['position_m_median_max'])
        checks['heading_deg_median'] = at_most(summary['heading_deg'] and summary['heading_deg']['median'], None, gate['heading_deg_median_max'])
    else:
        checks['position_m_median'] = checks['heading_deg_median'] = 'not_measured'
    if 'depth' in heads:
        checks['depth_abs_rel'] = at_most(summary['depth_abs_rel'], None, gate['depth_abs_rel_max'])
        delta = summary['depth_delta125']
        checks['depth_delta125'] = 'not_measured' if delta is None else bool(delta >= gate['depth_delta125_min'])
        checks['depth_abs_err_m_median'] = at_most(summary['depth_abs_err_m'] and summary['depth_abs_err_m']['median'], None,
                                                   gate['depth_abs_err_m_median_max'])
    else:
        checks['depth_abs_rel'] = checks['depth_delta125'] = checks['depth_abs_err_m_median'] = 'not_measured'
    agreement = summary['decision_agreement']
    checks['decision_agreement'] = 'not_measured' if agreement is None else bool(agreement >= gate['decision_agreement_min'])
    return {'passed': all(value is True for value in checks.values()), 'checks': checks, 'thresholds': dict(gate)}


def check_heldout(records, heldout, training_scenes):
    """Every record's scene must be on the held-out list and absent from the training rows' scene census."""
    if not records:
        raise ValueError('The gate needs at least one held-out scene')
    heldout = {tuple(item) for item in heldout}
    training = {tuple(item) for item in training_scenes}
    if heldout & training:
        raise ValueError('The held-out list overlaps the training rows')
    seen = set()
    for record in records:
        key = (record['dataset'], record['scene'])
        if key not in heldout:
            raise ValueError(f'Scene {key} is not on the held-out list')
        if key in seen:
            raise ValueError(f'Scene {key} appears twice')
        seen.add(key)


def evaluate(records, heads, heldout, training_scenes, gate=GATE):
    """Full gate report over held-out scene records (see evaluate_scene for the record layout)."""
    heads = set(heads)
    if 'pose' not in heads or heads - {'pose', 'gravity', 'scale', 'depth'}:
        raise ValueError('Heads must include pose and be drawn from pose, gravity, scale and depth')
    check_heldout(records, heldout, training_scenes)
    scenes = [evaluate_scene(record, heads) for record in records]
    overall = summarize(scenes)
    by_dataset = {d: summarize([s for s in scenes if s['dataset'] == d]) for d in sorted({s['dataset'] for s in scenes})}
    return {'schema': SCHEMA, 'heldout_contract': 'heldout_training_scenes_only_never_benchmark', 'heads': sorted(heads),
            'overall': overall, 'by_dataset': by_dataset,
            'g3t_reference': {d: G3T_REFERENCE.get(d) for d in by_dataset},
            'g3t_reference_source': G3T_REFERENCE['source'], 'g3t_reference_definitions': G3T_REFERENCE['definitions'],
            'gate': check_gate(overall, heads, gate), 'per_scene': scenes}
