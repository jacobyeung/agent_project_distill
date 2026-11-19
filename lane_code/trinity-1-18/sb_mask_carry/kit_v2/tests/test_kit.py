"""Unit tests for the mask carry kit (p1cpu interpreter: python -m pytest -q kit_v2/tests)."""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import mc_common as C
import mc_phrase as PH
import mc_track_io as IO
import mc_track_pass as TP
import mc_summary as SU
import mc_guard as G


def test_rle_roundtrip_both_start_states():
    rng = np.random.default_rng(0)
    for first in (False, True):
        m = rng.random((48, 64)) > .6
        m[0, 0] = first
        r = C.rle_encode(m)
        assert np.array_equal(C.rle_decode(r), m)
        assert sum(r['counts']) == m.size
    assert np.array_equal(C.rle_decode(C.rle_encode(np.zeros((5, 7), bool))), np.zeros((5, 7), bool))


def test_rle_rejects_bad_counts():
    with pytest.raises(ValueError):
        C.rle_decode(dict(size=[2, 2], counts=[1, 1]))


def test_pack_unpack():
    m = np.random.default_rng(1).random((3, 30, 40)) > .5
    p = C.pack(m)
    assert np.array_equal(C.unpack(p['shape'], p['bits']), m)


@pytest.mark.parametrize('raw', [
    dict(policies=[dict(fold=0, name='heater', policy=['radiator']), dict(fold=1, name='heater', policy=['heater', 'radiator'])]),
    dict(rows=[dict(fold='0', name='heater', phrases='radiator'), dict(fold=1, name='heater', phrases=['heater', 'radiator'])]),
    dict(folds={'0': {'heater': 'radiator'}, '1': {'heater': {'w1': 'heater', 'w2': 'radiator'}}}),
])
def test_phrase_folds_forms(raw):
    t = PH.parse(raw)
    assert t[0]['heater'] == ('radiator',)
    assert t[1]['heater'] == ('heater', 'radiator')


@pytest.mark.parametrize('raw', [
    dict(policies=[dict(fold=7, name='a', policy='b')]),
    dict(policies=[dict(fold=0, name='a', policy=['b', 'c', 'd'])]),
    dict(bars_passed=False, policies=[]),
    dict(something=[]),
])
def test_phrase_folds_rejects(raw):
    with pytest.raises(ValueError):
        PH.parse(raw)


def test_phrase_table_not_yet():
    if not C.PHRASE_FOLDS.exists():
        assert PH.table() == ('NOT_YET', None)


def test_object_record_seed_and_carried():
    seed = np.zeros((4, 6), bool); seed[1, 1] = True
    full = np.ones((4, 6), bool)
    empty = np.zeros((4, 6), bool)
    result = {0: (full, 2.), 1: (empty, 3.), 2: (full, -1.)}
    rec = IO.object_record(0, 'chair', 5, 2, [0, 1, 2], [0, 1, 2, None] + [None]*28, result, seed)
    a = {x['slot']: x for x in rec['anchors']}
    assert a[2]['seed'] and a[2]['carried'] and np.array_equal(C.rle_decode(a[2]['rle']), seed)
    assert a[1]['carried'] and not a[1]['seed']
    assert not a[3]['carried'] and not a[3]['positive_empty']
    assert a[4]['tracked'] is False and not a[4]['carried']
    rec2 = IO.object_record(0, 'chair', 5, 1, [0, 1, 2], [0, 1, 2] + [None]*29, result, seed)
    b = {x['slot']: x for x in rec2['anchors']}
    assert b[2]['positive_empty'] and not b[2]['carried']
    masks = IO.anchor_masks(rec)
    assert masks.shape == (32, 4, 6) and masks[0].all() and not masks[2].any()


def test_projection_and_drop():
    sets = ['S_A0/D64', 'S_GT/D64', 'S_A0/A32', 'S_GT/A32']
    means = {s: 10. for s in sets}
    assert TP.project(100., 10, 5., means, sets) == 100. + 10*45.
    assert TP.plan_drop(0., 100, 5., means, sets, 10_000.) == []
    assert TP.plan_drop(0., 100, 5., means, sets, 3_000.) == ['S_A0/A32', 'S_GT/A32']
    assert TP.plan_drop(0., 100, 5., means, sets, 2_000.) == ['S_GT/D64', 'S_A0/A32', 'S_GT/A32']
    assert TP.plan_drop(0., 100, 5., means, sets, 1_000.) is None


