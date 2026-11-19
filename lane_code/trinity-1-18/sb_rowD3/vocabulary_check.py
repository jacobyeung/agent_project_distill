"""Independently count names from source opening lines before/after room exclusions."""
import collections as C, hashlib,json,re,sqlite3,unicodedata
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE/'out'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())
def main():
 c=json.loads((OUT/'COUNTS.json').read_text());a=json.loads((OUT/'ROW_AUDIT.json').read_text())
 eligible={r['qid'] for r in a['records'] if not r['excluded_by']}
 db=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
 names=C.defaultdict(set);missing=[];counts=C.Counter()
 with sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True) as con:
  for raw, in con.execute('SELECT row FROM rows'):
   r=json.loads(raw)
   if not r.get('question_type','').startswith('object_rel_direction_'):continue
   first=r['target'].splitlines()[1]
   o='Step 1' if first.startswith('Step 1:') else 'Seen'
   if o=='Seen': ns=[part.rsplit(' in frame ',1)[0] for part in first[6:-1].split('; ')]
   else:
    body=first.split(' the ',1)[1][:-1]
    if ', then the ' in body:
     xy,z=body.split(', then the ');x,y=xy.split(' and the ',1);ns=[x,y,z]
    else:
     x,yz=body.split(', the ',1);y,z=yz.split(' and the ',1);ns=[x,y,z]
   assert len(ns)==3
   names['all',o].update(map(norm,ns));counts['all',o]+=1
   if r['qid'] in eligible:names['eligible',o].update(map(norm,ns));counts['eligible',o]+=1
 expected=C.defaultdict(set)
 for r in c['vocabulary']:expected[r['opening']].update(r['names'])
 assert all(names['all',o]==expected[o] for o in expected)
 pins={str(p):sha(p) for p in [Path(__file__),OUT/'COUNTS.json',OUT/'ROW_AUDIT.json',db]}
 assert pins[str(db)]==c['input_sha256'][str(db)]['sha256']
 result=dict(status='PASS_TEXT_VOCABULARY_ONLY',command='PYTHONDONTWRITEBYTECODE=1 python vocabulary_check.py',input_sha256=pins,
   cells=[dict(population=pop,opening=o,rows=counts[pop,o],distinct_names=len(ns),names=sorted(ns)) for (pop,o),ns in sorted(names.items())],
   excluded_only_step_names=sorted(names['all','Step 1']-names['eligible','Step 1']),
   note='Counts use literal normalized opening names. They do not establish GT identity or generated vocabulary coverage.')
 (OUT/'VOCABULARY_CHECK.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps([dict(population=r['population'],opening=r['opening'],rows=r['rows'],distinct_names=r['distinct_names']) for r in result['cells']],indent=2))
if __name__=='__main__':main()
