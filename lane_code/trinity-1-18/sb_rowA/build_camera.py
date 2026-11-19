"""Build camera wording inventory and exact-schema evaluation twins.

Usage: python -B build_camera.py
Training cells fail closed when the authenticated routed source is unavailable.
JSONL payload schemas are preserved; their input pins live in companion JSON.
"""
import copy,hashlib,json,re,sys,unicodedata
from pathlib import Path
from collections import Counter
from string import Formatter
from wordings import TYPES, candidates, HELDOUT
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
READ=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src')
SEED=20261118;THRESHOLD=0.20
INPUTS={}
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(x):return hashlib.sha256(encoded(x)).hexdigest()
def pin(p):
 p=Path(p).resolve()
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 INPUTS[str(p)]=h
 return dict(path=str(p),sha256=h)
def load(p):pin(p);return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps({**x,'input_sha256':dict(INPUTS)},ensure_ascii=False,indent=2)+'\n')
def normalized(s):
 s=unicodedata.normalize('NFKC',s).casefold().translate(str.maketrans({'’':"'",'–':'-','—':'-'}))
 s=re.sub(r'\{(?:i|j|n)\}', '#',s)
 s=re.sub(r'\d+(?:\.\d+)?','#',s)
 return ' '.join(s.split())
def extract(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in ('question','question_text','prompt') and isinstance(v,str) and len(v)>12:yield v
   elif isinstance(v,(dict,list)):yield from extract(v)
 elif isinstance(obj,list):
  for x in obj:yield from extract(x)
def levenshtein(a,b):
 if len(a)>len(b):a,b=b,a
 if not a:return len(b)
 eq={}
 for i,c in enumerate(a):eq[c]=eq.get(c,0)|(1<<i)
 vp=(1<<len(a))-1;vn=0;score=len(a);top=1<<(len(a)-1)
 for c in b:
  x=eq.get(c,0)|vn;d=(((x&vp)+vp)^vp)|x
  hp=vn|~(d|vp);hn=vp&d
  if hp&top:score+=1
  elif hn&top:score-=1
  hp=(hp<<1)|1;hn<<=1;vp=hn|~(d|hp);vn=d&hp
 return score

NEAR_CACHE={}
def near(q,corpus):
 q=normalized(q)
 key=(id(corpus),q)
 if key in NEAR_CACHE:return NEAR_CACHE[key]
 for s in corpus:
  if abs(len(q)-len(s))/max(len(q),len(s)) >= THRESHOLD:continue
  dist=levenshtein(q,s)/max(len(q),len(s))
  if dist < THRESHOLD:
   NEAR_CACHE[key]={'normalized_reference':s,'distance':dist}
   return NEAR_CACHE[key]
 NEAR_CACHE[key]=None
 return None

def schema(x):
 if isinstance(x,dict):return {k:schema(v) for k,v in x.items()}
 if isinstance(x,list):return ['list',sorted({json.dumps(schema(v),sort_keys=True) for v in x})]
 return type(x).__name__

def main():
 pin(__file__);pin(ROOT/'wordings.py');audit=load(OUT/'SOURCE_AUDIT.json')
 INPUTS.update(audit['input_sha256'])
 assert audit['status']=='MISSING','Resolve source admission explicitly before enabling training output.'
 original=load(READ/'items/devs1_routed.json')
 assert digest(original['items'])==original['item_set_sha256']
 corpus=set();files=[];r0_files=[];dedup={};r0cams={}
 for inv in ['item_file_inventory.txt','kit_json_inventory.txt']:
  pin(OUT/inv)
  for s in (OUT/inv).read_text().splitlines():
   p=Path(s);pp=pin(p)
   if pp['sha256'] not in dedup:
    if p.suffix=='.jsonl':
     d=[json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    else:d=json.loads(p.read_text())
    dedup[pp['sha256']]=d
   d=dedup[pp['sha256']]
   qs=list(extract(d));corpus.update(normalized(q) for q in qs)
   files.append(dict(**pp,question_occurrences=len(qs)))
   if '/items/' in s and 'r0' in p.name.lower():
    items=d['items'] if isinstance(d,dict) else d
    c=Counter(x.get('question_type',x.get('type')) for x in items)
    r0_files.append(dict(**pp,items=len(items),camera_counts={t:c[t] for t in TYPES}))
    for x in items:
     if x.get('question_type') in TYPES:
      if x['id'] in r0cams:assert r0cams[x['id']]==x
      r0cams[x['id']]=x
 assert not r0cams,'R0 camera input requires the read’s R0-specific room admission; do not merge silently.'
 assert corpus
 corpus=sorted(corpus)
 (OUT/'WORDING_CORPUS.txt').write_text('\n'.join(corpus)+'\n');pin(OUT/'WORDING_CORPUS.txt')
 print('Corpus:',len(corpus),'unique normalized questions from',len(files),'files',flush=True)
 # Candidate filtering never supplies wording: every proposal is authored in wordings.py.
 accepted={};removed=[]
 sample=dict(i=3,j=19,n=32,unit='meters',options='A. left; B. right; C. forward; D. backward')
 for t,templates in candidates().items():
  good=[]
  for k,template in enumerate(templates):
   hit=near(template.format(**sample),corpus)
   if hit:removed.append(dict(type=t,candidate=k,template=template,**hit))
   else:good.append(template)
  assert len(good)>=40,(t,'wordings short',len(good))
  accepted[t]=good[:40]
  print(t,'accepted',len(good),'selected',40,flush=True)
 for t in TYPES:
  assert len(set(accepted[t]))==40 and len(set(HELDOUT[t]))==8
  for template in accepted[t]+HELDOUT[t]:
   fields={v for _,v,_,_ in Formatter().parse(template) if v}
   assert fields=={'i','j','n',*(['unit'] if t==TYPES[0] else ['options'] if t==TYPES[2] else [])}
  for template in HELDOUT[t]:assert near(template.format(**sample),corpus) is None,(t,template)
  assert not ({normalized(s.format(**sample)) for s in accepted[t]} & {normalized(s.format(**sample)) for s in HELDOUT[t]})
 inventory=dict(status='TRAINING_SOURCES_MISSING',training=accepted,heldout=HELDOUT,
  training_per_type=40,heldout_per_type=8,normalization='NFKC, casefold, ASCII typographic punctuation, numbers -> #, collapse whitespace',
  distance='character Levenshtein / max normalized length; reject if distance < threshold',threshold=THRESHOLD,
  corpus_files=files,corpus_unique_normalized=len(corpus),candidate_removals=removed,
  training_candidates_per_type={t:len(v) for t,v in candidates().items()},
  unused_accepted_candidates_per_type={t:len(candidates()[t])-40-sum(x['type']==t for x in removed) for t in TYPES})
 write(OUT/'WORDINGS.json',inventory);pin(OUT/'WORDINGS.json')
 originals=[x for x in original['items'] if x['question_type'] in TYPES]
 assert Counter(x['question_type'] for x in originals)==Counter({t:150 for t in TYPES})
 new=[];twins=[];counts=Counter();actual_training=set();actual_heldout=set()
 for old in originals:
  t=old['question_type'];i,j=old['display_frame_pair'];n=len(old['source_frame_indices'])
  assert n==32 and 1<=i<j<=n
  # Stable assignment independent of file order and Python RNG implementation.
  k=int(hashlib.sha256(f'sb_rowA|heldout|{SEED}|{t}|{old["id"]}'.encode()).hexdigest(),16)%8
  options='; '.join(old['options'])
  vals=dict(i=i,j=j,n=n,unit='meters',options=options)
  q=HELDOUT[t][k].format(**vals)
  assert near(q,corpus) is None
  if t==TYPES[0]:assert 'meters' in q
  elif t==TYPES[1]:assert '(-180, 180]' in q and 'degrees' in q and 'positive' in q and 'left' in q
  else:
   for opt in old['options']:assert opt in q
  x=copy.deepcopy(old);x['id']=old['id']+f'-sbca-h{k:02d}';x['question']=q
  assert schema(x)==schema(old)
  assert {key for key in x if x[key]!=old[key]}=={'id','question'}
  assert x['answer']==old['answer'] and x['ground_truth']==old['ground_truth']
  new.extend([copy.deepcopy(old),x]);counts[f'{t}|h{k:02d}']+=1
  twins.append(dict(original_id=old['id'],reworded_id=x['id'],type=t,wording_id=f'h{k:02d}',
   original_item_sha256=digest(old),reworded_item_sha256=digest(x),source_file_sha256=INPUTS[str(READ/'items/devs1_routed.json')]))
  actual_heldout.add(normalized(q))
  actual_training.update(normalized(s.format(**vals)) for s in accepted[t])
 assert not actual_training & actual_heldout
 assert len(new)==900 and len({x['id'] for x in new})==900
 assert len(counts)==24 and min(counts.values())>0
 new.sort(key=lambda x:x['id'])
 reserve=READ/'auth/R0_ROOMS.txt';rp=pin(reserve);assert rp['sha256'].startswith('bdb5d402')
 rooms=set(reserve.read_text().splitlines());assert not any(x['room_key'] in rooms for x in new)
 m=dict(schema='h1-items-v1',name='heldout_camera_wording',status='ready',development_only=True,
  items=new,count=len(new),per_type=dict(Counter(x['question_type'] for x in new)),item_set_sha256=digest(new),
  r0_check=dict(checked=len(new),found=0,pin=copy.deepcopy(original['r0_check']['pin'])),sources=[pin(READ/'items/devs1_routed.json'),pin(ROOT/'wordings.py')])
 write(OUT/'HELDOUT_CAMERA_ITEMS.json',m);pin(OUT/'HELDOUT_CAMERA_ITEMS.json')
 # Exact native-task twins preserve original task schemas and all clip/label fields.
 taskpath=READ/'b/work/meta/x/sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl'
 pin(taskpath);tasks={x['id']:x for x in (json.loads(line) for line in taskpath.read_text().splitlines() if line.strip())}
 native=[]
 for twin in twins:
  task=tasks[twin['original_id']];old=next(x for x in originals if x['id']==task['id'])
  for key in ['question','question_type','options','dataset','scene','native','source_frame_indices','answer']:
   assert old[key]==task[key],(key,task['id'])
  native.append(copy.deepcopy(task));z=copy.deepcopy(task);z['id']=twin['reworded_id']
  z['question']=next(x['question'] for x in new if x['id']==z['id']);native.append(z)
  assert schema(z)==schema(task)
  assert {key for key in z if z[key]!=task[key]}=={'id','question'}
 native.sort(key=lambda x:x['id'])
 (OUT/'HELDOUT_NATIVE_TASKS.jsonl').write_text(''.join(encoded(x).decode()+'\n' for x in native))
 pin(OUT/'HELDOUT_NATIVE_TASKS.jsonl')
 write(OUT/'HELDOUT_CAMERA_TWINS.json',dict(seed=SEED,
  assignment="int(sha256('sb_rowA|heldout|20261118|'+question_type+'|'+original_id).hexdigest(),16) % 8",
  twins=twins,per_wording=dict(counts),r0_files=r0_files,r0_camera_items=0,
  native_tasks=pin(OUT/'HELDOUT_NATIVE_TASKS.jsonl'),item_manifest=pin(OUT/'HELDOUT_CAMERA_ITEMS.json')))
 # No rows may masquerade as a successful training build.
 (OUT/'CAMERA_ROWS.jsonl').write_text('')
 cells={f'{t}|t{k:02d}':dict(expected=50,actual=0,status='MISSING') for t in TYPES for k in range(40)}
 for t in TYPES:
  try:assert sum(cells[f'{t}|t{k:02d}']['actual'] for k in range(40))==2000
  except AssertionError:pass
  else:raise AssertionError('Missing source must fail cell assertions')
 write(OUT/'CAMERA_ROWS.MISSING.json',dict(status='MISSING',rows=0,expected_rows=6000,cells=cells,missing=audit['missing']))
 # This is a full held-out sample; it cannot replace the unavailable training READ30.
 sample_rows=[]
 for t in TYPES:
  rows=[x for x in new if x['question_type']==t and '-sbca-' in x['id']]
  picked=[]
  for k in range(8):picked.append(next(x for x in rows if x['id'].endswith(f'h{k:02d}')))
  picked += [x for x in rows if x not in picked][:2];sample_rows+=picked
 (OUT/'READ30.md').write_text('# Thirty held-out reworded items\n\nTraining-row READ30: MISSING (no authenticated source rows). These 30 evaluation items are printed in full.\n\n'+
  '\n\n'.join(f'## {i+1}. {x["id"]}\n\n```json\n'+json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n```' for i,x in enumerate(sample_rows))+'\n')
 checks=dict(overall_status='MISSING_TRAINING_SOURCES',all_required_checks_pass=False,
  training=dict(status='MISSING',rows=0,cells=cells,exact_cell_counts='FAIL: 120 cells short by 50',
   source_use_cap='NOT_RUN',pack_validate_every_source_and_row='NOT_RUN',unique_qids_candidate_ids='NOT_RUN',
   allowed_field_diff='NOT_RUN',independent_ground_truth='NOT_RUN',room_exclusions='NOT_RUN',read30='MISSING'),
  heldout=dict(status='PASS',originals=450,reworded=450,items=900,per_type=dict(Counter(x['question_type'] for x in new)),
   further_wordings_per_type=8,per_wording=dict(counts),seed=SEED,same_keys_and_recursive_types=900,
   unchanged_original_twins=450,only_id_question_changes=450,unchanged_ground_truth=450,unique_ids=900,
   quantity_and_convention_checks=450,native_task_schema_and_field_diff=450,
   train_heldout_wording_overlap=0,overlap_scope='120 reserved training templates instantiated on all 450 eval parameter sets; training rows MISSING',
   r0_camera_items=0,r0_item_files=r0_files,read30='WRITTEN_PENDING_MANUAL_REVIEW'),
  wording=dict(threshold=THRESHOLD,normalized_corpus_size=len(corpus),files=len(files),training_candidates_removed=len(removed),
   heldout_templates_removed=0,heldout_items_removed=0,training_rows_removed='NOT_RUN'),
  source_audit=pin(OUT/'SOURCE_AUDIT.json'))
 write(OUT/'CHECKS.json',checks)
 (ROOT/'STATUS.md').write_text('Held-out build: 900 exact-schema camera items contain 450 unchanged originals and 450 reworded twins. Eight independent held-out wordings per type are assigned by a recorded SHA256 rule. The inventory reserves 40 training wordings per type. Training cells fail with MISSING sources; native-loader validation and the full 30-item review remain.\n')
 print(json.dumps({'heldout':900,'training':'MISSING','removed_templates':len(removed),'corpus':len(corpus)}))
 raise SystemExit(2)  # Required training-cell assertions failed; partial delivery must not return success.
if __name__=='__main__':main()
