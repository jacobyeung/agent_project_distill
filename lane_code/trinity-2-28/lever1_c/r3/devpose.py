"""CPU-only, saved-input per-anchor box transport and room-clustered distance audit."""
import os
for _key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
import hashlib
import importlib
import itertools
import json
from pathlib import Path
import re
import sys
import time
from collections import Counter, defaultdict, OrderedDict
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = Path('/scratch/jjyeung/orch_n30/cont_ops24_c')
T1_SHA = 'fe9f10b875283b02e3c376b69c3601a4086312ac56ba77fbebedce4eb21e51b7'
SIGNS = np.array(list(itertools.product((-.5, .5), repeat=3)))
_GRID_CACHE, _TREE_CACHE = OrderedDict(), OrderedDict()
_CACHE_BYTES = {'grid': 0, 'tree': 0}


def arguments(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gbuild', type=Path, default=BASE/'gbuild')
    p.add_argument('--capture', type=Path, default=BASE/'cap/t1.gz')
    p.add_argument('--capture-sha256', default=T1_SHA)
    p.add_argument('--join', type=Path, default=BASE/'cap/score_t1/JOIN_T1.jsonl')
    p.add_argument('--funnel', type=Path, default=BASE/'cap/score_t1/FUNNEL_T1.json')
    p.add_argument('--camera-split', type=Path, default=BASE/'cap/score_t1/CAMERA_SPLIT.json')
    p.add_argument('--gt-dirs', type=Path, nargs='+', default=[BASE/'gt/t1_gt/gt', BASE/'gt/arkit_gt/gt'])
    p.add_argument('--manifest', type=Path, default=BASE/'gbuild/kit2/kit/rerun2/items544.json')
    p.add_argument('--out', type=Path, default=HERE/'out')
    return p.parse_args(argv)


def dependencies(gbuild):
    sys.path[:0] = [str(gbuild), str(gbuild/'work/payload/tree'), str(gbuild/'work/payload/b')]
    global boxes, fit_box, official_mra, unit_factor, names, name_key, full_box, mask_floor, Records, Bootstrap
    global spatial, original_tree, original_grid
    boxes = importlib.import_module('trace_format.box_v313')
    fit_box = importlib.import_module('e2e_reader.grounding').min_area_box
    scorer = importlib.import_module('gpkg.score_ceiling')
    official_mra, unit_factor, name_key = scorer.official_mra, scorer.unit_factor, scorer.name_key
    names = importlib.import_module('gt.adapter').names
    full_box = importlib.import_module('gt.v2').full_box
    mask_floor = importlib.import_module('trace_format.instance_policy314').mask_floor
    Records = importlib.import_module('gpkg.capture_io').Records
    Bootstrap = importlib.import_module('round7_common').Bootstrap
    spatial = importlib.import_module('scipy.spatial')
    original_tree, original_grid = spatial.cKDTree, boxes.grid_points


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path, pins):
    pins[str(path)] = sha(path)
    return json.loads(Path(path).read_text())


def corners(box):
    return (SIGNS*np.asarray(box['full_lengths'])) @ np.asarray(box['axes']) + box['center']


def refit(points):
    b = fit_box(points)
    return boxes.box(b['centroid'], b['axesLengths'], b['normalizedAxes'])


def transport(points, gt_camera, served_camera, translation_factor=1.):
    """GT metric points -> GT camera -> served metric world; scale translations only.

    camera_to_world_metric already contains the served scale. GT camera points are
    metric, so applying the depth/pose scale to them again would change GT object size.
    """
    g, s = np.asarray(gt_camera), np.asarray(served_camera)
    pc = (points-g[:3, 3]) @ g[:3, :3]
    return pc @ s[:3, :3].T + translation_factor*s[:3, 3]


def similarity(served, gt):
    x, y = np.asarray(served)[:, :3, 3], np.asarray(gt)[:, :3, 3]
    xc, yc = x-x.mean(0), y-y.mean(0)
    u, sv, vt = np.linalg.svd(xc.T@yc)
    d = np.diag([1., 1., np.linalg.det(vt.T@u.T)])
    rotation = vt.T@d@u.T
    denominator = float((xc*xc).sum())
    factor = float(np.sum(sv*np.diag(d))/denominator) if denominator else None
    if factor is None or factor <= 0:
        raise ValueError('Similarity scale is undefined or nonpositive')
    offset = y.mean(0)-factor*rotation@x.mean(0)
    residual = np.linalg.norm(factor*x@rotation.T+offset-y, axis=1)
    return dict(factor=factor, rotation=rotation.tolist(), offset=offset.tolist(),
                residual_m=residual.tolist(), rms_m=float(np.sqrt(np.mean(residual**2))),
                center_rank=int(np.linalg.matrix_rank(xc)), anchors=len(x),
                application='Only factor multiplies served metric camera translations; fit rotation/offset are diagnostic.')


def cache_value(cache, kind, key, make, cost, budget):
    if key in cache:
        value, size = cache.pop(key)
        cache[key] = (value, size)
        return value
    value = make()
    size = cost(value)
    while cache and _CACHE_BYTES[kind]+size > budget:
        _, (_, old_size) = cache.popitem(last=False)
        _CACHE_BYTES[kind] -= old_size
    if size <= budget:
        cache[key] = (value, size)
        _CACHE_BYTES[kind] += size
    return value


def cached_grid(value, step=.05):
    arrays = [np.asarray(value[k], dtype=np.float64) for k in ('centre', 'lengths', 'axes')]
    key = (float(step), *((p.shape, p.tobytes()) for p in arrays))
    return cache_value(_GRID_CACHE, 'grid', key, lambda: original_grid(value, step),
                       lambda p: p.nbytes, 512*1024**2)


