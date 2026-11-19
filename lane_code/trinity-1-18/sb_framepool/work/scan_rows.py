import json,sqlite3,hashlib,re,gzip
from pathlib import Path
from collections import Counter
C=json.load(open('work/captures.json'));A='/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json'
a=json.load(open(A));aliases={k:v['canonical'].replace('scannetppv2/','scannetpp/') for k,v in a['aliases'].items()};aliases.update(C['all_plan_aliases'])
target={c['canonical_scene']:c['token'] for c in C['captures']}
native={'d1':'scannet','d2':'scannetpp','d3':'arkitscenes','scannet':'scannet','scannetpp':'scannetpp','scannetppv2':'scannetpp','arkit':'arkitscenes','arkitscenes':'arkitscenes'}
def norm(x):return x.replace('scannetppv2/','scannetpp/')
def resolve(r):
 if not isinstance(r,dict):return None
 for ob in (r,r.get('provenance'),r.get('ground_record'),r.get('gt_authority'),r.get('metadata')):
  if not isinstance(ob,dict):continue
  for key in ('canonical','canonical_scene'):
   x=ob.get(key)
   if isinstance(x,str) and '/' in x:return norm(x)
 d=r.get('dataset',r.get('d'));s=r.get('scene',r.get('s',r.get('scene_id')))
 if isinstance(s,str):
  if str(d)+'/'+s in aliases:return aliases[str(d)+'/'+s]
  if s in aliases:return aliases[s]
  if re.fullmatch(r'(scannet|scannetppv2|scannetpp|arkitscenes)/[^/]+',s):return norm(s)
  if d in native and not re.fullmatch('v[0-9a-f]{12}',s):return native[d]+'/'+s
 for key in ('row_key','scene_key'):
  x=r.get(key)
  if isinstance(x,str) and '/' in x:return norm(x.split('|')[0])
 return None

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def scan(iterator):
 n=resolved=0;counts=Counter();pools=Counter();examples=[];unknown=Counter()
 for idx,r in iterator:
  n+=1;c=resolve(r)
  if c:resolved+=1
  else:unknown[str((r.get('dataset'),r.get('scene')))]+=1
  if c in target:
   counts[target[c]]+=1;pools[str(r.get('pool','MISSING'))]+=1
   if len(examples)<20:examples.append(dict(index=idx,canonical=c,qid=r.get('qid',r.get('id')),pool=r.get('pool')))
 return dict(rows=n,resolved_rows=resolved,unresolved_rows=n-resolved,coverage='complete' if n==resolved else 'partial',counts=dict(counts),hits=sum(counts.values()),hit_pools=dict(pools),examples=examples,unresolved_tokens=dict(unknown))

if __name__=='__main__':
 files=Path('work/files.txt').read_text().splitlines();results=[];seen={}
 # Every surviving real SQLite store in the mirror, plus all row slices in rows lanes and W.
 paths=[p for p in files if '/n30_mirror/' in p and p.endswith('.sqlite')]
 paths+= [p for p in files if p.endswith('.jsonl') and (any('/'+x+'/' in p for x in ('rows_r1','rows_r2','rows_a2')) or '/rows_slices/' in p or '/fixtures/rows/' in p) and any(x in Path(p).name.lower() for x in ('rows','a0_','slice')) and 'audit' not in Path(p).name.lower()]
 for p in sorted(set(paths)):
  digest=sha(p);source=dict(path=p,sha256=digest,bytes=Path(p).stat().st_size)
  if digest in seen:seen[digest]['copies'].append(source);continue
  if p.endswith('.sqlite'):
   with sqlite3.connect('file:'+p+'?mode=ro&immutable=1',uri=True) as db:
    res=scan((i,json.loads(r)) for i,r in db.execute('select i,row from rows order by i'))
  else:
   with open(p) as f:res=scan((i,json.loads(x)) for i,x in enumerate(f) if x.strip())
  res.update(source=source,copies=[],kind='row_store',command='python work/scan_rows.py');seen[digest]=res;results.append(res)
  print(Path(p).name,digest[:8],res['rows'],res['hits'],res['unresolved_rows'],flush=True)
 output=dict(inputs={A:dict(sha256=sha(A)),str(Path('work/captures.json').resolve()):dict(sha256=sha('work/captures.json'))},streams=results)
 Path('work/row_results.json').write_text(json.dumps(output,indent=2)+'\n')
 Path('STATUS.md').write_text('The direct row-store census is complete; work/row_results.json records each store hash, capture count, unresolved tokens, and duplicate copies. The target is 146 distinct captures (148 benchmark-group memberships). Archive metadata, scene-index availability, and evaluation item joins remain under review.\n')
