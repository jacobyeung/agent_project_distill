"""Adapted from in/review_an/indep_boot.py; independent numpy PLUMBING check."""
import json
from pathlib import Path
import sys
sys.path[:0] = ['/scratch/jjyeung/orch_n30/native_r2/work/np226',
                '/scratch/jjyeung/orch_n30/native_r2/work/pyextra']
import numpy as np

BUILD = Path(__file__).resolve().parents[2]
ROOT = BUILD.parents[1]
F = ROOT / 'builds/01_c8/work/rh_full_01/runs/c80000002/native/R1.json'
b = json.loads(F.read_text())
report_path = BUILD / 'out/fixture/NATIVE_VS_DIRECT.json'
res = json.loads(report_path.read_text())
d = {r['key']: r for r in json.loads((ROOT / 'work/direct/DIRECT_B2048_COMPACT.json').read_text())}
raw = {}
for name in ('main', 'camera'):
    with (BUILD / f'in/direct_raw/items_leg_m544_{name}.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row['key'] in b['expected_keys']: raw[row['key']] = row
M = ROOT / 'work/meta/sj/orch_cd'
room, cap, task = {}, {}, {}
for path in (M / 'legs1_reads/work/vendor/r3/TASKS.jsonl', M / 'legs1_routed/out2/CAMERA_TASKS.jsonl'):
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            c = row['native']; group, identity = c.split('/', 1); key = 'devrows:' + row['id']
            cap[key] = c; task[key] = row
            room[key] = 'd1/' + identity.rsplit('_', 1)[0] if group == 'd1' else c if group == 'd2' else row['room']
A = {arm: {r['key']: r for r in b['arms'][arm]} for arm in ('unflagged', 'scripted')}
U = A['unflagged']
aliases = {'absolute_distance_object': 'object_abs_distance', 'absolute_size_room': 'room_size_estimation'}
def typ(key): return aliases.get(U[key]['question_type'], U[key]['question_type'])
def score(row): return row['scores']['released_answer' if row['stratum'] == 'primary' else 'answer']
def error(row):
    dec = row.get('decode') or {}
    return bool(row.get('finish_reason') == 'error' or row.get('derivation_error') or row.get('producer_error')
                or dec.get('finish') == 'error' or dec.get('derivation_error') or dec.get('producer_error'))
def cap_native(row):
    dec = row.get('decode') or {}
    return bool(row['capped'] or row['no_answer'] or dec.get('strict_no_answer')
                or dec.get('finish') == 'call_limit' or (dec.get('decode_budget') or {}).get('fired'))

rng = np.random.default_rng(20261115)
checks = []
for group, selections in res['groups'].items():
    group_keys = b['expected_keys']
    for part in group.split('/'):
        if part in ('d1', 'd2', 'd3'): group_keys = [k for k in group_keys if cap[k].startswith(part + '/')]
        elif part == 'camera_all': group_keys = [k for k in group_keys if typ(k).startswith('camera')]
        elif part != 'all': group_keys = [k for k in group_keys if typ(k) == part]
    for selection in selections:
        keys = group_keys
        if selection == 'passed_geometry': keys = [k for k in keys if not U[k].get('geometry_refusal')]
        elif selection == 'no_producer_error':
            keys = [k for k in keys if not error(raw[k]) and not any(error(A[a][k]) for a in A)]
        elif selection == 'metre_only':
            keys = [k for k in keys if (typ(k), U[k]['question_unit']['unit']) in
                    (('object_abs_distance', 'meters'), ('room_size_estimation', 'square meters'))]
        expected = selections[selection]
        assert len(keys) == expected['items'], (group, selection, 'items')
        if not keys:
            assert all(expected['differences'][a]['points'] is None for a in A)
            continue
        rooms = sorted({room[k] for k in keys})
        assert len(rooms) == expected['rooms']
        lookup = {r: i for i, r in enumerate(rooms)}
        ids = np.array([lookup[room[k]] for k in keys])
        counts = np.bincount(ids, minlength=len(rooms))
        sampled = rng.integers(0, len(rooms), (50000, len(rooms)))
        denominator = counts[sampled].sum(axis=1)
        for arm in A:
            direct = np.array([d[k]['score'] for k in keys])
            native = np.array([score(A[arm][k]) for k in keys])
            if selection == 'capped_zeroed':
                for i, key in enumerate(keys):
                    if cap_native(A[arm][key]): native[i] = 0
                    if any(raw[key].get(f) for f in ('forced_close', 'hit_token_cap', 'parse_failed', 'stopped_unclosed')):
                        direct[i] = 0
            differences = native - direct
            sums = np.bincount(ids, weights=differences, minlength=len(rooms))
            draws = 100 * sums[sampled].sum(axis=1) / denominator
            ci = np.percentile(draws, [2.5, 97.5])
            target = expected['differences'][arm]
            point_gap = abs(float(100 * differences.mean()) - target['points'])
            endpoint_gap = float(np.max(np.abs(ci - target['paired95_rooms'])))
            assert point_gap < 1e-9, (group, selection, arm, point_gap)
            assert endpoint_gap < 2, (group, selection, arm, endpoint_gap)
            checks.append(dict(group=group, selection=selection, arm=arm,
                               point_gap=point_gap, endpoint_gap_pp=endpoint_gap))
out = dict(mode='PLUMBING — not model scores', status='PASS', numpy_version=np.__version__,
           draws=50000, seed=20261115, source_report=str(report_path), fixture_path=str(F),
           checked_cells=len(checks), max_endpoint_gap_pp=max(c['endpoint_gap_pp'] for c in checks),
           endpoint_tolerance_pp=2,
           caveat='Independent random draws have Monte Carlo differences; exact endpoints are tested by exhaustive enumeration in test_native_vs_direct.py.',
           checks=checks)
path = BUILD / 'out/tests/INDEPENDENT_BOOTSTRAP.json'
path.write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'checks'}))
