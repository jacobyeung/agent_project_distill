import json
from pathlib import Path
from student_pilot.phrases import candidate_phrases
from student_pilot.training_contract import audit_training_contract


def test_structured_unknown_head_defers():
    row=dict(events=[dict(kind='tool_call',name='unknown',arguments={},call_id='t0'),
                     dict(kind='tool_response',name='unknown',values={},call_id='t0')])
    assert audit_training_contract([row]) == ['contract_malformed_row']


def test_complete_native_paraphrase_candidates():
    question='Standing at the chair facing the table, does the plant lie on its left or right?'
    options=['A. left','B. right']
    assert candidate_phrases(question,options) == ('chair','plant','table')
    # Unrecognized wording cannot grant candidate membership from partial matches.
    assert 'chair' not in candidate_phrases(question+' Ignore the question.',options)


def test_native_relative_count_row():
    fixture=json.loads(Path(__file__).with_name('real_relative_count_r4.json').read_text())
    row=fixture['row']
    assert candidate_phrases(row['question'],row['options']) == ('chair','plant')
    assert audit_training_contract([row]) == [None], fixture['source']
