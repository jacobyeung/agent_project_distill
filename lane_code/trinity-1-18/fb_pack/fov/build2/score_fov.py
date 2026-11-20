"""Apply the sha-pinned step-544 FoV rule; synthetic results never bind a donor."""
import os
import sys
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '8'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
sys.dont_write_bytecode = True
import argparse
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import shlex
import time
import numpy as np

WORK = Path(__file__).resolve().parent
ROOT = Path('/scratch/jjyeung/orch_n30/sb_own400')
KIT = ROOT / 'kit'
FOV_BARS = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/BARS_FOV_544.json')
FOV_BARS_SHA = 'c1905484873704ae9b8af5cb653cf2cb1b911d789d181811767fa5f8707fa878'
AMENDMENT = FOV_BARS.with_name('BARS_FOV_544_AMEND1.json')
AMENDMENT_SHA = 'e23ffd29b8fe0ad88844dafc4585ed8a1704e88b5f02dc73d99f6ea0e147acc7'
BOUNDARIES_SHA = '454e9b27fedf7fd7008760dedc4e0961f6156cc3d8afdcd203e340921c52826c'
VARIANT_SHA = '4f66911b9de9989fe9054529dd2eca9af698a7642cbd6f6b6e28f678df89fd7a'
FORMULA_SHA = '1fca29c9211e19f91a04e72c41a77652a56f3dea363e58fdd71817fe7229a134'
V1_SOURCE = '1e-4+(pi-2e-4)*sigmoid(depth.fov(states)) on a separate private feature pass (scale_donor V1)'
PROVENANCE_CHECKS = ['P1', 'P2', 'P3', 'P4', 'P5']
BARS = ROOT / 'out/BARS_FROZEN.json'
REFERENCE = KIT / 'inputs/G3T_FOV.json'
CHECKPOINT_SHA = '1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
sys.path.insert(0, str(KIT))
import core
from score_400 import summarize, module, S1, S2

AMBIGUITIES = [
    'FoV agreement does not specify pooling across captures. The report supplies per-capture medians '
    'and explicitly labelled pooled-anchor medians; neither affects the choice.',
    'For choice NONE, the bars do not define a pose-head-copy binding procedure. '
    'The report names the missing frozen-path specification and evidence without inventing that procedure.'
]


def fail(name, detail):
    raise core.Refusal(name + ': ' + str(detail))


class Inputs:
    def __init__(self):
        self.pins = {}
        self.integrity = {}

    def blob(self, path, expected=None):
        path = Path(path).resolve()
        # All operational inputs are on local disk. Do not follow receipt paths to NFS.
        if not path.is_relative_to('/scratch'):
            fail('INPUT_LOCATION', path)
        if not path.is_file():
            fail('MISSING', path)
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        self.pins[str(path)] = actual
        if expected is not None and actual != expected:
            fail('FILE_SHA_MISMATCH', f'{path}; expected {expected}, got {actual}')
        return data

    def check(self, path, expected=None):
        path = Path(path).resolve()
        if not path.is_relative_to('/scratch'):
            fail('INPUT_LOCATION', path)
        if not path.is_file():
            fail('MISSING', path)
        actual = core.sha(path)
        self.pins[str(path)] = actual
        if expected is not None and actual != expected:
            fail('FILE_SHA_MISMATCH', f'{path}; expected {expected}, got {actual}')
        return actual

    def read(self, path, expected=None):
        return json.loads(self.blob(path, expected))

    def arrays(self, path, expected=None):
        with np.load(io.BytesIO(self.blob(path, expected)), allow_pickle=False) as z:
            return {k: z[k] for k in z.files}


def pin_value(value):
    return value['sha256'] if isinstance(value, dict) else value


