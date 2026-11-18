import json, sys, hashlib, tarfile
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/review_h1read5/work/k/kit/launcher')
import orchard_results as R, orchard_stage as S, chain_save as A
W = Path('/scratch/jjyeung/orch_n30/review_h1read5/work/es2')
arc = W/'p_d_1.tar.gz'; cfg = json.loads((W/'prep_d/CONFIG.json').read_text())
with tarfile.open(arc) as t: marker = json.load(t.extractfile('PARTIAL.json')); names = t.getnames()
rc = dict(schema='a3', synthetic=False, plan_sha256=cfg['plan_sha256'], status='PARTIAL', complete=False,
          archive=dict(bytes=arc.stat().st_size, sha256=hashlib.sha256(arc.read_bytes()).hexdigest()))
R.verify(rc, arc, cfg['plan_sha256'], allow_partial=True)
out = W/'x'; out.mkdir()
with arc.open('rb') as s: S.extract_stream(s, out, None, 512*1024**2)
print('verified+extracted', sorted(p.name for p in (out/'logs').iterdir()), {k:(v['retained_bytes'],v['truncated']) for k,v in marker['logs'].items()}, arc.stat().st_size)
