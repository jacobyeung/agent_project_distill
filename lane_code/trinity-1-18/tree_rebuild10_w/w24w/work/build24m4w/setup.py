from pathlib import Path
import sys, json, hashlib, gzip, collections, shutil, resource
resource.setrlimit(resource.RLIMIT_AS, (14*1024**3,14*1024**3))
L=Path(__file__).resolve().parents[2]; D=L/'work/build24m4w'; T=L/'work/tree_r1c'
sys.path[:0]=[str(L/'work/build24m4t'),str(T),str(L/'out/kit_qd/b')]
from common import kit, NAMES, input_file
import z
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest, file_pin
from student_pilot.extent_receipt import Extents
from launch_r1.build import verify
def write(p,v): p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
base=dict(tree=digest(inventory(T)), inventory=inventory(T), kits={n:verify(kit(n)) for n in NAMES},
 files={n:{str(p.relative_to(kit(n))):dict(sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in NAMES},
 rcj={p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()})
assert base['tree']=='de202f58b31793608f886360a9fdfb5f58c24932e35976efcf74acead62e3cfe'
write(D/'BASELINE.json',base)
sel=input_file('5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af')
sources=sorted(k for k,v in z.load(sel)['sources'].items() if v['status']=='ELIGIBLE');assert len(sources)==9
write(D/'SOURCES.json',dict(selection_sha256=z.sha(sel),names=sources))
U=L.parent/'w24u/work/build24m4u'; receipt=D/'c072905b.json'
shutil.copyfile(U/'c072905b.json',receipt)
assert z.sha(receipt)=='c072905be4405a92d7bb906112209f2d27a8c9b58d291b64373c5551c3e96495'
R=L.parent.parent/'work/d173725/173725'
R=L.parent/'../work/d173725/173725' if False else Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173725/173725')
sample=z.load(R/'p_sample.json')
rows=[json.loads(x['row']) for x in sample['rows']]
pool=next(r for r in rows if r.get('s1_source',{}).get('name') in sources)
write(D/'pool_row.json',pool)
try: Extents(file_pin(receipt)).check(pool,'routing')
except ValueError as e:
 assert str(e)=='EXTENT_ROW_UNAUDITED'
 write(D/'BEFORE.json',dict(status='EXPECTED_REFUSAL',error=str(e),qid=pool['qid'],source=pool['s1_source']['name'],row_sha256=digest(pool),origin=str(R/'p_sample.json'),origin_sha256=z.sha(R/'p_sample.json'),modification='none; exact parsed P row'))
else: raise AssertionError('Expected fail-before')
for f in ['p_sample.json','rd0/rdiff.json.gz','materialization.json','chain.json']:
 q=D/'published'/f;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/f,q)
print(json.dumps(dict(tree=base['tree'],sources=sources,fail_before=z.load(D/'BEFORE.json')),indent=2))
