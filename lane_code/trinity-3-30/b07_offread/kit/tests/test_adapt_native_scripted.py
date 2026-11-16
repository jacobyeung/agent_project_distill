import json

import pytest

from offkit import adapt_native as N


def _row(**k):
    r = dict(key='k', arm='unflagged', question_type='object_abs_distance', call_count=3,
             scores="{'answer': 0.9}", decode="{'text': '<think>x</think> 3.28', 'finish': 'stop'}")
    r.update(k)
    return r


def test_scripted_arm_refused(tmp_path):
    p = tmp_path / 'j.jsonl'
    p.write_text(json.dumps(_row(arm='scripted', script_answer='3.28', script_mode='native_v314_measurement_no_lm_answer')) + '\n')
    with pytest.raises(ValueError, match='unit conversion'):
        N.from_journal(p, 'scripted')


@pytest.mark.parametrize('field', ['script_answer', 'script_mode'])
def test_row_with_script_answer_refused_in_any_arm(tmp_path, field):
    p = tmp_path / 'j.jsonl'
    p.write_text(json.dumps(_row(**{field: 'x'})) + '\n')
    with pytest.raises(ValueError, match='script answer'):
        N.from_journal(p, 'unflagged')


@pytest.mark.parametrize('arm', ['unflagged', 'forced_route', 'Scripted', ' scripted '])
@pytest.mark.parametrize('form', ['dict_str', 'json_str'])
def test_scripted_record_inside_decode_refused(tmp_path, arm, form):
    dec = {'text': '<think>x</think> 3.28', 'finish': 'stop', 'script_answer': '3.28',
           'script_mode': 'native_v314_measurement_no_lm_answer'}
    p = tmp_path / 'j.jsonl'
    p.write_text(json.dumps(_row(arm=arm, decode=str(dec) if form == 'dict_str' else json.dumps(dec))) + '\n')
    with pytest.raises(ValueError, match='script|scripted'):
        N.from_journal(p, arm)
    with pytest.raises(ValueError, match='script|scripted'):
        N.unify(json.loads(p.read_text()))


def test_plain_row_still_unifies():
    u = N.unify(_row())
    assert u['score'] == 0.9 and u['status'] == 'complete'
