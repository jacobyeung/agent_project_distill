"""CPU diagnostics with a persisted amendment gate before the registered read."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import devpose as d
import argparse
import copy
import datetime
import json
import time
import numpy as np
from scipy.optimize import lsq_linear
from scipy.stats import rankdata

MODES = ('raw', 'rescaled')
DATASETS = ('all', 'ARKit', 'ScanNet/ScanNet++')


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def rigid_map(gt_camera, served_camera, factor=1.):
    """Use the nearest proper rotation to the stored relative camera rotation.

    GT c2w rotations have small serialization/estimation orthogonality errors.
    The polar projection makes the requested transport a rigid body operation;
    it neither fits scene alignment nor changes served metric translation scale.
    """
    g, s = np.asarray(gt_camera, float), np.asarray(served_camera, float)
    raw = s[:3, :3] @ g[:3, :3].T
    u, _, vt = np.linalg.svd(raw)
    rotation = u @ np.diag([1., 1., np.linalg.det(u @ vt)]) @ vt
    return rotation, factor*s[:3, 3] - rotation@g[:3, 3]


def rigid_box(box, rotation, offset):
    return dict(centre=np.asarray(box['centre'])@rotation.T+offset,
                axes=np.asarray(box['axes'])@rotation.T,
                lengths=np.asarray(box['lengths']).copy())


def original_box(box):
    # Keep the original OBB axes and lengths; this function performs no refit.
    return dict(centre=np.asarray(box['center'], float),
                axes=np.asarray(box['axes'], float),
                lengths=np.asarray(box['full_lengths'], float))


def exact_gap(a, b):
    """Closest points in two closed OBBs, as a bounded convex least square.

    Minimize ||ca + Aa ua - cb - Ab ub|| with each local coordinate in [-1,1].
    BVLS solves this convex problem, including touching/intersecting boxes.
    Round residuals <= 1e-9 m to contact, before the scorer's exact-zero branch.
    This tolerance is fixed independently of the real diagnostic results.
    """
    matrix = np.column_stack((np.asarray(a['axes']).T*(a['lengths']/2),
                              -np.asarray(b['axes']).T*(b['lengths']/2)))
    delta = b['centre']-a['centre']
    answer = lsq_linear(matrix, delta, bounds=(-1., 1.), method='bvls',
                        tol=1e-13, max_iter=10000)
    if not answer.success or answer.optimality > 1e-8:
        raise ArithmeticError(f'Closest-point solver did not converge: {answer.message}')
    value = float(np.linalg.norm(matrix@answer.x-delta))
    return 0. if value <= 1e-9 else value


def up_to_z(up):
    """Shortest proper rotation sending the transported GT up vector to +z."""
    up = np.asarray(up, float); up = up/np.linalg.norm(up)
    z = np.array([0., 0., 1.])
    v = np.cross(up, z); cosine = float(up@z)
    if np.linalg.norm(v) < 1e-12:
        return np.eye(3) if cosine > 0 else np.diag([1., -1., -1.])
    skew = np.array([[0., -v[2], v[1]], [v[2], 0., -v[0]], [-v[1], v[0], 0.]])
    return np.eye(3)+skew+skew@skew/(1+cosine)


def gravity_refit(gt_box, rotation, offset):
    """Refit with the anchor's GT up, then restore common served coordinates."""
    points = d.corners(gt_box)@rotation.T+offset
    turn = up_to_z(rotation@np.array([0., 0., 1.]))
    fitted = d.refit(points@turn.T)
    return rigid_box(fitted, turn.T, np.zeros(3))


def metadata(row):
    return {k: copy.deepcopy(v) for k, v in row.items()
            if k in ('item_id', 'capture', 'room', 'dataset_group', 'instance_ids',
                     'labels', 'anchors', 'pair_class', 'names', 'operands',
                     'label_m', 'L0_gap_m', 'exclusion', 'printed_anchors')}


def flattened(rows, mode):
    return [metadata(r) | r['modes'][mode] for r in rows]


def diagnostic_summary(boot, rows, keys):
    return {mode: d.cells(boot, flattened(rows, mode), keys) for mode in MODES}


