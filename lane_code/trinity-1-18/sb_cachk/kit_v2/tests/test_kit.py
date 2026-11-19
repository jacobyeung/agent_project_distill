"""Unit tests for the mask carry kit (p1cpu interpreter: python -m pytest -q kit_v2/tests)."""
import hashlib, json, os, signal, subprocess, sys
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
import mc_seeds as SE
import mc_price as MP
import mc_preflight as PF


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


# Phrase producer schema (review edit 2)

def sha(b):
    return hashlib.sha256(b).hexdigest()


def producer(tmp_path, arm='W1', rows=None, chosen=None, passing=None, safe='PASS', bars_sha=None):
    """A PHRASE_FOLDS.json body in the producer's schema, with its DECISION.json and BARS.json under tmp_path."""
    bars = tmp_path/'BARS.json'
    bars.write_text('{"bars": 1}\n')
    decision = dict(chosen_arm=chosen or arm, shippable_passing=passing if passing is not None else [arm],
                    bars={arm: dict(phrase_worth=dict(verdict='PASS'), phrase_safe=dict(verdict=safe))},
                    bars_file=dict(path=str(bars), sha256=sha(bars.read_bytes())))
    dpath = tmp_path/'DECISION.json'
    dpath.write_text(json.dumps(decision))
    if rows is None:
        rows = [dict(name='heater', policy='q:radiator', phrases=['radiator']), dict(name='chair', policy='raw', phrases=['chair'])]
    return dict(arm=arm, rule='r', folds=[dict(r, fold=k) for k in range(5) for r in rows], changed=[],
                bars_sha256=bars_sha or sha(bars.read_bytes()), input_sha256={str(dpath): sha(dpath.read_bytes())})


def test_phrase_parse_producer_w1(tmp_path):
    t = PH.parse(producer(tmp_path))
    assert sorted(t) == list(range(5))
    assert all(t[k] == {'heater': ('radiator',), 'chair': ('chair',)} for k in range(5))
    prov = PH.producer(producer(tmp_path))
    assert prov['arm'] == 'W1' and prov['phrase_worth'] == prov['phrase_safe'] == 'PASS'


def test_phrase_parse_producer_w2c_pair(tmp_path):
    rows = [dict(name='heater', policy='call:radiator', phrases=['heater', 'radiator']), dict(name='chair', policy='raw', phrases=['chair'])]
    t = PH.parse(producer(tmp_path, arm='W2c', rows=rows))
    assert t[3]['heater'] == ('heater', 'radiator')


@pytest.mark.parametrize('case', ['label_disagrees', 'fb_policy', 'w2_arm', 'q_in_w2c', 'chosen_other', 'not_passing', 'safe_fail',
                                  'bars_sha', 'decision_tampered', 'bars_tampered', 'fold_range', 'duplicate', 'missing_fold',
                                  'old_policies_form', 'bars_passed_false', 'three_phrases'])
def test_phrase_parse_refuses(tmp_path, case):
    raw = producer(tmp_path)
    if case == 'label_disagrees':
        raw['folds'][0]['phrases'] = ['heat']
    elif case == 'fb_policy':
        raw['folds'][0].update(policy='fb:radiator', phrases=['radiator'])
    elif case == 'w2_arm':
        raw = producer(tmp_path, arm='W2', rows=[dict(name='heater', policy='fb:radiator', phrases=['radiator'])])
    elif case == 'q_in_w2c':
        raw = producer(tmp_path, arm='W2c')
    elif case == 'chosen_other':
        raw = producer(tmp_path, chosen='W2c')
    elif case == 'not_passing':
        raw = producer(tmp_path, passing=['W2c'])
    elif case == 'safe_fail':
        raw = producer(tmp_path, safe='FAIL')
    elif case == 'bars_sha':
        raw = producer(tmp_path, bars_sha='0'*64)
    elif case == 'decision_tampered':
        (tmp_path/'DECISION.json').write_text((tmp_path/'DECISION.json').read_text()+' ')
    elif case == 'bars_tampered':
        (tmp_path/'BARS.json').write_text('{"bars": 2}\n')
    elif case == 'fold_range':
        raw['folds'][0]['fold'] = 7
    elif case == 'duplicate':
        raw['folds'].append(dict(raw['folds'][0]))
    elif case == 'missing_fold':
        raw['folds'] = [r for r in raw['folds'] if r['fold'] != 4]
    elif case == 'old_policies_form':
        raw = dict(policies=[dict(fold=0, name='heater', policy=['radiator'])])
    elif case == 'bars_passed_false':
        raw['bars_passed'] = False
    elif case == 'three_phrases':
        raw['folds'][0].update(policy='raw', phrases=['heater', 'a', 'b'])
    with pytest.raises((ValueError, KeyError)):
        PH.parse(raw)


