"""CPU geometry pricing with train-only fitting and deployed program arithmetic."""
import os
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '8'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import time
import traceback
import warnings
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
assert ROOT == Path('/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd')
TREE = Path('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')
MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
TOWERS = Path('/scratch/jjyeung/k1/run_tower_sam_2')
CONVERTER = Path('/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py')
IMPORTED = set()


def audit(event, args):
    if event != 'open' or not isinstance(args[0], (str, bytes)):
        return
    p = Path(os.fsdecode(args[0])).absolute()
    if p.name == 'candidates.json':
        raise PermissionError('Grounding kill-test boundary: candidates.json is forbidden')
    mode, flags = args[1:3]
    writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
        isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
    if writing and not p.resolve().is_relative_to(ROOT):
        raise PermissionError('Write outside harness workspace: ' + str(p))
    if str(p).startswith('/scratch/jjyeung/orch_cd/') and p.suffix in ('.py', '.pyc'):
        if p.suffix == '.pyc':
            import importlib.util
            try:
                p = Path(importlib.util.source_from_cache(str(p)))
            except ValueError:
                p = p.with_suffix('.py')
        IMPORTED.add(str(p))


sys.addaudithook(audit)
sys.path.insert(0, str(TREE))
import numpy as np
from student_pilot import camera_targets, ground_lifting, tower_scale_rule
from student_pilot.ground_profiles import load_geometry
from student_pilot import geometry_profiles
import gravity_guard
from student_pilot.scene_state import FrameMap
from trace_format.ground_v313 import Session
from trace_format import room_v314 as room
from rk import programs
from room_rules import r1
if 'torch' in sys.modules:
    sys.modules['torch'].set_num_threads(8)

OUT = ROOT / 'out'
TESTS = []
TIMINGS = defaultdict(float)
SCALES = ('S1', 'S2', 'S3', 'S4', 'SO')
GRAVITIES = ('GO', 'G1')
SEALED_VALIDATE = geometry_profiles.GeometryContract.validate
REVIEWED_VALIDATE = None
GRAVITY_RECORDER = gravity_guard.Recorder()


