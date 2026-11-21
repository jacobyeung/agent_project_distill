import json,os,shutil,subprocess,sys,hashlib
from pathlib import Path
O=Path(os.environ['TG_OUT']);K=Path(os.environ['TG_KIT']);job=os.environ['TG_JOB']
X=O/'x';N=O/'n';B=O/'bin'
for p in (X,N,B,O/'logs'):p.mkdir(exist_ok=True)
if (N/'live_spool').exists():raise SystemExit('E_USED_OUTPUT: choose a fresh output directory')
if os.environ['TG_FULL']=='full':subprocess.run(['mount','-t','tmpfs','-o','size=16m','tmpfs',str(X)],check=True)
(X/'n_s').mkdir(mode=0o700)
p=X/'n_s'/('sess_'+job+'.json');shutil.copyfile(os.environ['TG_SESS'],p);p.chmod(0o600)
T=N/'p/q/r';T.mkdir(parents=True)
for name,marker in [('m100','artifact.json'),('checkpoint_7','complete.json')]:
 d=T/name;d.mkdir();(d/'q.bin').write_bytes(os.urandom(1<<20))
 (d/marker).write_text(json.dumps(dict(step=7 if name.startswith('checkpoint') else 100)))
(N/'q.log').write_text('q 1\n')
if os.environ['TG_FULL']=='full':
 with (O/'logs/fill.log').open('wb') as f:
  subprocess.run(['dd','if=/dev/zero','of='+str(X/'fill'),'bs=1M','count=32'],stdout=f,stderr=f)
  subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
 if shutil.disk_usage(X).free:raise SystemExit('E_NOT_FULL')
shim=B/'python3'
shim.write_text('#!/bin/bash\nexec "$TG_PY" -I -s -B "$TG_DIR/observe.py" "$@"\n');shim.chmod(0o700)
env={**os.environ,'PATH':str(B)+':'+os.environ['PATH'],'ROOT':str(K),'N':str(N),'SLURM_JOB_ID':job,
     'TK_JOB_START':str(int(__import__('time').time())),'TK_FINAL_SECONDS':'180','TK_COPY_DEADLINE':str(int(__import__('time').time())+180)}
shell='set -euo pipefail\nsource "$ROOT/b/pc.sh"\nsleep 2\nexit 0\n'
with (O/'logs/copier.stdout').open('w') as out,(O/'logs/copier.stderr').open('w') as err:
 r=subprocess.run(['bash','-c',shell],env=env,stdout=out,stderr=err)
receipts=N/'live_spool/private/sess.json.receipts.jsonl'
rows=[json.loads(l) for l in receipts.read_text().splitlines()] if receipts.exists() else []
result=dict(status='PASS' if r.returncode==0 and len(rows)==16 else 'FAIL',returncode=r.returncode,job=job,free_bytes=shutil.disk_usage(X).free,receipts=rows,
            kit_sha256=hashlib.sha256((K/'SHA256SUMS.txt').read_bytes()).hexdigest())
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],returncode=r.returncode,receipts=len(rows),free_bytes=result['free_bytes'])))
raise SystemExit(r.returncode or (0 if len(rows)==16 else 1))