@pytest.mark.skipif(not C.PHRASE_FOLDS.exists(), reason='no phrase-fold file')
def test_phrase_table_reads_the_real_phrases_field():
    status, table, prov = PH.table()
    raw = json.loads(C.PHRASE_FOLDS.read_text())
    assert status == 'PRESENT' and prov['sha256'] == sha(C.PHRASE_FOLDS.read_bytes()) and prov['arm'] == raw['arm']
    assert len(raw['folds']) == 320
    assert all(table[r['fold']][r['name']] == tuple(r['phrases']) for r in raw['folds'])


def test_phrase_table_not_yet(tmp_path, monkeypatch):
    monkeypatch.setattr(C, 'PHRASE_FOLDS', tmp_path/'absent.json')
    status, table, prov = PH.table()
    assert status == 'NOT_YET' and table is None and prov['sha256'] is None


# S_PHR raw-name fallback (review edit 2)

def calls_log():
    log = []

    def call(phrase):
        log.append(phrase)
        return dict(status='NOT_SEEN' if phrase == 'miss' else 'OK', src=phrase), np.full((2, 2), phrase != 'miss')
    return log, call


A0 = dict(status='OK', src='A0')
A0_MASK = np.eye(2, dtype=bool)


def test_phr_choice_single_phrase_calls_it():
    log, call = calls_log()
    p, m = SE.phr_choice(['radiator'], 'heater', A0, A0_MASK, call)
    assert log == ['radiator'] and p['src'] == 'radiator' and p['calls'] == 1 and p['call'] == 'radiator'


def test_phr_choice_raw_first_seen_skips_second():
    log, call = calls_log()
    p, m = SE.phr_choice(['heater', 'radiator'], 'heater', A0, A0_MASK, call)
    assert log == [] and p['src'] == 'A0' and p['calls'] == 1 and m is A0_MASK


def test_phr_choice_raw_first_unseen_calls_second():
    log, call = calls_log()
    p, m = SE.phr_choice(['heater', 'radiator'], 'heater', dict(status='NOT_SEEN'), None, call)
    assert log == ['radiator'] and p['src'] == 'radiator' and p['calls'] == 2


def test_phr_choice_raw_second_restores_a0_seed():
    log, call = calls_log()
    p, m = SE.phr_choice(['miss', 'heater'], 'heater', A0, A0_MASK, call)
    assert log == ['miss'] and p['src'] == 'A0' and p['status'] == 'OK' and p['calls'] == 2 and m is A0_MASK


# Empty-mask carry (review edit 1)

def test_object_record_positive_empty_carries():
    seed = np.zeros((4, 6), bool); seed[1, 1] = True
    full = np.ones((4, 6), bool)
    empty = np.zeros((4, 6), bool)
    result = {0: (full, 2.), 1: (empty, 3.), 2: (full, -1.)}
    rec = IO.object_record(0, 'chair', 5, 2, [0, 1, 2], [0, 1, 2, None] + [None]*28, result, seed)
    a = {x['slot']: x for x in rec['anchors']}
    assert a[2]['seed'] and a[2]['carried'] and np.array_equal(C.rle_decode(a[2]['rle']), seed)
    assert a[1]['carried'] and not a[1]['seed'] and not a[1]['positive_empty']
    assert not a[3]['carried'] and not a[3]['positive_empty']
    assert a[4]['tracked'] is False and not a[4]['carried']
    rec2 = IO.object_record(0, 'chair', 5, 1, [0, 1, 2], [0, 1, 2] + [None]*29, result, seed)
    b = {x['slot']: x for x in rec2['anchors']}
    assert b[2]['carried'] and b[2]['positive_empty'] and not C.rle_decode(b[2]['rle']).any()
    masks = IO.anchor_masks(rec2)
    assert masks.shape == (32, 4, 6) and masks[0].any() and not masks[1].any() and not masks[2].any()
    added = MP.added_members(rec2, masks)
    assert [x.frame for x in added] == [2] and not added[0].mask.any()


def test_zero_score_does_not_carry():
    m = np.ones((2, 2), bool)
    rec = IO.object_record(0, 'a', 1, 1, [0, 1], [0, 1] + [None]*30, {0: (m, 1.), 1: (m, 0.)}, m)
    assert not {x['slot']: x for x in rec['anchors']}[2]['carried']


