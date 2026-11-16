"""Refute: H1 M2 task accuracy vs b04's reviewed parity.score on identical reader output."""
import json
from pathlib import Path
from e2e_reader import parity
from h1eval import scorers as S
K = Path('/scratch/jjyeung/orch_n30/h1_headsft/kit')
it = next(r for r in json.loads((K/'items/devs1_routed.json').read_text())['items'] if r['question_type'] == 'camera_displacement')
from e2e_reader import parity
rec = dict(call='<move from=18 to=23>', response='dx = 1.00 m, dy = 0.00 m, dz = 2.95 m, distance = 3.15 m', served=True, at_token=5)
for name, text in [('think_closed', 'x <move from=18 to=23> y</think><answer>3.15</answer>'),
                   ('no_think_close', 'x <move from=18 to=23> y <answer>3.15</answer>')]:
    out = dict(text=text, finish='eos', calls=[rec], tokens=[0]*10)
    h1 = S.accuracy(out, it)['task_accuracy']
    b04 = parity.score({**it, 'answer': it['ground_truth']}, out)['answer']
    assert h1==b04,(name,h1,b04)
    print(name, 'h1', h1, 'b04', b04, 'DIFF' if h1 != b04 else 'same')
for name, r in [('served_error_response', dict(rec, response='error: no pose')), ('served_false', dict(rec, served=False))]:
    out = dict(text='x <move from=18 to=23> y</think><answer>3.15</answer>', finish='eos', calls=[r], tokens=[0]*10)
    h1 = S.accuracy(out, it)['task_accuracy']; b04 = parity.score({**it, 'answer': it['ground_truth']}, out)['answer']
    assert h1==b04,(name,h1,b04)
    print(name, 'h1', h1, 'b04', b04, 'DIFF' if h1 != b04 else 'same')

assert h1==b04==1.0
