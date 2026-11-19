from pathlib import Path
import os,subprocess,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d';root=D/'go';k=L/'out/kit_n_go'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
cmd=J.load(D/'GO_VIEW.json')+[sys.executable,'-B',str(D/'boundary.py'),str(k/'b/u.py'),'/tmp/q_22c714e1/p2','/tmp/q_22c714e1/v.json']
with (root/'u_preflight.log').open('w') as log:
 r=subprocess.run(cmd,env={**os.environ,'WORLD_SIZE':'0'},stdout=log,stderr=subprocess.STDOUT)
message='C1 training requires a parent-authorized 4-GPU allocation'
assert r.returncode==1 and message in (root/'u_preflight.log').read_text()
J.write(D/'U_PREFLIGHT.json',dict(status='BOUNDARY',returncode=r.returncode,helper='u.py',passed=['kit seal and GO','ADMIT400 result','configuration identity and world_size','native host/review admission'],first_refusal=message,boundary='No distributed allocation: WORLD_SIZE=0; no second torchrun attempt',optimizer_created=False))
