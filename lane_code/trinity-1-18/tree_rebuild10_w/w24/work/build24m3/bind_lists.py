from common import *
from student_pilot.p3_provenance import file_pin
from student_pilot.r1_persisted import scope
from student_pilot.r1_launch22 import validate_removals
from copy import deepcopy

def bind(stream,source):
 if stream not in ('pose','routing','pointing','vqa'):raise ValueError('R1_PROTECTED_REMOVAL_STREAM_REQUIRED')
 source=Path(source).resolve();raw=source.read_bytes();h=hashlib.sha256(raw).hexdigest()
 rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
 if not rows or any(not isinstance(v.get('row_key'),str) or not v['row_key'] for v in rows):raise ValueError('R1_PROTECTED_LIST_INVALID')
 dest=D/'u'/h;dest.parent.mkdir(exist_ok=True)
 if not dest.exists():dest.write_bytes(raw)
 paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
 paths[h]=str(dest)
 records={}
 for name in ('q','n','n_go','qd'):
  k=kit(name);spec=J.load(k/'k/p.json')
  for doc in ('k/c.json','k/n.json'):
   cfg=J.load(k/doc);old=deepcopy(cfg['remove_files'])
   if h in [v['sha256'] for v in old]:raise ValueError('R1_NAMING_REMOVAL_ORDER')
   cfg['remove_files'].insert(-1,dict(path='u/'+h,sha256=h,role='protected_rooms',stream=stream))
   cfg['r1_training']['launch22']['removal_order']=[v['sha256'] for v in cfg['remove_files']]
   with scope(paths):validate_removals(cfg)
   cap(k,doc,cfg)
  spec['uploads'].append(dict(sha256=h,bytes=len(raw)))
  spec['pin_paths']={v['sha256']:spec['namespace']+'/u/'+v['sha256'] for v in spec['uploads']}
  cap(k,'k/p.json',spec)
  for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
  records[name]=reseal(k)
 return dict(stream=stream,sha256=h,keys=len(rows),kits=records,dependent_receipts='Native in-job pool, room audit, scene rebuild, preparation, target-filter, config identity and bound census')

if __name__=='__main__':
 source=Path('/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl')
 assert J.sha(source)=='d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'
 assert J.sha(source.with_name('AUDIT_POINTING_K1.json')).startswith('8d5c1a9a')
 value=bind('pointing',source);assert value['keys']==320
 J.write(D/'POINTING_BINDING.json',value)
 print(value)