def check_receipt(rec, path, capture, required, inputs):
    if rec.get('synthetic') is True or rec.get('binding', {}).get('synthetic') is True:
        fail('SYNTHETIC_RECEIPT', path)
    if rec.get('capture_sha256') != capture['capture_sha256']:
        fail('CAPTURE_SHA_MISMATCH', path)
    if rec.get('checkpoint', {}).get('sha256') != CHECKPOINT_SHA:
        fail('CHECKPOINT_SHA_MISMATCH', path)
    files = rec.get('files')
    if not isinstance(files, dict):
        fail('MISSING', f'{path}:files{{}}')
    if required is not None and required not in files:
        fail('MISSING', f'{path}:files[{required}]')
    for name, value in files.items():
        target = (path.parent / name).resolve()
        if not target.is_relative_to(path.parent.resolve()):
            fail('RECEIPT_FILE_PATH', target)
        if path.name == 'PHASE_COMPLETE.json' and name == 'own.npz' and not target.exists():
            # The accepted producer mapping binds absent served bytes through P1.
            continue
        inputs.check(target, pin_value(value))


def valid_depth(value, name):
    if value is None or value.shape != (32, 51, 51) or not np.isfinite(value).all() or not (value > 0).all():
        fail('DEPTH_INVALID', name)


def valid_fov(value, name):
    if value is None or value.shape != (32, 2) or not np.isfinite(value).all() or not ((value > 0) & (value < np.pi)).all():
        fail('FOV_RANGE_OR_SHAPE', name)


def equal_bits(left, right):
    return left.dtype == right.dtype and left.shape == right.shape and left.tobytes() == right.tobytes()


def delivery_root(root):
    root = Path(root).resolve()
    return root.parent.parent if root.name == 'probe' and root.parent.name == 'native' else root


def parity_rows(root, captures, inputs, path=None):
    path = Path(path) if path is not None else delivery_root(root) / 'FOV_CHECK.json'
    check = inputs.read(path)
    rows = check.get('rows')
    if not isinstance(rows, list):
        fail('P1_PARITY_ROWS_MISSING', f'MISSING: {path}:rows')
    indexed = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('key'), str):
            fail('P1_PARITY_KEY', path)
        key = row['key']
        if key in indexed:
            fail('P1_PARITY_DUPLICATE', f'{path}:rows[{key}]')
        if row.get('served_equal') is not True:
            fail('P1_PARITY_SERVED_EQUAL', f'{path}:rows[{key}].served_equal must be true')
        indexed[key] = row
    for c in captures:
        if c['key'] not in indexed:
            fail('P1_PARITY_KEY_MISSING', f'MISSING: {path}:rows[{c["key"]}]')
    inputs.integrity['parity_file'] = str(path.resolve())
    return indexed, path


def anchor_grid(row, capture, path):
    label = f'{path}:rows[{capture["key"]}]'
    if 'anchor_indices' not in row:
        fail('P3_ANCHOR_INDICES_MISSING', 'MISSING: ' + label + '.anchor_indices')
    if row['anchor_indices'] != capture['anchor_indices']:
        fail('P3_ANCHOR_INDICES', label)
    grid = np.linspace(0, 1000, 51, dtype=np.float32)
    evidence = []
    if 'grid_uv' in row:
        value = np.asarray(row['grid_uv'])
        if value.shape != grid.shape or not np.array_equal(value, grid):
            fail('P3_GRID_UV', label + '.grid_uv')
        evidence.append('grid_uv values')
    if 'grid_uv_sha256' in row:
        if row['grid_uv_sha256'] != hashlib.sha256(grid.tobytes()).hexdigest():
            fail('P3_GRID_UV_SHA256', label + '.grid_uv_sha256')
        evidence.append('grid_uv_sha256 float32 bytes')
    if not evidence:
        fail('P3_GRID_UV_MISSING', 'MISSING: ' + label + '.grid_uv or .grid_uv_sha256')
    return evidence


