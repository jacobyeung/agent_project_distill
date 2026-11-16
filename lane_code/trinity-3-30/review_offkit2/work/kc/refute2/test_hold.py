"""Re-review (review_offkit2): each test PASSES when the fix HOLDS (ports of test_refute.py F1-F4 to the new API plus new attacks)."""
import json
from pathlib import Path
import pytest
from offkit import report as R, bind as B, frames as F, adapt_native as N

IN = Path('/scratch/jjyeung/orch_n30/b07_offread/in')

def cohort():
    return [json.loads(l) for l in open(IN / 'kit_revsi/cohort/meta_5130.jsonl') if l.strip()]

def agg(kind):
    c = cohort()
    items = [dict(id=r['id'], question_type=r['question_type'], score=0.5, status='complete') for r in c]
    return R.aggregate(R.ReadMode('vsibench5130', kind), c, items, repetitions=20)

def e2e_pass(tmp_path, mode='production'):
    m = tmp_path / 'manifest.json'; m.write_text('{"x":1}')
    sha = B.sha256_file(m)
    e = tmp_path / 'eat1.json'
    e.write_text(json.dumps(dict(manifest_sha256=sha, verdict='PASS', clauses={'A1': dict(status='PASS')})))
    return B.bind('vsibench5130', 'step544', 'e2e:' + sha, mode=mode, e2e_manifest=m, eat1_report=e,
                  ledger=tmp_path / 'l.jsonl')

def harness(tmp_path, mode='production'):
    p = tmp_path / 'ROUTED_PATH_FROZEN_20261116.md'
    p.write_text('x\n```json\n{"freeze_values": {"selector": {}}}\n```\n')
    return B.bind('vsibench5130', 'step544', 'harness:' + B.sha256_file(p), mode=mode, freeze_file=p, ledger=tmp_path / 'l.jsonl')

# Fix 1
def test_h1_harness_aggregate_with_e2e_pass_binding_refused(tmp_path):
    with pytest.raises(ValueError, match='differs from the aggregate'):
        R.label_report(agg('harness'), binding=e2e_pass(tmp_path), arm='primary', role='primary')

def test_h1_harness_binding_always_prints_harness_words(tmp_path):
    lab = R.label_report(agg('harness'), binding=harness(tmp_path), arm='primary', role='primary')
    assert R.HARNESS_WORDS in lab['first_line'] and 'MODE production' in lab['first_line'] and 'FRAMES 32 duplicate' in lab['first_line']

def test_h1_tampered_binding_refused(tmp_path):
    b = e2e_pass(tmp_path); b = json.loads(json.dumps(b)); b['reader']['kind'] = 'harness'
    with pytest.raises(B.BindError):
        R.label_report(agg('harness'), binding=b, arm='primary', role='primary')

def test_h1_unknown_kind_refused(tmp_path):
    b = json.loads(json.dumps(harness(tmp_path))); b['reader']['kind'] = 'Harness'; b['binding_sha256'] = B.binding_sha256(b)
    with pytest.raises(ValueError, match='unknown reader kind'):
        R.label_report(agg('harness'), binding=b, arm='primary', role='primary')

def test_h1_fixture_e2e_pass_still_marked(tmp_path):
    lab = R.label_report(agg('e2e'), binding=e2e_pass(tmp_path, mode='fixture'), arm='primary', role='primary')
    assert any('fixture binding' in w for w in lab['number_words'])

def test_h1_harness_secondary_arm_not_on_e2e(tmp_path):
    with pytest.raises(ValueError, match='not an arm'):
        R.label_report(agg('e2e'), binding=e2e_pass(tmp_path), arm='secondary_fallback', role='secondary')

# Fix 2
def test_h2_bind_frames_has_no_caller_layout():
    with pytest.raises(TypeError):
        F.bind_frames(64, 'spread', export='step544', export_layout=dict(count=64, layout='spread'))

def test_h2_bind_64_spread_on_step544_refused(tmp_path):
    with pytest.raises(B.BindError, match='differs from the trained'):
        B.bind('vsibench5130', 'step544', 'direct', ledger=tmp_path / 'l', frames=(64, 'spread'))

def test_h2_bind_32_spread_on_step544_refused(tmp_path):
    with pytest.raises(B.BindError):
        B.bind('vsibench5130', 'step544', 'direct', ledger=tmp_path / 'l', frames=(32, 'spread'))