# Ledger, budget and binding (review edit 4)

def test_refusal_rules():
    assert TP.refusal(dict(stopped='KILLED by signal 15'), True)
    assert TP.refusal(dict(stopped='KILLED (exit 137) recorded by the launcher'), False)
    assert TP.refusal(dict(active=dict(pid=1, host='h')), True)
    assert TP.refusal(dict(stopped='HARD_STOP: 7200 s'), False)
    assert TP.refusal(dict(stopped='FAILED'), True)
    assert TP.refusal(dict(stopped='HARD_STOP: 7200 s'), True) is None
    assert TP.refusal(dict(stopped='PROJECTION: S_A0/D64 alone exceeds'), True) is None
    assert TP.refusal(TP.new_ledger(), False) is None


@pytest.fixture
def keep_signals():
    saved = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)}
    yield
    for s, h in saved.items():
        signal.signal(s, h)


def ledger_at(out, **kw):
    out.mkdir(parents=True, exist_ok=True)
    (out/'BUDGET.json').write_text(json.dumps(dict(TP.new_ledger(), **kw)))


@pytest.mark.parametrize('ledger', [dict(stopped='KILLED by signal 15'), dict(active=dict(pid=1, host='h'))])
def test_main_refuses_killed_even_with_resume(tmp_path, ledger, keep_signals):
    if not str(tmp_path).startswith('/scratch/'):
        pytest.skip('tmp_path is not on /scratch')
    out = tmp_path/'out'
    ledger_at(out, spent_seconds=10., **ledger)
    assert TP.main(['--device', 'cpu', '--out', str(out), '--resume-after-stop']) == 3
    assert json.loads((out/'EVENTS.jsonl').read_text().splitlines()[-1])['event'] == 'REFUSED'


def test_main_refuses_other_binding(tmp_path, keep_signals):
    if not str(tmp_path).startswith('/scratch/'):
        pytest.skip('tmp_path is not on /scratch')
    ledger_at(tmp_path/'out', binding=dict(population_id='another', contract={}))
    assert TP.main(['--device', 'cpu', '--out', str(tmp_path/'out')]) == 5


def test_main_saves_budget_on_exception(tmp_path, monkeypatch, keep_signals):
    if not str(tmp_path).startswith('/scratch/'):
        pytest.skip('tmp_path is not on /scratch')

    def boom(*a):
        raise RuntimeError('boom')
    monkeypatch.setattr(TP, 'run', boom)
    ledger_at(tmp_path/'out', spent_seconds=100.)
    with pytest.raises(RuntimeError):
        TP.main(['--device', 'cpu', '--out', str(tmp_path/'out')])
    led = json.loads((tmp_path/'out/BUDGET.json').read_text())
    assert led['spent_seconds'] >= 100. and led['active'] is None and 'boom' in led['failures'][-1]['error']
    assert led['binding']['population_id'] == C.population()['population_id']


# Global order, projection, receipt and caches (review edits 5 and 6)

def test_order_is_the_registered_order():
    assert C.ORDER[:2] == ['S_A0/D64', 'S_GT/D64'] and set(C.ORDER[2:4]) == {'S_A0/A32', 'S_GT/A32'}
    assert C.ORDER[4:] == ['S_PHR/D64', 'S_PHR/A32']


def test_units_are_arm_major():
    assert TP.units(['S_A0/D64', 'S_GT/D64'], ['a', 'b']) == [('S_A0/D64', 'a'), ('S_A0/D64', 'b'), ('S_GT/D64', 'a'), ('S_GT/D64', 'b')]


def test_unit_cost_counts_its_own_embedding():
    rate = dict(embed_per_frame=.1, track_per_object_frame=.01, overhead_per_unit=2.)
    assert TP.unit_cost(rate, 64, 3) == pytest.approx(2. + 6.4 + 1.92)
    assert TP.unit_cost(rate, 64, 0) == 0. and TP.unit_cost(None, 64, 3) == 0.


def test_projection_and_drop():
    sets = ['S_A0/D64', 'S_GT/D64', 'S_A0/A32', 'S_GT/A32']
    rem = {'S_A0/D64': 1000., 'S_GT/D64': 1000., 'S_A0/A32': 500., 'S_GT/A32': 500.}
    assert TP.project(100., rem, sets) == 3100.
    assert TP.plan_drop(100., rem, sets, 10_000.) == []
    assert TP.plan_drop(100., rem, sets, 2_700.) == ['S_GT/A32']
    assert TP.plan_drop(100., rem, sets, 2_000.) == ['S_GT/D64', 'S_A0/A32', 'S_GT/A32']
    assert TP.plan_drop(100., rem, sets, 1_000.) is None


