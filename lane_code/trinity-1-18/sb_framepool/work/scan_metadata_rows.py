import json,re,hashlib,collections
from pathlib import Path
from scan_rows import resolve,sha,C,target,aliases,native
reg=json.load(open('work/metadata_fixed.json'))['files'];summary=json.load(open('work/metadata_summary.json'))
unique={}
for c in C['captures']:
 for s in [c['canonical_scene'],c['scene_token'],c['canonical_scene'].split('/')[1],c['token']]:unique.setdefault(s,set()).add(c['canonical_scene'])
def identify(r):
 c=resolve(r)
 if c:return c
 if not isinstance(r,dict):return None
 for k in ['scene_name','video_id','capture','scene','scene_id']:
  s=r.get(k)
  if isinstance(s,str) and s in unique and len(unique[s])==1:return next(iter(unique[s]))
 return None
def fixture(p):return bool(re.search(r'/(?:tests?|test_[^/]*|tmp[^/]*|evidence|retained_test_products|proof[^/]*)/',p))
results=[];skip=[]
for e in summary['files']:
 h=e['sha256'];m=reg[h];locs=e['locations'];sample=e.get('sample');sample=sample[0] if isinstance(sample,list) and sample else sample
 if e['type']=='dict' and not any(k in e.get('keys',[]) for k in ['items','rows']):continue
 if e['type'] not in ('dict','list','jsonl'):continue
 if e['type']!='dict' and (not isinstance(sample,dict) or not any(k in sample for k in ['dataset','scene','scene_id','scene_name','video_id','canonical','canonical_scene','capture','row_key'])):continue
 if all(fixture(p) for p in locs):skip.append(h);continue
 n=resolved=0;counts=collections.Counter();examples=[];frames=collections.defaultdict(set)
 try:
  if e['type']=='jsonl':iterator=(json.loads(l) for l in open(m['blob']) if l.strip())
  else:
   d=json.load(open(m['blob']));iterator=d if isinstance(d,list) else d.get('items',d.get('rows',[]))
   if not isinstance(iterator,list):continue
  for i,r in enumerate(iterator):
   if not isinstance(r,dict):continue
   n+=1;can=identify(r)
   if can:resolved+=1
   if can in target:
    tok=target[can];counts[tok]+=1
    fi=r.get('frame_indices',[])
    if isinstance(fi,list):frames[tok].update(v for v in fi if isinstance(v,int))
    if len(examples)<10:examples.append(dict(index=i,canonical=can,row={k:v for k,v in r.items() if k in ['id','qid','scene','dataset','scene_name','video_id','canonical','pool','type','question_type','frames','frame_indices','split','bank','benchmark']}))
  if not n:continue
  results.append(dict(sha256=h,locations=locs,rows=n,resolved_rows=resolved,unresolved_rows=n-resolved,hits=sum(counts.values()),counts=dict(counts),examples=examples,frame_indices={k:sorted(v) for k,v in frames.items()},coverage='complete' if n==resolved else 'partial'))
  if counts:print('HIT',h[:12],n,sum(counts.values()),locs[0],flush=True)
 except Exception as ex:results.append(dict(sha256=h,locations=locs,error=str(ex),coverage='MISSING'))
output=dict(command='/usr/bin/python3 work/scan_metadata_rows.py',inputs={p:dict(sha256=sha(p)) for p in ['work/metadata_fixed.json','work/metadata_summary.json','work/captures.json','/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json']},streams=results,excluded_fixture_hashes=skip)
Path('work/metadata_row_results.json').write_text(json.dumps(output,indent=2)+'\n');print('DONE',len(results),len(skip),flush=True)
