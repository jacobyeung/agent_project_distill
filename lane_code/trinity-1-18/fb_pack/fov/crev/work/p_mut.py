"""Refusal probe: build3 validate_probe on 3-capture producer-format subtrees, one mutation each (files hardlinked from
the full tree unless mutated). Expect the named refusal; the baseline must pass."""
import copy, hashlib, importlib.util, io, json, os, sys
from pathlib import Path
import numpy as np
W = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/crev/work')
FULL = W / 'tree/in/own_544_fov/native/probe'
FAKE = W / 'tree/fake_heldout'
BASE_CHECK = W / 'tree/in/own_544_fov/k1fwd2/FOV_CHECK.json'
MUT = W / 'mut'
spec = importlib.util.spec_from_file_location('sf3', '/scratch/jjyeung/orch_n30/fb_pack/fov/build3/score_fov.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bars = json.loads(m.BARS.read_text())
reference = json.loads(m.REFERENCE.read_text())
caps = bars['captures'][:3]
keys = [c['key'] for c in caps]
base_check = json.loads(BASE_CHECK.read_text())
heldout_key = sorted(p.name for p in FAKE.iterdir())[0]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_npz(key):
    with np.load(FULL / key / 'fov.npz', allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def npz(arrays):
    buf = io.BytesIO(); np.savez_compressed(buf, **arrays); return buf.getvalue()


def make(name, files=None, check=None, drop=(), extra_dirs=()):
    """files: {(key, filename): bytes}; check: mutated FOV_CHECK dict or path; returns (root, check_path)."""
    root = MUT / name / 'probe'
    root.mkdir(parents=True)
    files = files or {}
    for key in keys:
        if key in drop:
            continue
        (root / key).mkdir()
        for f in sorted(set(p.name for p in (FULL / key).iterdir()) | {n for k, n in files if k == key}):
            if (key, f) in files:
                if files[key, f] is not None:
                    (root / key / f).write_bytes(files[key, f])
            else:
                os.link(FULL / key / f, root / key / f)
    for src, dst in extra_dirs:
        (root / dst).mkdir()
        for p in src.iterdir():
            os.link(p, root / dst / p.name)
    if check is None:
        cpath = BASE_CHECK
    elif isinstance(check, Path):
        cpath = check
    else:
        cpath = MUT / name / 'FOV_CHECK.json'
        cpath.write_text(json.dumps(check))
    return root, cpath


def receipt(key, **change):
    r = json.loads((FULL / key / 'FOV_RECEIPT.json').read_text())
    for k, v in change.items():
        if v is DEL:
            r.pop(k)
        else:
            r[k] = v
    return r


DEL = object()


def jb(x):
    return (json.dumps(x, indent=2) + '\n').encode()


def with_fov(key, arrays, **rchange):
    b = npz(arrays)
    r = receipt(key, **rchange)
    r['files'] = {'fov.npz': sha(b)}
    return {(key, 'fov.npz'): b, (key, 'FOV_RECEIPT.json'): jb(r)}


def row_change(key, **change):
    c = copy.deepcopy(base_check)
    for row in c['rows']:
        if row['key'] == key:
            for k, v in change.items():
                if v is DEL:
                    row.pop(k)
                else:
                    row[k] = v
    return c


k0, k1, k2 = keys
a0 = load_npz(k0)
phase0 = json.loads((FULL / k0 / 'PHASE_COMPLETE.json').read_text())
with np.load(caps[0]['own544']['path'], allow_pickle=False) as z:
    A0 = z['depth']
checks_false = receipt(k0); checks_false['checks'] = dict(checks_false['checks'], second_pass_pose_fov_bit_identical=False)
checks_max = receipt(k0); checks_max['checks'] = dict(checks_max['checks'], second_pass_pose_fov_max_abs=1e-9)
checks_nomax = receipt(k0); checks_nomax['checks'] = {'second_pass_pose_fov_bit_identical': True}
ckpt_bad = receipt(k0); ckpt_bad['checkpoint'] = dict(ckpt_bad['checkpoint'], sha256='0' * 64)
own_diff = A0.copy(); own_diff.flat[0] = np.nextafter(own_diff.flat[0], np.inf)
own_bytes = npz({'depth': own_diff, 'gravity': np.zeros(3)})
phase_own = dict(phase0, files={'own.npz': sha(own_bytes)})
tamper = bytearray((FULL / k0 / 'fov.npz').read_bytes()); tamper[-30] ^= 1
fov_v2_small = dict(a0, fov_V2=(a0['fov_V2'].astype(np.float64) + 1e-7).astype(np.float32))
fov_v2_big = dict(a0, fov_V2=(a0['fov_V2'].astype(np.float64) + 1e-5).astype(np.float32))
roll = {k: (lambda a: dict(a, depth_V2=np.roll(a['depth_V2'], 1, axis=0)))(load_npz(k)) for k in keys}
roll_files = {}
for k in keys:
    roll_files.update(with_fov(k, roll[k]))

cases = {
    'baseline': ({}, None, (), (), None),
    'missing_key': ({}, None, (k2,), (), 'MISSING_KEY'),
    'heldout_dir_present': ({}, None, (), ((FAKE / heldout_key, heldout_key),), 'UNEXPECTED_CAPTURE'),
    'fov_npz_bytes_tampered': ({(k0, 'fov.npz'): bytes(tamper)}, None, (), (), 'FILE_SHA_MISMATCH'),
    'receipt_fov_sha_wrong': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, files={'fov.npz': '0' * 64}))}, None, (), (), 'FILE_SHA_MISMATCH'),
    'receipt_files_absent': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, files=DEL))}, None, (), (), 'MISSING'),
    'receipt_absent': ({(k0, 'FOV_RECEIPT.json'): None}, None, (), (), 'MISSING'),
    'receipt_path_escape': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, files={'fov.npz': sha((FULL / k0 / 'fov.npz').read_bytes()), '../x': '0' * 64}))}, None, (), (), 'RECEIPT_FILE_PATH'),
    'receipt_synthetic': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, synthetic=True))}, None, (), (), 'SYNTHETIC_RECEIPT'),
    'phase_synthetic': ({(k0, 'PHASE_COMPLETE.json'): jb(dict(phase0, synthetic=True))}, None, (), (), 'SYNTHETIC_RECEIPT'),
    'phase_checkpoint_wrong': ({(k0, 'PHASE_COMPLETE.json'): jb(dict(phase0, checkpoint={'sha256': '0' * 64}))}, None, (), (), 'CHECKPOINT_SHA_MISMATCH'),
    'receipt_checkpoint_wrong': ({(k0, 'FOV_RECEIPT.json'): jb(ckpt_bad)}, None, (), (), 'CHECKPOINT_SHA_MISMATCH'),
    'receipt_capture_sha_wrong': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, capture_sha256='0' * 64))}, None, (), (), 'CAPTURE_SHA_MISMATCH'),
    'phase_lists_absent_file': ({(k0, 'PHASE_COMPLETE.json'): jb(dict(phase0, files={'own.npz': phase0['files']['own.npz'], 'extra.bin': '0' * 64}))}, None, (), (), 'MISSING'),
    'own_npz_present_one_bit_off': ({(k0, 'own.npz'): own_bytes, (k0, 'PHASE_COMPLETE.json'): jb(phase_own)}, None, (), (), 'SERVED_DEPTH_BITS'),
    'fov_npz_depth_one_bit_off': (with_fov(k0, dict(a0, depth=own_diff)), None, (), (), 'SERVED_DEPTH_BITS'),
    'P1_control_false': ({(k0, 'FOV_RECEIPT.json'): jb(checks_false)}, None, (), (), 'P1_CONTROL_BITS'),
    'P1_control_max_abs_1e-9': ({(k0, 'FOV_RECEIPT.json'): jb(checks_max)}, None, (), (), 'P1_CONTROL_MAX_ABS'),
    'P1_control_max_abs_absent': ({(k0, 'FOV_RECEIPT.json'): jb(checks_nomax)}, None, (), (), 'P1_CONTROL_MAX_ABS'),
    'P1_served_sha_wrong': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, served_depth_sha256='0' * 64))}, None, (), (), 'P1_SERVED_DEPTH_SHA256'),
    'P1_served_sha_float32': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, served_depth_sha256=sha(A0.astype(np.float32).tobytes())))}, None, (), (), 'P1_SERVED_DEPTH_SHA256'),
    'P1_fovcheck_absent': ({}, MUT / 'nonexistent_FOV_CHECK.json', (), (), 'MISSING'),
    'P1_fovcheck_train_served_false': ({}, row_change(k1, served_equal=False), (), (), 'P1_PARITY_SERVED_EQUAL'),
    'P1_fovcheck_train_served_absent': ({}, row_change(k1, served_equal=DEL), (), (), 'P1_PARITY_SERVED_EQUAL'),
    'P1_fovcheck_heldout_served_false': ({}, row_change(heldout_key, served_equal=False), (), (), 'P1_PARITY_SERVED_EQUAL'),
    'P1_fovcheck_train_row_absent': ({}, dict(base_check, rows=[r for r in base_check['rows'] if r['key'] != k1]), (), (), 'P1_PARITY_KEY_MISSING'),
    'P1_fovcheck_row_second_pass': ({}, row_change(k1, second_pass_max_abs=1e-7), (), (), 'P1_ROW_SECOND_PASS'),
    'P3_anchor_absent': ({}, row_change(k1, anchor_indices=DEL), (), (), 'P3_ANCHOR_INDICES_MISSING'),
    'P3_anchor_wrong': ({}, row_change(k1, anchor_indices=list(range(32))), (), (), 'P3_ANCHOR_INDICES'),
    'P3_grid_absent': ({}, row_change(k1, grid_uv=DEL), (), (), 'P3_GRID_UV_MISSING'),
    'P3_grid_sha_wrong': ({}, row_change(k1, grid_uv='0' * 64), (), (), 'P3_GRID_UV_SHA256'),
    'P3_grid_values_wrong': ({}, row_change(k1, grid_uv=np.linspace(0, 1000, 52).tolist()), (), (), 'P3_GRID_UV'),
    'P3_row_unscored': ({}, row_change(k1, scored=False), (), (), 'P3_ROW_NOT_SCORED'),
    'P3_row_receipt_ok_false': ({}, row_change(k1, receipt_ok=False), (), (), 'P3_ROW_RECEIPT_OK'),
    'P3_row_capture_sha_false': ({}, row_change(k1, capture_sha256_equal=False), (), (), 'P3_ROW_CAPTURE_SHA256_EQUAL'),
    'P4_boundaries_wrong': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, boundaries_sha256='1' * 64))}, None, (), (), 'P4_BOUNDARIES_SHA256'),
    'P4_boundaries_absent': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, boundaries_sha256=DEL))}, None, (), (), 'P4_BOUNDARIES_SHA256_MISSING'),
    'P4_V1_formula_wrong': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, sources={'V1': 'depth.fov(states)'}))}, None, (), (), 'P4_V1_FORMULA'),
    'P4_missing_nonempty': ({(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, missing={'V2': 'MISSING'}))}, None, (), (), 'P4_VARIANTS_MISSING'),
    'P4_fov_V2_off_1e-7': (with_fov(k0, fov_v2_small), None, (), (), 'P4_FOV_V2_EXACT'),
    'fov_V2_off_1e-5': (with_fov(k0, fov_v2_big), None, (), (), 'FOV_V2_MISMATCH'),
    'fov_V2_float64_same_values': (with_fov(k0, dict(a0, fov_V2=a0['fov_V2'].astype(np.float64))), None, (), (), 'P4_FOV_V2_EXACT'),
    'fov_B_equals_pi': (with_fov(k0, dict(a0, fov_B=np.full((32, 2), np.pi, np.float32))), None, (), (), 'FOV_RANGE_OR_SHAPE'),
    'fov_B_zero': (with_fov(k0, dict(a0, fov_B=np.zeros((32, 2), np.float32))), None, (), (), 'FOV_RANGE_OR_SHAPE'),
    'fov_V1_nan': (with_fov(k0, dict(a0, fov_V1=np.where(np.arange(64).reshape(32, 2) == 5, np.nan, a0['fov_V1']).astype(np.float32))), None, (), (), 'FOV_RANGE_OR_SHAPE'),
    'fov_B_absent': (with_fov(k0, {k: v for k, v in a0.items() if k != 'fov_B'}), None, (), (), 'FOV_RANGE_OR_SHAPE'),
    'fov_V1_shape': (with_fov(k0, dict(a0, fov_V1=a0['fov_V1'][:31])), None, (), (), 'FOV_RANGE_OR_SHAPE'),
    'depth_V1_negative': (with_fov(k0, dict(a0, depth_V1=-a0['depth_V1'])), None, (), (), 'DEPTH_INVALID'),
    'depth_V2_absent': (with_fov(k0, {k: v for k, v in a0.items() if k != 'depth_V2'}), None, (), (), 'DEPTH_INVALID'),
    'depth_V1_shape': (with_fov(k0, dict(a0, depth_V1=a0['depth_V1'][:, :, :50])), None, (), (), 'DEPTH_INVALID'),
    'P5_V1_transposed': (with_fov(k0, dict(a0, depth_V1=a0['depth_V1'].swapaxes(1, 2).copy())), None, (), (), 'P5_ORIENTATION'),
    'P5_V2_flipped_vertical': (with_fov(k0, dict(a0, depth_V2=a0['depth_V2'][:, ::-1, :].copy())), None, (), (), 'P5_ORIENTATION'),
    'P5_V2_anchors_rolled_all': (roll_files, None, (), (), 'P5_'),
}
results = {}
for name, (files, check, drop, extra, expect) in cases.items():
    root, cpath = make(name, files, check, drop, extra)
    inputs = m.Inputs()
    try:
        m.validate_probe(root, caps, reference, inputs, None, cpath, None, None)
        got = 'PASSED'
    except m.core.Refusal as exc:
        got = 'REFUSAL ' + str(exc)[:200]
    except Exception as exc:
        got = 'UNNAMED ' + type(exc).__name__ + ': ' + str(exc)[:160]
    ok = (got == 'PASSED') if expect is None else got.startswith('REFUSAL ' + expect)
    results[name] = {'expect': expect or 'PASSED', 'got': got, 'ok': ok}
    if name == 'baseline':
        results[name]['integrity'] = {k: v for k, v in inputs.integrity.items() if k != 'parity_file'}
# The code-diff option waives P4 boundaries for any receipt value with any non-empty file.
root, cpath = make('accept_diff_waives_boundaries', {(k0, 'FOV_RECEIPT.json'): jb(receipt(k0, boundaries_sha256='1' * 64)),
                                                     (k1, 'FOV_RECEIPT.json'): jb(receipt(k1, boundaries_sha256='2' * 64))})
diff = MUT / 'accept_diff_waives_boundaries' / 'any.txt'; diff.write_text('not a diff\n')
try:
    m.validate_probe(root, caps, reference, m.Inputs(), None, cpath, sha(diff.read_bytes()), diff)
    results['accept_diff_waives_boundaries'] = {'got': 'PASSED with two different non-pinned boundaries_sha256 and a non-diff file'}
except Exception as exc:
    results['accept_diff_waives_boundaries'] = {'got': type(exc).__name__ + ': ' + str(exc)[:200]}
print(json.dumps(results, indent=1))
print('ALL_OK' if all(r.get('ok', True) for r in results.values()) else 'SOME_UNEXPECTED',
      [n for n, r in results.items() if r.get('ok') is False])
