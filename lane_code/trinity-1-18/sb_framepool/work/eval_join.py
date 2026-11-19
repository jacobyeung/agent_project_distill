import json,gzip,re,collections
from pathlib import Path
from scan_rows import sha,C,target,resolve,native
reg=json.load(open('work/metadata_fixed.json'))['files'];meta=json.load(open('work/metadata_row_results.json'))['streams']
byhash=collections.defaultdict(set)
for line in gzip.open('work/frame_map.jsonl.gz','rt'):
 r=json.loads(line);byhash[r['sha256']].add(r['d']+'/'+r['s'])
target_tokens=set(target.values());hit_hash={h:v&target_tokens for h,v in byhash.items() if v&target_tokens}
def identify(r):
 c=resolve(r)
 if c:return c
 ds=str(r.get('dataset','')).lower();ds={'scannet++':'scannetpp','arkitscenes':'arkitscenes'}.get(ds,ds)
 s=r.get('scene_name',r.get('scene_id'))
 if isinstance(s,str) and ds in native:return native[ds]+'/'+s
 return None
def framehashes(r):
 if isinstance(r,dict):
  for v in r.values():yield from framehashes(v)
 elif isinstance(r,list):
  for v in r:yield from framehashes(v)
 elif isinstance(r,str):yield from re.findall(r'[0-9a-f]{64}',r)

sets=[]
for s in meta:
 if not any(any(x in p.lower() for x in ['items','cohort','tasks.json','questions']) for p in s['locations']):continue
 e=reg[s['sha256']];n=resolved=0;counts=collections.Counter();framecounts=collections.Counter();witness=[]
 if e['kind']=='jsonl':it=(json.loads(l) for l in open(e['blob']) if l.strip())
 else:
  d=json.load(open(e['blob']));it=d if isinstance(d,list) else d.get('items',d.get('rows',[]))
 for i,r in enumerate(it):
  n+=1;c=identify(r);resolved+=c is not None
  if c in target:counts[target[c]]+=1
  fhs=set(framehashes(r))&set(hit_hash)
  for tok in set(t for h in fhs for t in hit_hash[h]):framecounts[tok]+=1
  if fhs:witness.append(dict(index=i,id=r.get('id',r.get('qid')),frame_sha256s=sorted(fhs)))
 sets.append(dict(sha256=s['sha256'],locations=s['locations'],rows=n,resolved_rows=resolved,counts=dict(counts),frame_reference_counts=dict(framecounts),frame_witnesses=witness,coverage='complete' if n==resolved else 'partial',missing='MISSING scene alias for unresolved items' if n!=resolved else None))
Path('work/evaluation_results.json').write_text(json.dumps(dict(command='/usr/bin/python3 work/eval_join.py',inputs={p:{'sha256':sha(p)} for p in ['work/metadata_fixed.json','work/metadata_row_results.json','work/frame_map.jsonl.gz','work/captures.json','/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json']},sets=sets),indent=2)+'\n')
print('sets',len(sets),'scene_hit_sets',sum(bool(s['counts']) for s in sets),'frame_hit_sets',sum(bool(s['frame_reference_counts']) for s in sets))
