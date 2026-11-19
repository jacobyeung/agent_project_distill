from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build13'
prior=B/'retained_kits13'
assert not prior.exists()
(B/'kits').rename(prior)
for script in (L/'work/n1fix2/seal.py',B/'kits13.py'):
    r=subprocess.run([sys.executable,'-I','-s','-B',str(script)])
    if r.returncode:raise SystemExit('Stopped after failed staging; no automatic retry')
