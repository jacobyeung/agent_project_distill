"""Filter authored questions by normalized character Levenshtein distance."""
import gzip,json,re,unicodedata
from pathlib import Path
from census import W,BASE,TREE,reg,INPUTS,dump
QUESTIONS=[
 'Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.',
 'How many square meters of floor space do the areas visited in this video cover altogether?'
]
THRESHOLD=.25
def norm(s):return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKC',str(s)).casefold()))
def levenshtein(a,b):
 if len(a)>len(b):a,b=b,a
 prev=list(range(len(a)+1))
 for j,y in enumerate(b,1):
  cur=[j]
  for i,x in enumerate(a,1):cur.append(min(cur[-1]+1,prev[i]+1,prev[i-1]+(x!=y)))
  prev=cur
 return prev[-1]
def extract(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in {'question','source_question','question_text','prompt'} and isinstance(v,str):yield v
   elif isinstance(v,(dict,list)):yield from extract(v)
 elif isinstance(x,list):
  for v in x:yield from extract(v)
def main():
 reg(__file__);paths=set()
 for root in [BASE/'fixtures',TREE/'configs',TREE/'evalpath']:
  for p in root.rglob('*'):
   if p.is_file() and (p.suffix in {'.json','.jsonl'} or p.name.endswith('.jsonl.gz')):paths.add(p)
 root=Path('/scratch/jjyeung/n30_mirror')
 for p in root.rglob('*'):
  if p.is_file() and (p.suffix in {'.json','.jsonl'} or p.name.endswith('.jsonl.gz')) and any(s in str(p).lower() for s in ['dev','bench','items']):paths.add(p)
 corpus={};files=[];errors=[]
 for p in sorted(paths):
  reg(p);n=0
  try:
   opener=gzip.open if p.name.endswith('.gz') else open
   with opener(p,'rt') as f:
    values=map(json.loads,f) if '.jsonl' in p.name else [json.load(f)]
    for value in values:
     for q in extract(value):
      n+=1;corpus.setdefault(norm(q),[]).append(str(p))
  except Exception as e:errors.append(dict(path=str(p),error=str(e)))
  if n:files.append(dict(path=str(p),questions=n))
 # Include the existing room family conservatively; these are not a substitute for dev banks.
 p=reg('/scratch/jjyeung/n30_mirror/rows_r1/out/room_v4/rows.jsonl')
 for l in p.open():
  q=json.loads(l)['student_input']['question'];corpus.setdefault(norm(q),[]).append(str(p))
 result=[]
 for q in QUESTIONS:
  a=norm(q);best=(1.0,None)
  for b in corpus:
   lower=abs(len(a)-len(b))/max(len(a),len(b),1)
   if lower>=best[0]:continue
   d=levenshtein(a,b)/max(len(a),len(b),1)
   if d<best[0]:best=(d,b)
  result.append(dict(question=q,min_normalized_distance=best[0],nearest_normalized_wording=best[1],accepted=best[0]>THRESHOLD))
 dump(W/'out/WORDING.json',dict(threshold=THRESHOLD,normalization='NFKC, casefold, Unicode word tokens joined with single spaces; character Levenshtein/max length',unique_corpus_wordings=len(corpus),scanned_files=len(paths),files_with_questions=files,parse_errors=errors,questions=result,removed=sum(not x['accepted'] for x in result),missing=['/scratch/jjyeung/orch_cd/dose_pool/out/DEV_S1/QIDS.jsonl.gz'],scope='All JSON/JSONL under w19 fixtures/configs/evalpath plus mirror files whose paths contain dev, bench, or items; existing room questions added conservatively. No claim of complete external benchmark banks.'))
 print('wording',len(corpus),result,'parse errors',errors)
 assert all(x['accepted'] for x in result)
if __name__=='__main__':main()