def load_reviewed_geometry(path, c):
    """Use the reviewed validator only for this serial deployed-geometry load."""
    global REVIEWED_VALIDATE
    previous = geometry_profiles.GeometryContract.validate
    assert previous is SEALED_VALIDATE, 'reviewed validator leaked outside GD_reviewed'
    try:
        if REVIEWED_VALIDATE is None:
            gravity_guard.install(geometry_profiles, GRAVITY_RECORDER)
            REVIEWED_VALIDATE = geometry_profiles.GeometryContract.validate
        geometry_profiles.GeometryContract.validate = REVIEWED_VALIDATE
        with gravity_guard.capture('E3_GD_reviewed', c['canonical']):
            return load_geometry(path, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
    finally:
        geometry_profiles.GeometryContract.validate = previous


def deployed_conditions(c, gd_dir, f):
    options = [gd_dir / c['canonical'] / 'geometry.npz',
               gd_dir / (c['canonical'].replace('/', '__') + '.npz'),
               gd_dir / digest(c['canonical'])[:16] / 'geometry.npz']
    paths = [p for p in options if p.is_file()]
    if len(paths) > 1:
        raise ValueError('GD requires exactly one deployed geometry file for ' + c['canonical'])
    if not paths:
        reason = 'FileNotFoundError:deployed_geometry_missing'
        detail = dict(path=str(options[-1]), refusal=reason)
        receipt_path = options[-1].parent / 'CACHE_COMPLETE.json'
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text())
            refusal = receipt.get('geometry_refusal')
            if isinstance(refusal, dict) and refusal.get('code'):
                reason = 'GeometryError:' + refusal['code']
                detail.update(refusal=reason, geometry_refusal=refusal,
                              gravity_verdict=receipt.get('gravity_verdict'),
                              cache_receipt=str(receipt_path))
        for arm in ('GD_sealed', 'GD_reviewed'):
            f[arm] = dict(detail)
            yield arm, (reason, None), 'predicted'
        return
    path = paths[0]
    pin = dict(path=str(path), sha256=sha(path))
    for arm in ('GD_sealed', 'GD_reviewed'):
        f[arm] = dict(pin)
        try:
            geo = (load_reviewed_geometry(path, c) if arm == 'GD_reviewed' else
                   load_geometry(path, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled'))
            assert geo.depth_scale_count == 1
        except geometry_profiles.GeometryError as exc:
            reason = type(exc).__name__ + ':' + str(exc)
            f[arm]['refusal'] = reason
            yield arm, (reason, None), 'predicted'
        else:
            yield arm, geo, 'predicted'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def digest(value):
    # native_kit.bindings.digest deliberately uses json's default separators.
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def clean(value):
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(x) for x in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def dump(path, value):
    Path(path).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n')


def log_test(name, passed, **details):
    record = dict(test=name, passed=bool(passed), **clean(details))
    TESTS.append(record)
    with (OUT / 'tests.log').open('a') as f:
        f.write(json.dumps(record, allow_nan=False) + '\n')


def mra(pred, truth):
    if pred is None or not math.isfinite(pred) or truth <= 0:
        return 0.0
    # Integer thresholds avoid np.arange accumulation at exact boundaries.
    relative = abs(pred - truth) / abs(truth)
    return sum(relative < (100 - theta) / 100 for theta in range(50, 100, 5)) / 10


def inventory():
    manifest = json.loads(MANIFEST.read_text())
    index = {}
    for p in sorted(TOWERS.glob('*/PHASE_COMPLETE.json')):
        receipt = json.loads(p.read_text())
        key = receipt['capture_sha256']
        assert key not in index, 'duplicate tower receipt'
        index[key] = (p.parent, receipt)
    present, missing = [], []
    for c in manifest['captures']:
        assert digest(c) in index, 'capture digest not in tower cache: ' + c['canonical']
        if c.get('gt') and Path(c['gt']['path']).is_file():
            assert Path(c['gt']['path']).resolve().is_relative_to('/scratch')
            present.append(c)
        else:
            missing.append(dict(capture=c['canonical'], gt=c.get('gt')))
    assert len(present) == 296 and len(missing) == 4
    train = {c['room'] for c in present if c['k1_split'] == 'train'}
    heldout = {c['room'] for c in present if c['k1_split'] == 'heldout'}
    assert not train & heldout, 'physical rooms cross splits'
    assert all(c['k1_split'] in ('train', 'heldout') for c in present)
    ids = [r['id'] for c in present for r in c['rows']]
    assert len(ids) == len(set(ids)), 'row IDs are not unique'
    value = dict(captures=len(present), missing=missing, exact_tower_digest_matches=len(manifest['captures']),
                 gt_bytes=sum(Path(c['gt']['path']).stat().st_size for c in present),
                 tower_bytes=sum((index[digest(c)][0] / 'tower.npz').stat().st_size for c in present),
                 train_captures=sum(c['k1_split'] == 'train' for c in present),
                 heldout_captures=sum(c['k1_split'] == 'heldout' for c in present),
                 train_rooms=len(train), heldout_rooms=len(heldout), n_rows=len(ids))
    dump(OUT / 'INVENTORY.json', value)
    return present, index, value


class GTGeometry(programs._reference.GTSource):
    """Bind the deployed GT lifting arithmetic to each frame's intrinsics."""
    def __init__(self, arrays):
        self.depth, self.inst = arrays['depth'], arrays['inst']
        self.K, self.K_frames = arrays['K'], arrays['K_frames']
        self.c2w, self.valid = arrays['c2w'], arrays['valid'].astype(bool)
        self.H, self.W = self.depth.shape[1:]
        self.Kinv_frames = np.linalg.inv(self.K_frames)

    def lift(self, k, uv, mode='center'):
        # GTSource.lift itself is unchanged; this serial adapter binds K for k.
        self.Kinv = self.Kinv_frames[k - 1]
        return super().lift(k, uv, mode=mode)


def load_capture(c, entry, need_masks):
    start = time.monotonic()
    folder, receipt = entry
    # Hash and decompress the same bytes; avoid an extra physical read.
    data = Path(c['gt']['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == c['gt']['sha256'], 'GT hash mismatch'
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        names = ['depth', 'K', 'K_frames', 'c2w', 'valid', 'frame_indices']
        if need_masks:
            names.append('inst')
        gt = {k: z[k] for k in names}
    with np.load(folder / 'tower.npz', allow_pickle=False) as z:
        tower = {k: z[k] for k in ('raw_pose', 'depth_grid', 'depth_conf_grid', 'frame_indices', 'anchor_slots', 'grid_uv')}
    anchors = c['anchor_indices']
    assert np.array_equal(tower['frame_indices'][tower['anchor_slots']], anchors)
    assert np.array_equal(gt['frame_indices'], anchors)
    assert gt['depth'].shape[0] == 32 and gt['K_frames'].shape == (32, 3, 3)
    assert tower['depth_grid'].shape == (32, 51, 51)
    assert gt['valid'].any()
    TIMINGS['load_seconds'] += time.monotonic() - start
    return gt, tower, receipt['source_hw']


def norm(vector):
    length = np.linalg.norm(vector)
    if not np.isfinite(length) or length < 1e-6:
        raise ValueError('degenerate_gravity')
    return vector / length


def gravities(tower, gt):
    raw = tower['raw_pose'][tower['anchor_slots']]
    R = np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw])
    g1 = norm(np.mean(-R[:, :, 1], axis=0))
    valid = gt['valid'].astype(bool)
    camera_up = gt['c2w'][valid, :3, :3].transpose(0, 2, 1) @ np.array([0., 0., 1.])
    go = norm(np.mean(np.einsum('nij,nj->ni', R[valid], camera_up), axis=0))
    return dict(G1=g1, GO=go)


def geometry_npz(c, tower, hw, gravity, scale, label):
    R, t, fov = camera_targets.to_gravity_reference_frame(tower['raw_pose'][tower['anchor_slots']], gravity)
    H, W = map(int, hw)
    C = np.repeat(np.eye(4)[None], 32, axis=0)
    C[:, :3, :3], C[:, :3, 3] = R, t
    K = np.zeros((32, 3, 3))
    K[:, 0, 0], K[:, 1, 1] = W / (2 * np.tan(fov[:, 1] / 2)), H / (2 * np.tan(fov[:, 0] / 2))
    K[:, 0, 2], K[:, 1, 2], K[:, 2, 2] = W / 2, H / 2, 1
    A = np.repeat(np.diag([W / 1000, H / 1000, 1.])[None], 32, axis=0)
    dest = OUT / 'geometry' / c['canonical'].replace('/', '__')
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / (label + '.npz')
    np.savez(path, profile='scaled_g3t_depth', depth_unit='unscaled', pose_unit='unscaled',
             reference_source_frame=c['anchor_indices'][0], K=K, canvas_to_source=A, camera_to_world=C,
             scale=scale, depth_scale_count=0, pose_scale_count=0,
             anchor_frame_indices=c['anchor_indices'], depth_grid=tower['depth_grid'], grid_uv=tower['grid_uv'])
    result = load_geometry(path, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
    assert result.depth_scale_count == 1 and result.pose_scale_count == 1
    return result


def oracle_scale(tower, gt, so_mask):
    axis = tower['grid_uv']
    H, W = gt['depth'].shape[1:]
    x = np.clip(np.floor(axis / 1000 * W).astype(int), 0, W - 1)
    y = np.clip(np.floor(axis / 1000 * H).astype(int), 0, H - 1)
    truth = gt['depth'][:, y[:, None], x[None, :]].astype(float)
    truth[~gt['valid'].astype(bool)] = np.nan
    d, conf = (np.asarray(tower[k], float) for k in ('depth_grid', 'depth_conf_grid'))
    threshold = float(np.percentile(conf[np.isfinite(conf)], 50))
    selected = np.isfinite(conf) & (conf > threshold) & np.isfinite(d) & (d > 0) & np.isfinite(truth) & (truth > 0)
    expected_frozen = selected & (truth > .1) & (truth < 10)
    frozen_scale, frozen_mask, frozen_threshold = tower_scale_rule.estimate(d, conf, truth)
    assert np.array_equal(frozen_mask, expected_frozen) and threshold == frozen_threshold
    if so_mask == 'frozen':
        selected = frozen_mask
    assert selected.any()
    so = float(np.median(truth[selected] / d[selected]))
    all_valid = np.isfinite(truth) & (truth > 0) & np.isfinite(d) & (d > 0)
    return so, dict(so_selected_points=int(selected.sum()), frozen_selected_points=int(frozen_mask.sum()),
                    frozen_mask_equal=bool(np.array_equal(selected, frozen_mask)),
                    frozen_mask_different_points=int(np.count_nonzero(selected != frozen_mask)),
                    frozen_scale=frozen_scale, confidence_threshold=threshold,
                    absrel_so_selected=float(np.mean(np.abs(so * d[selected] - truth[selected]) / truth[selected])),
                    absrel_so_all_valid_grid=float(np.mean(np.abs(so * d[all_valid] - truth[all_valid]) / truth[all_valid])),
                    frozen_rule_check_pass=True)


def features(c, tower, gt, hw, so_mask):
    gravity = gravities(tower, gt)
    so, diagnostic = oracle_scale(tower, gt, so_mask)
    try:
        geo = geometry_npz(c, tower, hw, gravity['G1'], 1., 'features_s1_G1')
    except ValueError as exc:
        return dict(capture=c['canonical'], room=c['room'], split=c['k1_split'],
                    dataset=c['canonical'].split('/')[0], SO=so, refused=type(exc).__name__ + ':' + str(exc),
                    gravity={k: v.tolist() for k, v in gravity.items()},
                    gravity_error_deg=float(np.degrees(np.arccos(np.clip(np.dot(gravity['G1'], gravity['GO']), -1, 1)))),
                    **diagnostic)
    u, v = np.meshgrid(tower['grid_uv'], tower['grid_uv'])
    uv = np.column_stack((u.ravel(), v.ravel()))
    parts = []
    for k in range(1, 33):
        d = tower['depth_grid'][k - 1].ravel()
        R, t = geo.cam(k)
        p = (geo.rays(k, uv) * d[:, None]) @ R.T + t
        parts.append(p[np.isfinite(p).all(1) & np.isfinite(d) & (d > 0)])
    points = np.concatenate(parts)
    z1, z99 = np.percentile(points[:, 2], [1, 99])
    h_raw = float(np.median(geo.C[:, 2, 3] - z1))
    span = float(z99 - z1)
    if h_raw <= 0 or span <= 0:
        raise ValueError('nonpositive_height_feature')
    # Sensor room sampling verifies that the low-z tail lies below the cameras.
    gt_view = GTGeometry(dict(gt, inst=gt.get('inst')))
    sample = room.sample(gt_view, 'sensor')
    z = np.concatenate(sample['points'])[:, 2]
    gz1, gz99 = np.percentile(z, [1, 99])
    camera_height = float(np.median(gt['c2w'][gt['valid'].astype(bool), 2, 3]) - gz1)
    return dict(capture=c['canonical'], room=c['room'], split=c['k1_split'],
                dataset=c['canonical'].split('/')[0], SO=so, h_raw=h_raw, span=span,
                gravity={k: v.tolist() for k, v in gravity.items()},
                gravity_error_deg=float(np.degrees(np.arccos(np.clip(np.dot(gravity['G1'], gravity['GO']), -1, 1)))),
                gt_z1=float(gz1), gt_z99=float(gz99), gt_camera_height_above_z1=camera_height,
                gt_floor_at_low_z=bool(camera_height > 0), **diagnostic)


def fit_scales(train_features):
    assert train_features and all(x['split'] == 'train' for x in train_features), 'fit received heldout capture'
    refused = [x['capture'] for x in train_features if x.get('refused')]
    train_features = [x for x in train_features if not x.get('refused')]
    so = np.array([x['SO'] for x in train_features])
    h = np.array([x['h_raw'] for x in train_features])
    span = np.array([x['span'] for x in train_features])
    X = np.column_stack((np.ones(len(h)), np.log(h), np.log(span)))
    coef, residuals, rank, singular = np.linalg.lstsq(X, np.log(so), rcond=None)
    return dict(S1=float(np.median(so)), h_prior=float(np.median(so * h)),
                H_prior=float(np.median(so * span)), S4_coefficients=coef.tolist(),
                S4_design_rank=int(rank), S4_singular_values=singular.tolist(),
                provenance=dict(split='train', n_captures=len(train_features),
                                captures=[x['capture'] for x in train_features],
                                rooms=sorted({x['room'] for x in train_features}),
                                heldout_accessed_during_fit=False, refused_G1_excluded=refused), R2={})


def scales(f, fits):
    if f.get('refused'):
        return dict(SO=f['SO'], S1=fits['S1'], S2=float('nan'), S3=float('nan'), S4=float('nan'))
    h, span = f['h_raw'], f['span']
    return dict(SO=f['SO'], S1=fits['S1'], S2=fits['h_prior'] / h, S3=fits['H_prior'] / span,
                S4=float(np.exp(np.dot([1., np.log(h), np.log(span)], fits['S4_coefficients']))))


def distance(row, geo, gt, mode, lifted_cache=None):
    # Repeated benchmark rows may name the same raster instance. Memoization
    # preserves the deployed lifting output and avoids repeated dense queries.
    class CachedBackend:
        def __getattr__(self, name):
            return getattr(ground_lifting, name)

        def lift_object(self, name, masks, prob, geometry, *, tau, **kwargs):
            key = (row['gt_instances'][name], kwargs.get('depth_cut', False))
            if key not in lifted_cache:
                lifted_cache[key] = ground_lifting.lift_object(name, masks, prob, geometry, tau=tau, **kwargs)
            return dict(lifted_cache[key], name=name)

    def instances(name):
        iid = row.get('gt_instances', {}).get(name)
        if iid is None:
            return []
        masks = gt['inst'] == iid
        masks[~gt['valid'].astype(bool)] = False
        return [dict(instance_id=str(iid), masks=masks, prob=np.ones(32))]
    backend = ground_lifting if lifted_cache is None else CachedBackend()
    session = Session(backend, geo, masks=None, instances=instances,
                      program_version='3.14', geometry_mode=mode, tau=.5)
    a, b = row['operands']
    session.execute(f'<ground obj="{a}" mode="box">')
    session.execute(f'<ground obj="{b}" mode="box">')
    response = session.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
    match = re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m', response)
    return (float(match[1]), None) if match else (None, response)


def attempt(fn):
    try:
        return fn()
    except (ValueError, KeyError, FloatingPointError, np.linalg.LinAlgError) as exc:
        return None, type(exc).__name__ + ':' + str(exc)


def areas(geo, mode):
    try:
        sample = room.sample(geo, mode)
    except (ValueError, KeyError, FloatingPointError, np.linalg.LinAlgError) as exc:
        return {r: (None, type(exc).__name__ + ':' + str(exc)) for r in ('R0', 'R1')}
    def evaluate(kernel):
        result = kernel(**sample)
        return float(room.parse_response(room.format_result(result))['area_m2']), None
    return {r: attempt(lambda kernel=kernel: evaluate(kernel)) for r, kernel in [('R0', room.from_points), ('R1', r1)]}


def item(c, row, arm, prediction):
    pred, refusal = prediction
    return dict(row_id=row['id'], capture=c['canonical'], room=c['room'], split=c['k1_split'],
                dataset=c['canonical'].split('/')[0], type=row['type'], arm=arm, pred=pred,
                gt=float(row['gt_value']), mra=mra(pred, float(row['gt_value'])), refusal_code=refusal)


def evaluate_capture(c, gt, tower, hw, f, fits, gd_dir, test_linearity):
    rows = []
    scale_values = scales(f, fits)
    f['scales'] = scale_values
    f['scale_to_SO'] = {k: v / f['SO'] for k, v in scale_values.items()}
    f['scale_within_20pct'] = {k: .8 <= v <= 1.2 for k, v in f['scale_to_SO'].items()}
    geos = [('GT', GTGeometry(gt), 'sensor')]
    # Generate one arm at a time to bound memory.
    def conditions():
        yield from geos
        for g in GRAVITIES:
            for s in SCALES:
                arm = s + '+' + g
                if not np.isfinite(scale_values[s]):
                    yield arm, ('ValueError:feature_geometry_refused', None), 'predicted'
                    continue
                try:
                    yield arm, geometry_npz(c, tower, hw, f['gravity'][g], scale_values[s], arm), 'predicted'
                except ValueError as exc:
                    yield arm, (type(exc).__name__ + ':' + str(exc), None), 'predicted'
        if gd_dir:
            yield from deployed_conditions(c, gd_dir, f)
    for arm, geo, mode in conditions():
        start = time.monotonic()
        lifted_cache = {}
        if isinstance(geo, tuple):
            for row in c['rows']:
                if row['type'] == 'object_abs_distance':
                    rows.append(item(c, row, arm, (None, geo[0])))
                else:
                    for r in ('R0', 'R1'):
                        rows.append(item(c, row, arm + '+' + r, (None, geo[0])))
            continue
        ar = areas(geo, mode) if any(r['type'] == 'room_size_estimation' for r in c['rows']) else {}
        for row in c['rows']:
            if row['type'] == 'object_abs_distance':
                result = attempt(lambda: distance(row, geo, gt, mode, lifted_cache))
                rows.append(item(c, row, arm, result))
            elif row['type'] == 'room_size_estimation':
                for r in ('R0', 'R1'):
                    rows.append(item(c, row, arm + '+' + r, ar[r]))
            else:
                raise ValueError('unsupported row type')
        TIMINGS['program_seconds'] += time.monotonic() - start
        lifted_cache.clear()
        if test_linearity and arm == 'S1+G1':
            doubled = geometry_npz(c, tower, hw, f['gravity']['G1'], 2 * scale_values['S1'], 'linearity_2S1_G1')
            drows = [r for r in c['rows'] if r['type'] == 'object_abs_distance'][:1]
            for row in drows:
                first = next(r for r in rows if r['row_id'] == row['id'] and r['arm'] == arm)
                second, error = attempt(lambda: distance(row, doubled, gt, mode))
                deviation = None if first['pred'] is None or second is None else abs(second - 2 * first['pred'])
                log_test('distance_scale_linearity', deviation is not None and deviation <= .010000001,
                         capture=c['canonical'], row_id=row['id'], at_s=first['pred'], at_2s=second,
                         absolute_error_m=deviation, refusal=error, tolerance_m=.01)
            if ar:
                doubled_area = areas(doubled, mode)['R0']
                p, q = ar['R0'][0], doubled_area[0]
                ratio = q / p if p and q else None
                log_test('room_scale_linearity', ratio is not None and abs(ratio / 4 - 1) <= .10,
                         capture=c['canonical'], at_s=p, at_2s=q, ratio=ratio, relative_tolerance=.10,
                         note='Fixed 5 cm cells, 20 cm closing and frame votes need not be scale invariant.')
    f['loaded_depth_scale_count'] = 1
    return rows


def fit_r2(train_rows, fits):
    assert train_rows and all(r['split'] == 'train' for r in train_rows), 'R2 fit received heldout row'
    grouped = defaultdict(list)
    for r in train_rows:
        if r['type'] == 'room_size_estimation' and r['arm'].endswith('+R0') and not r['arm'].startswith('GT+'):
            grouped[r['arm'][:-3]].append(r)
    for condition, rows in grouped.items():
        eligible = [r for r in rows if r['pred'] is not None and r['pred'] > 0 and r['refusal_code'] is None]
        fits['R2'][condition] = dict(k=float(np.median([r['gt'] / r['pred'] for r in eligible])) if eligible else None,
                                    split='train', row_ids=[r['row_id'] for r in eligible],
                                    n_used=len(eligible), n_refused=len(rows) - len(eligible))


def add_r2(rows, fits):
    added = []
    for r in rows:
        if r['type'] != 'room_size_estimation' or not r['arm'].endswith('+R0') or r['arm'].startswith('GT+'):
            continue
        k = fits['R2'][r['arm'][:-3]]['k']
        pred = None if r['pred'] is None or k is None else r['pred'] * k
        added.append(dict(r, arm=r['arm'][:-1] + '2', pred=pred, mra=mra(pred, r['gt']),
                          refusal_code=r['refusal_code'] or ('no_train_R2_fit' if k is None else None)))
    return rows + added


def interval(values, rooms, draws):
    """Item-weighted mean with whole physical rooms resampled with replacement."""
    unique = sorted(set(rooms))
    sums = np.array([sum(v for v, r in zip(values, rooms) if r == name) for name in unique])
    counts = np.array([rooms.count(name) for name in unique])
    if not len(unique):
        return [None, None]
    indices = draws[len(unique)]
    estimates = sums[indices].sum(1) / counts[indices].sum(1)
    return (100 * np.percentile(estimates, [2.5, 97.5])).tolist()


class BootstrapDraws(dict):
    def __missing__(self, n):
        # Shared draws give paired comparisons identical room multiplicities.
        self[n] = np.random.default_rng(20261116).integers(0, n, size=(10000, n))
        return self[n]


def summarise(rows, captures, fits, inventory_data, so_mask):
    draws, stats = BootstrapDraws(), []
    by_key = {(r['row_id'], r['arm']): r for r in rows}
    for split in ('train', 'heldout'):
        for dataset in ('all', 'arkitscenes', 'scannet', 'scannetpp'):
            for typ in ('object_abs_distance', 'room_size_estimation'):
                subset = [r for r in rows if r['split'] == split and r['type'] == typ and (dataset == 'all' or r['dataset'] == dataset)]
                for arm in sorted({r['arm'] for r in subset}):
                    current = [r for r in subset if r['arm'] == arm]
                    rooms = [r['room'] for r in current]
                    values = [r['mra'] for r in current]
                    record = dict(split=split, dataset=dataset, type=typ, arm=arm,
                                  mean_mra=100 * float(np.mean(values)), ci95=interval(values, rooms, draws),
                                  n_items=len(current), n_rooms=len(set(rooms)),
                                  refusal_count=sum(r['refusal_code'] is not None for r in current), paired={})
                    refs = ['S1+G1', 'GT', 'SO+G1'] if typ == 'object_abs_distance' else ['S1+G1+R0', 'GT+R0', 'SO+G1+R0']
                    for ref in refs:
                        base = [by_key[(r['row_id'], ref)] for r in current]
                        assert all(a['room'] == b['room'] and a['split'] == b['split'] for a, b in zip(current, base))
                        difference = [a['mra'] - b['mra'] for a, b in zip(current, base)]
                        record['paired'][ref] = dict(mean_delta=100 * float(np.mean(difference)), ci95=interval(difference, rooms, draws))
                    stats.append(record)
    primary = []
    for dataset in ('all', 'arkitscenes', 'scannet', 'scannetpp'):
        for typ, arm, ref in [('object_abs_distance', 'S4+G1', 'S1+G1')] + [
                ('room_size_estimation', 'S4+G1+' + r, 'S1+G1+R0') for r in ('R0', 'R1', 'R2')]:
            matched = [s for s in stats if (s['dataset'], s['type'], s['arm']) == (dataset, typ, arm)]
            if len(matched) != 2:
                continue
            train = next(s for s in matched if s['split'] == 'train')['paired'][ref]
            heldout = next(s for s in matched if s['split'] == 'heldout')['paired'][ref]
            primary.append(dict(dataset=dataset, type=typ, arm=arm, reference=ref,
                                train_lower=train['ci95'][0], heldout_delta=heldout['mean_delta'],
                                c_rule=train['ci95'][0] > 0 and heldout['mean_delta'] > 0))
    diagnostic = []
    for split in ('train', 'heldout'):
        for dataset in ('all', 'arkitscenes', 'scannet', 'scannetpp'):
            cs = [c for c in captures if c['split'] == split and (dataset == 'all' or c['dataset'] == dataset)]
            if not cs:
                continue
            diagnostic.append(dict(split=split, dataset=dataset, n_captures=len(cs),
                                   scale_fraction_within_20pct={s:float(np.mean([c['scale_within_20pct'][s] for c in cs])) for s in SCALES},
                                   median_gravity_error_deg=float(np.median([c['gravity_error_deg'] for c in cs])),
                                   mean_absrel_so=float(np.mean([c['absrel_so_all_valid_grid'] for c in cs])),
                                   gt_floor_low_z_failures=[c['capture'] for c in cs if not c['gt_floor_at_low_z']]))
    return dict(units='benchmark points (100 x MRA)', bootstrap=dict(draws=10000, seed=20261116, unit='physical room',
                 interval='95% percentile', estimator='item-weighted mean; room clusters resampled with replacement'),
                room_reference='R0 for every paired reference', so_mask=so_mask, inventory=inventory_data,
                results=stats, primaries=primary, diagnostics=diagnostic, tests=TESTS)


def report(summary):
    lines = ['# E3 geometry pricing', '',
             'The harness measures deployed box-grid distance with GT instance masks and deployed room area. '
             'Scale fits and room calibration use train rooms only. Held-out rooms do not enter fitting.', '',
             'MRA values and paired differences are benchmark points. Intervals resample physical rooms '
             '10,000 times (seed 20261116). Errors and refusals receive zero. Room comparisons use R0 for '
             'S1+G1, GT and SO+G1 references.', '',
             'SO mask: ' + summary['so_mask'] + '. R2 multiplies the parsed R0 area by its train calibration factor.', '']
    for split in ('heldout', 'train'):
        for dataset in ('all', 'arkitscenes', 'scannet', 'scannetpp'):
            for typ in ('object_abs_distance', 'room_size_estimation'):
                lines += [f'## {split}: {dataset}, {typ}', '',
                          '| Arm | MRA [95% CI] | Items / rooms | Refusals | Δ S1+G1 [95% CI] | Δ GT [95% CI] | Δ SO+G1 [95% CI] | C-rule |',
                          '|---|---:|---:|---:|---:|---:|---:|:---:|']
                for s in summary['results']:
                    if (s['split'], s['dataset'], s['type']) != (split, dataset, typ):
                        continue
                    fmt = lambda mean, ci: f'{mean:.2f} [{ci[0]:.2f}, {ci[1]:.2f}]'
                    diffs = [fmt(v['mean_delta'], v['ci95']) for v in s['paired'].values()]
                    primary = next((p for p in summary['primaries'] if (p['dataset'], p['type'], p['arm']) == (dataset, typ, s['arm'])), None)
                    c_rule = ('PASS' if primary['c_rule'] else 'FAIL') if primary else '—'
                    lines.append(f"| {s['arm']} | {fmt(s['mean_mra'], s['ci95'])} | {s['n_items']} / {s['n_rooms']} | {s['refusal_count']} | " + ' | '.join(diffs) + f' | {c_rule} |')
                lines.append('')
    lines += ['## Diagnostics', '', '| Split | Dataset | Captures | Median gravity error (°) | SO AbsRel | S1 / S2 / S3 / S4 within 20% |',
              '|---|---|---:|---:|---:|---|']
    for d in summary['diagnostics']:
        fractions = ' / '.join(f"{100*d['scale_fraction_within_20pct'][s]:.1f}%" for s in SCALES[:-1])
        lines.append(f"| {d['split']} | {d['dataset']} | {d['n_captures']} | {d['median_gravity_error_deg']:.2f} | {d['mean_absrel_so']:.3f} | {fractions} |")
    lines += ['', '## Validation', '']
    for test in TESTS:
        lines.append('- ' + ('PASS' if test['passed'] else 'FAIL') + ': ' + json.dumps(test))
    lines += ['', '## Missing GT', '']
    lines += ['- ' + r['capture'] for r in summary['inventory']['missing']]
    lines += ['', 'Every imported tree source is hashed in RUN_RECEIPT.json. No candidate files or grounding scores are used.', '']
    (OUT / 'REPORT.md').write_text('\n'.join(lines))


def receipt(start, status, extra=None):
    for module in list(sys.modules.values()) + [programs._reference]:
        path = getattr(module, '__file__', None)
        if path and str(path).startswith(str(TREE)) and str(path).endswith('.py'):
            IMPORTED.add(path)
    IMPORTED.add(str(programs.REFERENCE))
    return dict(status=status, environment=sys.executable, python=sys.version, numpy=np.__version__,
                CPU_only=True, thread_limit=8, CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],
                manifest=dict(path=str(MANIFEST), sha256=sha(MANIFEST)),
                imported_source_sha256={p:sha(p) for p in sorted(IMPORTED) if Path(p).is_file()},
                converter=dict(path=str(CONVERTER), sha256=sha(CONVERTER)),
                harness_sha256={p.name:sha(p) for p in [ROOT / 'harness.py', ROOT / 'room_rules.py', ROOT / 'run.sh']},
                elapsed_seconds=time.monotonic() - start, timings=dict(TIMINGS),
                forbidden_data_access='candidates.json blocked by Python audit hook', **(extra or {}))


def unit_tests():
    cases = [(100,100,1.), (50,100,0.), (75,100,.5), (95,100,.9), (None,100,0.), (200,100,0.)]
    for pred, truth, expected in cases:
        assert mra(pred,truth) == expected, (pred, truth, expected, mra(pred,truth))
    log_test('MRA_hand_values', True, cases=cases)
    d = np.ones((32,51,51))
    conf = np.arange(d.size).reshape(d.shape).astype(float)
    gt = dict(depth=np.ones((32,51,51))*2, valid=np.ones(32,bool))
    tower = dict(grid_uv=np.linspace(0,1000,51), depth_grid=d, depth_conf_grid=conf)
    so, diag = oracle_scale(tower,gt,'specified')
    assert so == 2 and diag['frozen_mask_equal']
    log_test('frozen_rule_synthetic_same_domain', True, selected=diag['so_selected_points'])
    gt['depth'][31,50,50] = 12
    _, diag = oracle_scale(tower,gt,'specified')
    assert diag['frozen_mask_different_points'] == 1
    log_test('frozen_rule_GT_range_contract', True, note='Specified positive-GT SO differs from frozen 0.1–10 m eligibility.', **diag)
    raw = np.zeros((64,9)); raw[:,6] = 1; raw[:,7:] = 1.2
    c = dict(canonical='synthetic/test', anchor_indices=list(range(0,64,2)))
    tower.update(raw_pose=raw, anchor_slots=np.arange(0,64,2))
    geo = geometry_npz(c,tower,[240,320],[0,-1,0],2,'unit')
    assert np.allclose(geo.depth_grid,2) and geo.depth_scale_count == 1
    log_test('geometry_load_single_scale', True, depth_scale_count=geo.depth_scale_count)
    u, v = np.meshgrid(np.linspace(0,1,51), np.linspace(0,1,51))
    tower['depth_grid'] = np.broadcast_to(2 + .2*u + .1*v, (32,51,51)).copy()
    geo = geometry_npz(c,tower,[40,48],[0,-1,0],1,'session_unit')
    inst = np.zeros((32,40,48),int)
    inst[:,10:25,5:17] = 1
    inst[:,10:25,30:42] = 2
    row = dict(operands=['a','b'],gt_instances={'a':1,'b':2})
    gt = dict(inst=inst,valid=np.ones(32,bool))
    first = distance(row,geo,gt,'predicted')
    cache = {}
    second = distance(row,geo,gt,'predicted',cache)
    third = distance(row,geo,gt,'predicted',cache)
    assert first[0] is not None and first == second == third
    log_test('deployed_session_GT_masks_and_cache_parity', True, prediction=first[0],cached_instances=len(cache))
    x,y = np.meshgrid(np.arange(0,1,.025),np.arange(0,1,.025))
    floor = np.column_stack((x.ravel(),y.ravel(),np.zeros(x.size)))
    high = np.column_stack((x.ravel()+1,y.ravel(),np.ones(x.size)))
    sample = dict(points=[np.concatenate((floor,high))]*2,frames=[1,2],geometry_mode='predicted',gravity_source='test')
    full, band = room.from_points(**sample),r1(**sample)
    assert band['area_m2'] < full['area_m2'] and band['min_frames'] == 2
    log_test('R1_excludes_high_overhang',True,R0=full['area_m2'],R1=band['area_m2'])
    try:
        fit_scales([dict(split='heldout')])
    except AssertionError:
        log_test('fit_rejects_heldout', True)
    else:
        raise AssertionError('heldout fit accepted')


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('command', choices=['preflight', 'run'])
    parser.add_argument('--approved-heavy-io', action='store_true')
    parser.add_argument('--so-mask', choices=['specified','frozen'], default='specified')
    parser.add_argument('--gd-dir', type=Path)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    start = time.monotonic()
    try:
        unit_tests()
        cs, cache, inv = inventory()
        if args.command == 'preflight':
            dump(OUT / 'RUN_RECEIPT.json', receipt(start,'preflight', dict(inventory=inv)))
            print(json.dumps(inv), flush=True)
            return
        if not args.approved_heavy_io:
            raise ValueError('The cluster rules require explicit approval before the full raster read.')
        train_cs = [c for c in cs if c['k1_split'] == 'train']
        heldout_cs = [c for c in cs if c['k1_split'] == 'heldout']
        train_features = []
        # This loop never opens a heldout raster, row or tower cache.
        for i,c in enumerate(train_cs):
            assert c['k1_split'] == 'train'
            gt,tower,hw = load_capture(c,cache[digest(c)],False)
            f = features(c,tower,gt,hw,args.so_mask)
            train_features.append(f)
            print(json.dumps(dict(stage='train_features', done=i+1,total=len(train_cs),capture=c['canonical'])),flush=True)
        fits = fit_scales(train_features)
        fits['manifest_sha256'] = sha(MANIFEST)
        fits['SO_mask'] = args.so_mask
        fits['GD_directory'] = str(args.gd_dir) if args.gd_dir else None
        dump(OUT / 'FITS.json',fits)
        feature_map = {f['capture']:f for f in train_features}
        all_rows, capture_diagnostics = [], []
        tested_types = defaultdict(int)
        for split, selected in [('train',train_cs),('heldout',heldout_cs)]:
            split_rows = []
            for i,c in enumerate(selected):
                gt,tower,hw = load_capture(c,cache[digest(c)],True)
                f = feature_map[c['canonical']] if split == 'train' else features(c,tower,gt,hw,args.so_mask)
                test = any(tested_types[r['type']] < 3 for r in c['rows'])
                result = evaluate_capture(c,gt,tower,hw,f,fits,args.gd_dir,test)
                if test:
                    for typ in set(r['type'] for r in c['rows']):
                        tested_types[typ] += 1
                split_rows.extend(result)
                capture_diagnostics.append(f)
                # Persist per-capture results so an interruption leaves reviewable evidence.
                dest = OUT / 'captures'
                dest.mkdir(exist_ok=True)
                dump(dest / (c['canonical'].replace('/','__') + '.json'),dict(diagnostics=f,items=result))
                print(json.dumps(dict(stage=split+'_evaluate',done=i+1,total=len(selected),capture=c['canonical'],seconds=time.monotonic()-start)),flush=True)
            if split == 'train':
                fit_r2(split_rows,fits)
                dump(OUT / 'FITS.json',fits)
            all_rows.extend(add_r2(split_rows,fits))
        assert len(capture_diagnostics) == 296
        for filename, values in [('PER_ITEM.jsonl',all_rows),('PER_CAPTURE.jsonl',capture_diagnostics)]:
            with (OUT / filename).open('w') as f:
                for value in values:
                    f.write(json.dumps(clean(value),allow_nan=False)+'\n')
        log_test('all_capture_single_scale_and_frozen_selection', all(c['loaded_depth_scale_count']==1 and c['frozen_rule_check_pass'] for c in capture_diagnostics),n_captures=len(capture_diagnostics),
                 literal_SO_frozen_mask_equal_captures=sum(c['frozen_mask_equal'] for c in capture_diagnostics),
                 mean_SO_absrel=float(np.mean([c['absrel_so_all_valid_grid'] for c in capture_diagnostics])))
        log_test('literal_SO_mask_equals_frozen_estimator',all(c['frozen_mask_equal'] for c in capture_diagnostics),
                 different_points=sum(c['frozen_mask_different_points'] for c in capture_diagnostics),
                 note='The specified positive-GT rule and frozen 0.1–10 m rule are checked separately; a mismatch is not treated as a pass.')
        log_test('GT_low_z_floor_sanity',all(c['gt_floor_at_low_z'] for c in capture_diagnostics),
                 failed_captures=[c['capture'] for c in capture_diagnostics if not c['gt_floor_at_low_z']])
        for typ,arm,expected in [('object_abs_distance','GT',82),('room_size_estimation','GT+R0',99)]:
            rows=[r for r in all_rows if r['split']=='train' and r['type']==typ and r['arm']==arm]
            mean=100*float(np.mean([r['mra'] for r in rows]))
            log_test('GT_ceiling_'+typ,mean>=expected-10,train_mra=mean,n_items=len(rows),
                     reference_expectation=expected,note='Sanity threshold is reference expectation minus 10 points; results are not adjusted.')
        summary=summarise(all_rows,capture_diagnostics,fits,inv,args.so_mask)
        dump(OUT/'SUMMARY.json',summary)
        report(summary)
        dump(OUT/'RUN_RECEIPT.json',receipt(start,'complete',dict(inventory=inv,tests_failed=[t for t in TESTS if not t['passed']])))
        print('COMPLETE',flush=True)
    except BaseException as exc:
        dump(OUT/'RUN_RECEIPT.json',receipt(start,'failed',dict(error=repr(exc),traceback=traceback.format_exc())))
        raise


if __name__ == '__main__':
    main()
