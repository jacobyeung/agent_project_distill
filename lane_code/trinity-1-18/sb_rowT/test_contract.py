"""Mutation checks for losses of instance evidence and malformed tally structure."""
import copy,hashlib,json,random
from pathlib import Path
import convert_rows as c
ROOT=Path(__file__).resolve().parent

def run():
 sample=None;compound=None
 for line in (ROOT/'inputs/removed_rows.jsonl').open():
  row=json.loads(line)
  if sample is None and row['provenance'].get('instances'):sample=row
  if row['qid']=='b12ct_c4a08bea818d85cad0ef2466':compound=row
  if sample and compound:break
 cats=c.parse(sample);c.independent_truth(sample,cats);tests=[]
 def refused(name,row):
  try:c.independent_truth(row,c.parse(row))
  except c.Refusal as e:tests.append({'name':name,'pass':True,'reason':str(e)});return
  raise AssertionError(name+' unexpectedly accepted')
 r=copy.deepcopy(sample);r['answer']=str(int(r['answer'])+1);refused('wrong stored total',r)
 r=copy.deepcopy(sample);r['target']=r['target'].replace('frame 1','frame 33',1);refused('frame outside sampled range',r)
 r=copy.deepcopy(sample);r['student_input']['question']='Count the invented category(s) in this room. How many are there?';refused('asked category missing',r)
 r=copy.deepcopy(sample);r['provenance']['instances'][1]['id']=r['provenance']['instances'][0]['id'];refused('duplicate annotation id',r)
 r=copy.deepcopy(sample);r['provenance']['instances'][0]['frame']=32;refused('frame annotation mismatch',r)
 r=copy.deepcopy(sample);r['provenance']['instances'][0]['region']='right';refused('region annotation mismatch',r)
 r=copy.deepcopy(sample);r['provenance'].pop('instances');refused('missing independent evidence',r)
 cc=c.parse(compound);assert [x[0] for x in cc]==['cabinet','dustpan and brush'];c.independent_truth(compound,cc)
 tests.append({'name':'compound category stays intact','pass':True})
 assert len(cats[0][1])==2 and len(set(cats[0][1]))==1
 target=c.render(cats,sample['answer'],'tally');assert 'frame 1: 2 (left: 2) -> 2.' in target
 tests.append({'name':'same frame and region preserve two distinct instances','pass':True})
 def exact(a,b):
  p=list(range(len(b)+1))
  for i,x in enumerate(a,1):
   q=[i]
   for j,y in enumerate(b,1):q.append(min(q[-1]+1,p[j]+1,p[j-1]+(x!=y)))
   p=q
  return p[-1]
 rng=random.Random(11)
 for _ in range(3000):
  a=''.join(rng.choices('abc def123',k=rng.randrange(40)));b=''.join(rng.choices('abc def123',k=rng.randrange(40)));k=rng.randrange(10)
  d=c.edit_distance(a,b,k);truth=exact(a,b);assert (d<=k)==(truth<=k)
  if d<=k:assert d==truth
 tests.append({'name':'bounded Levenshtein matches independent full DP on 3000 cases','pass':True})
 result={'input_sha256':{str(p.relative_to(ROOT)):c.sha(p) for p in [Path(__file__),ROOT/'convert_rows.py',ROOT/'ned_filter.c',ROOT/'ned_filter.so',ROOT/'inputs/removed_rows.jsonl']},'status':'PASS','tests':tests}
 (ROOT/'out/CONTRACT_TESTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('PASS:',len(tests),'checks')
if __name__=='__main__':run()
