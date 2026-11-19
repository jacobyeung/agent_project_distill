from pathlib import Path
from types import SimpleNamespace as NS
from contextlib import nullcontext
import hashlib, importlib.util, json, sys
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
torch.set_num_threads(8)
pins = {}
def read(p):
    b = p.read_bytes()
    pins[str(p)] = hashlib.sha256(b).hexdigest()
    return b
def module(name, path):
    read(path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
test = module('review_tests', ROOT/'work/test_cachefix.py')
sys.modules['student_pilot'] = sys.modules['sp_patched']
sys.modules['student_pilot.routed_features'] = test.NEW.F
sys.modules['student_pilot'].routed_features = test.NEW.F
stage = module('served_stage', ROOT/'work/orig/src/b/e2e_reader/stage1.py')
prompts = []
def text(names, device):
    prompts.append(names)
    return {}
calls = []
def grounding(**kwargs):
    i = len(calls)
    calls.append(kwargs)
    return dict(pred_logits=torch.tensor([3.,2.]), presence_logit_dec=torch.tensor(float(i*2-1)),
                pred_masks=torch.ones(2,4,4))
model = NS(backbone=NS(forward_text=text), forward_grounding=grounding, _get_dummy_prompt=lambda:None)
tower = NS(_load=lambda:None, _autocast=nullcontext, device=torch.device('cpu'),
           _backend=NS(model=model, find_stage=None))
features = NS(frames=[dict(backbone_fpn=[torch.ones(1)]) for _ in range(2)], sizes=[(480,640)]*2)
frames = stage.sam3_detect(tower, features, '  CHAIRS  ')
assert prompts == [['chairs']] and len(calls) == 2
assert all(len(frame) == 2 and len({v['presence'] for v in frame}) == 1 for frame in frames)
assert frames[0][0]['presence'] != frames[1][0]['presence']

raw = test.mixed_frames()
raw[0][0]['presence'] = 0.
raw[0][1]['presence'] = 1.
cache = test.NEW.F.cache_for('chair',raw)
props,_ = test.NEW.C.lift(cache,'chair',test.Geo(),floor=.3,phrase='chair')
assert [p.presence for p in props] == [0.,1.]
# Explicitly demonstrate the eager evaluation of dict.get's default.
missing = test.NEW.F.cache_for('chair',raw)
missing['frames']['0']['phrases']['chair'].pop('presence')
try:
    test.NEW.C.lift(missing,'chair',test.Geo(),floor=.3,phrase='chair')
except KeyError as exc:
    assert exc.args == ('presence',)
else:
    raise AssertionError('Expected mandatory record presence')

def decode(rle):
    return np.repeat(np.arange(len(rle['counts']))%2==1,rle['counts']).reshape(rle['size'],order='F')
source = NS(cache=cache,reader=NS(phrase=lambda n:n,rle_decode=decode),frame_indices=np.arange(32))
detected,_ = test.NEW.F.detections(source,'chair',NS(require=lambda x:None))
assert [i['presence'] for i in detected[0]] == [0.,0.]

# Classify every ground call whose journal lacks pool diagnostics.
audit = json.loads(read(ROOT/'evidence/input_audit.json'))
unobserved = {}
for label, data in audit['journals'].items():
    c = dict(calls=0,served_true=0,served_false=0,served_absent=0)
    for name in data['files']:
        for line in read(Path(name)).splitlines():
            for rec in ((json.loads(line).get('output') or {}).get('calls') or {}).get('records') or []:
                if rec.get('family') != 'ground' or 'sam3' in (rec.get('stage1') or {}):
                    continue
                c['calls'] += 1
                c['served_true' if rec.get('served') is True else 'served_false' if rec.get('served') is False else 'served_absent'] += 1
    unobserved[label] = c
for folder in ('orig','patched'):
    for name in ('routed_candidates.py','routed_features.py'):
        read(ROOT/'work'/folder/'src/tree/student_pilot'/name)
read(Path(__file__))
out = dict(input_sha256=pins,served_prompts=prompts,served_frame_presences=[[v['presence'] for v in f] for f in frames],
           zero_presence_preserved=True,record_presence_required=True,
           detections_still_collapses=[v['presence'] for v in detected[0]],ground_without_pool=unobserved)
(ROOT/'evidence/contracts.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='input_sha256'},indent=2))