def metric(cells, dataset='all', pair='same', key='label_free_term'):
    return next(c for c in cells if c['dataset'] == dataset and c['pair_class'] == pair)['metrics'][key]


def correlation(rows, xkey, ykey):
    if len(rows) < 3:
        return None
    x, y = (np.array([r[k] for r in rows], float) for k in (xkey, ykey))
    if np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def correlation_interval(boot, rows, xkey, ykey):
    totals = np.zeros((len(boot.rooms), 6))
    for row in rows:
        x, y = row[xkey], row[ykey]
        totals[boot.lookup[row['room']]] += [1, x, y, x*x, y*y, x*y]
    n, sx, sy, sxx, syy, sxy = (boot.draws@totals).T
    denominator = np.sqrt(np.maximum(n*sxx-sx*sx, 0)*np.maximum(n*syy-sy*sy, 0))
    values = np.divide(n*sxy-sx*sy, denominator, out=np.full(10000, np.nan),
                       where=(n >= 3) & (denominator > 1e-12))
    return boot.summarize(correlation(rows, xkey, ykey), values)


def gravity_report(records, base, cameras, boot):
    captures, groups = [], {}
    for cap, (gt, served, gravity) in cameras.items():
        angles = []
        for g, s in zip(gt, served):
            # Directly use the captured camera table for this report-only angle.
            up = s[:3, :3] @ np.linalg.solve(g[:3, :3], [0., 0., 1.])
            cosine = up@gravity/(np.linalg.norm(up)*np.linalg.norm(gravity))
            angles.append(float(np.degrees(np.arccos(np.clip(cosine, -1, 1)))))
        captures.append(dict(capture=cap, dataset_group='ARKit' if cap.startswith('arkitscenes/') else 'ScanNet/ScanNet++',
                             anchor_angles_deg=angles, median_gravity_error_deg=float(np.median(angles))))
    by_capture = {r['capture']: r for r in captures}
    items = {r['item_id']: r for r in base['items']}
    occurrences = []
    for obj in base['objects']:
        if obj['capture'] not in by_capture:
            continue
        item = items[obj['item_id']]
        operand = next(o for o in item['operands'] if o['name'] == obj['name'])
        r = copy.deepcopy(obj)
        r.update(instance_id=operand['instance_id'], dataset_group=item['dataset_group'],
                 gravity_error_deg=by_capture[obj['capture']]['median_gravity_error_deg'])
        occurrences.append(r)
        if r['printed_longest_m'] is not None and r['GT_longest_m'] is not None and r['GT_longest_m'] > 0:
            groups.setdefault((r['capture'], r['instance_id']), []).append(r)
    objects = []
    for (cap, iid), rr in groups.items():
        assert len({r['GT_longest_m'] for r in rr}) == 1
        printed = float(np.median([r['printed_longest_m'] for r in rr]))
        obj = dict(capture=cap, room=rr[0]['room'], instance_id=iid,
                   dataset_group=rr[0]['dataset_group'], gravity_error_deg=rr[0]['gravity_error_deg'],
                   printed_longest_m=printed, GT_longest_m=rr[0]['GT_longest_m'],
                   ratio=printed/rr[0]['GT_longest_m'], occurrences=len(rr),
                   stages=sorted({r['stage'] for r in rr}), occurrence_keys=[r['key'] for r in rr])
        objects.append(obj)
    summaries = []
    for dataset in DATASETS:
        rr = [r for r in objects if dataset == 'all' or r['dataset_group'] == dataset]
        cc = [r for r in captures if dataset == 'all' or r['dataset_group'] == dataset]
        oo = [r for r in occurrences if (dataset == 'all' or r['dataset_group'] == dataset) and r['ratio'] is not None]
        summary = dict(dataset=dataset, objects=len(rr), occurrences=len(oo), captures=len(cc),
                       median_capture_gravity_deg=float(np.median([r['median_gravity_error_deg'] for r in cc])),
                       median_printed_longest_m=float(np.median([r['printed_longest_m'] for r in rr])),
                       median_GT_longest_m=float(np.median([r['GT_longest_m'] for r in rr])),
                       median_ratio=float(np.median([r['ratio'] for r in rr])),
                       gravity_vs_ratio=correlation_interval(boot, rr, 'gravity_error_deg', 'ratio'),
                       printed_vs_GT=correlation_interval(boot, rr, 'printed_longest_m', 'GT_longest_m'),
                       occurrence_gravity_vs_ratio=correlation_interval(boot, oo, 'gravity_error_deg', 'ratio'))
        ranked = [dict(x=float(x), y=float(y)) for x, y in zip(
            rankdata([r['gravity_error_deg'] for r in rr]), rankdata([r['ratio'] for r in rr]))]
        summary['gravity_vs_ratio_spearman'] = correlation(ranked, 'x', 'y')
        summaries.append(summary)
    for c in captures:
        c['objects'] = [o for o in objects if o['capture'] == c['capture']]
    return dict(captures=captures, objects=objects, occurrences=occurrences, summaries=summaries,
                definition='Angle between captured served up and S_R inverse(G_R) GT +z; median of all 32 anchors per capture. '
                'Unique object=(capture,GT instance); repeated printed longest sides aggregate by median. '
                'Primary correlation is Pearson(gravity error,printed/GT longest-side ratio), with paired room bootstrap. '
                'Printed-vs-GT correlation, Spearman, and occurrence-weighted correlation are also reported.')


