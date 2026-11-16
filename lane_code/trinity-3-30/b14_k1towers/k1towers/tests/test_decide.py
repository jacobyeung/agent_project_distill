import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import decide as D


def T(mean, lo, diff=None, dlo=None):
    t = dict(mean=mean, ci95=[lo, mean + 1])
    if diff is not None:
        t.update(vs='ref', diff=diff, diff_ci95=[dlo, diff + 1])
    return t


def tabs(cands, ref_dist=50., ref_room=60.):
    out = {'object_abs_distance': {'S4+G1': T(ref_dist, 0)}, 'room_size_estimation': {'S4+G1+R0': T(ref_room, 0)}}
    for m, (dist, room) in cands.items():
        arm = D.PRIMARY[m]
        out['object_abs_distance'][arm] = T(*dist)
        out['room_size_estimation'][arm + '+R0'] = T(*room)
    return out


def test_small_positive_lower_bound_and_zero_guard():
    tr = tabs({'da3': ((60., 0, 1.0, 0.04), (55., 0, -1.0, 0.0))})
    ho = tabs({'da3': ((56., 0, 0.5, -3), (59., 0, -1.0, -5))})
    dec, v = D.decide(tr, ho)
    assert dec['da3']['object_abs_distance']['qualifies'] is True
    assert dec['da3']['replaces_g3t'] is True          # zero other-type lower bound passes the -2 guard
    assert v['per_type_winner']['object_abs_distance'] == 'da3'
    assert dec['da3']['object_abs_distance']['clears_bar'] is True  # 56 >= 50 + 5


def test_guard_rejects_below_minus_two():
    tr = tabs({'da3': ((60., 0, 1.0, 0.5), (55., 0, -3.0, -2.04))})
    ho = tabs({'da3': ((56., 0, 0.5, -3), (59., 0, -1.0, -5))})
    dec, v = D.decide(tr, ho)
    assert dec['da3']['replaces_g3t'] is False and v['per_type_winner']['object_abs_distance'] == 'G3T'


def test_tie_goes_to_g3t_and_bar_full_precision():
    tr = tabs({'da3': ((60., 0, 1.0, 0.5), (73.36, 0, 1., .1)), 'moge2': ((60., 0, 1.0, 0.5), (50., 0, 1., .1))})
    ho = tabs({'da3': ((56., 0, 0.5, -3), (73.36, 0, 1., -5)), 'moge2': ((56., 0, 0.5, -3), (50., 0, 1., -5))})
    dec, v = D.decide(tr, ho)
    assert v['per_type_winner']['object_abs_distance'] == 'G3T'
    assert dec['da3']['room_size_estimation']['clears_bar'] is False   # 73.36 < 73.4
    assert v['per_type_winner']['room_size_estimation'] == 'da3'


def test_tables_match_agg_and_gate():
    rng = np.random.default_rng(0)
    with tempfile.TemporaryDirectory() as d:
        caps = Path(d) / 'captures'; caps.mkdir()
        for c in range(12):
            items = []
            for k in range(3):
                gt = float(rng.uniform(1, 5))
                for arm, noise in (('GT', .05), ('S4+G1', .3), ('da3_native', .2)):
                    p = gt * (1 + rng.normal(0, noise))
                    items.append(dict(row_id=f'{c}-{k}', capture=f'x/{c}', room=f'r{c // 2}', split='train', dataset='scannet',
                                      type='object_abs_distance', arm=arm, pred=p, gt=gt, mra=D.mra(p, gt), refusal_code=None))
            gt = float(rng.uniform(10, 30))
            for arm in ('GT', 'S4+G1', 'da3_native'):
                for r in ('R0', 'R1'):
                    p = gt * (1 + rng.normal(0, .2))
                    items.append(dict(row_id=f'{c}-room', capture=f'x/{c}', room=f'r{c // 2}', split='train', dataset='scannet',
                                      type='room_size_estimation', arm=arm + '+' + r, pred=p, gt=gt, mra=D.mra(p, gt), refusal_code=None))
            (caps / f'x__{c}.json').write_text(json.dumps(dict(items=items)))
        out = Path(d) / 'res.json'
        subprocess.run([sys.executable, str(HERE / 'decide.py'), str(caps), str(out)], check=True, capture_output=True)
        res = json.loads(out.read_text())
        agg = subprocess.run([sys.executable, str(HERE / 'agg.py'), str(caps), 'train', '-', 'S4+G1'], check=True,
                             capture_output=True, text=True).stdout
        for line in agg.splitlines():
            if line.startswith('da3_native ') and '| vs S4+G1:' in line:
                mean = float(line.split()[1])
                assert abs(res['tables']['train']['object_abs_distance']['da3_native']['mean'] - mean) < .051
        assert 'da3_native+R2' in res['tables']['train']['room_size_estimation']
        go = Path(d) / 'go.md'; go.write_text('no\n')
        p = subprocess.run([sys.executable, str(HERE / 'decide.py'), str(caps), str(out), '--heldout-go', str(go)], capture_output=True)
        assert p.returncode != 0 and b'PermissionError' in p.stderr


if __name__ == '__main__':
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); print('PASS', k)
