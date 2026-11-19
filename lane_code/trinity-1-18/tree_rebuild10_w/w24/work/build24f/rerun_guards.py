from pathlib import Path
import subprocess,sys,json
D=Path(__file__).resolve().parent;rows=json.loads((D/'SUITES.json').read_text())
for v in rows:
 if not v['name'].startswith('guard_'):continue
 with (D/(v['name']+'.log')).open('w') as log:
  p=subprocess.run([sys.executable,'-I','-B',str(D/(v['name']+'.py'))],stdout=log,stderr=subprocess.STDOUT)
 v['returncode']=p.returncode;print(v['name'],p.returncode,flush=True)
(D/'SUITES.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(v['returncode']==0 for v in rows)
