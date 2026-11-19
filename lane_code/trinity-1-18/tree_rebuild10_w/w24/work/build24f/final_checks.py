from pathlib import Path
import json,sys,ast,subprocess,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';T=L/'work/tree_r1'
sys.path[:0]=[str(D),str(L/'work/build24'),str(T)]
import joblib as J
from kit24f import upgrade
from student_pilot.source_seal import inventory
before=J.load(L/'work/build24b/TREE_FILES.json');after=inventory(T)
changed=[n for n in sorted(set(before)|set(after)) if before.get(n)!=after.get(n)]
assert changed==['launch_r2/persistence.py'],changed
for n,v in J.load(L/'work/build24e/INVARIANTS.json')['packages'].items():assert J.sha(L/'out'/n)==v['sha256']
e=J.load(L/'out/DELIVERY_24E.json');assert J.sha(L/e['package'])==e['sha256']
rows={}
for name in ('q','n','n_go'):
 k=L/'out/kit_n_go' if name=='n_go' else L/'work/build24/kits'/name
 expected=J.seal(k);assert upgrade(k)==expected,(name,'non-idempotent upgrade')
 assert J.load(k/'k/a.json')['GO']==(name=='n_go')
 old=L/'attic/build24f'/k.relative_to(L)
 for f in ('k/n.json','k/r.json','k/h.json','b/z.py','b/g.py','b/t.py','b/u.py'):
  if (k/f).exists():assert (k/f).read_bytes()==(old/f).read_bytes(),(name,f)
 c=J.load(k/'k/c.json');oldc=J.load(old/'k/c.json');c.pop('code');oldc.pop('code');assert c==oldc
 rows[name]=dict(kit_seal=expected,production_config_unchanged_except_source_pin=True,identity_checks_unchanged=True)
for p in D.glob('*.py'):ast.parse(p.read_text())
for p in [D/'go_rehearsal.sh',D/'live.sh',L/'work/build24/kits/n/job.sh']:
 subprocess.run(['/bin/bash','-n',str(p)],check=True)
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_changed=changed,existing_packages_unchanged=True,kits=rows))
print(json.dumps(rows,indent=2))
