"""Small fabricated local receipts exercise gates, never supply decision evidence."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK))
import score_fov as f
import json
import time
import numpy as np


def main():
    begin = time.monotonic()
    inputs = f.Inputs()
    bars = inputs.read(f.BARS)
    reference = inputs.read(f.REFERENCE)
    inputs.check(f.__file__)
    inputs.check(f.KIT / 'core.py')
    inputs.check(f.KIT / 'score_400.py')
    inputs.check(sys.executable)
    inputs.check(__file__)
    fixtures = WORK / 'tests' / ('fixtures_' + str(time.time_ns()))
    fixtures.mkdir()
    captures = bars['captures'][:2]
    blobs = {c['key']: inputs.blob(c['own544']['path'], c['own544']['sha256']) for c in captures}
    arrays = {c['key']: inputs.arrays(c['own544']['path'], c['own544']['sha256']) for c in captures}
    outcomes = []

    def write(c, mutation=None):
        folder = fixtures / c['key']
        folder.mkdir(exist_ok=True)
        own = {k: v.copy() for k, v in arrays[c['key']].items()}
        depth = own['depth'].copy()
        ref = np.asarray(reference['captures'][c['canonical']]['fov_hw_rad'], dtype=np.float32)
        values = {'depth': depth.copy(), 'depth_V1': depth.copy(), 'depth_V2': depth.copy(),
                  'fov_B': ref.copy(), 'fov_V1': ref.copy(), 'fov_V2': ref.copy()}
        if mutation == 'own_bit':
            own['depth'].view(np.uint64).flat[0] ^= np.uint64(1)
        if mutation == 'fov_bit':
            values['depth'].view(np.uint64).flat[0] ^= np.uint64(1)
        if mutation == 'v2':
            values['fov_V2'][0, 0] += 1e-5
        if mutation == 'range':
            values['fov_V1'][0, 0] = 0
        if mutation == 'nan':
            values['depth_V2'][0, 0, 0] = np.nan
        if mutation == 'shape':
            values['depth_V1'] = depth[:31]
        if mutation == 'own_bit':
            np.savez(folder / 'own.npz', **own)
        else:
            (folder / 'own.npz').write_bytes(blobs[c['key']])
        np.savez(folder / 'fov.npz', **values)
        for receipt_name, filename in [('PHASE_COMPLETE.json', 'own.npz'), ('FOV_RECEIPT.json', 'fov.npz')]:
            rec = {'test_fixture': True, 'input_sha256': dict(inputs.pins), 'capture_sha256': c['capture_sha256'],
                   'checkpoint': {'path': 'TEST_FIXTURE_ONLY', 'sha256': f.CHECKPOINT_SHA},
                   'files': {filename: f.core.sha(folder / filename)}, 'served_equal': True}
            if mutation == 'checkpoint' and receipt_name == 'FOV_RECEIPT.json':
                rec['checkpoint']['sha256'] = '0' * 64
            if mutation == 'phase_checkpoint' and receipt_name == 'PHASE_COMPLETE.json':
                rec['checkpoint']['sha256'] = '0' * 64
            if mutation == 'file_sha' and receipt_name == 'FOV_RECEIPT.json':
                rec['files']['fov.npz'] = '0' * 64
            if mutation == 'synthetic':
                rec['synthetic'] = True
            if mutation == 'capture':
                rec['capture_sha256'] = '0' * 64
            (folder / receipt_name).write_text(json.dumps(rec, indent=2) + '\n')

    for c in captures:
        write(c)

    def check(name, expected=None, population=None):
        t = time.monotonic()
        observed = None
        checked = f.Inputs()
        try:
            f.validate_probe(fixtures, captures if population is None else population, reference, checked)
        except f.core.Refusal as exc:
            observed = str(exc)
        passed = observed is None if expected is None else observed is not None and observed.startswith(expected + ':')
        outcomes.append({'name': name, 'pass': passed, 'expected': expected, 'observed': observed,
                         'seconds': time.monotonic() - t, 'input_sha256': {**inputs.pins, **checked.pins}})
        if not passed:
            raise AssertionError(outcomes[-1])

    check('valid fabricated probe')
    check('missing key', 'MISSING_KEY', bars['captures'][:3])
    check('unexpected capture', 'UNEXPECTED_CAPTURE', captures[:1])
    cases = [('own served depth one bit off', 'own_bit', 'SERVED_DEPTH_BITS'),
             ('fov served depth one bit off', 'fov_bit', 'SERVED_DEPTH_BITS'),
             ('wrong checkpoint sha', 'checkpoint', 'CHECKPOINT_SHA_MISMATCH'),
             ('wrong phase checkpoint sha', 'phase_checkpoint', 'CHECKPOINT_SHA_MISMATCH'),
             ('fov_V2 off by 1e-5', 'v2', 'FOV_V2_MISMATCH'),
             ('FoV out of range', 'range', 'FOV_RANGE_OR_SHAPE'),
             ('fov.npz sha mismatch', 'file_sha', 'FILE_SHA_MISMATCH'),
             ('synthetic receipt', 'synthetic', 'SYNTHETIC_RECEIPT'),
             ('wrong capture sha', 'capture', 'CAPTURE_SHA_MISMATCH'),
             ('nonfinite depth', 'nan', 'DEPTH_INVALID'),
             ('wrong depth shape', 'shape', 'DEPTH_INVALID')]
    for name, mutation, expected in cases:
        write(captures[0], mutation)
        check(name, expected)
    write(captures[0])
    check('restored valid fabricated probe')
    # Threshold boundaries and preference are deterministic rule tests, not observed scores.
    def rule_case(mean=-.25, lower=-.5, folds=(-.5, -.5), upper=(0., 0., 0.)):
        disp = {'combined': {a+'-A': {'points': mean, 'ci95': [lower, 0.]} for a in ('V1','V2')},
                'folds': [{'name': str(i), **{a+'-A': {'points': x} for a in ('V1','V2')}} for i,x in enumerate(folds)]}
        dist = {'combined': {a+'-A': {'ci95': [0., upper[2]]} for a in ('V1','V2')},
                'folds': [{'name': str(i), **{a+'-A': {'ci95': [0., x]} for a in ('V1','V2')}} for i,x in enumerate(upper[:2])]}
        return f.evaluate(disp, dist)
    assert rule_case()[1] == 'V2'
    for kwargs in ({'mean': -.25000001}, {'lower': -.50000001}, {'folds': (-.50000001, 0)}, {'upper': (0, -.00000001, 0)}):
        assert rule_case(**kwargs)[1] == 'NONE'
    result = {'input_sha256': inputs.pins, 'test_fixture': True, 'decision_usable': False,
              'command': f.shlex.join([sys.executable, '-B', str(Path(__file__).resolve())]),
              'tests': outcomes, 'rule_boundary_tests': 'PASS (inclusive thresholds; each single failure rejects)',
              'seconds': time.monotonic() - begin}
    result_path = WORK / 'tests' / ('REFUSAL_RESULTS_' + str(time.time_ns()) + '.json')
    result_path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'tests': len(outcomes), 'pass': all(t['pass'] for t in outcomes),
                      'seconds': result['seconds'], 'result': str(result_path)}))


if __name__ == '__main__':
    main()
