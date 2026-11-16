"""Fail-closed capture eligibility using all named exclusion authorities."""
import argparse, functools, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
INPUTS=['revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json','own_probe/out/EVAL_ROOMS.json',
        'ofs_e1/out/ROOM_SPLIT.json','devs1_masks/out/MANIFEST.json',
        'dose_pool/out/POOL_S1/EXCLUDE_DEV_S1.tsv','dose_pool/out/POOL_S1/EXCLUDE_EVAL_ROOMS.tsv',
        'dose_pool/out/POOL_S1/FRAMES_GATE.json']
ALIASES={'d1':'scannet','d2':'scannetpp','d3':'arkitscenes','scannetppv2':'scannetpp',
         'scannet':'scannet','scannetpp':'scannetpp','arkitscenes':'arkitscenes'}
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def canonical(ds,cap):
 if ds not in ALIASES or '/' in cap or not cap:return None
 return ALIASES[ds]+'/'+cap
def normalize(s):
 ds,cap=s.split('/',1);return canonical(ds,cap)
@functools.lru_cache(None)
def authorities():
 b,e,s,d=[json.loads((ROOT/p).read_text()) for p in INPUTS[:4]]
 aliases={normalize(k):v for k,v in e['alias_rooms'].items() if normalize(k)}
 aliases.update({'arkitscenes/'+k:v for k,v in e['arkit_rooms'].items()})
 denied={}
 def add(room,reason):denied.setdefault(room,set()).add(reason)
 for v in b['members'].values():
  for bench in v['benchmarks']:add(v['group'],bench)
 for tag in ('evaluation_rooms','qualification_rooms'):
  for r in e[tag]:add(r,tag)
 for k in ('tuning_scenes','legacy_read_scenes','room_disjoint_scenes'):
  for x in s[k]:add('scannet/'+re.sub(r'_\d\d$','',x.split('/')[-1]),'dev84')
 for c in d['captures']:
  k=normalize(c['scene']);r=aliases.get(k)
  if r is None:raise ValueError('Unknown dev-S1 physical room: '+k)
  add(r,'dev_s1')
 # Pool TSV files are supplementary exclusions, never an eligibility grant.
 known_rooms=set(aliases.values())
 for p in INPUTS[4:6]:
  for line in (ROOT/p).read_text().splitlines():
   for token in line.split('\t'):
    if '/' not in token:continue
    k=normalize(token)
    if k in aliases:add(aliases[k],Path(p).stem)
    if token in known_rooms:add(token,Path(p).stem)
 return aliases,denied,b
def verdict(dataset,capture):
 key=canonical(dataset,capture);aliases,denied,_=authorities()
 room=aliases.get(key)
 reasons=sorted(denied.get(room,())) if room else ['unknown_alias']
 return dict(capture=key or dataset+'/'+capture,room=room,eligible=bool(room) and not reasons,reasons=reasons)
def eligible(dataset,capture):return verdict(dataset,capture)['eligible']
def receipt(captures):
 rows=[verdict(*s.split('/',1)) for s in captures]
 return dict(inputs={str(ROOT/p):sha(ROOT/p) for p in INPUTS},captures=rows,
             selected=len(rows),refusals=sum(not r['eligible'] for r in rows),
             benchmarks=sorted(authorities()[2]['by_benchmark']))
def main():
 p=argparse.ArgumentParser();p.add_argument('captures');p.add_argument('--out',required=True);a=p.parse_args()
 x=json.loads(Path(a.captures).read_text());x=x.get('pilot',x) if isinstance(x,dict) else x
 r=receipt([v['canonical'] if isinstance(v,dict) else v for v in x]);Path(a.out).write_text(json.dumps(r,indent=2)+'\n')
 return int(r['refusals']>0)
if __name__=='__main__':raise SystemExit(main())