class ExactMinimumTree:
    """Reuse SciPy's exact query, with a witnessed upper bound for a minimum.

    A seed subset supplies an attained distance U. Querying every point with an
    upper bound immediately above U finds every possible better distance. We
    retain the seed witness explicitly, including when U=0. This preserves the
    minimum consumed by box_grid_5cm; other returned entries may be infinite.
    """
    def __init__(self, points):
        # Keep the input alive as well as the tree, so its identity cannot be
        # recycled even if SciPy makes a data copy.
        def make():
            indices = np.linspace(0, len(points)-1, min(512, len(points)), dtype=np.int64)
            return points, original_tree(points), original_tree(points[indices]), indices
        entry = cache_value(_TREE_CACHE, 'tree', id(points), make,
                            lambda v: v[0].nbytes+v[1].data.nbytes+72*v[1].size+v[2].data.nbytes+72*v[2].size,
                            1024*1024**2)
        self.tree, self.coarse, self.coarse_indices = entry[1:]

    def query(self, points, workers=1):
        if max(len(points), len(self.tree.data)) < 4096:
            return self.tree.query(points, workers=workers)
        seed = np.linspace(0, len(points)-1, min(256, len(points)), dtype=np.int64)
        # Both coarse clouds are subsets of the exact reader grids. Their
        # closest pair is an attained upper bound, without an unbounded search
        # against a huge hollow grid. Refine that witness on the full tree.
        distances, indices = self.coarse.query(points[seed], workers=workers)
        j = int(np.argmin(distances)); upper = float(distances[j])
        witness_b, witness_a = int(seed[j]), int(self.coarse_indices[indices[j]])
        refined, refined_indices = self.tree.query(points[seed], workers=workers,
            distance_upper_bound=np.nextafter(upper, np.inf))
        jj = int(np.argmin(refined))
        if refined[jj] < upper:
            upper = float(refined[jj]); witness_b, witness_a = int(seed[jj]), int(refined_indices[jj])
        full_distances, full_indices = self.tree.query(points, workers=workers,
            distance_upper_bound=np.nextafter(upper, np.inf))
        # The witness protects zero and strict-bound equality cases.
        if upper < full_distances[witness_b]:
            full_distances[witness_b], full_indices[witness_b] = upper, witness_a
        return full_distances, full_indices


def gap(a, b):
    # The imported reader formula runs unchanged. These temporary adapters cache
    # its exact samples/trees and bound its exact nearest-neighbour searches.
    old_grid, old_tree = boxes.grid_points, spatial.cKDTree
    boxes.grid_points, spatial.cKDTree = cached_grid, ExactMinimumTree
    try:
        return boxes.box_grid_5cm(a, b)
    finally:
        boxes.grid_points, spatial.cKDTree = old_grid, old_tree


def score(pred, target):
    return 100*official_mra(pred, target)


def load_capture(args, refs):
    rec = Records(args.capture, {'sha256': args.capture_sha256})
    result = {}
    for row in rec:
        if row.get('excluded') or row.get('pass_index', 0) != 0:
            continue
        key = row['item_id']
        assert key not in result and key in refs
        assert row['capture'] == refs[key]['capture']
        assert row['source_indices'] == refs[key]['source_indices']
        objects = []
        for obj in row['objects']:
            objects.append({k: obj.get(k) for k in ('name', 'lift', 'fitted_box')} | {
                'linked_track_count': len(obj.get('linked_tracks', [])),
                'candidate_count': len(obj.get('candidates', []))})
        result[key] = {k: row[k] for k in ('item_id', 'capture', 'source_indices', 'geometry', 'calls')}
        result[key]['objects'] = objects
    assert len(result) == len(refs) == 150
    assert not rec.report['salvaged']
    return result, rec.report


def printed_info(row, operand_names):
    best, sizes, values = {}, {}, []
    for c in row['calls']:
        if not c.get('served'):
            continue
        response = c.get('response') or ''
        m = re.fullmatch(r'<ground obj="([^"]+)" mode="box">', c['call'])
        if m:
            b = re.search(r'\(best (\d+)\)', response)
            s = re.search(r'size ([\d.]+) x ([\d.]+) x ([\d.]+) m', response)
            best[name_key(m[1])] = int(b[1]) if b else None
            sizes[name_key(m[1])] = max(map(float, s.groups())) if s else None
        if c['call'].startswith('<gap '):
            v = re.fullmatch(r'distance ([\d.]+) m', response)
            if v:
                values.append(float(v[1]))
    return [best.get(name_key(n)) for n in operand_names], sizes, values[-1] if values else None


def reproduce_printed(records, refs):
    checks = []
    for key, row in records.items():
        nn = names(refs[key])[0]
        _, _, printed = printed_info(row, nn)
        oo = {name_key(o['name']): o for o in row['objects']}
        fitted = [oo.get(name_key(n), {}).get('fitted_box') for n in nn]
        if printed is None or not all(fitted):
            continue
        actual = gap(*[b['f1'] for b in fitted])
        world = gap(*[boxes.box(b['world']['centroid'], b['world']['axesLengths'], b['world']['normalizedAxes']) for b in fitted])
        checks.append(dict(item_id=key, printed_m=printed, recomputed_m=actual,
                           matches=float(boxes.number(actual, 2)) == printed,
                           world_f1_difference_m=abs(world-actual)))
    assert len(checks) >= 20 and all(x['matches'] for x in checks)
    return checks