def centered_log(depth, label):
    value = np.log(depth.astype(np.float64)).reshape(32, -1)
    value -= value.mean(axis=1, keepdims=True)
    norm = np.linalg.norm(value, axis=1, keepdims=True)
    if not np.isfinite(norm).all() or np.any(norm == 0):
        fail('P5_UNDEFINED_CORRELATION', label)
    return value / norm


def sanity(baseline, variant, label):
    a = centered_log(baseline, label + ':A')
    v = centered_log(variant, label)
    scores = {'identity': float(np.mean(np.sum(a * v, axis=1)))}
    for name, transformed in [('transpose', variant.swapaxes(1, 2)),
                              ('flip_vertical', variant[:, ::-1, :]),
                              ('flip_horizontal', variant[:, :, ::-1])]:
        scores[name] = float(np.mean(np.sum(a * centered_log(transformed, label), axis=1)))
    if not all(scores['identity'] > scores[name] for name in scores if name != 'identity'):
        fail('P5_ORIENTATION', f'{label}: {scores}')
    correlation = v @ a.T
    same = np.diag(correlation).copy()
    np.fill_diagonal(correlation, -np.inf)
    # A tie is not evidence that an anchor correlates best with itself.
    matched = int(np.sum(same > correlation.max(axis=1)))
    return {'orientation_mean_correlation': scores, 'same_anchor_matches': matched, 'anchors': 32}


