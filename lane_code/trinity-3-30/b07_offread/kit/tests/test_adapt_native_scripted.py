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
