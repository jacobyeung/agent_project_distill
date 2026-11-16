"""cont_ops7: after a governed pull of DEST/fetched/result.tar.gz, verify like orchard_launcher.fetch and extract to DEST/fetched/x."""
import sys, json, tarfile, hashlib
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/kit/launcher')
import orchard_results as R
d = Path(sys.argv[1]); t = d/'fetched'
cfg = json.loads((d/'CONFIG.json').read_text()); sub = json.loads((d/'SUBMISSION.json').read_text())
rec = json.loads((t/'EXIT.json').read_text())
assert rec['token']==cfg['token'] and str(rec['job'])==str(sub['job']) and rec['plan_sha256']==cfg['plan_sha256']
R.verify(rec, t/'result.tar.gz', cfg['plan_sha256'])
x = t/'x'; x.mkdir(exist_ok=False)
with tarfile.open(t/'result.tar.gz') as tf: tf.extractall(x, filter='data')
sha = hashlib.sha256((t/'result.tar.gz').read_bytes()).hexdigest()
(t/'FETCH.json').write_text(json.dumps(dict(status=rec['status'], channel='governed', token=cfg['token'], job=sub['job'], sha256=sha, no_files_removed=True), indent=2)+'\n')
print('OK', sha, sorted(p.name for p in x.iterdir()))