def validate_probe(root, captures, reference, inputs, synthetic=None, fov_check=None,
                   accept_fov_code_diff=None, fov_code_diff=None):
    """Authenticate the complete population before any estimate or pair score."""
    if synthetic is None:
        root = Path(root).resolve()
        if not root.is_dir():
            fail('MISSING_KEY', root)
        expected = {c['key'] for c in captures}
        present = {p.name for p in root.iterdir() if p.is_dir()}
        extra = sorted(present - expected)
        if extra:
            # Reject an unknown directory by name without opening its data.
            fail('UNEXPECTED_CAPTURE', ', '.join(str(root / key) for key in extra))
        missing = sorted(expected - present)
        if missing:
            fail('MISSING_KEY', ', '.join(str(root / key) for key in missing))
        parity, parity_path = parity_rows(root, captures, inputs, fov_check)
        if fov_code_diff is not None and accept_fov_code_diff is None:
            fail('P4_CODE_DIFF_ACCEPTANCE_MISSING', '--fov-code-diff requires --accept-fov-code-diff SHA256')
        if accept_fov_code_diff is not None:
            if len(accept_fov_code_diff) != 64 or any(x not in '0123456789abcdef' for x in accept_fov_code_diff):
                fail('P4_CODE_DIFF_SHA256', accept_fov_code_diff)
            diff = Path(fov_code_diff) if fov_code_diff is not None else delivery_root(root) / 'FOV_CODE_DIFF.patch'
            data = inputs.blob(diff, accept_fov_code_diff)
            if not data.strip():
                fail('P4_CODE_DIFF_EMPTY', diff)
            inputs.integrity['accepted_fov_code_diff'] = {'path': str(diff.resolve()),
                'sha256': accept_fov_code_diff, 'against_variant_sha256': VARIANT_SHA}
        inputs.integrity.update(status='PASSED', checked=PROVENANCE_CHECKS, skipped=[],
            formula_pin={'source': 'PATCH_DONOR3 student_pilot/scale_donor.py', 'sha256': FORMULA_SHA})
    else:
        inputs.integrity.update(status='SYNTHETIC: P1-P5 skipped; no provenance or donor decision',
                                checked=[], skipped=PROVENANCE_CHECKS)
    payloads = {}
    for c in captures:
        ref = reference['captures'].get(c['canonical'])
        if ref is None:
            fail('MISSING', f'{REFERENCE}:captures[{c["canonical"]}]')
        if ref['capture_sha256'] != c['capture_sha256'] or ref['anchor_indices'] != c['anchor_indices']:
            fail('REFERENCE_IDENTITY', c['canonical'])
        ref_fov = np.asarray(ref['fov_hw_rad'], dtype=np.float64)
        valid_fov(ref_fov, c['canonical'] + ':reference')
        a = c['own544']
        if 'path' not in a:
            fail('MISSING', a.get('expected', str(c) + ':own544.path'))
        baseline = inputs.arrays(a['path'], a['sha256'])['depth']
        valid_depth(baseline, a['path'])
        if synthetic is not None:
            variants = {arm: baseline * factor for arm, factor in zip(('V1', 'V2'), synthetic)}
            fovs = {arm: ref_fov.astype(np.float32) for arm in ('B', 'V1', 'V2')}
            receipts = {'status': 'SYNTHETIC: B/V1 FoVs stand in with G3T; V1/V2 depths multiply A'}
        else:
            folder = root / c['key']
            receipts = {}
            for name, required in [('PHASE_COMPLETE.json', None), ('FOV_RECEIPT.json', 'fov.npz')]:
                path = folder / name
                rec = inputs.read(path)
                check_receipt(rec, path, c, required, inputs)
                receipts[name] = rec
            rec = receipts['FOV_RECEIPT.json']
            if rec.get('served_equal') is False:
                fail('SERVED_DEPTH_BITS', str(folder / 'FOV_RECEIPT.json') + ':served_equal=false')
            checks = rec.get('checks', {})
            if checks.get('second_pass_pose_fov_bit_identical') is not True:
                fail('P1_CONTROL_BITS', f'{folder}/FOV_RECEIPT.json:checks.second_pass_pose_fov_bit_identical')
            maximum = checks.get('second_pass_pose_fov_max_abs')
            if type(maximum) not in (int, float) or maximum != 0.0:
                fail('P1_CONTROL_MAX_ABS', f'{folder}/FOV_RECEIPT.json:checks.second_pass_pose_fov_max_abs')
            served_sha = hashlib.sha256(np.ascontiguousarray(baseline, dtype=np.float64).tobytes()).hexdigest()
            if rec.get('served_depth_sha256') != served_sha:
                fail('P1_SERVED_DEPTH_SHA256', f'{folder}/FOV_RECEIPT.json:served_depth_sha256')
            fov = inputs.arrays(folder / 'fov.npz', pin_value(rec['files']['fov.npz']))
            if (folder / 'own.npz').exists():
                own = inputs.arrays(folder / 'own.npz')
                if 'depth' not in own or not equal_bits(own['depth'], baseline):
                    fail('SERVED_DEPTH_BITS', folder / 'own.npz')
            if 'depth' in fov and not equal_bits(fov['depth'], baseline):
                fail('SERVED_DEPTH_BITS', folder / 'fov.npz')
            evidence = anchor_grid(parity[c['key']], c, parity_path)
            source_sha = rec.get('boundaries_sha256')
            if not isinstance(source_sha, str) or len(source_sha) != 64 or any(x not in '0123456789abcdef' for x in source_sha):
                fail('P4_BOUNDARIES_SHA256_MISSING', f'MISSING: {folder}/FOV_RECEIPT.json:boundaries_sha256')
            if source_sha != BOUNDARIES_SHA and accept_fov_code_diff is None:
                fail('P4_BOUNDARIES_SHA256', folder / 'FOV_RECEIPT.json')
            if rec.get('sources', {}).get('V1') != V1_SOURCE:
                fail('P4_V1_FORMULA', f'{folder}/FOV_RECEIPT.json:sources.V1')
            if rec.get('missing') != {}:
                fail('P4_VARIANTS_MISSING', f'MISSING: {folder}/FOV_RECEIPT.json:missing must equal {{}}')
            receipts['provenance'] = {'P1_served_depth_sha256': served_sha,
                'own_npz_present': (folder / 'own.npz').exists(),
                'P2': 'served encode FoV bound by accepted producer code; finite (32,2) radians',
                'P3_grid_evidence': evidence, 'P4_boundaries_sha256': source_sha,
                'V1_formula_sha256': FORMULA_SHA}
            variants = {arm: fov.get('depth_' + arm) for arm in ('V1', 'V2')}
            fovs = {arm: fov.get('fov_' + arm) for arm in ('B', 'V1', 'V2')}
        for arm, value in variants.items():
            valid_depth(value, c['key'] + ':depth_' + arm)
        for arm, value in fovs.items():
            valid_fov(value, c['key'] + ':fov_' + arm)
        if np.any(np.abs(fovs['V2'].astype(np.float64) - ref_fov) > 1e-6):
            fail('FOV_V2_MISMATCH', c['key'] + ':fov_V2 differs by > 1e-6 rad')
        if synthetic is None:
            if not equal_bits(fovs['V2'], ref_fov.astype(np.float32)):
                fail('P4_FOV_V2_EXACT', c['key'] + ':fov_V2 must equal the float32 reference bit for bit')
            receipts['provenance']['V2_max_abs_diff_rad'] = float(np.max(np.abs(fovs['V2'].astype(np.float64) - ref_fov)))
            receipts['provenance']['P5'] = {arm: sanity(baseline, value, c['key'] + ':' + arm)
                                          for arm, value in variants.items()}
        payloads[c['canonical']] = {'depths': {'A': baseline, **variants}, 'fovs': fovs, 'receipts': receipts}
    if synthetic is None:
        totals = {}
        for arm in ('V1', 'V2'):
            count = sum(p['receipts']['provenance']['P5'][arm]['same_anchor_matches'] for p in payloads.values())
            total = 32 * len(payloads)
            fraction = count / total if total else 0.0
            totals[arm] = {'same_anchor_matches': count, 'anchors': total, 'fraction': fraction, 'minimum': .95}
            if fraction < .95:
                fail('P5_ANCHOR_MATCH', f'{arm}: {count}/{total} = {fraction}; requires >= 0.95')
        inputs.integrity['P5_anchor_match'] = totals
    return payloads


