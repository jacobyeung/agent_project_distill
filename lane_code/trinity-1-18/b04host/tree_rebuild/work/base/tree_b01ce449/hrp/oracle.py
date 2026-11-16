"""Serial local-cache oracle and routed read; no model inference."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import numpy as np

from .pointing import RKIT, write
from .selector import Candidate, centroid, select
from .sources import sam_candidates
from .export import export_scene

BASE = Path('/scratch/jjyeung/orch_cd')
HEADS = BASE/'ttower/work/geo/heads_g3s64_vcd'
GT = BASE/'toolprog/work/gt/scannet'
SAM = BASE/'ttower/work/sam3/raw/heldout'
CURRENT = BASE/'mdg_next/work/out/s3zs_dev/export'
DIRECT = BASE/'evalx/work/pulled5/dd_t0m800.jsonl'


def metric(position, targets):
    if position is None or not len(targets):
        return None
    p = np.asarray(position)
    if not np.isfinite(p).all():
        return None
    return float(np.linalg.norm(targets-p, axis=1).min())


def gt_targets(centers, c2w0, geometry):
    """Align raw GT world to predicted world using only their first camera frame.

    No trajectory fit or GT scale correction. First-camera alignment accounts for
    the predicted gravity gauge, while preserving every later pose/depth error.
    """
    r, t = geometry.cam(1)
    return ((centers-c2w0[:3, 3]) @ c2w0[:3, :3]) @ r.T + t


def gt_candidates(inst, ids, matched_ids):
    candidates, areas = [], []
    for k in range(32):
        masks = [(int((inst[k] == i).sum()), int(i)) for i in matched_ids]
        if not masks:
            continue
        area, instance = max(masks, key=lambda v: (v[0], -v[1]))
        if area/inst[k].size < .002:
            continue
        mask = inst[k] == instance
        candidates.append(Candidate(k+1, centroid(mask), instance=instance, source='GT_mask_centroid'))
        areas.append(area)
    return candidates, areas


def current_frame_point(candidates, areas, geometry):
    if not candidates:
        return None
    # V311Scene.best_frame: largest mask area, then earliest viewpoint.
    i = min(range(len(candidates)), key=lambda i: (-areas[i], candidates[i].frame))
    c = candidates[i]
    P, Pc, _ = geometry.lift(c.frame, np.asarray(c.uv)[None], mode='center')
    return P[0].tolist() if np.isfinite(P).all() and Pc[0, 2] > 0 else None


def summarize(rows):
    result = {}
    conditions = sorted({r['condition'] for r in rows})
    for condition in conditions:
        group = [r for r in rows if r['condition'] == condition]
        metrics = {}
        for method in ('current', 'consensus'):
            errors = [r[method+'_error_m'] for r in group]
            successes = sum(e is not None and e <= .5 for e in errors)
            metrics[method] = dict(successes=successes, n=len(errors), within_0_5m=successes/len(errors),
                                   missing_position=sum(e is None for e in errors))
        scenes = sorted({r['scene'] for r in group})
        sums = np.array([[sum((r['consensus_error_m'] is not None and r['consensus_error_m'] <= .5)
                             -(r['current_error_m'] is not None and r['current_error_m'] <= .5)
                             for r in group if r['scene'] == scene),
                          sum(r['scene'] == scene for r in group)] for scene in scenes])
        rng = np.random.default_rng(17)
        draws = rng.integers(0, len(scenes), (4000, len(scenes)))
        boot = sums[draws].sum(axis=1)
        metrics['paired_delta_scene_bootstrap_95ci'] = np.quantile(boot[:, 0]/boot[:, 1], [.025, .975]).tolist()
        metrics['unique_pairs'] = len({(r['scene'], r['obj']) for r in group})
        metrics['unique_scenes'] = len(scenes)
        metrics['singleton'] = sum(r['selection']['status'] == 'singleton' for r in group)
        metrics['ambiguous'] = sum(r['selection']['status'] == 'ambiguous' for r in group)
        result[condition] = metrics
    return result


def run(out, heads=HEADS, gt_root=GT, sam_root=SAM, current=CURRENT, seeds=(17, 18, 19, 20, 21), radius=.5, scenes=None):
    sys.path.insert(0, str(RKIT))
    from rk import sets
    from rk.programs import load_heads, T, read_index, assert_frame_indices, assert_export_frames
    from rk.ground import MaskGround, mdg
    from rk.scheme import V311Scene
    from rk.sam3mask import tower, SAM3
    labels = sets.scene_labels('dev')
    if scenes:
        labels = {s: v for s, v in labels.items() if s in scenes}
    frozen = json.loads((SAM3/'tau_frozen.json').read_text())
    current_root, entries = read_index(current)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = dict(radius_m=radius, seeds=list(seeds), scene_count=len(labels), expected_pairs=sum(map(len, labels.values())),
                  source=dict(heads=str(heads), gt=str(gt_root), sam=str(sam_root), current=str(current)),
                  metric='distance <= 0.5m to nearest matching annotated GT OBB centroid; missing position fails',
                  alignment='GT world -> first GT camera -> first predicted gravity-aligned camera; no fitted alignment',
                  corruption='uniform pixel on round(fraction * 32) sampled frames, including absent frames',
                  gt_centroid='largest matching GT instance per frame; arithmetic 2D mask centroid',
                  gt_baseline='V311 largest-area/earliest-frame rule on equal-area centroid click proxies (earliest frame)',
                  sam_baseline='unchanged V311Scene.centroid on cached frozen-rule top-instance masks',
                  sam_candidates='all cached instances within frozen accepted frames; one vote per frame',
                  sam_frame_provenance='raw caches have slot numbers but no frame indices/pixel hashes; use current kit export mapping',
                  exclusions=[], per_scene_seconds={})
    rows = []
    indices = {name: {} for name in ('sam_selected', 'native_top_050', 'native_selected')}
    for scene, names in sorted(labels.items()):
        started = time.monotonic()
        stem = scene.replace('/', '__')
        head = Path(heads)/(stem+'.npz')
        gt_path = Path(gt_root)/(scene.split('/')[1]+'.npz')
        geo = load_heads(head)
        expected = entries[scene]['frame_indices']
        assert_frame_indices(head, expected)
        with np.load(gt_path, allow_pickle=False) as z:
            if 'frame_indices' not in z.files or not np.array_equal(z['frame_indices'], expected):
                raise ValueError('GT frame-index identity missing or different: '+scene)
            inst, ids, gt_labels = z['inst'], z['ids'], z['labels'].tolist()
            centers, c2w, valid = z['obb_centroid'], z['c2w'], z['valid']
        if not valid[0] or not np.isfinite(c2w[0]).all():
            raise ValueError('Cannot align GT first camera: '+scene)
        cache = tower().load_cache(sam_root, scene)
        if cache['checkpoint']['size'] != frozen['checkpoint']['size'] or cache['checkpoint']['mtime_ns'] != frozen['checkpoint']['mtime_ns']:
            raise ValueError('SAM checkpoint differs from its frozen threshold')
        # The pinned current export supplies the same cached SAM scene/frame provenance.
        ground = MaskGround(current_root/entries[scene]['npz'])
        assert_export_frames(current_root/entries[scene]['npz'], ground.audit, expected)
        baseline = V311Scene(geo, ground, gates=False)
        # Preserve every baseline mask and click; change only frame acceptance.
        native_values = dict(ground.values)
        native_values['prob'] = np.zeros_like(ground.values['prob'])
        for q, name in enumerate(ground.names):
            phrase = tower().phrase(name)
            if phrase not in cache['phrases']:
                continue
            for k in range(32):
                record = cache['frames'][str(k)]['phrases'][phrase]
                scores = [float(i['score']) for i in record.get('instances') or []]
                native_values['prob'][q, k] = float(bool(scores) and float(record['presence'])*max(scores) > .5)
        native_values['frame_prob'] = native_values['prob'].copy()
        native_path = out/'native_top_050'/(stem+'.npz')
        native_path.parent.mkdir(parents=True, exist_ok=True)
        mdg().save_npz(native_path, ground.names, native_values,
                       {**ground.audit, 'tau': .5, 'source': 'native joint score strictly >0.5'})
        native_baseline = V311Scene(geo, MaskGround(native_path), gates=False)
        indices['native_top_050'][scene] = dict(scene=scene, npz=native_path.name, frame_indices=expected)
        candidates_by_name, selections, native_by_name, native_selections = {}, {}, {}, {}
        for name in names:
            matches = T.match_labels(name, gt_labels)
            matched = [i for i, label in zip(ids, gt_labels) if label in matches]
            positions = gt_targets(np.asarray([c for i, c in zip(ids, centers) if i in matched]), c2w[0], geo) if matched else np.empty((0, 3))
            positions = positions[np.isfinite(positions).all(axis=1)]
            sam_points = sam_candidates(cache, name, float(frozen['tau']))
            chosen = select(sam_points, geo, radius)
            candidates_by_name[name], selections[name] = sam_points, chosen
            # Native gate applies to EACH proposal before the 3D selector.
            native_points = sam_candidates(cache, name, .5, proposal_gate=True)
            native_chosen = select(native_points, geo, radius)
            native_by_name[name], native_selections[name] = native_points, native_chosen
            if not len(positions):
                report['exclusions'].append(dict(scene=scene, obj=name, reason='no_matching_GT_centroid'))
                continue
            current_position = baseline.centroid(name)[0]
            rows.append(dict(scene=scene, obj=name, condition='sam3_instances', seed=None,
                             target_instances=len(positions), current_error_m=metric(current_position, positions),
                             consensus_error_m=metric(chosen['position'], positions), selection=chosen))
            rows.append(dict(scene=scene, obj=name, condition='sam3_native_050', seed=None,
                             target_instances=len(positions),
                             current_error_m=metric(native_baseline.centroid(name)[0], positions),
                             consensus_error_m=metric(native_chosen['position'], positions), selection=native_chosen))
            clean, areas = gt_candidates(inst, ids, matched)
            if not clean:
                report['exclusions'].append(dict(scene=scene, obj=name, reason='no_GT_visible_frame'))
                continue
            for fraction in (0., .3, .5):
                for seed in ((seeds[0],) if fraction == 0 else seeds):
                    key = hashlib.sha256(f'{scene}/{name}/{seed}/{fraction}'.encode()).digest()
                    rng = np.random.default_rng(int.from_bytes(key[:8], 'little'))
                    count = int(np.floor(32*fraction+.5))
                    bad = set(rng.choice(32, count, replace=False).tolist())
                    by_frame = {c.frame: c for c in clean}
                    points = []
                    for k in range(32):
                        if k in bad:
                            points.append(Candidate(k+1, rng.uniform(0, 1000, 2).tolist(), source='random_corruption'))
                        elif k+1 in by_frame:
                            points.append(by_frame[k+1])
                    selection = select(points, geo, radius)
                    base_position = current_frame_point(points, [1]*len(points), geo)
                    rows.append(dict(scene=scene, obj=name, condition=f'gt_corrupt_{int(fraction*100):02d}', seed=seed,
                                     target_instances=len(positions), visible_frames=len(clean), replaced_frames=count,
                                     current_error_m=metric(base_position, positions),
                                     consensus_error_m=metric(selection['position'], positions), selection=selection))
        indices['sam_selected'][scene] = export_scene(out/'sam_selected', scene, names, candidates_by_name, selections, expected,
                                    audit=dict(sam_source=str(Path(sam_root)/(stem+'.npz')), radius_m=radius))
        indices['native_selected'][scene] = export_scene(out/'native_selected', scene, names, native_by_name,
                                    native_selections, expected, audit=dict(native_joint_gate='>0.5', radius_m=radius))
        report['per_scene_seconds'][scene] = round(time.monotonic()-started, 3)
        # Journal one scene at a time. A failed pass remains inspectable without relaunching.
        with (out/'per_pair.jsonl').open('a') as f:
            for r in rows:
                if r['scene'] == scene:
                    f.write(json.dumps(r, allow_nan=False)+'\n')
        print(json.dumps(dict(scene=scene, pairs=len(names), seconds=report['per_scene_seconds'][scene])), flush=True)
    for name, index in indices.items():
        write(out/name/'INDEX.json', index)
    report['native_candidates'] = 'each cached proposal with presence * raw score strictly >0.5'
    report['bootstrap'] = dict(samples=4000, seed=17, unit='scene', weighting='item')
    report['metrics'] = summarize(rows)
    write(out/'metrics.json', report)
    return report


def routed_reads(out, heads=HEADS, current=CURRENT, direct=DIRECT, scenes=None):
    """Use the unchanged kit and the audit's exact paired score/bootstrap code."""
    sys.path.insert(0, str(RKIT))
    from rk import programs, report, sets
    out = Path(out)
    summary = {}
    for name, export in [('current', current), ('sam_selected', out/'sam_selected'),
                         ('native_top_050', out/'native_top_050'), ('native_selected', out/'native_selected')]:
        dest = out/'routed'/name
        rows = programs.run(SimpleNamespace(mdg_export=export, heads=heads, out=dest, set='dev',
                            scenes=','.join(scenes) if scenes else None, limit_per_type=None,
                            allow_gt_substitution=False, gates=False))
        result = report.make_report(rows, report.read_jsonl(direct), sets.answers('dev'), samples=4000, seed=17)
        result['input_pins'] = {str(Path(direct).resolve()): programs.sha256(direct)}
        write(dest/'REPORT.json', result)
        (dest/'REPORT.md').write_text(report.markdown(result))
        summary[name] = dict(types=result['types'], n=result['n'], bootstrap=result['bootstrap'])
    write(out/'routed_summary.json', summary)
    return summary


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--out', required=True)
    p.add_argument('--heads', type=Path, default=HEADS)
    p.add_argument('--gt-root', type=Path, default=GT)
    p.add_argument('--sam-root', type=Path, default=SAM)
    p.add_argument('--current', type=Path, default=CURRENT)
    p.add_argument('--radius', type=float, default=.5)
    p.add_argument('--scenes', help='Optional comma-separated scannet/scene keys')
    p.add_argument('--skip-routed', action='store_true')
    a = p.parse_args()
    if Path(a.out).exists():
        raise FileExistsError('Choose a fresh output directory; do not silently retry a stopped pass')
    result = run(a.out, a.heads, a.gt_root, a.sam_root, a.current, radius=a.radius,
                 scenes=a.scenes.split(',') if a.scenes else None)
    print(json.dumps(result['metrics'], indent=2))
    if not a.skip_routed:
        routed_reads(a.out, a.heads, a.current, scenes=a.scenes.split(',') if a.scenes else None)


if __name__ == '__main__':
    main()