def registered_read(lc, ac, ww):
    """Apply the registered ordering; a parity stop prevents later conditions."""
    same = metric(lc, key='pose_term')['mean']
    close = metric(lc, pair='all', key='L2_within_10pct')['mean']
    parity = same is not None and abs(same) <= .5 and close is not None and close >= .95
    lines = [f'1. Parity: {"PASS" if parity else "STOP"}; same-anchor signed term {same:.6f}; L2 within 10% on {100*close:.2f}% of items.']
    if not parity:
        lines += ['2. Pose binds on dev: NOT EVALUATED (parity stop).',
                  '3. Pose costs no distance: NOT EVALUATED (parity stop).',
                  '4. Reopen dense ARKit tower work: NOT EVALUATED (parity stop).']
        return dict(parity_pass=False, lines=lines, conditions=None)
    w = ww[0]['weighted_term']; contrast = ww[0]['ladder_different_minus_same']
    arkit = next(r for r in ww if r['dataset'] == 'ARKit')['weighted_term']
    bind = contrast['mean'] >= 10 and contrast['ci95'][0] > 0 and w['mean'] >= 5
    no_cost = w['mean'] <= 2
    reopen = arkit['mean'] >= 10 and arkit['ci95'][0] > 0
    lines += [f'2. Pose binds on dev: {"YES" if bind else "NO"}.',
              f'3. Pose costs no distance: {"YES" if no_cost else "NO"}.',
              f'4. Reopen dense ARKit tower work: {"YES" if reopen else "NO"}.']
    return dict(parity_pass=True, lines=lines,
                conditions=dict(pose_binds=bool(bind), no_cost=bool(no_cost), ARKit_reopens=bool(reopen)))


