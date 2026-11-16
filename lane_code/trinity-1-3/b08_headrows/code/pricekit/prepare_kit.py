import sys, os
sys.dont_write_bytecode=True
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import ast,json,hashlib,pickle,gzip,collections
import numpy as np
ROOT=Path('/scratch/jjyeung/orch_cd'); W=ROOT/'devs1_masks/work'; O=W.parent/'out'; V=W/'vendor'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={}
def copy(rel,name=None):
 p=ROOT/rel; dest=V/(name or p.name);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());pins[str(p)]=sha(p);return dest
def extract(rel,name,names,header):
 p=ROOT/rel;s=p.read_text();tree=ast.parse(s);parts=[ast.get_source_segment(s,n) for n in tree.body if getattr(n,'name',None) in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
 (V/name).write_text(header+'\n\n'+'\n\n'.join(parts)+'\n');pins[str(p)]=sha(p)
for n in ['programs','prog_v2','geomswap','tplib','common','scene_gt','binding','pool_common','label_adapter','lane_geometry','devs1_pricing']:
 copy(f'devs1_price/work/{n}.py')
copy('ofs_e1/ofs/core.py','linker.py');p=V/'linker.py';p.write_text(p.read_text().replace('from rk.sam3mask import tower','from compat import tower'))
copy('grd_selector/work/setsel/setlib.py')
extract('grd_selector/work/selector/features.py','features.py',['logit','box_iou','mask_box','mask_uv','project','lift_member','reprojection','object_rows','check','Scene','MAX_PIXELS','H','W','FORBIDDEN'], 'import math\nimport numpy as np\nfrom scipy import ndimage\nfrom compat import tower, cache')
extract('grd_selector/work/setsel/build.py','set_features.py',['set_features','match_ids','iou'], 'import numpy as np')
extract('grd_selector/work/setsel/pairs.py','pair_features.py',['geom_of','box_iou','reproj','pair_features','MAXPTS','REPROJ_D'], 'import numpy as np\nimport selector_geom as PZ\nfrom setlib import PFEATS\nMAXPTS, REPROJ_D = 1500, 3.0')
extract('grd_selector/work/setsel/price.py','selector_geom.py',['GeomTower','lift','union','H','W'], 'import math\nimport numpy as np')
copy('sam3_tower/work/c1mix_e2e/student_pilot/sam3_tower.py','sam3_tower.py')
extract('sam3_tower/work/c1mix_e2e/student_pilot/sam3_tower.py','phrase.py',['SINGULAR','normalize_phrase'],'')
copy('grd_selector/work/dense/stub_backend.py')
extract('grd_selector/work/dense/dense_recache.py','sam_backend.py',['make_postprocess','detect_prompt','prediction','rle_encode'],'import numpy as np')
copy('sam3_tower/out/SAM3_RECEIPT.json')
copy('official_reads/FUSION_POLICY_FROZEN_VSI_20261111.md')
# Export fitted sklearn states without importing or training sklearn.
class State:
 def __setstate__(self,s):self.__dict__.update(s)
class Reader(pickle.Unpickler):
 def find_class(self,module,name):
  if module.startswith('sklearn.'):return State
  if module.startswith('numpy') or module=='builtins':return super().find_class(module,name)
  raise ValueError((module,name))
models={}
for tag,rel,probkey,table in [
 ('accept','grd_selector/work/setsel/data/probs2/deploy_portable_np_logistic.pkl','DEPLOY|portable_np|logistic','grd_selector/work/setsel/data/vsi_tab.jsonl'),
 ('pairs','grd_selector/work/setsel/data/pairs_fit/deploy_pairs_logistic.pkl','DEPLOY|logistic','grd_selector/work/setsel/data/vsi_pairs.jsonl')]:
 p=ROOT/rel;d=Reader(p.open('rb')).load();sc,lr=[s for _,s in d['model'].steps]
 m=dict(features=d['feats'],mean=sc.mean_.tolist(),scale=sc.scale_.tolist(),coef=lr.coef_[0].tolist(),intercept=float(lr.intercept_[0]),source=str(p),source_sha256=sha(p));models[tag]=m
 probs=json.loads((p.parent/('probs.json' if tag=='accept' else 'pair_probs.json')).read_text())[probkey]
 errs=[]
 for line in (ROOT/table).open():
  r=json.loads(line)
  if tag=='accept' and r['kind']!='candidate':continue
  f=r['features'] if tag=='accept' else r['f'];key=f"{r['object_id']}|{r['candidate_id']}" if tag=='accept' else f"{r['object_id']}|{r['a']}|{r['b']}"
  x=np.array([f[k] for k in m['features']]);z=np.dot((x-sc.mean_)/sc.scale_,lr.coef_[0])+lr.intercept_[0];pred=1/(1+np.exp(-z));errs.append(abs(pred-probs[key]))
 m['parity_rows']=len(errs);m['max_probability_error']=max(errs);assert max(errs)<1e-12
(V/'MODELS.json').write_text(json.dumps(models,indent=2))
(O/'SOURCE_PINS.json').write_text(json.dumps(pins,indent=2))
sys.path.insert(0,str(V))
import binding as B,label_adapter as A
from phrase import normalize_phrase
plan=json.loads((ROOT/'devs1_tower/out/r2/kit/PLAN.json').read_text());caps={c['native']:c for c in plan['captures']}
qref={}
with gzip.open(ROOT/'devs1_tower/out/r2/kit/QIDS.jsonl.gz','rt') as f:
 for line in f:
  r=json.loads(line)
  if r['native'] in caps:qref[r['qid']]=r
items={r['qid']:r for r in map(json.loads,(ROOT/'devs1_price/out/ITEMS.jsonl').open())}
fixed={r['id']:r for r in map(json.loads,(ROOT/'devs1_direct/out/r3/TASKS.jsonl').open())}
releases={}
for line in (ROOT/'weak_data/in/v590kgt/inv/QUESTIONS.jsonl').open():
 r=json.loads(line)
 if r['qid'] in qref:releases[r['qid']]=r
ex=[]
with gzip.open(ROOT/'dose_pool/out/pool_v0/ROWS_ALL.jsonl.gz','rt') as f:
 for line in f:
  r=json.loads(line);qid=r['qid']
  if qid not in qref or qid in items:continue
  ref=qref[qid];t=ref['type']
  if t not in B.TYPES:continue
  inp=r['student_input'];release=releases.get(qid);opts=B.PC.split_question(release['question'])[1] if release else []
  q=dict(qid=qid,id=qid,question_type=t,question=inp['question'],options=inp.get('options') or [],answer=r['answer'],released_answer=r.get('released_answer'),released_options=opts,source_target=r['target'],native=r['native'],room=ref['room'],scene=caps[r['native']]['scene'],fixed=qid in fixed)
  q['dataset']=q['scene'].split('/')[0];st=A.strata(q);q.update(stratum=st['stratum'],released_answer_in_options=st['released_answer_in_options'])
  try:program,names,unit=B.bind(q);q.update(program=program,operands=names,unit=unit,binding_error=None)
  except Exception as e:q.update(program=None,operands=[],unit=None,binding_error=str(e));ex.append(dict(qid=qid,reason=str(e)))
  q.pop('source_target');items[qid]=q
for qid,q in fixed.items():
 if qid not in items and q['native'] in caps and q['question_type']=='room_size_estimation':
  q=dict(q,qid=qid,fixed=True);pr,ns,u=B.bind(q);q.update(program=pr,operands=ns,unit=u,binding_error=None);items[qid]=q
for row in map(json.loads,(ROOT/'devs1_direct/out/r3/EXCLUDED_MISSING_ROOM.jsonl').open()):
 qid=row['id']
 if qid not in items and row['native'] in caps:
  q=dict(row,qid=qid,fixed=False,released_answer_in_options=None,released_options=[])
  pr,ns,u=B.bind(q);q.update(program=pr,operands=ns,unit=u,binding_error=None);items[qid]=q
rows=[]
for c in plan['captures']:
 frames=[c['dense'][slot] for slot in c['anchor_slots']];assert [f['index'] for f in frames]==c['anchor_indices']
 names=sorted({n.lower() for q in items.values() if q['native']==c['native'] for n in q['operands']})
 rows.append({k:c[k] for k in ['native','scene','group','hw','anchor_indices']}|dict(frames=frames,names={n:normalize_phrase(n) for n in names},phrases=sorted({normalize_phrase(n) for n in names})))
manifest=dict(schema='devs1-mask-manifest-v1',captures=rows,density=dict(joint_floor=.2,cap=10,prompts='P0 only',mask_threshold=.5,resolution=1008,dtype='bf16',link_instance_floor=.3),plan_sha256=sha(ROOT/'devs1_tower/out/r2/kit/PLAN.json'),receipt_sha256=sha(V/'SAM3_RECEIPT.json'),checkpoint_sha256=json.loads((V/'SAM3_RECEIPT.json').read_text())['checkpoint_sha256'],detect_calls=sum(len(c['phrases']) for c in rows))
(O/'MANIFEST.json').write_text(json.dumps(manifest,indent=1));(O/'ITEMS.jsonl').write_text(''.join(json.dumps(q)+'\n' for q in sorted(items.values(),key=lambda q:q['qid'])));(O/'BINDING_EXCLUSIONS.json').write_text(json.dumps(ex,indent=2))
(O/'FRAMES_TAR.txt').write_text(''.join(p+'\n' for p in sorted({f['path'] for c in rows for f in c['frames']})))
print(json.dumps(dict(captures=len(rows),items=len(items),detect_calls=manifest['detect_calls'],binding_errors=len(ex),model_parity={k:(v['parity_rows'],v['max_probability_error']) for k,v in models.items()})))

manifest['items_sha256']=sha(O/'ITEMS.jsonl');(O/'MANIFEST.json').write_text(json.dumps(manifest,indent=1))