def test_plan_unit_reuses_phr_twin_and_reads_its_frames():
    fsr = dict(dense=[dict(path=f'p{i}', sha256=str(i)) for i in range(64)], A32=[2*i for i in range(32)])
    entry = dict(objects=[dict(k=0, name='a', instance=1, S_A0=dict(status='OK', slot=3), S_PHR=dict(status='OK', slot=3, same_as_S_A0=True)),
                          dict(k=1, name='b', instance=2, S_A0=dict(status='OK', slot=5), S_PHR=dict(status='OK', slot=6, same_as_S_A0=False))])
    frames, pos, track, reuse, skipped = TP.plan_unit('S_PHR', 'A32', fsr, entry, list(range(64)), True)
    assert frames == fsr['A32'] and [o['k'] for o in track] == [1] and [o['k'] for o in reuse] == [0]
    frames, pos, track, reuse, skipped = TP.plan_unit('S_A0', 'D64', fsr, entry, list(range(64)), True)
    assert frames == list(range(64)) and len(track) == 2 and pos[2] == 4


def test_timing_receipt_writes_only_the_track_dir(tmp_path):
    before = (C.OUT/'TIMING_RECEIPT.json').exists()
    TP.timing_receipt(tmp_path/'track', dict(decision='continue with every set'))
    assert json.loads((tmp_path/'track/TIMING_RECEIPT.json').read_text())['decision'] == 'continue with every set'
    assert (C.OUT/'TIMING_RECEIPT.json').exists() == before


def test_gpu_inner_keeps_caches_under_track():
    text = (KIT/'gpu_inner.sh').read_text()
    assert 'work/v2' not in text and 'W="$MC_OUT/cache"' in text
    for var in ('XDG_CACHE_HOME', 'HF_HOME', 'TORCH_HOME', 'TRITON_CACHE_DIR', 'CUDA_CACHE_PATH', 'TMPDIR'):
        assert f'{var}="$W/' in text
    assert 'timeout -k 30 "$MC_TIMEOUT"' in text


def test_nothing_reads_data_paths():
    for name in ('launch_gpu.sh', 'gpu_inner.sh', 'mc_track_pass.py', 'mc_tracker.py', 'mc_common.py', 'mc_preflight.py'):
        assert '/data' not in (KIT/name).read_text().replace('/data*', ''), name


# Bars and summary

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


def test_frame_spacing_by_dataset():
    fs = dict(captures=[dict(capture='scannet/s1', anchor_indices=[0, 30, 70], dense=[dict(index=i) for i in (0, 15, 30, 50, 70)]),
                        dict(capture='arkitscenes/a1', anchor_indices=[0, 25], dense=[dict(index=i) for i in (0, 12, 25)]),
                        dict(capture='scannet/out', anchor_indices=[0, 999], dense=[dict(index=0), dict(index=999)])])
    sp = SU.frame_spacing(fs, {'scannet/s1', 'arkitscenes/a1'})
    assert sorted(sp) == ['arkitscenes', 'scannet']
    assert sp['scannet']['anchor_gap']['median'] == 35. and sp['scannet']['captures'] == 1
    assert sp['arkitscenes']['dense_gap']['median'] == 12.5 and sp['scannet']['spec_anchor_gap_median'] == 35


def test_completeness_reads_each_population():
    pop = dict(decision=dict(captures=['a'], rows=['r1']), beside=dict(captures=['a', 'b'], rows=['r1', 'r2']))
    arm = dict(captures={'a': dict(status='OK', partial=False)},
               rows={'C_best1': [dict(capture='a', row_id='r1')], 'C_fused': [dict(capture='a', row_id='r1')]})
    SU.completeness(arm, pop)
    assert arm['complete_decision'] and not arm['complete_beside'] and arm['reached_beside'] == 1


@pytest.mark.skipif(not C.BARS_AMENDMENT.exists(), reason='BARS_AMENDMENT.json not built yet')
def test_bars_amendment_keeps_bars_and_names_population():
    amend = json.loads(C.BARS_AMENDMENT.read_text())
    frozen = json.loads((C.OUT/'BARS_FROZEN.json').read_text())
    assert amend['bars_frozen_sha256'] == C.sha256_file(C.OUT/'BARS_FROZEN.json')
    assert 'non-empty' in frozen['builder_resolutions'][1] and 'no other threshold' in amend['effective_resolutions'][1]
    assert amend['population']['population_id'] == C.population()['population_id']


