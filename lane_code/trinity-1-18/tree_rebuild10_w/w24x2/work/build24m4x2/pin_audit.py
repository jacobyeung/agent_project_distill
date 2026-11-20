from pathlib import Path
import sys,os,json,hashlib,re
L=Path.cwd();D=L/'work/build24m4x2';sys.path.insert(0,str(D))
from common import z,kit,NAMES,write
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
base=inventory(D/'base_tree');new=inventory(L/'work/tree_r1c');changed={n for n in base if base[n]!=new[n]}
hashes={h:n for n,h in base.items()};hashes[digest(base)]='C_tree';hashes['7a8022ad478678eb68139a0bd27fc2b8a1262c76f4bc0e44d1217c860508e263']='review_tree'
import base64
audit=[];scanned=[]
for label,root in [('rcj',L/'out/rcj')]+[(n,kit(n)) for n in NAMES]:
 paths=list(root.iterdir()) if label=='rcj' else [p for part in ('b','k') for p in (root/part).rglob('*') if p.is_file() and p.suffix!='.tar']
 for p in paths:
  if not p.is_file():continue
  scanned.append(label+'/'+str(p.relative_to(root)))
  text=p.read_text()
  try:
   v=json.loads(text)
   if isinstance(v,dict) and v.get('encoding')=='base64-json':text=base64.b64decode(v['payload']).decode()
  except ValueError:pass
  for h in sorted(set(re.findall(r'[0-9a-f]{64}',text))&hashes.keys()):
   name=hashes[h];stale=name in changed or name in ('C_tree','review_tree')
   audit.append(dict(path=scanned[-1],sha256=h,source=name,classification='STALE' if stale else 'UNCHANGED_SOURCE',reason='N file bytes equal C; retain the valid pin' if not stale else 'Launch pin needs replacement'))
assert not [r for r in audit if r['classification']=='STALE']
write(D/'PIN_AUDIT.json',dict(status='PASS',scanned=scanned,fixed=[dict(path=p,before=b,after=digest(new),role='N launch tree') for p,b in [('rcj/nd.py:TREE',digest(base)),('rcj/ch.py:TREE','7a8022ad478678eb68139a0bd27fc2b8a1262c76f4bc0e44d1217c860508e263'),('rcj/f.json:tree_sha256',digest(base))]],dependent_helper_pin=dict(path='rcj/nd.py:FIELDS',sha256=z.sha(L/'out/rcj/f.json')),kit_updates=['k/7.json','k/c0.json','k/a.json','k/c.json','k/n.json','k/p.json','k/t_e047002134f979bd.tar','SHA256SUMS.txt','BUILD.json'],retained_file_pins=audit,deliberate_old_tree_pins=[],stale_pins=[]))
print('PIN AUDIT PASS',len(scanned),'files',len(audit),'retained identical file pins')
