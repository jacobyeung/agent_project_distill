import gzip,csv,json
from pathlib import Path
from collections import Counter,defaultdict
from parse_direction import parse
counts=Counter();examples=defaultdict(list);families=Counter()
with gzip.open('out/DIRECTION_ROWS.tsv.gz','rt') as f:
 for r in csv.DictReader(f,delimiter='\t'):
  d=parse(r);key=(d['clause'],d['difficulty'],d['forward_relation'],d['answer_side'])
  counts[key]+=1;families[r['family']]+=1
  if 'MISSING' in key and len(examples[key])<4:examples[key].append({'qid':r['qid'],'question':r['question'],'target':r['target'],'parsed':d})
print('FAMILIES',dict(families))
for k,v in sorted(counts.items()):print(k,v)
for k,v in examples.items():
 print('UNKNOWN',k)
 for r in v:print(json.dumps(r))
