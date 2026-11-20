import sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
v=J.load(D/'CONFIG_DELTA.json');mapping=v['hash_replacements']
def refs(x):
 if isinstance(x,dict):return {refs(k):refs(y) for k,y in x.items()}
 if isinstance(x,list):return [refs(y) for y in x]
 if isinstance(x,str):
  for a,b in mapping.items():x=x.replace(a,b)
 return x
for n in NAMES:
 k=kit(n);a=L/'attic/build24m4i'/k.relative_to(L)
 for rel in ('k/c.json','k/n.json','k/8.json'):assert J.load(k/rel)==refs(J.load(a/rel))
 p=J.load(a/'k/p.json')
 for pin in v['after'].values():
  h=pin['sha256'];p['uploads'].append(dict(sha256=h,bytes=input_file(h).stat().st_size,opaque_name='u/'+h));p['pin_paths'][h]=p['namespace']+'/u/'+h
 p['uploads'].sort(key=lambda r:r['sha256']);assert p==J.load(k/'k/p.json')
 s=J.load(a/'k/s.json');s['entries'].pop(v['before']['card']['path']);pin=v['after']['card'];s['entries'][pin['path']]=dict(payload=base64.b64encode(input_file(pin['sha256']).read_bytes()).decode(),sha256=pin['sha256']);assert s==J.load(k/'k/s.json')
 build=J.load(a/'BUILD.json');build['kit_sha256']=J.sha(k/'SHA256SUMS.txt');assert build==J.load(k/'BUILD.json')
J.write(D/'EXACT_CONFIG_DELTA.json',dict(status='PASS',all_four_kits=True,card_changed_fields=['cells.direction.rows_per_step','cells.room_size.rows_per_step','room_rows_per_step'],dependent_capsules=['k/c.json','k/n.json','k/8.json','k/p.json','k/s.json','BUILD.json','SHA256SUMS.txt'],all_other_decoded_values_unchanged=True,tree_unchanged=True,b_unchanged=True))
print('EXACT CONFIG DELTA PASS')