def summaries(s, records, folds):
    # Relabel only. The imported function calculates all means and intervals.
    rename = {'A': 'A', 'B': 'V1', 'G': 'V2', 'B-A': 'V1-A', 'G-A': 'V2-A', 'G-B': 'V2-V1'}
    def one(rows):
        if not rows:
            fail('MISSING', 'no eligible records for frozen summary')
        adapted = [dict(r, pred={'A': r['pred']['A'], 'B': r['pred']['V1'], 'G': r['pred']['V2']}) for r in rows]
        return {rename[k]: v for k, v in summarize(s, adapted).items()}
    return {'folds': [dict(name=f['name'], **one([r for r in records if r['room'] in f['test_rooms']])) for f in folds],
            'combined': one(records)}


def evaluate(displacement, distance):
    criteria = {}
    for arm in ('V1', 'V2'):
        key = arm + '-A'
        combined = displacement['combined'][key]
        fold_means = {f['name']: f[key]['points'] for f in displacement['folds']}
        upper = {f['name']: f[key]['ci95'][1] for f in distance['folds']}
        upper['combined'] = distance['combined'][key]['ci95'][1]
        criteria[arm] = {
            'D1': {'pass': combined['points'] >= -0.25, 'mean': combined['points'], 'minimum': -0.25},
            'D2': {'pass': combined['ci95'][0] >= -0.50, 'ci95_lower': combined['ci95'][0], 'minimum': -0.50},
            'D3': {'pass': all(x >= -0.50 for x in fold_means.values()), 'fold_means': fold_means, 'minimum': -0.50},
            'H': {'pass': all(x >= 0 for x in upper.values()), 'ci95_upper': upper, 'minimum': 0.0}}
        criteria[arm]['acceptable'] = all(criteria[arm][k]['pass'] for k in ('D1', 'D2', 'D3', 'H'))
    choice = next((arm for arm in ('V2', 'V1') if criteria[arm]['acceptable']), 'NONE')
    return criteria, choice