# Population (review edit 8)

def test_population_counts_and_digest():
    pop = C.population()
    assert (pop['counts']['decision_captures'], pop['counts']['decision_rows'], pop['counts']['beside_captures'],
            pop['counts']['beside_rows']) == (204, 1012, 209, 1037)
    dec, bes = pop['decision']['captures'], pop['beside']['captures']
    assert set(dec) < set(bes) and pop['track_order'][:204] == sorted(dec) and sorted(pop['track_order']) == sorted(bes)
    assert C.population_digest(pop) == pop['population_id']
    assert C.population_digest(dict(pop, track_order=pop['track_order'][::-1])) != pop['population_id']


def test_guard_forms():
    f = G.forms('scannet/scene0201_02', 'scannet/scene0201')
    assert {'d1/scene0201_02', 'd1/scene0201', 'scannet/scene0201'} <= f
    assert 'd3/venue1' in G.forms('arkitscenes/41048124', 'arkitscenes/venue1')
    assert 'd2/abc' in G.forms('scannetpp/abc', 'scannetpp/abc')


# Preflight and staging (review edits 3 and 7)

@pytest.mark.skipif(not C.PHRASE_FOLDS.exists(), reason='no phrase-fold file')
def test_preflight_phrase_hash_against_seed_provenance(tmp_path):
    seeds = json.loads((C.OUT/'seeds/SEEDS.json').read_text())['summary']
    assert PF.phrase_check(seeds, C.PHRASE_FOLDS) == []
    other = tmp_path/'PHRASE_FOLDS.json'
    other.write_bytes(C.PHRASE_FOLDS.read_bytes())
    assert PF.phrase_check(seeds, other)
    bad = json.loads(json.dumps(seeds))
    bad['S_PHR']['phrase_folds']['sha256'] = '0'*64
    assert PF.phrase_check(bad, C.PHRASE_FOLDS)
    assert PF.phrase_check(seeds, tmp_path/'absent.json')
    assert PF.phrase_check(dict(S_PHR=dict(status='NOT_YET')), C.PHRASE_FOLDS)
    assert PF.phrase_check(dict(S_PHR=dict(status='NOT_YET')), tmp_path/'absent.json') == []


@pytest.mark.skipif(not (C.OUT/'STAGING.json').exists(), reason='STAGING.json not built yet')
def test_staging_is_self_contained():
    st = json.loads((C.OUT/'STAGING.json').read_text())
    paths = [p for i in st['items'] for p in (i['path'] if isinstance(i['path'], list) else [i['path']])]
    assert all(p.startswith('/scratch/') for p in paths)
    for need in (C.OUT/'STAGING.json', C.OUT/'STAGING_FRAMES.txt', C.POPULATION, C.BARS_AMENDMENT, C.OUT/'BARS_FROZEN.json',
                 C.OUT/'KIT_MANIFEST.sha256', C.RULING, C.KIT):
        assert str(need) in paths, need
    assert st['total_bytes'] == sum(i['bytes'] for i in st['items'])
    me = next(i for i in st['items'] if i['path'] == str(C.OUT/'STAGING.json'))
    assert me['bytes'] == (C.OUT/'STAGING.json').stat().st_size
    assert PF.staging_check(st) == []
    seeds = json.loads((C.OUT/'seeds/SEEDS.json').read_text())['summary']['S_PHR']
    if seeds['status'] == 'PRESENT':
        assert seeds['phrase_folds']['path'] in paths and seeds['phrase_folds']['decision'] in paths


def test_vendor_vnice_is_pinned_and_local():
    for name, pin in C.VENDOR_SHA256.items():
        assert C.sha256_file(KIT/'vendor'/name) == pin and os.access(KIT/'vendor'/name, os.X_OK)
    text = (KIT/'launch_gpu.sh').read_text()
    assert 'VNICE="$KIT/vendor/vnice.sh"' in text and C.VENDOR_SHA256['vnice.sh'] in text and C.VENDOR_SHA256['terminator.sh'] in text


# Launcher (review edits 4, 6 and the 24 GB bf16 acceptance)

