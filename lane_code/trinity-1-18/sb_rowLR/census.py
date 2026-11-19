"""CPU-only census of the pinned room rows and the GT pool referenced by the kit."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='')
import sys,json,hashlib,collections,sqlite3
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parent
BASE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19')
TREE=BASE/'work/tree_r1'; sys.path.insert(0,str(TREE))
from student_pilot.r1_rooms import Rooms
from generator.derivgen_v7.derivgen import room_v314
INPUTS={}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def reg(p,expect=None):
 p=Path(p);h=sha(p);assert expect is None or h==expect,(p,h,expect);INPUTS[str(p)]=h;return p
def read(p):return json.loads(reg(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(dict(x,input_sha256=INPUTS),indent=2,sort_keys=True)+'\n')
def band(a):return '<20' if a<20 else '20-40' if a<40 else '40-60' if a<60 else '60-100' if a<100 else '>=100'
def rules():
 pins=read(BASE/'work/build18/inputs/room_audit.json')['authority']
 for v in pins.values():
  v['path']=str(BASE/'work/build18/inputs'/Path(v['path']).name);reg(v['path'],v['sha256'])
 rules=Rooms(pins);extra={}
 for name,part,prefix in [('dev-S1','kit07ca49df_meta/m/k/dev_scene_exclusions.json','969cdb56'),('BENCH-v2','kit07ca49df_meta/m/k/benchmark_scene_exclusions.json','3119aa4a'),('withheld-80','shared/WITHHELD_ROOMS_80.json','634820b4')]:
  p=BASE/'fixtures/work'/part;x=read(p);assert INPUTS[str(p)].startswith(prefix);extra[name]={s.replace('scannetppv2/','scannetpp/') for s in x.get('physical_groups',x.get('rooms'))}
 return rules,extra
def status(c,rules,extra):
 st=rules.status({'canonical':c})[0];room=rules.room(c);return ([st] if st!='ok' else [])+[k for k,v in extra.items() if room in v]
class Geo:
 def __init__(self,z):
  self.depth=z['depth'];self.K=z['K'];self.K_frames=z['K_frames'];self.c2w=z['c2w'];self.valid=z['valid']
 def cam(self,k):return self.c2w[k-1,:3,:3],self.c2w[k-1,:3,3]
 def has(self,k):return bool(self.valid[k-1])
 def has_pose(self,k):return bool(self.valid[k-1])

def main():
 reg(__file__)
 seal=read(BASE/'out/TREE_SEAL.json')
 for f in ['generator/derivgen_v7/derivgen/room_v314.py','student_pilot/r1_rooms.py','student_pilot/ground_rows.py','student_pilot/trace_grammar.py']:
  reg(TREE/f,seal['files'][f])
 rules_,extra=rules()
 root=Path('/scratch/jjyeung/n30_mirror/rows_r1/out')
 srcpath=reg(root/'room_v4/rows.jsonl');assert INPUTS[str(srcpath)].startswith('1b4ed850')
 rows=[json.loads(l) for l in srcpath.open()]; source=collections.defaultdict(list)
 for r in rows:source[r['provenance']['canonical'].replace('scannetppv2/','scannetpp/')].append(r)
 store=root/'a2_vqa_v7';index=read(store/'FAMILY_INDEX_RANGES.json')['families']['room_size_estimation']
 db=reg(store/'vqa/rows.sqlite','210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443')
 con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);store_rows=[]
 for lo,hi in index:store_rows += [json.loads(raw) for raw, in con.execute('SELECT row FROM rows WHERE i BETWEEN ? AND ? ORDER BY i',(lo,hi))]
 con.close();reg(store/'FAMILY_QIDS/room_size_estimation.txt');assert {r['qid'] for r in store_rows}==set((store/'FAMILY_QIDS/room_size_estimation.txt').read_text().splitlines())
 hist=collections.Counter();hist_unit=collections.Counter()
 for r in store_rows:
  unit=r['provenance']['details']['unit'];a=float(r['answer'])/(10.763910416709722 if unit=='square feet' else 1);hist[band(a)]+=1;hist_unit[unit+'|'+band(a)]+=1
 (W/'inputs/store_room_rows.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in store_rows))
 pool=Path('/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt');results=[]
 for i,p in enumerate(sorted(pool.glob('*.npz'))):
  canonical=p.stem.replace('__','/').replace('scannetppv2/','scannetpp/');hits=status(canonical,rules_,extra)
  entry=dict(path=str(p),canonical=canonical,physical_room=rules_.room(canonical),exclusions=hits)
  if not hits:
   reg(p)
   with np.load(p) as z:
    pins=z['frame_indices'].tolist();sr=[r for r in source[canonical] if r['student_input']['frame_indices']==pins];entry.update(frame_indices=pins,matching_source_qids=[r['qid'] for r in sr],matching_metric_qids=[r['qid'] for r in sr if r['provenance']['details']['unit']=='square meters'])
    try:entry['measurement']=room_v314.measure(Geo(z),'sensor');entry['band']=band(entry['measurement']['area_m2'])
    except Exception as e:entry['measurement_error']=str(e)
  results.append(entry)
  if i%30==0:print('census',i+1,flush=True)
 counts=collections.Counter((x['canonical'].split('/')[0],','.join(x['exclusions']) or x.get('band','error')) for x in results)
 dump(W/'out/CENSUS.json',dict(status='MEASURED_LOCAL_POOL',tree_sha256=seal['tree_sha256'],pool=str(pool),pool_scope='171 GT rasters at kit-referenced t1_gt; not a complete dataset inventory',counts={d+'|'+b:n for (d,b),n in counts.items()},entries=results,store_room_rows=len(store_rows),before_histogram=dict(hist),before_by_unit=dict(hist_unit)))
 (W/'STATUS.md').write_text('Census: used the sealed w19 tree and pinned five-way room exclusions; measured the local kit-referenced GT pool and joined each raster to room_v4 by canonical capture and exact frame pins. out/CENSUS.json records the measured area bands, source matches, and store-v7 histogram.\n')
 print('COUNTS',dict(counts));print('HIST',hist);print('matches',sum(bool(x.get('matching_metric_qids')) for x in results));print('large matches',[(x['canonical'],x.get('measurement',{}).get('area_m2'),x.get('matching_metric_qids')) for x in results if x.get('measurement',{}).get('area_m2',0)>=40])
if __name__=='__main__':main()
