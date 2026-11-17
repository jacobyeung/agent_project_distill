"""Refute: the reviewed path builds ONE cached generator with the first mode's factory; does each item still get its own mode?"""
import json, types, sys
from pathlib import Path
import numpy as np
import h1eval.h10.launch as L
import h1eval.h10.parity_adapter as PA
import h1eval.h10.perception_own as PO
W = Path(__import__('os').environ['A_TEST'])/'cm'; (W/'e').mkdir(parents=True, exist_ok=True); (W/'e/x.bin').write_bytes(b'x')
(W/'art.json').write_text(json.dumps(dict(root='/dev/shm', name='a', sha256='0'*64)))
(W/'b/e2e_reader').mkdir(parents=True, exist_ok=True); (W/'b/parity_kit').mkdir(parents=True, exist_ok=True); (W/'b/parity_kit/x.py').write_text('')
items = '/scratch/jjyeung/orch_n30/h1_headsft/kit/items/devs1_routed.json'
PA.settings_for = lambda p, n: dict(export_dir=str(W/'e'), artifact_manifest=str(W/'art.json'))
PA.map_items = lambda its, s, name=None: ({r['id']: r for r in its}, dict(sha256='m', items=[]))
PA.validate_own_settings = lambda s, i: None; PA.prepare_runtime = lambda s: None
PA.reader_code_hash = lambda r: 'r'
class Fake:
    def __init__(self, mode): self.mode = mode; self.last = {}
def configured(mode, **kw):
    def make(artifact, model, device, *, processor=None, item=None, settings=None):
        p = Fake(mode); p.last = dict(heads=types.SimpleNamespace(pose9=np.zeros((1, 9)), gravity=np.zeros(3)), intervention=dict(mode=mode)); return p
    return make
PO.configured = configured
def maker(export, spec, its, *, perception_factory=None, device='cpu', settings=None):
    def gen(item):
        perception_factory(artifact=None, model=None, processor=None, device=device, item=item)
        return dict(text='t', finish='eos')
    return gen
maker.__qualname__ = 'make_real'
L.reader_factory = lambda root, entry=L.ENTRY: maker
L.inspect.getsourcefile = lambda f: __file__
for t in ('camera_displacement', 'camera_rotation'):
    out = W/('o_'+t)
    a = L.parser().parse_args(['--items', items, '--export', str(W/'e'), '--artifact-manifest', str(W/'art.json'),
        '--reader-root', str(W/'b'), '--out', str(out), '--arms', 'own', '--types', t, '--shard', '0/50', '--device', 'cpu'])
    print(L.run(a))
    bad = 0; n = 0
    for line in (out/'items.jsonl').read_text().splitlines():
        r = json.loads(line); n += 1
        if r['output']['intervention']['mode'] != r['intervention']: bad += 1; print('MISMATCH', r['mode'], r['output']['intervention'])
    print(t, 'records', n, 'mismatches', bad)
    assert n and bad==0