def agreement(payloads):
    pooled = defaultdict(lambda: defaultdict(list))
    per_capture = {}
    def metrics(delta):
        return {'median_abs_degrees': float(np.median(delta)),
                'vertical_median_abs_degrees': float(np.median(delta[:, 0])),
                'horizontal_median_abs_degrees': float(np.median(delta[:, 1])), 'anchors': len(delta)}
    for name, p in payloads.items():
        per_capture[name] = {}
        for left, right in [('B', 'V1'), ('B', 'V2'), ('V1', 'V2')]:
            delta = np.abs(p['fovs'][left].astype(float) - p['fovs'][right].astype(float)) * 180 / np.pi
            key = left + '-' + right
            pooled[name.split('/')[0]][key].append(delta)
            per_capture[name][key] = metrics(delta)
    return {'pooling': 'all 32 anchors per capture, all 242 train captures; each axis separately',
            'per_dataset_pooled_anchors': {ds: {k: metrics(np.concatenate(v)) for k, v in pairs.items()} for ds, pairs in pooled.items()},
            'per_capture': per_capture}


def fresh_output(path, synthetic):
    path = Path(path).resolve()
    if synthetic is not None and path.is_relative_to(WORK):
        # Test-only allowance. Call the same fresh() and restore its module root.
        old = core.ROOT
        try:
            core.ROOT = WORK
            return core.fresh(path)
        finally:
            core.ROOT = old
    if not path.is_relative_to(ROOT / 'out') or path == ROOT / 'out':
        fail('OUTPUT_LOCATION', 'real output must be a fresh child of ' + str(ROOT / 'out'))
    return core.fresh(path)