def make_report(result):
    lines = ['# DEV-POSE round 2', '',
             f"Diagnostic (i): exact OBB closest-point gap with rigid transport and no refit; {len(result['diagnostic_i']['pairs'])} same-anchor audit pairs."]
    for mode in MODES:
        v = metric(result['diagnostic_i']['cells'][mode])
        lines.append(f"{mode}: same-anchor audit loss {d.fmt(v)}; maximum gap discrepancy {result['diagnostic_i']['max_abs_gap_error_m'][mode]:.3g} m.")
    if result['diagnostic_ii'] is not None:
        lines += ['', 'Diagnostic (ii): map GT up through each operand anchor, rotate to z-up, use the reader refit, return to the common served world, and use the reader gap.']
        for mode in MODES:
            v = metric(result['diagnostic_ii']['audit_cells'][mode])
            ll = metric(result['diagnostic_ii']['ladder_cells'][mode], key='pose_term')
            free = metric(result['diagnostic_ii']['ladder_cells'][mode])
            lines.append(f'{mode}: same-anchor audit loss {d.fmt(v)}; ladder signed term {d.fmt(ll)}; ladder label-free loss {d.fmt(free)} (n=1).')
        one = result['diagnostic_ii']['items'][0]
        lines.append(f"Single ladder item: {one['item_id']}, {one['capture']}, anchors {one['anchors']}; GT visibility requires one fallback; L2={one['L2_gap_m']:.9f} m, raw L1={one['modes']['raw']['L1_gap_m']:.9f} m, rescaled L1={one['modes']['rescaled']['L1_gap_m']:.9f} m.")
    lines += ['', 'Amendment gate: '+('PASS.' if result['gate']['pass'] else 'FAIL; STOP. No round-2 verdict was computed or read.'),
              'Gate requires diagnostic (i) audit loss <=0.5 and diagnostic (ii) audit loss <=0.5 plus the single ladder signed/label-free losses <=0.5, in both modes.']
    if result['amendment']:
        lines += [f"AMENDMENT.md was written at {result['amendment']['utc']}, before any round-2 verdict computation/read; amended L1 is diagnostic (ii).", '']
        for mode in MODES:
            lines += [mode+': '+line for line in result['statistics'][mode]['verdicts']['lines']]
        lines += ['', '| Mode | Dataset | Ladder same/diff signed term | Audit same/diff loss | Weighted audit loss |',
                  '| --- | --- | --- | --- | --- |']
        for mode in MODES:
            stat = result['statistics'][mode]
            for ds in DATASETS:
                ls = metric(stat['ladder_cells'], ds, 'same', 'pose_term')
                ld = metric(stat['ladder_cells'], ds, 'different', 'pose_term')
                aa = metric(stat['audit_cells'], ds, 'same'); ab = metric(stat['audit_cells'], ds, 'different')
                w = next(r for r in stat['weighted'] if r['dataset'] == ds)['weighted_term']
                lines += [f'| {mode} | {ds} | {d.fmt(ls)} / {d.fmt(ld)} | {d.fmt(aa)} / {d.fmt(ab)} | {d.fmt(w)} |']
    if result.get('failure_location'):
        lines += ['', result['failure_location']]
    lines += ['', '| Dataset | Captures / objects | Gravity error median (deg) | Printed / GT longest-side medians (m) | Median side ratio | Gravity vs ratio Pearson r [95% CI] | Printed vs GT r |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for s in result['gravity']['summaries']:
        if s['dataset'] == 'all':
            continue
        lines += [f"| {s['dataset']} | {s['captures']} / {s['objects']} | {s['median_capture_gravity_deg']:.2f} | {s['median_printed_longest_m']:.3f} / {s['median_GT_longest_m']:.3f} | {s['median_ratio']:.3f} | {d.fmt(s['gravity_vs_ratio'])} | {s['printed_vs_GT']['mean']:.3f} |"]
    lines += ['Gravity is report-only: each capture uses the median of all 32 anchor angles; JSON lists all capture angles and object-side pairs. Objects deduplicate by capture and GT instance; repeated printed sides use their median.',
              'All intervals use 10,000 paired room-bootstrap draws over 46 manifest rooms, seed 20261120; undefined draws are counted and omitted. A one-item interval is degenerate when defined.',
              f"Stored camera rotations are projected to their nearest proper relative rotation for rigid transport; maximum entry correction {result['rotation_validation']['max_relative_projection_entry_change']:.3g}. Exact gaps <=1e-9 m count as contact.",
              f"Population: {result['counts']['ladder_items']} ladder items (1 same, 65 different), 38 audit captures, {result['counts']['audit_pairs']} audit pairs. Six of the expected 72 items lack a second binding; 74 additional items lack a GT capture.",
              'The reader refit and 5 cm grid-gap functions are imported unchanged. Scale sensitivity changes served camera translations only. Tests and source/input hashes accompany DEVPOSE2.json.']
    assert len(lines) <= 60, len(lines)
    return '\n'.join(lines)+'\n'


def run(args):
    start = time.monotonic()
    if any((HERE/p).exists() for p in ('DEVPOSE2.json', 'AMENDMENT.md')):
        raise FileExistsError('A round-2 result or amendment already exists; refusing another read.')
    d.dependencies(args.gbuild)
    pins = {}
    base = d.read(args.base_result, pins)
    original_out_hashes = {str(p): d.sha(p) for p in sorted(args.base_result.parent.iterdir()) if p.is_file()}
    refs = {r['item_id']: r for r in d.read(args.manifest, pins)['items']}
    records, receipt = d.load_capture(args, refs)
    pins[str(args.capture)] = receipt['raw_sha256']
    boot = d.Bootstrap(refs)
    cameras, instances = {}, {}
    validation = dict(max_relative_projection_entry_change=0., captures=[])
    for inventory in base['GT_inventory']:
        cap = inventory['capture']
        filename = cap.split('/')[1]+'.npz' if cap.startswith('arkitscenes/') else cap.replace('/', '__')+'.npz'
        path = next(p/filename for p in args.gt_dirs if (p/filename).is_file())
        pins[str(path)] = d.sha(path)
        assert pins[str(path)] == base['input_sha256'][str(path)]
        with np.load(path, allow_pickle=False) as z:
            gt, frames = z['c2w'].astype(float), z['frame_indices'].tolist()
        geometries = [r['geometry'] for r in records.values() if r['capture'] == cap]
        assert all(g == geometries[0] for g in geometries)
        geometry = geometries[0]
        assert geometry['source_indices'] == frames
        served = np.array(geometry['camera_to_world_metric'], float)
        assert np.allclose(np.array(geometry['camera_to_world_unscaled'])[:, :3, 3]*geometry['scale'], served[:, :3, 3])
        cameras[cap] = (gt, served, np.array(geometry['gravity_up'], float))
        instances[cap] = {r['instance_id']: r for r in inventory['instances']}
        err = max(float(np.max(np.abs(rigid_map(g, s)[0]-s[:3, :3]@g[:3, :3].T))) for g, s in zip(gt, served))
        validation['max_relative_projection_entry_change'] = max(validation['max_relative_projection_entry_change'], err)
        validation['captures'].append(dict(capture=cap, max_relative_projection_entry_change=err,
            GT_max_orthogonality_error=float(np.max(np.abs(gt[:, :3, :3]@gt[:, :3, :3].transpose(0, 2, 1)-np.eye(3))))))
    for path, expected in base['input_sha256'].items():
        if path not in pins:
            pins[path] = d.sha(path)
        assert pins[path] == expected, f'Round-1 input changed: {path}'
    print('Authenticated T1, round-1 input pins, and all 38 GT camera tables.', flush=True)

    def transform(cap, anchor, mode):
        gt, served, _ = cameras[cap]
        factor = 1. if mode == 'raw' else base['similarity_fits'][cap]['factor']
        return rigid_map(gt[anchor-1], served[anchor-1], factor)

    same_pairs = [r for r in base['pairs'] if r['pair_class'] == 'same']
    rigid_rows = []
    for row in same_pairs:
        cap = row['capture']; originals = [original_box(instances[cap][i]['box']) for i in row['instance_ids']]
        l2 = exact_gap(*originals)
        out = metadata(row) | dict(L2_gap_m=l2, modes={})
        for mode in MODES:
            l1 = exact_gap(*[rigid_box(b, *transform(cap, anchor, mode)) for b, anchor in zip(originals, row['anchors'])])
            out['modes'][mode] = dict(L1_gap_m=l1, label_free_term=100-d.score(l1, l2), abs_gap_error_m=abs(l1-l2))
        rigid_rows.append(out)
    rigid_cells = diagnostic_summary(boot, rigid_rows, ('label_free_term', 'abs_gap_error_m'))
    rigid_pass = all(metric(rigid_cells[mode])['mean'] <= .5 for mode in MODES)
    result = dict(schema='DEVPOSE2-v1', started_utc=utc(), counts=base['counts'],
                  diagnostic_i=dict(pairs=rigid_rows, cells=rigid_cells,
                    max_abs_gap_error_m={m: max(r['modes'][m]['abs_gap_error_m'] for r in rigid_rows) for m in MODES}),
                  diagnostic_ii=None, gate=dict(pass_i=rigid_pass, pass_ii=None, **{'pass': False}),
                  amendment=None, verdict_read_count=0, statistics=None,
                  rotation_validation=validation, similarity_fits=base['similarity_fits'],
                  bootstrap=base['bootstrap'], validation=dict(capture=receipt), input_sha256=pins,
                  definitions=dict(diagnostic_i='Exact closed-OBB gap; original GT boxes rigidly carried without refitting; <=1e-9 m is contact.',
                    diagnostic_ii='Shortest rotation from each anchor-mapped GT +z to +z; imported reader refit on eight transported GT corners; inverse rotation restores common served coordinates; imported reader grid gap.',
                    L2='Unchanged round-1 reader gap on reader-refitted GT corners.',
                    camera_rotation='Nearest SO(3) projection of served_R times GT_R transpose; offset=served_translation*factor-R*GT_translation.',
                    amendment_gate='Both raw and rescaled: diagnostic (i) audit loss <=0.5; diagnostic (ii) audit loss <=0.5 and abs(single ladder signed term), ladder label-free loss <=0.5.',
                    verdict_read='Exactly one registered reading, reporting raw and rescaled cells; no registered condition evaluated before amendment.'))
    print('Diagnostic (i): '+json.dumps({m: metric(rigid_cells[m]) for m in MODES}), flush=True)
    cache = {}

    def fit(cap, iid, anchor, mode):
        key = (cap, iid, anchor, mode)
        if key not in cache:
            cache[key] = gravity_refit(instances[cap][iid]['box'], *transform(cap, anchor, mode))
        return cache[key]

    def measure(row, ladder=False):
        out = metadata(row)
        if ladder:
            out['anchors'] = [o['anchor'] for o in row['operands']]
            out['instance_ids'] = [o['instance_id'] for o in row['operands']]
        cap = row['capture']; l2 = row['L2_gap_m']
        out.update(L2_gap_m=l2, modes={})
        for mode in MODES:
            l1 = d.gap(*[fit(cap, iid, a, mode) for iid, a in zip(out['instance_ids'], out['anchors'])])
            m = d.metrics_row(row['L0_gap_m'], l1, l2, row['label_m']) if ladder else dict(label_free_term=100-d.score(l1, l2))
            out['modes'][mode] = m | dict(L1_gap_m=l1)
        return out

    if rigid_pass:
        ii_pairs = [measure(r) for r in same_pairs]
        ii_items = [measure(r, True) for r in base['items'] if r.get('pair_class') == 'same']
        ac = diagnostic_summary(boot, ii_pairs, ('label_free_term',))
        lc = diagnostic_summary(boot, ii_items, ('pose_term', 'label_free_term'))
        ii_pass = all(metric(ac[m])['mean'] <= .5 and abs(metric(lc[m], key='pose_term')['mean']) <= .5
                      and metric(lc[m])['mean'] <= .5 for m in MODES)
        result['diagnostic_ii'] = dict(pairs=ii_pairs, items=ii_items, audit_cells=ac, ladder_cells=lc)
        result['gate'].update(pass_ii=ii_pass, **{'pass': ii_pass})
        print('Diagnostic (ii): '+json.dumps({m: dict(audit=metric(ac[m]), ladder_signed=metric(lc[m], key='pose_term'), ladder_free=metric(lc[m])) for m in MODES}), flush=True)
        write_json(HERE/'DIAGNOSTICS.json', dict(diagnostic_i=result['diagnostic_i'], diagnostic_ii=result['diagnostic_ii'], gate=result['gate']))

    if result['gate']['pass']:
        stamp = utc()
        text = (f'# DEV-POSE round-2 amendment\n\nUTC: {stamp}\n\n'
                'No round-2 verdict had been read or computed when this amendment was written.\n\n'
                'The amended L1 is diagnostic (ii): carry each GT box through its selected anchor into the served world, '
                'map GT +z through that anchor, rotate those served coordinates so that mapped up becomes +z, '
                'refit with the imported reader function, rotate the fitted OBB back to the common served world, '
                'and use the imported reader gap. Each operand uses its own anchor.\n\n'
                'The rigid transform uses the nearest proper relative camera rotation to remove stored rotation '
                'orthogonality error. Raw translations and the registered translation-scale sensitivity both remain. '
                'L2, labels, eligibility, anchors, room bootstrap, and the four registered verdict rules remain fixed.\n\n'
                'Both modes passed the two same-anchor diagnostics before this amendment. '
                'The registered reading follows once, reporting both modes.\n')
        with (HERE/'AMENDMENT.md').open('x') as f:
            f.write(text); f.flush(); d.os.fsync(f.fileno())
        result['amendment'] = dict(utc=stamp, path=str(HERE/'AMENDMENT.md'), sha256=d.sha(HERE/'AMENDMENT.md'))
        print('Gate PASS; amendment persisted. Starting amended measurements for the single registered read.', flush=True)
        known_pairs = {(r['capture'], *r['instance_ids']): r for r in ii_pairs}
        known_items = {r['item_id']: r for r in ii_items}
        items = [known_items[r['item_id']] if r['item_id'] in known_items else measure(r, True)
                 for r in base['items'] if 'exclusion' not in r]
        pairs = []
        for j, row in enumerate(base['pairs']):
            key = (row['capture'], *row['instance_ids'])
            pairs.append(known_pairs[key] if key in known_pairs else measure(row))
            if (j+1) % 2000 == 0:
                print(f'Amended audit: {j+1}/{len(base["pairs"])} pairs.', flush=True)
        result.update(items=items, pairs=pairs, statistics={})
        # This is the only registered reading, after all geometry is fixed.
        result['verdict_read_utc'] = utc()
        for mode in MODES:
            ll, aa = flattened(items, mode), flattened(pairs, mode)
            lc = d.cells(boot, ll, ('L0_score', 'L1_score', 'L2_score', 'pose_term', 'label_free_term', 'L2_within_10pct'))
            ac = d.cells(boot, aa, ('label_free_term',))
            ww = [d.weighted(boot, ll, aa, dataset) for dataset in DATASETS]
            result['statistics'][mode] = dict(ladder_cells=lc, audit_cells=ac, weighted=ww,
                                               verdicts=registered_read(lc, ac, ww))
        result['verdict_read_count'] = 1
    elif not rigid_pass:
        bad = [r for r in rigid_rows if r['modes']['raw']['label_free_term'] > .5]
        result['failure_location'] = 'Rigid diagnostic failed before any refit; failing pair records isolate camera transport or exact-gap scoring: '+str(len(bad))+' raw failures. Diagnostic (ii) and verdicts were not run.'
    else:
        bad = [r for r in result['diagnostic_ii']['pairs'] if r['modes']['raw']['label_free_term'] > .5]
        result['failure_location'] = 'The rigid diagnostic passed, but the gravity-aware reader refit/grid failed parity on '+str(len(bad))+' raw same-anchor audit pairs; these pairs are retained in diagnostic_ii. No amendment or verdict read occurred.'
    result['gravity'] = gravity_report(records, base, cameras, boot)
    for path in (HERE/'devpose2.py', HERE/'test_devpose2.py'):
        pins[str(path)] = d.sha(path)
    assert all(d.sha(path) == expected for path, expected in original_out_hashes.items())
    result['validation']['round1_outputs_unchanged'] = original_out_hashes
    result['completed_utc'] = utc(); result['runtime_seconds'] = time.monotonic()-start
    write_json(HERE/'DEVPOSE2.json', result)
    with (HERE/'REPORT_R3B.md').open('x') as f:
        f.write(make_report(result))
    paths = [p for p in sorted(HERE.iterdir()) if p.is_file() and p.name not in ('SHA256SUMS', 'RUN.log')]
    with (HERE/'SHA256SUMS').open('x') as f:
        f.writelines(f'{d.sha(p)}  {p.name}\n' for p in paths)
    print(json.dumps(dict(gate=result['gate'], verdict_read_count=result['verdict_read_count'],
          verdicts=None if result['statistics'] is None else {m: result['statistics'][m]['verdicts']['lines'] for m in MODES},
          runtime_seconds=result['runtime_seconds']), indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-result', type=Path, default=HERE.parent/'out/DEVPOSE.json')
    options, rest = parser.parse_known_args()
    args = d.arguments(rest); args.base_result = options.base_result
    run(args)
