"""Near-nadir capture: what the runtime serves vs what the training audit admits."""
import sys, json
TREE = sys.argv[1]
sys.path[:0] = [TREE, '/scratch/jjyeung/orch_n30/review_contracts/work/btests']
import numpy as np
from pathlib import Path
from fixtures_contracts import fixture, session, response, CALLS
from trace_format.contracts import contract_epoch, response_status
from student_pilot.training_contract import audit_training_contract

root = Path('/scratch/jjyeung/orch_n30/review_contracts/work/tmp/nadir_flow')
out = {}
for kind in ('nadir_positive', 'landscape'):
    c, make = fixture(kind)
    for epoch in (True, False):
        with contract_epoch(epoch):
            s = session(make(), root / f'{kind}_{epoch}')
            out[f'{kind}_epoch{epoch}'] = {call: response(s, call) for call in CALLS}
for k, v in out.items():
    print('==', k)
    for call, text in v.items():
        print('  ', call, '->', text.replace('\n', ' | '), '   [status=%s]' % response_status(text))

r = out['nadir_positive_epochTrue']
w = lambda t: '<tool_response>\n' + t + '\n</tool_response>'
row = dict(qid='x', question='What is the distance between the chair and the table (in meters)?', options=[],
           candidate_phrases=['chair', 'table'], trace_revision='3.14',
           events=[dict(call=CALLS[0], response=w(r[CALLS[0]])), dict(call=CALLS[1], response=w(r[CALLS[1]])),
                   dict(call=CALLS[2], response=w(r[CALLS[2]]))],
           target='<think>\n...\n</think>\n<answer>1.2</answer>')
with contract_epoch(True):
    print('audit of served near-nadir distance row (ground, ground, gap):', audit_training_contract([row]))
    row2 = dict(row, events=row['events'][:1] + row['events'][2:])
    print('audit of (ground chair, gap):', audit_training_contract([row2]))
json.dump(out, open(sys.argv[2], 'w'), indent=1)