def run(args, out, inputs):
    begin = time.monotonic()
    inputs.check(__file__)
    rule = inputs.read(FOV_BARS, FOV_BARS_SHA)
    amendment = inputs.read(AMENDMENT, AMENDMENT_SHA)
    if amendment['amends']['sha256'] != FOV_BARS_SHA:
        fail('AMENDMENT_BASE_PIN', AMENDMENT)
    for path, expected in rule['input_sha256'].items():
        inputs.check(path, expected)
    bars = inputs.read(BARS, rule['input_sha256'][str(BARS)])
    reference = inputs.read(REFERENCE, rule['input_sha256'][str(REFERENCE)])
    inputs.check(__file__)
    inputs.check(sys.executable)
    if len(bars['captures']) != 242 or any(c['k1_split'] != 'train' for c in bars['captures']):
        fail('FROZEN_POPULATION', BARS)
    # Only pinned train identity metadata is used; no held-out payload is opened.
    for path, expected in bars['input_sha256'].items():
        inputs.check(path, expected)
    payloads = validate_probe(args.own_root, bars['captures'], reference, inputs, args.synthetic,
        args.fov_check, args.accept_fov_code_diff, args.fov_code_diff)
    print('Integrity passed for all 242 train captures', file=sys.stderr, flush=True)
    s = module(S1, 'fov_scale1')
    d = module(S2, 'fov_scale2')
    d.OUT = out
    if 'torch' in sys.modules:
        sys.modules['torch'].set_num_threads(8)
    for path, expected in d.codepins().items():
        inputs.check(path, expected)
    cs = {c['canonical']: c for c in s.training()}
    for c in bars['captures']:
        full = cs.get(c['canonical'])
        if full is None or full['k1_split'] != 'train' or core.digest(full) != c['capture_sha256']:
            fail('CAPTURE_SHA_MISMATCH', c['canonical'])
        for arm in ('own544', 'tower'):
            q = c[arm]
            receipt = inputs.read(q['receipt'], bars['input_sha256'].get(q['receipt']))
            if receipt['capture_sha256'] != c['capture_sha256'] or receipt.get('synthetic') is True:
                fail('BASELINE_RECEIPT', q['receipt'])
            inputs.check(q['path'], q['sha256'])
    core.atomic(out / 'PREFLIGHT.json', {'input_sha256': dict(inputs.pins), 'synthetic': args.synthetic is not None,
        'decision_usable': False, 'status': 'ALL_INTEGRITY_CHECKS_PASSED', 'captures': len(payloads),
        'provenance_checks': inputs.integrity})
    records, distance, distance_rows, missing, scales = [], [], [], [], {}
    for n, frozen in enumerate(bars['captures']):
        c = cs[frozen['canonical']]
        if not frozen['gt_present']:
            missing.append({'capture': c['canonical'], 'expected': c['gt'], 'status': 'MISSING: GT excluded by frozen bars'})
            continue
        rows = [r for r in c['rows'] if r['type'] == 'object_abs_distance']
        gt, tower, hw = s.load_capture(c, (Path(frozen['tower']['path']).parent, core.read(frozen['tower']['receipt'])), bool(rows))
        # load_capture checks GT sha against the capture digest's GT pin.
        inputs.pins[c['gt']['path']] = c['gt']['sha256']
        values = {arm: float(s.estimate(tower['depth_grid'], tower['depth_conf_grid'], depth)[0])
                  for arm, depth in payloads[c['canonical']]['depths'].items()}
        scales[c['canonical']] = values
        _, centres, _ = s.to_gravity_reference_frame(tower['raw_pose'][tower['anchor_slots']], [0., -1., 0.])
        i, j = np.triu_indices(32, 1)
        truth = np.linalg.norm(gt['c2w'][i, :3, 3] - gt['c2w'][j, :3, 3], axis=1)
        ok = gt['valid'][i].astype(bool) & gt['valid'][j].astype(bool) & np.isfinite(truth) & (truth >= .1)
        raw = np.linalg.norm(centres[i] - centres[j], axis=1)[ok]
        if not len(raw) or not np.isfinite(raw).all():
            fail('MISSING', c['canonical'] + ':eligible displacement pairs')
        records.append({'capture': c['canonical'], 'room': c['room'], 'gt': truth[ok],
                        'pred': {arm: raw * scale for arm, scale in values.items()}})
        if rows:
            predictions = {}
            # Identical numeric scales yield identical routed geometry. Reuse only exact equality.
            by_scale = {}
            for arm, scale in values.items():
                if scale not in by_scale:
                    try:
                        # A single file per capture bounds workspace size. The helper is unchanged.
                        geo = d.geometry_npz(c, tower, hw, d.gravities(tower, gt)['G1'], scale, 'working')
                        error = None
                    except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
                        geo, error = None, str(exc)
                    cache = {}
                    routed = []
                    for row in rows:
                        p, err = (None, error) if geo is None else d.attempt(lambda: d.distance(row, geo, gt, 'predicted', cache))
                        routed.append((p, err))
                    by_scale[scale] = routed
                routed = by_scale[scale]
                predictions[arm] = np.array([np.nan if p is None else p for p, _ in routed])
                distance_rows.extend({'capture': c['canonical'], 'row_id': row['id'], 'arm': arm,
                    'pred': p, 'gt': float(row['gt_value']), 'refusal': err}
                    for row, (p, err) in zip(rows, routed))
            distance.append({'capture': c['canonical'], 'room': c['room'],
                'gt': np.array([float(row['gt_value']) for row in rows]), 'pred': predictions})
        if (n + 1) % 20 == 0:
            print(f'Scored {n + 1}/242 captures; {time.monotonic() - begin:.1f}s', file=sys.stderr, flush=True)
    displacement = summaries(s, records, bars['folds'])
    routed_distance = summaries(s, distance, bars['folds'])
    criteria, choice = evaluate(displacement, routed_distance)
    coefficients = {f['name']: {arm: {'factor': s.fit(records, set(f['fit_rooms']), arm),
        'fit_rooms': sorted({r['room'] for r in records if r['room'] in f['fit_rooms']})}
        for arm in ('A', 'V1', 'V2')} for f in bars['folds']}
    ratios = {name: {arm: value / row['A'] for arm, value in row.items()} for name, row in scales.items()}
    result = {'schema': 'fb-pack-fov-score-v2', 'input_sha256': dict(inputs.pins),
        'provenance_checks': inputs.integrity,
        'command': shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), *sys.argv[1:]]),
        'synthetic': args.synthetic is not None, 'synthetic_factors': args.synthetic,
        'decision_usable': args.synthetic is None, 'choice': choice, 'criteria': criteria,
        'displacement': displacement, 'routed_distance': routed_distance,
        'captures': len(records), 'pairs': sum(len(r['gt']) for r in records),
        'distance_captures': len(distance), 'distance_items': sum(len(r['gt']) for r in distance),
        'missing': missing, 'seconds': time.monotonic() - begin,
        'report_only': {'V2-V1': 'report-only in both metric summaries', 'fov_agreement': agreement(payloads),
            'fov_synthetic_note': 'B/V1 stand-ins equal G3T; agreement is not source evidence' if args.synthetic is not None else None,
            'own_depth_scales': scales, 'own_depth_scale_ratios_to_A': ratios, 'global_fit_half_factors': coefficients},
        'receipt_metadata': {name: p['receipts'] for name, p in payloads.items()}, 'ambiguities': AMBIGUITIES,
        'none_requirement': ('Donor does not bind. A frozen pose-head FoV copy would need the exact frozen module/state '
            'and preprocessing specification, checkpoint and source pins, capture-bound served-depth/FoV receipts, '
            'and a separately authorized binding rule. That specification and rule are MISSING.') if choice == 'NONE' else None}
    core.atomic(out / 'FOV_RESULT.json', result)
    core.atomic(out / 'DISTANCE_ROWS.json', {'input_sha256': dict(inputs.pins),
        'synthetic': args.synthetic is not None, 'decision_usable': args.synthetic is None, 'rows': distance_rows})
    print(json.dumps({'choice': choice, 'V1-A': displacement['combined']['V1-A'], 'V2-A': displacement['combined']['V2-A']}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--own-root', type=Path)
    parser.add_argument('--fov-check', type=Path, help='default: <delivery root>/FOV_CHECK.json')
    parser.add_argument('--accept-fov-code-diff', metavar='SHA256', help='accept a published variant-code diff with this hash')
    parser.add_argument('--fov-code-diff', type=Path, help='default: <delivery root>/FOV_CODE_DIFF.patch')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--synthetic', nargs=2, type=float, metavar=('F1', 'F2'))
    args = parser.parse_args()
    if args.synthetic is None and args.own_root is None:
        parser.error('--own-root is required without --synthetic')
    if args.synthetic is not None and not all(np.isfinite(x) and x > 0 for x in args.synthetic):
        parser.error('synthetic factors must be finite and positive')
    inputs = Inputs()
    inputs.check(__file__)
    try:
        out = fresh_output(args.out, args.synthetic)
    except core.Refusal as exc:
        print(str(exc), file=sys.stderr)
        return 2
    core.write_guard(out)
    for var, name in [('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'cache'), ('HF_HOME', 'hf'), ('TORCH_HOME', 'torch')]:
        p = out / name
        p.mkdir()
        os.environ[var] = str(p)
    try:
        run(args, out, inputs)
    except (core.Refusal, FileNotFoundError, KeyError, ValueError, AssertionError, TypeError, AttributeError) as exc:
        core.atomic(out / 'FOV_RESULT.json', {'input_sha256': dict(inputs.pins), 'status': 'REFUSED',
            'provenance_checks': {**inputs.integrity, 'status': 'REFUSED'},
            'reason': str(exc), 'synthetic': args.synthetic is not None, 'decision_usable': False,
            'choice': 'MISSING', 'command': shlex.join(sys.argv)})
        print('REFUSED: ' + str(exc), file=sys.stderr, flush=True)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