def run_launch(tmp_path, readings, host='trinity-1-18', args=(), env_extra=None, ledger=None):
    """readings: one list of nvidia-smi lines per call (the last repeats)."""
    smi = tmp_path/'smi.sh'
    body = '#!/bin/bash\nn=$(cat "$0.n" 2>/dev/null || echo 0); echo $((n+1)) > "$0.n"\ncase "$n" in\n'
    for i, lines in enumerate(readings):
        body += f'  {i if i < len(readings)-1 else "*"}) ' + '; '.join(f'echo "{l}"' for l in lines) + ' ;;\n'
    smi.write_text(body + 'esac\n')
    smi.chmod(0o755)
    out = tmp_path/'out'
    if ledger is not None:
        ledger_at(out, **ledger)
    env = dict(os.environ, MC_DRY_LAUNCH='1', MC_NVIDIA_SMI=str(smi), MC_WAIT_SECONDS='0', MC_HOST=host,
               MC_TEST_OUT=str(out), MC_SKIP_PREFLIGHT='1', **(env_extra or {}))
    p = subprocess.run(['bash', str(KIT/'launch_gpu.sh'), *args], env=env, capture_output=True, text=True)
    events = [json.loads(l) for l in (out/'EVENTS.jsonl').read_text().splitlines()] if (out/'EVENTS.jsonl').exists() else []
    return p.returncode, events


manifest = pytest.mark.skipif(not (C.OUT/'KIT_MANIFEST.sha256').exists(), reason='KIT_MANIFEST.sha256 not built yet')


@manifest
@pytest.mark.parametrize('card', ['24564, 3, 8.6', '23028, 0, 8.6', '49140, 0, 8.9', '81559, 0, 9.0'])
def test_launch_accepts_24e9_bytes_with_bf16(tmp_path, card):
    code, ev = run_launch(tmp_path, [['0, 49140, 2000, 8.6', f'1, {card}']])
    assert code == 0 and ev[-1]['event'] == 'LAUNCH' and ev[-1]['gpu'] == '1'


@manifest
@pytest.mark.parametrize('card', ['24564, 0, 7.5', '22000, 0, 8.6', '16384, 0, 8.9', '49140, 1025, 8.6', '49140, 0',
                                  '49140, 0, [N/A]', '[N/A], 0, 8.6'])
def test_launch_refuses_cards(tmp_path, card):
    code, ev = run_launch(tmp_path, [[f'0, {card}']])
    assert code == 1 and ev[-1]['event'] == 'LAUNCH_REFUSED'


@manifest
def test_launch_refuses_busy_second_reading(tmp_path):
    code, ev = run_launch(tmp_path, [['0, 49140, 0, 8.6'], ['0, 49140, 2000, 8.6']])
    assert code == 1 and ev[-1]['event'] == 'LAUNCH_REFUSED'


@manifest
@pytest.mark.parametrize('ledger,resume,ok', [
    (dict(stopped='KILLED (exit 137) recorded by the launcher'), '1', False),
    (dict(stopped='KILLED by signal 15'), '1', False),
    (dict(active=dict(pid=1, host='h')), '1', False),
    (dict(stopped='HARD_STOP: 7200 s'), '0', False),
    (dict(stopped='HARD_STOP: 7000 s', spent_seconds=7000.), '1', False),
    (dict(stopped='PROJECTION: drop', spent_seconds=3000.), '1', True),
    (dict(spent_seconds=600.), '0', True),
])
def test_launch_ledger_rules(tmp_path, ledger, resume, ok):
    code, ev = run_launch(tmp_path, [['0, 49140, 0, 8.6']], ledger=ledger, env_extra=dict(MC_RESUME_AFTER_STOP=resume))
    assert (code == 0 and ev[-1]['event'] == 'LAUNCH') if ok else (code == 1 and ev[-1]['event'] == 'LAUNCH_REFUSED')
    if ok:
        assert int(ev[-1]['timeout_seconds']) == 7200 - int(ledger.get('spent_seconds', 0))


@manifest
def test_launch_refuses_arguments(tmp_path):
    code, ev = run_launch(tmp_path, [['0, 49140, 0, 8.6']], args=('--exclude-withheld',))
    assert code == 1 and ev[-1]['event'] == 'LAUNCH_REFUSED'


@pytest.mark.parametrize('host', ['trinity', 'trinity-0-13', 'laptop'])
def test_launch_refuses_hosts(tmp_path, host):
    code, ev = run_launch(tmp_path, [['0, 49140, 0, 8.6']], host=host)
    assert code == 1 and ev[-1]['event'] == 'LAUNCH_REFUSED'
