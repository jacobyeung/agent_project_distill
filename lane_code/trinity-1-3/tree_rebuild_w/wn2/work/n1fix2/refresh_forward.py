from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';O=B/'proofs/forward'
for name in ('store','input'):
    old=O/name
    if old.exists():old.rename(O/('retained_'+name))
with (B/'forward.log').open('w') as log:
    code=subprocess.run([sys.executable,'-I','-s','-B',str(B/'proof_forward9.py')],cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
if code<0:raise SystemExit('Proof killed; stop without retry')
raise SystemExit(code)