def load_gt(args, refs, captures, pins):
    gt = {}
    for directory in args.gt_dirs:
        for path in sorted(directory.glob('*.npz')):
            cap = path.stem.replace('__', '/') if '__' in path.stem else 'arkitscenes/'+path.stem
            if cap not in captures:
                continue
            pins[str(path)] = sha(path)
            with np.load(path, allow_pickle=False) as z:
                arrays = {k: z[k] for k in ('inst', 'ids', 'labels', 'frame_indices', 'valid', 'c2w', 'obb_centroid', 'obb_lengths', 'obb_axes')}
            rr = [r for r in refs.values() if r['capture'] == cap]
            assert rr and all(r['source_indices'] == arrays['frame_indices'].tolist() for r in rr)
            assert arrays['valid'].all() and len(arrays['c2w']) == 32
            areas = defaultdict(lambda: [0]*32)
            for a, raster in enumerate(arrays['inst']):
                ii, cc = np.unique(raster, return_counts=True)
                for i, c in zip(ii, cc):
                    areas[int(i)][a] = int(c)
            instances = {}
            for j, iid in enumerate(arrays['ids']):
                iid = int(iid)
                box, rule, alt = full_box(arrays, j, cap.split('/')[0])
                instances[iid] = dict(instance_id=iid, label=str(arrays['labels'][j]),
                    box=box, alternative_half_extent_box=alt, extent_rule=rule,
                    visible_pixels=areas[iid], largest_anchor=int(np.argmax(areas[iid]))+1,
                    largest_pixels=max(areas[iid]))
            gt[cap] = dict(c2w=arrays['c2w'], instances=instances,
                threshold=mask_floor(arrays['inst'].shape), room=rr[0]['task']['room'],
                source_indices=arrays['frame_indices'].tolist(), path=str(path))
            assert len({r['task']['room'] for r in rr}) == 1
    assert set(gt) == set(captures)
    return gt


def metrics_row(l0, l1, l2, truth):
    return dict(L0_score=score(l0, truth), L1_score=score(l1, truth), L2_score=score(l2, truth),
                pose_term=score(l2, truth)-score(l1, truth),
                label_free_term=100-score(l1, l2),
                L2_within_10pct=float(abs(l2-truth) <= .1*abs(truth)))


def select(rows, dataset, pair):
    return [r for r in rows if (dataset == 'all' or r['dataset_group'] == dataset)
            and (pair == 'all' or r['pair_class'] == pair)]


def cells(boot, rows, keys):
    return [dict(dataset=ds, pair_class=pc, n=len(rr), rooms=len({r['room'] for r in rr}),
                 metrics={k: boot.metric(rr, k) for k in keys})
            for ds in ('all', 'ARKit', 'ScanNet/ScanNet++')
            for pc in ('all', 'same', 'different') for rr in [select(rows, ds, pc)]]


def weighted(boot, ladder, audit, dataset):
    ll = select(ladder, dataset, 'all')
    aa, bb = select(audit, dataset, 'same'), select(audit, dataset, 'different')
    share = float(np.mean([r['pair_class'] == 'same' for r in ll])) if ll else None
    sv, _ = boot.samples([dict(r, same=float(r['pair_class'] == 'same')) for r in ll], 'same')
    av, _ = boot.samples(aa, 'label_free_term')
    bv, _ = boot.samples(bb, 'label_free_term')
    # A stratum with zero estimated weight need not have observations in that draw.
    draws = np.where(sv == 0, 0., sv*av) + np.where(sv == 1, 0., (1-sv)*bv)
    mean = None
    if share is not None and (aa or share == 0) and (bb or share == 1):
        mean = (share*np.mean([r['label_free_term'] for r in aa]) if share else 0.)
        mean += ((1-share)*np.mean([r['label_free_term'] for r in bb]) if share != 1 else 0.)
        mean = float(mean)
    return dict(dataset=dataset, same_share=boot.summarize(share, sv),
                weighted_term=boot.summarize(mean, draws),
                audit_different_minus_same=boot.contrast(bb, aa, 'label_free_term'),
                ladder_different_minus_same=boot.contrast(select(ll, 'all', 'different'), select(ll, 'all', 'same'), 'pose_term'))


def verdicts(ladder_cells, audit_cells, weighted_rows):
    def cell(cc, ds, pc, key):
        return next(r for r in cc if r['dataset'] == ds and r['pair_class'] == pc)['metrics'][key]
    same = cell(ladder_cells, 'all', 'same', 'pose_term')['mean']
    same_free = cell(ladder_cells, 'all', 'same', 'label_free_term')['mean']
    audit_same = cell(audit_cells, 'all', 'same', 'label_free_term')['mean']
    close = cell(ladder_cells, 'all', 'all', 'L2_within_10pct')['mean']
    # Apply the registered signed ladder gate. Keep both label-free controls as
    # diagnostics, without silently adding requirements to the registration.
    parity = same is not None and abs(same) <= .5 and close is not None and close >= .95
    w = weighted_rows[0]['weighted_term']
    contrast = weighted_rows[0]['ladder_different_minus_same']
    arkit = next(r for r in weighted_rows if r['dataset'] == 'ARKit')['weighted_term']
    cond2 = contrast['mean'] is not None and contrast['mean'] >= 10 and contrast['ci95'][0] > 0 and w['mean'] is not None and w['mean'] >= 5
    cond3 = w['mean'] is not None and w['mean'] <= 2
    cond4 = arkit['mean'] is not None and arkit['mean'] >= 10 and arkit['ci95'][0] > 0
    return dict(parity_pass=bool(parity), same_anchor_signed_term=same, same_anchor_label_free_term=same_free,
        audit_same_anchor_term=audit_same, L2_within_10pct_share=close,
        conditions_without_parity=dict(pose_binds=bool(cond2), no_cost=bool(cond3), ARKit_reopens=bool(cond4)),
        lines=[f"1. Parity: {'PASS' if parity else 'STOP'}; same signed / label-free / audit terms {same:.2f} / {same_free:.2f} / {audit_same:.2f}; L2 within 10% on {100*close:.2f}%.",
               '2. Pose binds on dev: '+('NOT EVALUATED (parity stop).' if not parity else 'YES.' if cond2 else 'NO.'),
               '3. Pose costs no distance: '+('NOT EVALUATED (parity stop).' if not parity else 'YES.' if cond3 else 'NO.'),
               '4. Reopen dense ARKit tower work: '+('NOT EVALUATED (parity stop).' if not parity else 'YES.' if cond4 else 'NO.')])


