import json, sys, time, gzip
sys.path.insert(0, '/scratch/jjyeung/orch_n30/b05_owngrd/code')
import torch
torch.set_num_threads(8)
import functools
def _cpu(fn):
    @functools.wraps(fn)
    def w(*a, **k):
        d = k.get('device')
        if d is not None and 'cuda' in str(d):
            k['device'] = 'cpu'
        return fn(*a, **k)
    return w
for _n in ('zeros', 'ones', 'empty', 'arange', 'tensor', 'full', 'linspace', 'zeros_like', 'ones_like', 'rand', 'randn', 'as_tensor'):
    setattr(torch, _n, _cpu(getattr(torch, _n)))
_to = torch.Tensor.to
def _tocpu(self, *a, **k):
    a = tuple('cpu' if (isinstance(x, (str, torch.device)) and 'cuda' in str(x)) else x for x in a)
    if 'device' in k and 'cuda' in str(k['device']): k['device'] = 'cpu'
    return _to(self, *a, **k)
torch.Tensor.to = _tocpu
torch.Tensor.cuda = lambda self, *a, **k: self
torch.Tensor.pin_memory = lambda self, *a, **k: self
from owngrd import teacher
from owngrd.common import rle_decode
man = json.load(open('/scratch/jjyeung/orch_n30/b05_owngrd/work/manifests/TEACHER_K1.json'))
c = dict(man['captures'][0]); c['frames'] = c['frames'][:2]; c['names'] = c['names'][:2]
settings = json.load(open(sys.argv[1]))
t0 = time.time()
be = teacher.TowerBackend(settings, teacher.CONTRACT['joint_floor'], teacher.CONTRACT['cap'])
out, secs = teacher.run_capture(be, c)
summ = {n: [(len(out['frames'][str(s)]['phrases'][n]['instances']), round(out['frames'][str(s)]['phrases'][n]['presence'], 4),
             [round(i['joint_score'], 3) for i in out['frames'][str(s)]['phrases'][n]['instances']][:5]) for s in (0, 1)] for n in out['phrases']}
for fr in out['frames'].values():
    for p in fr['phrases'].values():
        for i in p['instances']:
            assert rle_decode(i['mask']).shape == tuple(fr['size'])
print(json.dumps({'capture': c['canonical'], 'names': out['phrases'], 'roles': out['roles'], 'summary': summ,
                  'secs_run': secs, 'secs_total': time.time() - t0}))
open('/scratch/jjyeung/orch_n30/b05_owngrd/work/x118/smoke_out.json.gz', 'wb').write(gzip.compress(json.dumps(out).encode()))
