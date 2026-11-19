import json,gzip,hashlib,multiprocessing as mp
from pathlib import Path
BASE=Path('/scratch/jjyeung/orch_n30/sb_evidence/aws_sources')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def mint(d,s):return 'v'+hashlib.sha256(('rung1 scene '+d+'/'+s).encode()).hexdigest()[:12]
def arkit(args):
 lo,hi,targets=args;h=hashlib.sha256(b'rung1 scene arkitscenes/');out=[]
 for i in range(lo,hi):
  x=h.copy();x.update(str(i).encode());t='v'+x.hexdigest()[:12]
  if t in targets:out.append((t,'arkitscenes/'+str(i)))
 return out
if __name__=='__main__':
 inputs={};tokens=set()
 for p in sorted(BASE.glob('*scenes.jsonl.gz')):
  inputs[str(p)]={'sha256':sha(p)}
  with gzip.open(str(p),'rt') as f:
   for line in f:tokens.add(json.loads(line)['scene'])
 p=Path('work/captures.json');inputs[str(p)]={'sha256':sha(p)};caps=json.load(open(p))['captures'];tokens|={c['scene_token'] for c in caps}
 matches={}
 for a in range(10000):
  for b in range(100):
   s='scene%04d_%02d'%(a,b);t=mint('scannet',s)
   if t in tokens:matches.setdefault(t,[]).append('scannet/'+s)
 with mp.Pool(16) as pool:
  for hits in pool.imap_unordered(arkit,[(i*1562500,(i+1)*1562500,tokens) for i in range(64)]):
   for t,c in hits:matches.setdefault(t,[]).append(c)
 p=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pk/benchmark_scene_exclusions.json');inputs[str(p)]={'sha256':sha(p)}
 bench=json.load(open(p));spp={x.split('/')[1] for x in bench['scenes'] if x.startswith('d2/')}
 p=Path('work/captures.json');plan=json.load(open(p))['all_plan_aliases']
 # Plan maps native scene keys to frame tokens; retain only known ScanNet++ candidates.
 for k,v in plan.items():
  for x in [k,v] if isinstance(v,str) else [k]:
   if x.startswith('d2/') and not x.split('/')[1].startswith('v'):spp.add(x.split('/')[1])
 for s in spp:
  t=mint('scannetppv2',s)
  if t in tokens:matches.setdefault(t,[]).append('scannetpp/'+s)
 out={'command':'/usr/bin/python3 work/fpjoin_invert.py','inputs':inputs,'ranges':{'scannet':'scene0000_00..scene9999_99 (1,000,000)','arkitscenes':'0..99,999,999 (100,000,000)','scannetpp':'BENCH v2 and frame-plan known natives; not exhaustive 2^40'},'tokens':len(tokens),'preimages':matches,'unresolved_tokens':sorted(tokens-set(matches)),'collisions':{t:v for t,v in matches.items() if len(v)>1}}
 Path('work/fpjoin_preimages.json').write_text(json.dumps(out,indent=1)+'\n')
 print('inverted',len(matches),'of',len(tokens),'collisions',len(out['collisions']))
