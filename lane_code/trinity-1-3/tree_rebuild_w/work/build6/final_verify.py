"""Verify delivered identities and the closed authorization boundary."""
import hashlib,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load
d=json.loads((B/'DELIVERY.json').read_text());a=json.loads((B/'proofs/package/ARCHIVE.json').read_text())
assert digest(inventory(L/'work/tree_r1'))==d['tree_seal']==a['source_sha256']
assert a['sha256']==d['sha256'] and a['status']=='verified'
assert (L/d['path']).stat().st_size==d['bytes']<150_000_000
closed=[]
for name in ('a2','a0'):
 launch=load(B/'kits'/name/'k/launch.json')
 assert launch.get('production_authorized') is False
 closed.append(dict(kit=name,production_authorized=False))
for name in ('a0_pool_abs_distance_reworded','a0_recovery','a0_room','a0_units'):
 proof=json.loads((B/'proofs/rows'/(name+'.json')).read_text());assert len(proof['examples'])<=200
units=json.loads((B/'proofs/rows/UNITS.json').read_text());assert units['errors']==[]
result=dict(source_seal=d['tree_seal'],archive_sha256=d['sha256'],closed=closed,real_example_limits=True,unit_conversion_errors=0)
(B/'FINAL_VERIFY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
