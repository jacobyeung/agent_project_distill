from pathlib import Path
import sys,tarfile,json,collections,io
B=Path.cwd();R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
source=R/'from113/work/full_c8r/result.tar.gz'
with tarfile.open(source) as t:
 items=[json.loads(line) for line in t.extractfile('native/paired/results/items.jsonl')]
 print(collections.Counter((x['question_type'],x['arm']) for x in items if 'camera' in x['question_type']))
 selected=[]
 for typ,count in [('camera_displacement',3),('camera_movement_direction',3),('camera_rotation',4)]:
  group=[x for x in items if x['question_type']==typ and x['arm']=='unflagged']
  selected+=sorted(group,key=lambda x:x['key'])[:count]
 assert len(selected)==10
 refs=[dict(key=x['key'],question_type=x['question_type'],decode=x['decode']) for x in selected]
 dump(B/'work/proof_reference.json',refs)
 dump(B/'out/PROOF_KEYS.json',dict(source=pin(source),keys=[dict(key=x['key'],question_type=x['question_type']) for x in selected]))
 dest=B/'work/reference';dest.mkdir(exist_ok=True)
 request=json.load(t.extractfile('native/paired/request.json'));geom=json.load(t.extractfile('native/geometry/GEOMETRY_MANIFEST.json'))
 # Full original request and geometry manifest authenticate the original namespace.
 for name in ['native/geometry/GEOMETRY_MANIFEST.json','native/paired/request.json','metadata/CONFIG.json']:
  target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(t.extractfile(name).read())
 # Prepared geometry arrays are small; preserve original manifest membership for its validator.
 for member in t:
  if member.name.startswith('native/geometry/') and member.name.endswith('.npz'):
   (dest/member.name).write_bytes(t.extractfile(member).read())
 dump(dest/'a.json',refs)
 dump(dest/'b.json',dict(source=pin(source),array_members=sum(x.name.endswith('.npz') for x in t),prepared_arrays_available=True))
with tarfile.open(B/'out/d.tar','w') as t:
 for p in sorted(dest.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(dest)),recursive=False)
print('proof payload',pin(B/'out/d.tar'))
