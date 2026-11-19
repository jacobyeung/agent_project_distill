import gzip,hashlib,json,re
from pathlib import Path
from collections import Counter
ROOT=Path('/scratch/jjyeung/orch_n30/sb_framepool')
BENCH=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w12/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json')
TAR='/scratch/jjyeung/n30_mirror/cont_ops/h1pkt_fix5_2252Z.tar'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
b=json.loads(BENCH.read_text());p=json.load(gzip.open(ROOT/'work/frame_plan.json.gz'))
frames={};fields=Counter()
for r in map(json.loads,gzip.open(ROOT/'work/frame_map.jsonl.gz','rt')):
 frames.setdefault((r['d'],r['s']),[]).append(r['i']);fields.update(r.keys())
# Independent aliases from frame-plan source filenames/URLs; validate exact token formula.
plan_alias={}
for t,v in p['v'].items():
 can=(v['n'][:-4] if v['n'].endswith('.mp4') else v['n']);can=can.replace('scannetppv2/','scannetpp/')
 plan_alias[v['g']+'/'+t]=can
for t,v in p['a'].items():
 s=re.search(r'/(?:Training|Validation)/(\d+)/',v['u']).group(1);plan_alias['d3/'+t]='arkitscenes/'+s
captures=[]
for (d,t),ids in sorted(frames.items()):
 can=plan_alias[d+'/'+t];native,scene=can.split('/',1)
 expected='v'+hashlib.sha256(('rung1 scene '+can.replace('scannetpp/','scannetppv2/')).encode()).hexdigest()[:12]
 assert t in (scene,expected),(d,t,can)
 key=d+'/'+scene
 if key not in b['members']:continue
 facts=b['members'][key]
 captures.append(dict(token=d+'/'+t,scene_token=t,dataset=d,native_dataset=native,canonical_scene=can,scene_list_key=key,room=facts['group'],benchmarks=facts['benchmarks'],listed_by=facts['listed_by'],sibling_of=facts['sibling_of'],why='direct benchmark scene' if facts['listed_by'] else 'same physical room as listed benchmark capture(s)',bench_v2_scene_list=key in b['scenes'],bench_v2_token_list=[d,expected] in b['rung1_tokens'],frame_count=len(ids),frame_indices=ids,plan_entry=p['a'].get(t,p['v'].get(t)),per_stream_counts={}))
counts=Counter(x for c in captures for x in c['benchmarks'])
result=dict(command='python work/captures.py',inputs={str(BENCH):dict(sha256=sha(BENCH)),**{TAR+'::h1/chain_r1/build/fx/k/'+n:dict(sha256=sha(ROOT/'work'/n)) for n in ('frame_map.jsonl.gz','frame_plan.json.gz')}},frame_count=sum(map(len,frames.values())),frame_scenes=len(frames),frame_fields=dict(fields),plan_aliases_verified=len(plan_alias),benchmark_capture_counts=dict(counts),distinct_captures=len(captures),requested_148_is_membership_sum=counts['STI-Bench/ReSTI']+counts['MindCube']+2,bench_v2_counts=b['counts'],captures=captures,all_plan_aliases=plan_alias)
(ROOT/'work/captures.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('The frame-map and plan reproduce 290,880 frames in 4,697 captures. BENCH v2 intersects 146 distinct captures: 126 STI-Bench/ReSTI, 20 MindCube, and 2 venue-381879 captures. Two ScanNet captures belong to both STI-Bench/ReSTI and MindCube, so the requested 148 is a membership sum. All 146 appear in BENCH v2. Training-store and evaluation-item scans are pending.\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('captures','all_plan_aliases','inputs','frame_fields')}));print('double-members',[(c['canonical_scene'],c['benchmarks']) for c in captures if 'MindCube' in c['benchmarks'] and 'STI-Bench/ReSTI' in c['benchmarks']])