def test_seed_digest_tracks_masks():
    entry = dict(objects=[dict(k=0), dict(k=1)])
    a = {'S_A0_0': np.eye(4, dtype=bool)}
    b = {'S_A0_0': np.eye(4, dtype=bool)[::-1]}
    assert TP.seed_digest('S_A0', entry, a) == TP.seed_digest('S_A0', entry, dict(a))
    assert TP.seed_digest('S_A0', entry, a) != TP.seed_digest('S_A0', entry, b)
    assert TP.seed_digest('S_A0', entry, a) != TP.seed_digest('S_GT', entry, a)


def test_timing_receipt(tmp_path):
    run = dict(device='cpu', host='h', load_seconds=1.)
    body = TP.timing_receipt(tmp_path, run, 10, [2., 4.], {'S_A0/D64': [1., 3.]}, ['S_A0/D64'], 199, 900., [], 7200., 50.)
    saved = json.loads((tmp_path/'TIMING_RECEIPT.json').read_text())
    assert saved['embed_mean_seconds'] == 3. and saved['set_mean_seconds'] == {'S_A0/D64': 2.}
    assert body['decision'] == 'continue with every set'


def m(prec, est, lb, size, slb, rate):
    return dict(member_precision=dict(precision=prec), C_fused=dict(vs_A0=dict(estimate=est, ci95=[lb, lb+1])),
                size=dict(estimate=size, ci95=[slb, slb+1]), first_seen=dict(rate=rate))


def test_verdicts():
    assert set(SU.verdicts(None, False).values()) == {'MISSING'}
    assert set(SU.verdicts(m(.95, 3., .1, 6., .5, .91), False).values()) == {'MISSING'}
    v = SU.verdicts(m(.90, 2., .01, 5., .01, .90), True)
    assert v == dict(carry_precision='PASS', carry_fusion='PASS', size_screen='PASS', first_seen_screen='PASS')
    v = SU.verdicts(m(.8999, 2.5, 0., 4.9, 1., .89), True)
    assert v == dict(carry_precision='FAIL', carry_fusion='FAIL', size_screen='FAIL', first_seen_screen='FAIL')
    assert SU.verdicts(m(None, 2.5, 1., 6., 1., .95), True)['carry_precision'] == 'FAIL'


def test_guard_forms():
    f = G.forms('scannet/scene0201_02', 'scannet/scene0201')
    assert {'d1/scene0201_02', 'd1/scene0201', 'scannet/scene0201'} <= f
    assert 'd3/venue1' in G.forms('arkitscenes/41048124', 'arkitscenes/venue1')
    assert 'd2/abc' in G.forms('scannetpp/abc', 'scannetpp/abc')


def run_launch(tmp_path, smi_lines, host='trinity-1-18'):
    smi = tmp_path/'smi.sh'
    smi.write_text('#!/bin/bash\n' + ''.join(f'echo "{l}"\n' for l in smi_lines))
    smi.chmod(0o755)
    env = dict(os.environ, MC_DRY_LAUNCH='1', MC_NVIDIA_SMI=str(smi), MC_WAIT_SECONDS='0', MC_HOST=host,
               MC_TEST_OUT=str(tmp_path/'out'), MC_SKIP_PREFLIGHT='1')
    p = subprocess.run(['bash', str(KIT/'launch_gpu.sh')], env=env, capture_output=True, text=True)
    events = [json.loads(l) for l in (tmp_path/'out/EVENTS.jsonl').read_text().splitlines()] if (tmp_path/'out/EVENTS.jsonl').exists() else []
    return p.returncode, events


manifest = pytest.mark.skipif(not (C.OUT/'KIT_MANIFEST.sha256').exists(), reason='KIT_MANIFEST.sha256 not built yet')


@manifest
def test_launch_picks_free_48g_card(tmp_path):
    code, ev = run_launch(tmp_path, ['0, 49140, 2000', '1, 49140, 3'])
    assert code == 0 and ev[-1]['event'] == 'LAUNCH' and ev[-1]['gpu'] == '1'


@manifest
def test_launch_refuses_busy_or_small_cards(tmp_path):
    code, ev = run_launch(tmp_path, ['0, 49140, 1025', '1, 24564, 0'])
    assert code == 1 and ev[-1]['event'] == 'LAUNCH_REFUSED'


@pytest.mark.parametrize('host', ['trinity', 'trinity-0-13', 'laptop'])
def test_launch_refuses_hosts(tmp_path, host):
    code, ev = run_launch(tmp_path, ['0, 49140, 0'], host=host)
    assert code == 1 and ev[-1]['event'] == 'LAUNCH_REFUSED'


def test_order_is_the_registered_order():
    assert C.ORDER[:2] == ['S_A0/D64', 'S_GT/D64'] and set(C.ORDER[2:4]) == {'S_A0/A32', 'S_GT/A32'}
    assert C.ORDER[4:] == ['S_PHR/D64', 'S_PHR/A32']
