from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/'work/build24'));import joblib as J
for name in ('q','n'):
 k=L/'work/build24/kits'/name
 for f in ('k/p.json','k/n.json','k/r.json'):
  d=J.load(k/f)
  if f=='k/p.json': d={a:b for a,b in d.items() if a not in ('p_files','uploads','pin_paths','p_sources')}
  if f=='k/n.json': d={a:d[a] for a in ('init_artifact','r1_training')};d['r1_training']={a:b for a,b in d['r1_training'].items() if a in ('proof_mode','p_run','handover_receipt','persisted_files','donor_config_sha256')}
  print(name,f,json.dumps(d,indent=2))
 if name=='n':
  import base64
  raw=json.loads((k/'k/j.json').read_text());s=base64.b64decode(raw['payload']).decode()
  (L/'work/build24b/j_before.sh').write_text(s);print('J SHELL',s)
real=L.parent/'ext/m400real'
print('EXT top files',[(p.name,p.stat().st_size) for p in real.iterdir()])
for f in ('DONE.json','e.json','RP.json','h.out'):
 print('REAL',f,(real/f).read_text()[:15000])
