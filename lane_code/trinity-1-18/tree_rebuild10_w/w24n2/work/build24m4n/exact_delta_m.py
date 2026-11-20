from common import *
import copy
from launch_r1.build import verify
base=J.load(D/'BASE_FILES.json');records={}
for n in NAMES:
 k=kit(n);old=L/'attic/build24m4n'/k.relative_to(L)
 current={str(p.relative_to(k)):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob('*') if p.is_file()}
 assert current.keys()==base[n].keys()
 changed=sorted(rel for rel in current if current[rel]!=base[n][rel])
 arc=J.load(k/'k/a.json')['source']['path']
 assert set(changed)=={'k/7.json','k/c0.json','k/p.json','k/c.json','k/n.json','k/a.json','BUILD.json','SHA256SUMS.txt',arc},changed
 for rel in changed:assert J.sha(old/rel)==base[n][rel]['sha256']
 seal=J.load(D/'TREE_CPRIME.json')['after'];ah=J.sha(k/arc)
 for rel in ('k/7.json','k/c0.json'):
  a=J.load(old/rel);b=J.load(k/rel)
  assert {p for p in a['files'] if a['files'][p]!=b['files'][p]}=={'tests/test_host24j.py'}
  a['files']['tests/test_host24j.py']=b['files']['tests/test_host24j.py']
  a.update(commit='sha256:'+seal,tree_sha256=seal);a['archive']['sha256']=ah
  assert a==b,(n,rel)
 for rel in ('k/c.json','k/n.json'):
  a=J.load(old/rel);b=J.load(k/rel);a['code']=b['code'];assert a==b,(n,rel)
 a=J.load(old/'k/a.json');b=J.load(k/'k/a.json');a['source'].update(sha256=ah,tree_sha256=seal);assert a==b
 a=J.load(old/'BUILD.json');b=J.load(k/'BUILD.json')
 a.update(source_seal=seal,config_sha256=J.sha(k/'k/c.json'),kit_sha256=J.sha(k/'SHA256SUMS.txt'));assert a==b
 a=J.load(old/'k/p.json');b=J.load(k/'k/p.json');before=a['code_sha256'];after=b['code_sha256']
 a['code_sha256']=after
 for row in a['uploads']:
  if row['sha256']==before:row.update(sha256=after,bytes=(D/'inputs'/after).stat().st_size,opaque_name='u/'+after)
 a['uploads'].sort(key=lambda r:r['sha256']);a['pin_paths']={r['sha256']:a['namespace']+'/u/'+r['sha256'] for r in a['uploads']}
 assert a==b,(n,'k/p.json')
 assert b['code_sha256']==J.load_raw(k/'k/c0.json')['sha256']
 assert J.load(k/'k/a.json')['GO']==J.load(k/'BUILD.json')['GO']==(n=='n_go')
 records[n]=dict(seal=verify(k),changed_files=changed,only_tree_dependent_pins=True)
J.write(D/'EXACT_KIT_DELTA.json',dict(status='PASS',kits=records))
print('All four kits change exactly nine tree-dependent files; decoded non-tree fields unchanged')
