"""Fabricated two-capture provenance tests; these receipts cannot bind a donor."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK))
import score_fov as f
import copy
import json
import time
import numpy as np


def main():
    inputs = f.Inputs()
    for path in (f.__file__, __file__, sys.executable, f.KIT / 'core.py', f.KIT / 'score_400.py'):
        inputs.check(path)
    inputs.read(f.FOV_BARS, f.FOV_BARS_SHA)
    inputs.read(f.AMENDMENT, f.AMENDMENT_SHA)
    bars = inputs.read(f.BARS)
    reference = inputs.read(f.REFERENCE)
    captures = bars['captures'][:2]
    baseline = {c['key']: inputs.arrays(c['own544']['path'], c['own544']['sha256']) for c in captures}
    root = WORK / 'tests' / ('amendment_' + str(time.time_ns()))
    probe = root / 'native' / 'probe'
    probe.mkdir(parents=True)
    outcomes = []

    def prepare():
        rows = []
        receipts = []
        phases = []
        values = []
        for c in captures:
            folder = probe / c['key']
            folder.mkdir(exist_ok=True)
            if (folder / 'own.npz').exists():
                (folder / 'own.npz').rename(folder / 'optional-own.saved')
            depth = baseline[c['key']]['depth'].copy()
            ref = np.asarray(reference['captures'][c['canonical']]['fov_hw_rad'], dtype=np.float32)
            values.append({'depth_V1': depth.copy(), 'depth_V2': depth.copy(),
                           'fov_B': ref.copy(), 'fov_V1': ref.copy(), 'fov_V2': ref.copy()})
            receipts.append({'test_fixture': True, 'input_sha256': dict(inputs.pins),
                'capture_sha256': c['capture_sha256'], 'checkpoint': {'sha256': f.CHECKPOINT_SHA},
                'checks': {'second_pass_pose_fov_bit_identical': True, 'second_pass_pose_fov_max_abs': 0.0},
                'served_depth_sha256': f.hashlib.sha256(np.ascontiguousarray(depth, dtype=np.float64).tobytes()).hexdigest(),
                'boundaries_sha256': f.BOUNDARIES_SHA, 'sources': {'V1': f.V1_SOURCE}, 'missing': {}})
            phases.append({'test_fixture': True, 'input_sha256': dict(inputs.pins),
                           'capture_sha256': c['capture_sha256'], 'checkpoint': {'sha256': f.CHECKPOINT_SHA}, 'files': {}})
            rows.append({'key': c['key'], 'served_equal': True, 'anchor_indices': c['anchor_indices'][:],
                         'grid_uv': np.linspace(0, 1000, 51, dtype=np.float32).tolist()})
        return values, receipts, phases, {'test_fixture': True, 'input_sha256': dict(inputs.pins), 'rows': rows}

    def case(name, expected=None, mutation=None, options=None):
        values, receipts, phases, parity = prepare()
        options = options or {}
        if mutation:
            mutation(values, receipts, phases, parity)
        for c, value, rec, phase in zip(captures, values, receipts, phases):
            folder = probe / c['key']
            np.savez(folder / 'fov.npz', **value)
            rec.setdefault('files', {'fov.npz': f.core.sha(folder / 'fov.npz')})
            phase['files'].setdefault('fov.npz', f.core.sha(folder / 'fov.npz'))
            for filename, obj in [('FOV_RECEIPT.json', rec), ('PHASE_COMPLETE.json', phase)]:
                (folder / filename).write_text(json.dumps(obj, allow_nan=False))
        (root / 'FOV_CHECK.json').write_text(json.dumps(parity, allow_nan=False))
        checked = f.Inputs()
        observed = None
        try:
            payloads = f.validate_probe(probe, captures, reference, checked, **options)
            assert len(payloads) == 2
        except f.core.Refusal as exc:
            observed = str(exc)
        passed = observed is None if expected is None else observed is not None and observed.startswith(expected + ':')
        outcomes.append({'name': name, 'pass': passed, 'expected': expected, 'observed': observed,
                         'input_sha256': {**inputs.pins, **checked.pins}, 'integrity': checked.integrity})
        assert passed, outcomes[-1]

    def recfield(key, value):
        return lambda v, r, p, q: r[0].__setitem__(key, value)
    def checkfield(key, value):
        return lambda v, r, p, q: r[0]['checks'].__setitem__(key, value)
    def rowfield(key, value):
        return lambda v, r, p, q: q['rows'][0].__setitem__(key, value)
    def drop_row(key):
        return lambda v, r, p, q: q['rows'][0].pop(key)

    case('accepted producer layout: no own.npz and no fov depth')
    case('P1 absent own.npz may be claimed by phase', mutation=lambda v,r,p,q: p[0]['files'].update({'own.npz': '0'*64}))
    case('P1 false same-function control', 'P1_CONTROL_BITS', checkfield('second_pass_pose_fov_bit_identical', False))
    case('P1 control field absent', 'P1_CONTROL_BITS', lambda v,r,p,q: r[0]['checks'].pop('second_pass_pose_fov_bit_identical'))
    case('P1 nonzero control residual', 'P1_CONTROL_MAX_ABS', checkfield('second_pass_pose_fov_max_abs', 1e-15))
    case('P1 max residual absent', 'P1_CONTROL_MAX_ABS', lambda v,r,p,q: r[0]['checks'].pop('second_pass_pose_fov_max_abs'))
    case('P1 bool is not a numeric residual', 'P1_CONTROL_MAX_ABS', checkfield('second_pass_pose_fov_max_abs', False))
    case('P1 served depth hash mismatch', 'P1_SERVED_DEPTH_SHA256', recfield('served_depth_sha256', '0'*64))
    case('P1 served depth hash absent', 'P1_SERVED_DEPTH_SHA256', lambda v,r,p,q: r[0].pop('served_depth_sha256'))
    case('P1 parity false', 'P1_PARITY_SERVED_EQUAL', rowfield('served_equal', False))
    case('P1 parity field absent', 'P1_PARITY_SERVED_EQUAL', drop_row('served_equal'))
    case('P1 parity capture absent', 'P1_PARITY_KEY_MISSING', lambda v,r,p,q: q['rows'].pop())
    case('P1 duplicate parity capture', 'P1_PARITY_DUPLICATE', lambda v,r,p,q: q['rows'].append(copy.deepcopy(q['rows'][0])))
    case('P1 all parity rows checked', 'P1_PARITY_SERVED_EQUAL', lambda v,r,p,q: q['rows'].append({'key':'TEST_METADATA_ONLY','served_equal':False}))
    case('P1 missing explicit parity file', 'MISSING', options={'fov_check': root/'MISSING_FOV_CHECK.json'})
    case('P1 explicit parity path accepted', options={'fov_check': root/'FOV_CHECK.json'})
    def own(v,r,p,q, corrupt=False):
        depth = baseline[captures[0]['key']]['depth'].copy()
        if corrupt: depth.view(np.uint64).flat[0] ^= np.uint64(1)
        np.savez(probe/captures[0]['key']/'own.npz', depth=depth)
    case('P1 optional own accepted', mutation=own)
    case('P1 optional own one bit off', 'SERVED_DEPTH_BITS', lambda v,r,p,q: own(v,r,p,q,True))
    case('P1 optional control depth accepted', mutation=lambda v,r,p,q: v[0].update(depth=baseline[captures[0]['key']]['depth'].copy()))
    case('P1 optional control depth differs', 'SERVED_DEPTH_BITS', lambda v,r,p,q: v[0].update(depth=baseline[captures[0]['key']]['depth']*1.000001))
    for suffix, bad in [('zero',0),('pi',np.pi),('nan',np.nan)]:
        case('P2 served FoV '+suffix, 'FOV_RANGE_OR_SHAPE', lambda v,r,p,q,bad=bad: v[0]['fov_B'].__setitem__((0,0),bad))
    case('P2 served FoV shape', 'FOV_RANGE_OR_SHAPE', lambda v,r,p,q: v[0].update(fov_B=v[0]['fov_B'][:31]))
    case('P2 served FoV absent', 'FOV_RANGE_OR_SHAPE', lambda v,r,p,q: v[0].pop('fov_B'))
    case('P3 anchors absent', 'P3_ANCHOR_INDICES_MISSING', drop_row('anchor_indices'))
    case('P3 anchors reordered', 'P3_ANCHOR_INDICES', rowfield('anchor_indices', captures[0]['anchor_indices'][::-1]))
    case('P3 grid absent', 'P3_GRID_UV_MISSING', drop_row('grid_uv'))
    case('P3 wrong grid', 'P3_GRID_UV', rowfield('grid_uv', list(range(51))))
    case('P3 wrong grid shape', 'P3_GRID_UV', rowfield('grid_uv', [0]))
    def grid_hash(v,r,p,q):
        for row in q['rows']:
            row.pop('grid_uv')
            row['grid_uv_sha256'] = f.hashlib.sha256(np.linspace(0,1000,51,dtype=np.float32).tobytes()).hexdigest()
    case('P3 float32 grid digest accepted', mutation=grid_hash)
    case('P3 both grid representations checked', 'P3_GRID_UV_SHA256', rowfield('grid_uv_sha256', '0'*64))
    case('P4 code pin differs', 'P4_BOUNDARIES_SHA256', recfield('boundaries_sha256', '0'*64))
    case('P4 code pin absent', 'P4_BOUNDARIES_SHA256_MISSING', lambda v,r,p,q: r[0].pop('boundaries_sha256'))
    case('P4 V1 formula differs', 'P4_V1_FORMULA', recfield('sources', {'V1':'sigmoid(depth.fov(states))'}))
    case('P4 V1 formula absent', 'P4_V1_FORMULA', recfield('sources', {}))
    case('P4 variant reported missing', 'P4_VARIANTS_MISSING', recfield('missing', {'V2':'MISSING'}))
    case('P4 missing field absent', 'P4_VARIANTS_MISSING', lambda v,r,p,q: r[0].pop('missing'))
    case('P4 fov bytes mismatch', 'FILE_SHA_MISMATCH', recfield('files', {'fov.npz':'0'*64}))
    case('P4 fov hash absent', 'MISSING', recfield('files', {}))
    case('P4 checkpoint differs', 'CHECKPOINT_SHA_MISMATCH', recfield('checkpoint', {'sha256':'0'*64}))
    case('P4 checkpoint absent', 'CHECKPOINT_SHA_MISMATCH', lambda v,r,p,q: r[0].pop('checkpoint'))
    case('P4 capture differs', 'CAPTURE_SHA_MISMATCH', recfield('capture_sha256', '0'*64))
    case('P4 capture absent', 'CAPTURE_SHA_MISMATCH', lambda v,r,p,q: r[0].pop('capture_sha256'))
    def perturb_v2(v,r,p,q):
        v[0]['fov_V2'][0,0] = np.nextafter(v[0]['fov_V2'][0,0], np.float32(np.inf))
    case('P4 V2 one float32 ULP off below bars tolerance', 'P4_FOV_V2_EXACT', perturb_v2)
    case('P4 V2 wrong dtype', 'P4_FOV_V2_EXACT', lambda v,r,p,q: v[0].update(fov_V2=v[0]['fov_V2'].astype(np.float64)))
    published = WORK / 'k1fwd2_example_boundaries_diff.txt'
    inputs.check(published)
    accepted = {'accept_fov_code_diff':f.core.sha(published),'fov_code_diff':published}
    case('P4 explicit published diff accepted and recorded', mutation=recfield('boundaries_sha256','0'*64), options=accepted)
    case('P4 diff does not waive absent source pin', 'P4_BOUNDARIES_SHA256_MISSING', lambda v,r,p,q:r[0].pop('boundaries_sha256'), accepted)
    case('P4 diff does not waive formula', 'P4_V1_FORMULA', recfield('sources',{}), accepted)
    case('P4 diff file absent', 'MISSING', options={**accepted,'fov_code_diff':root/'MISSING_DIFF.patch'})
    case('P4 diff wrong hash', 'FILE_SHA_MISMATCH', options={**accepted,'accept_fov_code_diff':'0'*64})
    case('P4 diff requires explicit acceptance', 'P4_CODE_DIFF_ACCEPTANCE_MISSING', options={'fov_code_diff':published})
    case('P4 invalid hash argument', 'P4_CODE_DIFF_SHA256', options={'accept_fov_code_diff':'bad'})
    for arm in ('V1','V2'):
        for label, transform in [('transpose',lambda x:x.swapaxes(1,2)),
                                 ('vertical flip',lambda x:x[:,::-1,:]),
                                 ('horizontal flip',lambda x:x[:,:,::-1])]:
            case('P5 '+arm+' '+label, 'P5_ORIENTATION', lambda v,r,p,q,arm=arm,transform=transform:v[0].update({ 'depth_'+arm:transform(v[0]['depth_'+arm])}))
        case('P5 '+arm+' constant depth undefined correlation', 'P5_UNDEFINED_CORRELATION', lambda v,r,p,q,arm=arm:v[0].update({'depth_'+arm:np.ones((32,51,51))}))
        def swap(v,r,p,q, arm=arm, both=False):
            for value in v if both else v[:1]:
                value['depth_'+arm][[0,1]] = value['depth_'+arm][[1,0]]
        case('P5 '+arm+' 62/64 anchors accepted', mutation=swap)
        case('P5 '+arm+' 60/64 anchors refused', 'P5_ANCHOR_MATCH', lambda v,r,p,q,swap=swap:swap(v,r,p,q,both=True))
    case('phase non-own missing file refused', 'MISSING', lambda v,r,p,q:p[0]['files'].update({'MISSING.npz':'0'*64}))
    case('phase listed fov bytes checked', 'FILE_SHA_MISMATCH', lambda v,r,p,q:p[0]['files'].update({'fov.npz':'0'*64}))
    case('phase path traversal refused', 'RECEIPT_FILE_PATH', lambda v,r,p,q:p[0]['files'].update({'../outside':'0'*64}))
    case('restored producer fixture')
    # Synthetic mode must skip all provenance even when its optional paths are absent.
    checked = f.Inputs()
    f.validate_probe(root/'MISSING', captures, reference, checked, synthetic=[1.,1.], fov_check=root/'MISSING_FOV_CHECK.json')
    assert checked.integrity['skipped'] == f.PROVENANCE_CHECKS
    outcomes.append({'name':'synthetic explicitly skips P1-P5','pass':True,'input_sha256':{**inputs.pins,**checked.pins}})
    report = {'input_sha256':inputs.pins, 'test_fixture':True, 'decision_usable':False,
              'command':f.shlex.join([sys.executable,'-B',str(Path(__file__).resolve())]),'tests':outcomes}
    dest = WORK/'tests'/('AMENDMENT_RESULTS_'+str(time.time_ns())+'.json')
    dest.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'pass':True,'tests':len(outcomes),'result':str(dest)}))


if __name__ == '__main__':
    main()
