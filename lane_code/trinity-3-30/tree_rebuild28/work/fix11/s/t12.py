"""fix11: b/pf.py frames() on the job's staged config under the staging scope (sha256 -> q/u/<sha256>),
as pl.py stage() calls it, for the fixed and the 174134 mapping."""
import hashlib, importlib, json, os, sys
from pathlib import Path
mode = sys.argv[1]
sys.path.insert(0, '/tmp/q_22c714e1/p/s'); sys.path.insert(0, '/tmp/a15_f11_174134/b')
import pf
PK = bytes.fromhex('73747564656e745f70696c6f74').decode()
scope = importlib.import_module(PK + '.r1_persisted').scope
X = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b'
H = [hashlib.sha256(s.encode()).hexdigest() for s in (X + '/data2root', X + '/u/4d66fc2a/f')]
q = Path('/tmp/jjyeung/q_22c714e1' if mode == 'fixed' else '/tmp/q_22c714e1') / 'p/q'
roots = [str(q / 'f' / h) for h in H]
paths = {p.name: str(p) for p in (q / 'u').iterdir() if len(p.name) == 64}
for name, h in (('base/rows.sqlite', None),):
    pass
cfg = json.loads((q / 'n.json').read_text())
res = dict(mode=mode, map=os.environ.get('Q_E4'), staged_objects=len(paths))
with scope(paths):
    r = json.loads(Path(paths[cfg['streams']['routing']['sha256']]).read_text()) if cfg['streams']['routing']['sha256'] in paths else None
    res['routing_database'] = dict(pin=r and r.get('database'), staged=bool(r) and r['database']['sha256'] in paths)
    try:
        res['preflight_pf_frames'] = dict(result='PASS', value=pf.frames(cfg, roots))
    except Exception as e:
        res['preflight_pf_frames'] = dict(result='REFUSE', error=type(e).__name__ + ': ' + str(e)[:400])
print('RESULT ' + json.dumps(res, default=str))
