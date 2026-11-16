"""Check the numerical facts used in the verdict."""
import json
from pathlib import Path
import torch
from probes_r3.variants import make_reader
from eat1.toy.reader import read_frames

ROOT = Path(__file__).resolve().parent
item = json.loads((ROOT/'fixture'/'move.jsonl').read_text())
control = make_reader(ROOT/'fixture', 'control')
with torch.no_grad():
    feats = control.model.perception(read_frames(item['frames']))['feats']
    head = control.model.perception.move_head
    first = float(head(torch.cat([feats[0], feats[1]]))[0])
    second = float(head(torch.cat([feats[1], feats[0]]))[0])
print(json.dumps(dict(maximum_candidates=[first, second], maximum=max(first, second))))
for name in ('tensor_scale', 'table_tensor', 'class_tensor'):
    head = make_reader(ROOT/'fixture', name).model.perception.move_head
    print(json.dumps(dict(name=name, scale=float(head.scale), state_keys=list(head.state_dict()),
                         parameter_keys=list(dict(head.named_parameters())), buffer_keys=list(dict(head.named_buffers())))))
def output(name):
    return json.loads((ROOT/'results'/name/'ITEMS.jsonl').read_text())['output']
base = output('control')
print(json.dumps(dict(bookkeeping_identical=output('bookkeeping') == base,
                      scalar_identical=output('scalar') == base)))
for name in ('positive_answer', 'unit_answer', 'fields_extra'):
    print(json.dumps(dict(name=name, **output(name))))