def test_h2_64_duplicate_impossible(tmp_path):
    with pytest.raises(B.BindError):
        B.bind('vsibench5130', 'step544', 'direct', ledger=tmp_path / 'l', frames=(64, 'duplicate'), frames_override_reason='x')

def test_h2_override_binds_hashes_and_labels(tmp_path):
    b32 = B.bind('vsibench5130', 'step544', 'direct', ledger=tmp_path / 'l')
    b64 = B.bind('vsibench5130', 'step544', 'direct', ledger=tmp_path / 'l', frames=(64, 'spread'), frames_override_reason='64 test')
    assert b32['binding_sha256'] != b64['binding_sha256'] and b64['frames']['count'] == 64
    t = json.loads(json.dumps(b64)); t['frames']['layout_override_reason'] = None
    with pytest.raises(B.BindError):
        B.verify_binding(t)
    lab = R.label_report(agg('direct') if False else _direct_agg(), binding=b64, arm='primary', role='primary')
    assert 'FRAMES 64 spread' in lab['first_line'] and any('differs from training: 64 test' in w for w in lab['number_words'])

def _direct_agg():
    c = [r for r in cohort() if r['question_type'] in R.ReadMode('vsibench5130', 'direct').types]
    items = [dict(id=r['id'], question_type=r['question_type'], score=0.5, status='complete') for r in c]
    return R.aggregate(R.ReadMode('vsibench5130', 'direct'), c, items, repetitions=20)

def _done(tmp_path, step=400, **over):
    sha = 'a' * 64
    d = tmp_path / 'm.done'; d.write_text(f'q8/8865619b/359fcc3c_m{step}.tar 123 {sha}\n')
    sel = dict(selected_sha256=sha, init_rule_sha256=B.INIT_RULE_SHA, selected_step=step,
               d0_ended=dict(reason='completed_step_1000', event='e'))
    sel.update(over)
    s = tmp_path / 'sel.json'; s.write_text(json.dumps(sel))
    return d, s

def test_h2_done_export_64_spread_refused(tmp_path):
    d, s = _done(tmp_path)
    with pytest.raises(B.BindError, match='differs from the trained'):
        B.bind('revsi999t32', 'done:' + str(d), 'direct', init_selection=s, ledger=tmp_path / 'l', frames=(64, 'spread'))

# Fixes 3 and 4 (in passing)
def test_h3_production_needs_ledger(tmp_path):
    d, s = _done(tmp_path)
    with pytest.raises(B.BindError, match='ledger'):
        B.bind('revsi999t32', 'done:' + str(d), 'direct', init_selection=s)

@pytest.mark.parametrize('step,over', [(100, {}), (50, {}), (400, dict(selected_step=600)), (400, dict(selected_step='400')),
                                       (400, dict(init_rule_sha256='0' * 64)), (400, dict(d0_ended={})),
                                       (400, dict(d0_ended=dict(reason='other', event='e')))])
def test_h4_bad_selection_refused(tmp_path, step, over):
    d, s = _done(tmp_path, step, **over)
    with pytest.raises(B.BindError):
        B.bind('revsi999t32', 'done:' + str(d), 'direct', init_selection=s, ledger=tmp_path / 'l')

def test_h4_good_selection_binds(tmp_path):
    d, s = _done(tmp_path)
    assert B.bind('revsi999t32', 'done:' + str(d), 'direct', init_selection=s, ledger=tmp_path / 'l')['export']['kind'] == 'done'

def test_h3_second_d0_export_refused(tmp_path):
    d, s = _done(tmp_path)
    led = tmp_path / 'l'; led.write_text(json.dumps(dict(export_kind='done', export_sha256='b' * 64)) + '\n')
    with pytest.raises(B.BindError, match='another D0'):
        B.bind('revsi999t32', 'done:' + str(d), 'direct', init_selection=s, ledger=led)

# Fix 5
def test_h5_scripted_arm_refused(tmp_path):
    p = tmp_path / 'j.jsonl'; p.write_text(json.dumps(dict(key='k', arm='scripted', question_type='x')) + '\n')
    with pytest.raises(ValueError, match='never scored'):
        N.from_journal(p, 'scripted')
