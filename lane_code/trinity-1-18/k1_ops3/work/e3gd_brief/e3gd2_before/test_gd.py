"""CPU subset driver and regression checks; keep every artifact under e3gd/out.

Run: python -B test_gd.py --gd-dir out/gd_tests/convert_fixture
The stock harness CLI has no capture subset option. This driver calls its real
load/features/evaluate functions on three selected captures with frozen fits.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import types
from unittest.mock import patch

import harness as H

ORIGINAL = Path('/scratch/jjyeung/orch_n30/e3_geom/work/harness')
CANARY = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests/canary')
NAMES = ('arkitscenes/41048124', 'arkitscenes/41069076', 'arkitscenes/41069175')
CODE = 'GeometryError:reference_camera_up_opposes_gravity'


def encoded(value):
    return (json.dumps(H.clean(value), indent=2, allow_nan=False) + '\n').encode()


def sealed():
    assert H.geometry_profiles.GeometryContract.validate is H.SEALED_VALIDATE


def baseline():
    source = (ORIGINAL / 'harness.py').read_bytes()
    assert hashlib.sha256(source).hexdigest() == 'a38d1ad20f6c0cd7843320d0ba98dc6f43f16624c715a04a47ee51ef16c9cfa1'
    # Redirect only the workspace assertion; __file__ binds all writes to e3gd.
    source = source.decode().replace(str(ORIGINAL), str(H.ROOT))
    mod = types.ModuleType('e3_original_test')
    mod.__file__ = str(H.ROOT / 'harness.py')
    exec(compile(source, str(ORIGINAL / 'harness.py'), 'exec'), mod.__dict__)
    mod.OUT = H.OUT / 'baseline'
    mod.OUT.mkdir(exist_ok=True)
    return mod


def check_aggregation(root):
    captures = root / 'agg_captures'
    captures.mkdir()
    rows = []
    arms = ('S4+G1', 'GD_sealed', 'GD_reviewed')
    for split in ('train', 'heldout'):
        for i in range(3):
            for typ in ('object_abs_distance', 'room_size_estimation'):
                for a in arms:
                    for suffix in (('',) if typ == 'object_abs_distance' else ('+R0', '+R1')):
                        pred = None if a == 'GD_sealed' and i == 0 else 10.
                        rows.append(dict(row_id=f'{split}_{typ}_{i}', room=f'room_{i}',
                            split=split, type=typ, arm=a+suffix, dataset='fixture', gt=10.,
                            pred=pred, mra=H.mra(pred, 10.), refusal_code=CODE if pred is None else None))
    H.dump(captures / 'fixture.json', dict(items=rows))
    fits = dict(R2={a:dict(k=1., split='train') for a in arms})
    H.dump(root / 'agg_fits.json', fits)
    for split in ('train', 'heldout'):
        for ref in ('GD_reviewed', 'GD_sealed', 'GD_reviewed,GD_sealed'):
            result = subprocess.run([sys.executable, '-B', str(H.ROOT / 'agg.py'), str(captures),
                split, str(root / 'agg_fits.json'), ref], text=True, capture_output=True, check=True)
            (root / f'agg_{split}_{ref}.txt').write_text(result.stdout)
            for reference in ref.split(','):
                assert f'vs {reference}:' in result.stdout
                for rule in ('R0', 'R1', 'R2'):
                    assert f'vs {reference}+{rule}:' in result.stdout
            assert 'items=3 rooms=3' in result.stdout
    print('PASS aggregation: train/heldout, both references, comma list, R0/R1/R2, refusal denominator', flush=True)


def edge_cases(root, capture, source):
    empty = root / 'empty_convert'
    empty.mkdir()
    diag = {}
    result = list(H.deployed_conditions(capture, empty, diag))
    assert all(x[1] == ('FileNotFoundError:deployed_geometry_missing', None) for x in result)
    sealed()
    with H.np.load(source, allow_pickle=False) as z:
        arrays = {k:z[k] for k in z.files}
    for label, mutation, expected in (
        ('reviewed_refused', 'rotation', CODE),
        ('invalid_scale', 'scale', 'GeometryError:invalid_scale')):
        c = dict(capture, canonical='synthetic/' + label)
        dest = root / 'edge_convert' / H.digest(c['canonical'])[:16]
        dest.mkdir(parents=True)
        values = {k:v.copy() for k,v in arrays.items()}
        if mutation == 'rotation':
            values['camera_to_world'][:, :3, :3] = [[1,0,0],[0,0,-1],[0,1,0]]
        else:
            values['scale'] = H.np.array(-1.)
        H.np.savez(dest / 'geometry.npz', **values)
        diag = {}
        result = list(H.deployed_conditions(c, dest.parent, diag))
        assert all(x[1] == (expected, None) for x in result)
        assert all(d['refusal'] == expected and d['sha256'] == H.sha(dest / 'geometry.npz') for d in diag.values())
        sealed()
    with patch.object(H, 'load_geometry', side_effect=RuntimeError('test_non_geometry_failure')):
        try:
            H.load_reviewed_geometry(source, capture)
        except RuntimeError as exc:
            assert str(exc) == 'test_non_geometry_failure'
        else:
            raise AssertionError('non-geometry failure swallowed')
    sealed()
    try:
        H.gravity_guard.install(H.geometry_profiles, H.GRAVITY_RECORDER)
    except RuntimeError as exc:
        assert str(exc) == 'gravity_guard_already_installed'
    else:
        raise AssertionError('second install succeeded')
    sealed()
    print('PASS edge cases: missing file, reviewed refusal, invalid scale, finally restoration, one install', flush=True)


def room_refusals(root, old, fits):
    np = H.np
    raw = np.zeros((64,9)); raw[:,6] = 1; raw[:,7:] = 1.2
    c = dict(canonical='synthetic/room', room='synthetic/room', k1_split='train',
             anchor_indices=list(range(0,64,2)), rows=[dict(id='synthetic_room',
             type='room_size_estimation', gt_value=1.)])
    u,v = np.meshgrid(np.linspace(0,1,51), np.linspace(0,1,51))
    tower = dict(raw_pose=raw, anchor_slots=np.arange(0,64,2), grid_uv=np.linspace(0,1000,51),
                 depth_grid=np.broadcast_to(2+.2*u+.1*v,(32,51,51)).copy())
    geo = H.geometry_npz(c,tower,[40,48],[0,-1,0],1,'room_fixture')
    gt = dict(depth=np.ones((32,40,48))*2, inst=np.zeros((32,40,48),int),
              K=geo.K[0], K_frames=geo.K, c2w=geo.C, valid=np.ones(32,bool))
    f = dict(SO=1., h_raw=1., span=1., gravity=dict(GO=[0,-1,0],G1=[0,-1,0]))
    bf, af = copy.deepcopy(f), copy.deepcopy(f)
    before = old.evaluate_capture(c,gt,tower,[40,48],bf,fits,None,False)
    after = H.evaluate_capture(c,gt,tower,[40,48],af,fits,root/'empty_convert',False)
    assert encoded(before) == encoded([r for r in after if not r['arm'].startswith('GD_')])
    assert encoded(bf) == encoded({k:v for k,v in af.items() if not k.startswith('GD_')})
    local_fits = copy.deepcopy(fits)
    H.fit_r2(after,local_fits)
    after = H.add_r2(after,local_fits)
    for arm in ('GD_sealed','GD_reviewed'):
        selected = [r for r in after if r['arm'].startswith(arm+'+')]
        assert {r['arm'] for r in selected} == {arm+'+'+rule for rule in ('R0','R1','R2')}
        assert all(r['pred'] is None and r['mra'] == 0 and
                   r['refusal_code'] == 'FileNotFoundError:deployed_geometry_missing' for r in selected)
        assert local_fits['R2'][arm]['n_refused'] == 1
    H.dump(root/'ROOM_REFUSALS.json',dict(items=after,fits=local_fits))
    sealed()
    print('PASS synthetic room: non-GD byte parity; missing GD scores zero in R0/R1/R2; R2 train denominator', flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--gd-dir', type=Path, required=True)
    args = parser.parse_args()
    fixture = args.gd_dir.resolve()
    assert fixture.is_relative_to(H.ROOT / 'out')
    fixture.mkdir(parents=True, exist_ok=False)
    root = fixture.parent
    H.OUT = root / 'changed'
    H.OUT.mkdir()
    captures_out = H.OUT / 'captures'
    captures_out.mkdir()
    old = baseline()
    manifest = json.loads(H.MANIFEST.read_text())
    cs = {c['canonical']:c for c in manifest['captures'] if c['canonical'] in NAMES}
    assert len(cs) == 3
    fits = json.loads((H.ROOT / 'out/FITS.json').read_text())
    fixtures = []
    for name in NAMES:
        c = cs[name]
        dest = fixture / H.digest(name)[:16]
        dest.mkdir()
        if name == NAMES[1]:
            H.dump(dest / 'CACHE_COMPLETE.json', dict(geometry=None,
                geometry_refusal=dict(code=CODE.split(':',1)[1], message=CODE.split(':',1)[1]),
                gravity_verdict=dict(sealed_refused=True, reviewed_refused=True)))
            fixtures.append(dict(capture=name, kind='synthetic missing/refused disposition'))
        else:
            source = CANARY / dest.name / 'geometry.npz'
            (dest / 'geometry.npz').write_bytes(source.read_bytes())
            assert H.sha(dest / 'geometry.npz') == H.sha(source)
            fixtures.append(dict(capture=name, source=str(source), sha256=H.sha(source)))
    H.dump(root / 'FIXTURE.json', fixtures)
    parity = []
    start = time.monotonic()
    for name in NAMES:
        c = cs[name]
        tower_dir = H.TOWERS / H.digest(name)[:16]
        receipt = json.loads((tower_dir / 'PHASE_COMPLETE.json').read_text())
        assert receipt['capture_sha256'] == H.digest(c)
        gt, tower, hw = H.load_capture(c, (tower_dir, receipt), True)
        sealed()
        before_f = old.features(c, tower, gt, hw, 'specified')
        before_rows = old.evaluate_capture(c, gt, tower, hw, before_f, fits, None, False)
        sealed()
        after_f = H.features(c, tower, gt, hw, 'specified')
        after_rows = H.evaluate_capture(c, gt, tower, hw, after_f, fits, fixture, False)
        sealed()
        before = dict(diagnostics=before_f, items=before_rows)
        after = dict(diagnostics={k:v for k,v in after_f.items() if k not in ('GD_sealed','GD_reviewed')},
            items=[r for r in after_rows if not r['arm'].startswith('GD_')])
        assert encoded(before) == encoded(after), name
        H.dump(old.OUT / (name.replace('/','__') + '.json'), before)
        H.dump(captures_out / (name.replace('/','__') + '.json'), dict(diagnostics=after_f, items=after_rows))
        H.dump(root / (name.replace('/','__') + '.non_GD.json'), after)
        for arm in ('GD_sealed','GD_reviewed'):
            selected = [r for r in after_rows if r['arm'] == arm]
            assert len(selected) == len(c['rows'])
            if name == NAMES[1] or (name == NAMES[2] and arm == 'GD_sealed'):
                assert after_f[arm]['refusal'] == CODE
                assert all(r['pred'] is None and r['mra'] == 0 and r['refusal_code'] == CODE for r in selected)
            else:
                assert 'refusal' not in after_f[arm]
                assert all(r['pred'] is not None for r in selected)
        parity.append(dict(capture=name, non_GD_rows=len(before_rows), bytes=len(encoded(before)),
                           sha256=hashlib.sha256(encoded(before)).hexdigest()))
        print('PASS real capture byte parity + GD disposition:', name, 'non_GD_rows',len(before_rows), flush=True)
    H.unit_tests()
    sealed()
    print('PASS original harness unit tests under sealed validator after GD_reviewed loads', flush=True)
    edge_cases(root, cs[NAMES[0]], fixture / H.digest(NAMES[0])[:16] / 'geometry.npz')
    room_refusals(root,old,fits)
    check_aggregation(root)
    result = dict(status='PASS', fixture=str(fixture), captures=parity,
                  elapsed_seconds=time.monotonic()-start, guard_identity=H.gravity_guard.identity())
    H.dump(root / 'RESULT.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
