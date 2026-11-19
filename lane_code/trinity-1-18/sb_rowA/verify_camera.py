"""Independently check frozen evaluation payloads, lineage and assignment."""
import copy,hashlib,json,re,sys,importlib.util,random
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
READ=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src')
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def dh(x):return hashlib.sha256(enc(x)).hexdigest()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def types_equal(a,b):
 assert type(a) is type(b)
 if isinstance(a,dict):
  assert set(a)==set(b)
  for k in a:types_equal(a[k],b[k])
 elif isinstance(a,list):
  assert len(a)==len(b)
  for x,y in zip(a,b):types_equal(x,y)
def main():
 from build_camera import levenshtein
 def independent_distance(a,b):
  row=list(range(len(b)+1))
  for i,x in enumerate(a,1):
   new=[i]
   for j,y in enumerate(b,1):new.append(min(new[-1]+1,row[j]+1,row[j-1]+(x!=y)))
   row=new
  return row[-1]
 rng=random.Random(17)
 for _ in range(100):
  a=''.join(rng.choices('abc #',k=rng.randrange(60)));b=''.join(rng.choices('abc #',k=rng.randrange(60)))
  assert levenshtein(a,b)==independent_distance(a,b)
 m=json.load(open(OUT/'HELDOUT_CAMERA_ITEMS.json'));t=json.load(open(OUT/'HELDOUT_CAMERA_TWINS.json'))
 w=json.load(open(OUT/'WORDINGS.json'));c=json.load(open(OUT/'CHECKS.json'))
 src=json.load(open(READ/'items/devs1_routed.json'));original={x['id']:x for x in src['items']}
 items={x['id']:x for x in m['items']}
 assert len(items)==m['count']==900 and dh(m['items'])==m['item_set_sha256']
 assert list(items)==sorted(items)
 assert Counter(x['question_type'] for x in items.values())==Counter(m['per_type'])
 assert len(t['twins'])==450
 seen=set();counts=Counter()
 for pair in t['twins']:
  o=original[pair['original_id']];a=items[pair['original_id']];b=items[pair['reworded_id']]
  assert o==a and dh(o)==pair['original_item_sha256'] and dh(b)==pair['reworded_item_sha256']
  types_equal(o,b)
  assert {k for k in o if o[k]!=b[k]}=={'id','question'}
  assert o['answer']==b['answer'] and o['ground_truth']==b['ground_truth']
  typ=o['question_type'];seed=t['seed']
  h=hashlib.sha256(f'sb_rowA|heldout|{seed}|{typ}|{o["id"]}'.encode()).hexdigest()
  k=int(h,16)%8;assert pair['wording_id']==f'h{k:02d}'
  i,j=o['display_frame_pair'];n=len(o['source_frame_indices']);assert 1<=i<j<=n==32
  vals={'i':i,'j':j,'n':n,'unit':'meters','options':'; '.join(o['options'])}
  assert b['question']==w['heldout'][typ][k].format(**vals)
  assert b['question'] not in [s.format(**vals) for s in w['training'][typ]]
  assert all(str(v) in b['question'] for v in (i,j,n))
  if typ=='camera_displacement':assert 'meters' in b['question']
  if typ=='camera_rotation':assert all(s in b['question'] for s in ['(-180, 180]','degrees','positive','left'])
  if typ=='camera_movement_direction':assert all(s in b['question'] for s in o['options'])
  counts[typ+'|'+pair['wording_id']]+=1;seen.update([a['id'],b['id']])
 assert seen==set(items) and dict(counts)==t['per_wording'] and len(counts)==24
 tasks=[json.loads(s) for s in (OUT/'HELDOUT_NATIVE_TASKS.jsonl').read_text().splitlines()]
 assert len(tasks)==900 and len({x['id'] for x in tasks})==900
 for task in tasks:
  item=items[task['id']]
  for k in ('question','question_type','options','dataset','scene','native','source_frame_indices','answer'):
   assert task[k]==item[k]
 reserve=READ/m['r0_check']['pin']['path']
 assert sha(reserve)==m['r0_check']['pin']['sha256']
 rooms=set(reserve.read_text().splitlines());assert not any(x['room_key'] in rooms for x in items.values())
 assert m['r0_check']['found']==0 and m['r0_check']['checked']==900
 freeze=json.load(open(OUT/'HELDOUT_FREEZE.json'))
 for file,h in freeze['input_sha256'].items():assert sha(file)==h
 assert c['training']['rows']==6000
 patch=json.load(open(OUT/'SCORER_PATCH/CHECKS.json'))
 assert patch['status']=='PASS' and patch['native_manifest_items']==patch['native_mapped_unique_keys']==900
 result=dict(status='PASS',scope='Independent CPU evaluation verification; training checks are in INDEPENDENT_TRAINING_CHECK.json',
  items=900,twins=450,native_tasks=900,all_24_wording_cells_nonempty=True,levenshtein_independent_dp_pairs=100,
  checks=['exact item keys and recursive value types','original twins unchanged','id/question only edits',
          'ground truth preserved','quantity and convention completeness','seed assignment','native task binding',
          'manifest hash and counts','R0 exclusion','held-out bytes frozen'],
  native_loader={'status':'PASS','items':900,'unique_reader_keys':900,'evidence':'SCORER_PATCH/CHECKS.json'},
  input_sha256={str(ROOT/'verify_camera.py'):sha(ROOT/'verify_camera.py'),
   **{str(OUT/f):sha(OUT/f) for f in ['HELDOUT_CAMERA_ITEMS.json','HELDOUT_CAMERA_TWINS.json','HELDOUT_NATIVE_TASKS.jsonl','WORDINGS.json','CHECKS.json']}})
 (OUT/'INDEPENDENT_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['status','items','twins','native_tasks']}))
if __name__=='__main__':main()
