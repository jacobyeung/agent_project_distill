"""Refutation tests (reviewer review_offkit). Each test PASSES when the defect exists (the kit accepts what it should refuse)."""
import hashlib, json
from pathlib import Path
import pytest
from offkit import report as R, bind as B, frames as F, adapt_native as N

IN = Path('/scratch/jjyeung/orch_n30/b07_offread/in')

def _harness_report():
    cohort = [json.loads(l) for l in open(IN / 'kit_revsi/cohort/meta_5130.jsonl') if l.strip()]
    items = [dict(id=r['id'], question_type=r['question_type'], score=0.5, status='complete') for r in cohort]
    return R.aggregate(R.ReadMode('vsibench5130', 'harness'), cohort, items, repetitions=50)

def test_F1_harness_aggregate_labelled_as_claimable_e2e():
    rep = _harness_report()
    assert rep['reader_kind'] == 'harness'
    lab = R.label_report(rep, reader=dict(kind='e2e', id='x', eat1=dict(passed=True)), export=dict(kind='step544', sha256='1'), arm='primary', role='primary')
    assert R.HARNESS_WORDS not in lab['first_line'] and lab['number_words'] == []   # claimable wording on a harness read

def test_F1b_unknown_reader_kind_gets_no_words():
    rep = _harness_report()
    lab = R.label_report(rep, reader=dict(kind='Harness', eat1=dict(passed=False)), export={}, arm='primary', role='primary')
    assert lab['number_words'] == []

def test_F2_step544_layout_overridden_by_caller_export_layout():
    f = F.bind_frames(64, 'spread', export='step544', export_layout=dict(count=64, layout='spread'))
    assert f['layout_override_reason'] is None   # 64-spread read of a 32-dup export, no override recorded

def test_F2b_binding_does_not_carry_frames(tmp_path):
    b = B.bind('vsibench5130', 'step544', 'direct')
    assert 'frames' not in b and 'duplicated' in b['frame_path']   # hard-coded; 32 and 64 reads bind to the same sha

def _done(tmp_path, sha='a' * 64, step=100):
    d = tmp_path / 'm.done'; d.write_text(f'q8/8865619b/359fcc3c_m{step}.tar 123 {sha}\n')
    s = tmp_path / 'sel.json'; s.write_text(json.dumps(dict(selected_sha256=sha)))
    return d, s

def test_F3_production_bind_without_ledger_skips_one_export_rule(tmp_path):
    d, s = _done(tmp_path)
    b = B.bind('vsibench5130', 'done:' + str(d), 'direct', mode='production', init_selection=s, ledger=None)
    assert b['mode'] == 'production'

def test_F3b_bare_selection_json_for_noncandidate_m100_binds(tmp_path):
    d, s = _done(tmp_path, step=100)
    b = B.bind('revsi999t32', 'done:' + str(d), 'direct', mode='production', init_selection=s,
               ledger=tmp_path / 'l.jsonl')
    assert b['export']['object'].endswith('_m100.tar')   # init rule item 1: m100 is not a candidate; selection JSON carries no rule sha

def test_F4_scripted_arm_is_scored(tmp_path):
    row = dict(key='k', arm='scripted', question_type='object_abs_distance', call_count=3,
               scores="{'answer': 0.9}", decode="{'text': '<think>x</think> 3.28', 'finish': 'stop'}",
               script_answer='3.28', script_mode='native_v314_measurement_no_lm_answer')
    p = tmp_path / 'j.jsonl'; p.write_text(json.dumps(row) + '\n')
    u = N.from_journal(p, 'scripted')
    assert u[0]['status'] == 'complete' and u[0]['score'] == 0.9 and not u[0]['refusal']   # unit-converted script answer counted