def fmt(x):
    return 'undefined' if x['mean'] is None else f"{x['mean']:.2f} [{x['ci95'][0]:.2f}, {x['ci95'][1]:.2f}]"


def report(result):
    lines = ['# DEV-POSE', '']
    for mode in ('raw', 'rescaled'):
        lines += [mode+': '+s for s in result['statistics'][mode]['verdicts']['lines']]
    c = result['counts']
    lines += ['', f"Ladder: {c['ladder_items']}/150 items, {c['ladder_captures']}/38 captures; all-pairs audit covers 38 captures. Exclusions: {c['excluded_reasons']}.",
        f"Actual transport anchors: {c['same']} same, {c['different']} different ({100*c['different']/c['ladder_items']:.2f}%); {c['fallback_operands']} operand fallbacks. Printed-anchor census: {c['printed_anchor_census']}.",
        f"Expected 72 items: {c['count_explanation']} The ladder has {c['ladder_rooms']} rooms; the audit has {c['audit_rooms']}.",
        f"Audit: {c['audit_instances']} eligible instances, {c['audit_pairs']} unordered pairs ({c['audit_same']} same / {c['audit_different']} different).",
        '', '| Mode | Dataset | Anchors | n | L0 | L1 | L2 | L2−L1 [95% CI] | Label-free loss [95% CI] |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for mode in ('raw', 'rescaled'):
        for r in result['statistics'][mode]['ladder_cells']:
            m = r['metrics']
            scores = ' | '.join('undefined' if m[k]['mean'] is None else f"{m[k]['mean']:.2f}" for k in ('L0_score', 'L1_score', 'L2_score'))
            lines.append(f"| {mode} | {r['dataset']} | {r['pair_class']} | {r['n']} | {scores} | {fmt(m['pose_term'])} | {fmt(m['label_free_term'])} |")
    lines += ['', '| Mode | Dataset | Audit n: same / different | Same loss [95% CI] | Different loss [95% CI] | Weighted loss [95% CI] |', '| --- | --- | --- | --- | --- | --- |']
    for mode in ('raw', 'rescaled'):
        st = result['statistics'][mode]
        for w in st['weighted']:
            cc = [next(r for r in st['audit_cells'] if r['dataset'] == w['dataset'] and r['pair_class'] == pc) for pc in ('same', 'different')]
            lines.append(f"| {mode} | {w['dataset']} | {cc[0]['n']} / {cc[1]['n']} | {fmt(cc[0]['metrics']['label_free_term'])} | {fmt(cc[1]['metrics']['label_free_term'])} | {fmt(w['weighted_term'])} |")
    lines += ['', 'Scores are routed-distance MRA ×100. L1/L2 use unrounded reader gaps; JSON also records gaps rounded to 0.01 m and their score sensitivity.',
        'The imported reader gap function uses cached reader grids/trees and a witnessed exact search bound. Every sampled grid point participates; no approximate nearest-neighbour tolerance is used.',
        'Transport uses GT metric camera coordinates and served metric c2w. The saved scale is already in translations; it is not applied again to metric GT points. Rescaled changes only served translations by the fitted similarity factor.',
        'Both worlds use z-up and the reader min-area refit of all eight corners. GT axes are rows. ARKit uses full lengths; ScanNet++ doubles stored half lengths. ScanNet uses stored full lengths, with doubled-length sensitivity in JSON.',
        'The 154-pixel rule is ceil(154 × raster area / 76800); both supplied raster orientations give 154. Largest-anchor ties choose the first anchor, including one all-zero-mask operand. Missing/invisible printed anchors use this flagged fallback.',
        'All intervals use 10,000 paired draws of the 46 manifest rooms, seed 20261120: ladder items, audit pairs, or side-ratio object occurrences receive equal weight. Weighted audit re-estimates the within-dataset ladder same-anchor share in each draw. Undefined draws are counted and omitted in JSON.',
        'Rule 2 compares signed ladder pose losses (different minus same); rule 4 uses the ARKit weighted audit loss. JSON also reports the audit contrast. The parity stop gates every interpretation.',
        '', '| T1 stage | Side pairs | Printed longest / GT longest, mean [95% CI] | Linked tracks / visible same-name GT instances (matched occurrences) |', '| --- | --- | --- | --- |']
    for r in result['side_summary']:
        t = r.get('track_comparison', {})
        counts = f"{t['linked_tracks']} / {t['visible_GT_instances']} ({t['occurrences']})" if t else 'unavailable'
        lines.append(f"| {r['stage']} | {r['n']} | {fmt(r['ratio'])} | {counts} |")
    lines += ['', f"Validation: {len(result['validation']['printed_gap_checks'])} real printed gaps match exactly after reader rounding; CPU synthetic tests are in test_devpose.py. Full-run seconds: {result['runtime_seconds']:.1f}.",
        'Limits: gravity-aligned refitting is not invariant to a shared tilted rotation; same-anchor loss can therefore be nonzero without relative-pose error. Sampled-grid gaps also have discretization effects.',
        'Limits: the sole same-anchor ladder control comes from a fallback; all three printed same-anchor items lack two GT bindings. Its bootstrap interval is degenerate when defined. Tiny L2 gaps can amplify label-free MRA loss.',
        'Limits: ScanNet extent ambiguity and GT-box/label mismatch can fail parity. NPZ anchors match recorded source indices, but do not independently authenticate native RGB/pose identity. No causal interpretation is made after STOP.',
        'Track diagnostics compare per-name linked/candidate counts with same-name visible GT instances; they are query-conditional counts, not capture-wide recall. Every object, pair, fit, cell, interval and input SHA256 is in DEVPOSE.json.',
        'Rerun in a fresh folder with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B devpose.py --out out_rerun`; run tests with the same interpreter flags and `test_devpose.py`.',
        ]
    assert len(lines) <= 80, len(lines)
    return '\n'.join(lines)+'\n'


def finalize(result, args, refs=None):
    """Recompute summaries from saved geometry rows; preserve all pair measurements.

    Bound objects remain eligible even when every mask is empty: the first of
    the tied largest-mask anchors is an explicit, flagged deterministic choice.
    This function also permits an interrupted reporting stage to be completed
    from its fully materialized geometry JSON without recomputing the audit.
    """
    pins = result['input_sha256']
    if refs is None:
        refs = {r['item_id']: r for r in read(args.manifest, pins)['items']}
    inv = {g['capture']: g for g in result['GT_inventory']}
    instances = {c: {i['instance_id']: i for i in g['instances']} for c, g in inv.items()}
    repair = [r for r in result['items'] if 'exclusion' in r and r['capture'] in inv
              and all(instances[r['capture']].get(o['instance_id'], {}).get('box') for o in r['operands'])]
    if repair:
        records, _ = load_capture(args, refs)
        for r in repair:
            cap = r['capture']
            filename = cap.split('/')[1]+'.npz' if cap.startswith('arkitscenes/') else cap.replace('/', '__')+'.npz'
            path = next(p/filename for p in args.gt_dirs if (p/filename).is_file())
            assert sha(path) == pins[str(path)]
            with np.load(path, allow_pickle=False) as z:
                cameras, source_indices = z['c2w'], z['frame_indices'].tolist()
            served = np.asarray(records[r['item_id']]['geometry']['camera_to_world_metric'])
            pts = []
            for o in r['operands']:
                inst = instances[cap][o['instance_id']]
                a = o['printed_anchor']
                if a is None or inst['visible_pixels'][a-1] == 0:
                    o['fallback'] = 'missing printed best' if a is None else 'GT invisible at printed best'
                    a = inst['largest_anchor']
                if inst['largest_pixels'] == 0:
                    o['fallback'] = 'GT invisible at all anchors; first of 32 largest-mask ties'
                o.update(anchor=a, anchor_source_index=source_indices[a-1],
                         GT_pixels_at_anchor=inst['visible_pixels'][a-1], largest_anchor=inst['largest_anchor'])
                pts.append(corners(inst['box']))
            r['pair_class'] = 'same' if r['operands'][0]['anchor'] == r['operands'][1]['anchor'] else 'different'
            l2 = r['L2_gap_m'] = gap(*map(refit, pts))
            for mode in ('raw', 'rescaled'):
                factor = 1. if mode == 'raw' else result['similarity_fits'][cap]['factor']
                l1 = gap(*[refit(transport(p, cameras[o['anchor']-1], served[o['anchor']-1], factor)) for p, o in zip(pts, r['operands'])])
                m = metrics_row(r['L0_gap_m'], l1, l2, r['label_m']) | {'L1_gap_m': l1}
                m['rounded_gap_scores'] = metrics_row(r['L0_gap_m'], float(boxes.number(l1, 2)), float(boxes.number(l2, 2)), r['label_m'])
                r['modes'][mode] = m
            r.pop('exclusion')
    included = [r for r in result['items'] if 'exclusion' not in r]
    for r in included:
        for o in r['operands']:
            o['visible_in_any_GT_anchor'] = instances[r['capture']][o['instance_id']]['largest_pixels'] > 0
    boot = Bootstrap(refs)
    keys = ('L0_score', 'L1_score', 'L2_score', 'pose_term', 'label_free_term', 'L2_within_10pct')
    for mode in ('raw', 'rescaled'):
        ll = [{k: r[k] for k in ('item_id', 'room', 'dataset_group', 'pair_class')} | r['modes'][mode] for r in included]
        aa = [{k: r[k] for k in ('room', 'dataset_group', 'pair_class')} | r['modes'][mode] for r in result['pairs']]
        lc, ac = cells(boot, ll, keys), cells(boot, aa, ('label_free_term', 'rounded_label_free_term'))
        ww = [weighted(boot, ll, aa, ds) for ds in ('all', 'ARKit', 'ScanNet/ScanNet++')]
        rounded = [{k: r[k] for k in ('item_id', 'room', 'dataset_group', 'pair_class')} | r['modes'][mode]['rounded_gap_scores'] for r in included]
        result['statistics'][mode] = dict(ladder_cells=lc, ladder_rounded_gap_cells=cells(boot, rounded, keys),
            audit_cells=ac, weighted=ww, verdicts=verdicts(lc, ac, ww))
    c = result['counts']
    c.update(ladder_items=len(included), ladder_captures=len({r['capture'] for r in included}),
             ladder_rooms=len({r['room'] for r in included}), same=sum(r['pair_class'] == 'same' for r in included),
             different=sum(r['pair_class'] == 'different' for r in included),
             fallback_operands=sum(bool(o['fallback']) for r in included for o in r['operands']),
             all_zero_mask_operands=sum(not o['visible_in_any_GT_anchor'] for r in included for o in r['operands']),
             excluded_reasons=dict(Counter(r['exclusion'] for r in result['items'] if 'exclusion' in r)))
    c['count_explanation'] = ('66 bind both operands; 74 lack a GT capture and 10 bind only one operand. '
        'The funnel count of 72 includes six known-failure items with a missing binding. One all-zero-mask operand remains in the binding-only ladder.')
    for summary in result['side_summary']:
        rr = [o for o in result['objects'] if o['stage'] == summary['stage']
              and o['visible_same_name_GT_instances'] is not None and o['linked_track_count'] is not None]
        summary['track_comparison'] = dict(occurrences=len(rr), linked_tracks=sum(o['linked_track_count'] for o in rr),
            candidates=sum(o['candidate_count'] for o in rr), visible_GT_instances=sum(o['visible_same_name_GT_instances'] for o in rr))
    census = []
    for ds in ('all', 'ARKit', 'ScanNet/ScanNet++'):
        rr = [r for r in result['items'] if ds == 'all' or r['dataset_group'] == ds]
        cc = Counter(r['printed_pair_class'] for r in rr)
        for r in rr:
            r['L0_score'] = score(None if r['L0_gap_m'] is None else r['L0_gap_m']*r['unit_factor'], float(r['label_native']))
        known = [dict(r, different=float(r['printed_pair_class'] == 'different')) for r in rr if r['printed_pair_class'] != 'unknown']
        census.append(dict(dataset=ds, counts=dict(cc), L0_score=boot.metric(rr, 'L0_score'),
                           different_share_among_known=boot.metric(known, 'different')))
    result['printed_anchor_census_by_dataset'] = census
    result['definitions']['parity'] = 'signed ladder same-anchor term within +/-0.5 AND L2 within 10% on >=95% of ladder items; label-free controls reported separately'
    result['definitions']['zero_visibility'] = 'Binding-only eligibility; an all-zero mask uses anchor 1, the first of 32 largest-mask ties, and is flagged.'
    for rel in ('work/payload/tree/evalpath/official.py', 'work/payload/h1eval/scorers.py',
                'work/payload/b/e2e_reader/stage1.py', 'kit2/kit/analyze.py'):
        p = args.gbuild/rel
        pins[str(p)] = sha(p)
    for p in (HERE/'devpose.py', HERE/'test_devpose.py'):
        pins[str(p)] = sha(p)
    return result


def save(result, args):
    args.out = args.out.resolve()
    (args.out/'DEVPOSE.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    (args.out/'REPORT_R3.md').write_text(report(result))
    paths = [HERE/'devpose.py', HERE/'test_devpose.py', args.out/'DEVPOSE.json', args.out/'REPORT_R3.md']
    (args.out/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(HERE)}\n' for p in paths))


def run(args):
    started = time.monotonic()
    dependencies(args.gbuild)
    args.out = args.out.resolve()
    args.out.relative_to(HERE)
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ('DEVPOSE.json', 'REPORT_R3.md', 'SHA256SUMS'):
        target = args.out/name
        if target.exists() and not os.access(target, os.W_OK):
            raise PermissionError(f'{target} is read-only; choose a fresh --out folder')
    pins = {}
    refs = {r['item_id']: r for r in read(args.manifest, pins)['items']}
    funnel = read(args.funnel, pins)
    split = read(args.camera_split, pins)
    pins[str(args.join)] = sha(args.join)
    joins = {r['key']: r for r in map(json.loads, args.join.read_text().splitlines())}
    stages = {r['key']: r for r in funnel['objects']['t1']}
    records, receipt = load_capture(args, refs)
    pins[str(args.capture)] = receipt['raw_sha256']
    validation = reproduce_printed(records, refs)
    print(f"Authenticated {len(records)} primary reads; reproduced {len(validation)} printed gaps.", flush=True)
    gt = load_gt(args, refs, {r['capture'] for r in split['captures']}, pins)
    geom, fits = {}, {}
    for cap, g in gt.items():
        gg = [r['geometry'] for r in records.values() if r['capture'] == cap]
        s = gg[0]
        assert all(v == s for v in gg)
        assert s['source_indices'] == g['source_indices']
        assert np.allclose(s['gravity_up'], [0, 0, 1])
        raw, metric = np.array(s['camera_to_world_unscaled']), np.array(s['camera_to_world_metric'])
        np.testing.assert_allclose(raw[:, :3, 3]*s['scale'], metric[:, :3, 3])
        np.testing.assert_allclose(raw[:, :3, :3], metric[:, :3, :3])
        geom[cap] = metric
        fits[cap] = similarity(metric, g['c2w']) | {'served_scale': s['scale'], 'room': g['room']}
    boot = Bootstrap(refs)
    all_items, object_rows, ladder = [], [], {m: [] for m in ('raw', 'rescaled')}
    printed_census = Counter()
    for key, ref in refs.items():
        cap = ref['capture']; row = records[key]; nn = names(ref)[0]
        printed, sizes, l0 = printed_info(row, nn)
        printed_class = 'unknown' if None in printed else 'same' if printed[0] == printed[1] else 'different'
        printed_census[printed_class] += 1
        unit = unit_factor(ref['task']['question'])
        truth = float(ref['task']['released_answer'])/unit
        assert ref['task']['released_answer'] == ref['task']['ground_truth']
        item = dict(item_id=key, capture=cap, room=ref['task']['room'], dataset=cap.split('/')[0],
                    dataset_group='ARKit' if cap.startswith('arkitscenes/') else 'ScanNet/ScanNet++',
                    names=nn, label_m=truth, label_native=ref['task']['released_answer'], unit_factor=unit,
                    L0_gap_m=l0, printed_anchors=printed, printed_pair_class=printed_class, operands=[], modes={})
        selected = []
        obs = {name_key(o['name']): o for o in row['objects']}
        for name, anchor in zip(nn, printed):
            objkey = key+':'+name
            binding = joins.get(objkey, {}).get('binding', {})
            # Both artifacts must agree wherever they carry a binding.
            if binding:
                assert binding == stages[objkey]['binding']
            iid = binding.get('instance_id')
            inst = gt.get(cap, {}).get('instances', {}).get(iid)
            operand = dict(name=name, instance_id=iid, printed_anchor=anchor, anchor=None, fallback=None,
                           stage=stages[objkey]['stage'])
            oo = obs.get(name_key(name), {})
            diag = dict(key=objkey, item_id=key, capture=cap, room=item['room'], name=name,
                        stage=operand['stage'], printed_longest_m=sizes.get(name_key(name)),
                        GT_longest_m=max(inst['box']['full_lengths']) if inst and inst['box'] else None,
                        linked_track_count=oo.get('linked_track_count'), candidate_count=oo.get('candidate_count'),
                        visible_same_name_GT_instances=sum(name_key(i['label']) == name_key(name) and i['largest_pixels'] > 0 for i in gt[cap]['instances'].values()) if cap in gt else None)
            diag['ratio'] = diag['printed_longest_m']/diag['GT_longest_m'] if diag['printed_longest_m'] is not None and diag['GT_longest_m'] else None
            object_rows.append(diag)
            if inst and inst['box']:
                if anchor is None or inst['visible_pixels'][anchor-1] == 0:
                    operand['fallback'] = 'missing printed best' if anchor is None else 'GT invisible at printed best'
                    anchor = inst['largest_anchor']
                if inst['largest_pixels'] == 0:
                    operand['fallback'] = 'GT invisible at all anchors; first of 32 largest-mask ties'
                operand.update(anchor=anchor, anchor_source_index=gt[cap]['source_indices'][anchor-1],
                               GT_pixels_at_anchor=inst['visible_pixels'][anchor-1], largest_anchor=inst['largest_anchor'])
                selected.append(inst)
            item['operands'].append(operand)
        if len(selected) != 2:
            item['exclusion'] = 'missing GT capture' if cap not in gt else 'missing unique binding' if any(o['instance_id'] is None for o in item['operands']) else 'no visible GT anchor or invalid box'
        else:
            item['pair_class'] = 'same' if item['operands'][0]['anchor'] == item['operands'][1]['anchor'] else 'different'
            pts = [corners(i['box']) for i in selected]
            l2 = gap(*[refit(p) for p in pts])
            item['L2_gap_m'] = l2
            for mode in ladder:
                factor = 1. if mode == 'raw' else fits[cap]['factor']
                bb = [refit(transport(p, gt[cap]['c2w'][o['anchor']-1], geom[cap][o['anchor']-1], factor)) for p, o in zip(pts, item['operands'])]
                l1 = gap(*bb)
                mm = metrics_row(l0, l1, l2, truth) | {'L1_gap_m': l1}
                mm['rounded_gap_scores'] = metrics_row(l0, float(boxes.number(l1, 2)), float(boxes.number(l2, 2)), truth)
                item['modes'][mode] = mm
                ladder[mode].append({k: item[k] for k in ('item_id', 'room', 'dataset_group', 'pair_class')} | mm)
            if cap.startswith('scannet/'):
                pp = [corners(i['alternative_half_extent_box']) for i in selected]
                alt_l2 = gap(*[refit(p) for p in pp])
                item['scannet_half_extent_sensitivity'] = {'L2_gap_m': alt_l2, 'modes': {}}
                for mode in ladder:
                    factor = 1. if mode == 'raw' else fits[cap]['factor']
                    alt_l1 = gap(*[refit(transport(p, gt[cap]['c2w'][o['anchor']-1], geom[cap][o['anchor']-1], factor)) for p, o in zip(pp, item['operands'])])
                    item['scannet_half_extent_sensitivity']['modes'][mode] = metrics_row(l0, alt_l1, alt_l2, truth) | {'L1_gap_m': alt_l1}
        all_items.append(item)
    pairs, audit, inventories = [], {m: [] for m in ladder}, []
    for cap, g in gt.items():
        eligible = [i for i in g['instances'].values() if i['largest_pixels'] >= g['threshold'] and i['box']]
        prepared = {}
        for i in eligible:
            p = corners(i['box']); a = i['largest_anchor']-1
            prepared[i['instance_id']] = dict(L2=refit(p), **{mode: refit(transport(p, g['c2w'][a], geom[cap][a], 1. if mode == 'raw' else fits[cap]['factor'])) for mode in ladder})
        inventories.append(dict(capture=cap, room=g['room'], threshold=g['threshold'], instances=list(g['instances'].values()),
                                eligible_instance_ids=[i['instance_id'] for i in eligible]))
        for pair_index, (ia, ib) in enumerate(itertools.combinations(eligible, 2), 1):
            ids = [ia['instance_id'], ib['instance_id']]
            aa, bb = [prepared[i] for i in ids]
            l2 = gap(aa['L2'], bb['L2'])
            pair = dict(capture=cap, room=g['room'], dataset_group='ARKit' if cap.startswith('arkitscenes/') else 'ScanNet/ScanNet++',
                        instance_ids=ids, labels=[ia['label'], ib['label']], anchors=[ia['largest_anchor'], ib['largest_anchor']],
                        pair_class='same' if ia['largest_anchor'] == ib['largest_anchor'] else 'different', L2_gap_m=l2, modes={})
            for mode in ladder:
                l1 = gap(aa[mode], bb[mode])
                value = dict(L1_gap_m=l1, label_free_term=100-score(l1, l2),
                             rounded_label_free_term=100-score(float(boxes.number(l1, 2)), float(boxes.number(l2, 2))))
                pair['modes'][mode] = value
                audit[mode].append({k: pair[k] for k in ('room', 'dataset_group', 'pair_class')} | value)
            pairs.append(pair)
            if pair_index % 1000 == 0:
                print(f"Audit {cap}: {pair_index}/{len(eligible)*(len(eligible)-1)//2} pairs measured.", flush=True)
        print(f"Audit {cap}: {len(eligible)} instances, {len(eligible)*(len(eligible)-1)//2} pairs.", flush=True)
    stats = {}
    for mode in ladder:
        lc = cells(boot, ladder[mode], ('L0_score', 'L1_score', 'L2_score', 'pose_term', 'label_free_term', 'L2_within_10pct'))
        ac = cells(boot, audit[mode], ('label_free_term', 'rounded_label_free_term'))
        ww = [weighted(boot, ladder[mode], audit[mode], ds) for ds in ('all', 'ARKit', 'ScanNet/ScanNet++')]
        stats[mode] = dict(ladder_cells=lc, audit_cells=ac, weighted=ww, verdicts=verdicts(lc, ac, ww))
    included = [r for r in all_items if 'exclusion' not in r]
    count = dict(ladder_items=len(included), ladder_captures=len({r['capture'] for r in included}),
        ladder_rooms=len({r['room'] for r in included}), audit_rooms=len({r['room'] for r in pairs}),
        same=sum(r['pair_class'] == 'same' for r in included), different=sum(r['pair_class'] == 'different' for r in included),
        fallback_operands=sum(bool(o['fallback']) for r in included for o in r['operands']),
        excluded_reasons=dict(Counter(r['exclusion'] for r in all_items if 'exclusion' in r)), printed_anchor_census=dict(printed_census),
        audit_instances=sum(len(i['eligible_instance_ids']) for i in inventories), audit_pairs=len(pairs),
        audit_same=sum(r['pair_class'] == 'same' for r in pairs), audit_different=sum(r['pair_class'] == 'different' for r in pairs))
    count['count_explanation'] = ('matches expected item count.' if len(included) == 72 else 'binding/visibility exclusions are listed per item; expected count is not forced.')
    side = [dict(stage=s, n=len(rr), ratio=boot.metric(rr, 'ratio')) for s in ('S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'censored', 'no-GT') for rr in [[o for o in object_rows if o['stage'] == s and o['ratio'] is not None]]]
    # Hash every imported project source, including source-pin manifests.
    for mod in list(sys.modules.values()):
        path = getattr(mod, '__file__', None)
        if path and Path(path).is_relative_to(args.gbuild) and Path(path).is_file():
            pins[path] = sha(path)
    for path in (args.gbuild/'gpkg/READER_PINS.json', HERE/'devpose.py', HERE/'test_devpose.py'):
        if path.exists():
            pins[str(path)] = sha(path)
    result = dict(schema='devpose-r3-v1', counts=count, items=all_items, pairs=pairs, objects=object_rows,
        GT_inventory=inventories, similarity_fits=fits, statistics=stats, side_summary=side,
        bootstrap=dict(draws=10000, seed=20261120, rooms=boot.rooms, weighting='items for ladder, unordered instance pairs for audit; same shared room draws', rng='Python random.Random; round7_common.Bootstrap'),
        definitions=dict(L0='served printed gap', L1='eight GT corners via one GT inverse c2w and served metric c2w; z-up reader refit',
            L2='same reader refit on GT corners in z-up GT world', scale='served metric translations already include scale; sensitivity multiplies translations only',
            pose_term='MRA(L2,label)-MRA(L1,label), x100', label_free_term='100*(1-MRA(L1,L2))',
            weighted='within-dataset ladder same-anchor share times same audit loss plus complement times different audit loss',
            threshold='instance_policy314.mask_floor; ceil(154*raster_area/76800), largest-mask anchor',
            parity='signed ladder same-anchor +/-0.5, with label-free ladder and audit same-anchor controls, plus L2 within 10% on >=95% of ladder items',
            rule2='signed ladder different-minus-same >=10, contrast CI lower >0, weighted audit loss >=5',
            rule4='ARKit weighted audit loss >=10 and its CI lower >0'),
        validation=dict(capture=receipt, printed_gap_checks=validation), input_sha256=pins,
        runtime_seconds=time.monotonic()-started)
    finalize(result, args, refs)
    save(result, args)
    print(json.dumps({'counts': result['counts'], 'runtime_seconds': result['runtime_seconds'], 'verdicts': {m: result['statistics'][m]['verdicts']['lines'] for m in result['statistics']}}, indent=2))
    return result


if __name__ == '__main__':
    run(arguments())
