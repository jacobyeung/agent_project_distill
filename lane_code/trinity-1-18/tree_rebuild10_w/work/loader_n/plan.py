import json,os,sys,collections
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg');T=K/'work/tree_r1';sys.path[:0]=[str(T)]
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n');os.environ.update(R2_FIXTURES=str(K/'fixtures'),R2_PROOFS=str(W/'tmp'))
from student_pilot.r1_mix import plans,validate_binding
from student_pilot.p3_provenance import file_pin,write,digest
CFG=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/n1fix2/inputs/config.json'))
cardpin=CFG['r1_training']['mix'];card=json.load(open(cardpin['path']))
plan=json.load(open(W/'ROW_PLAN.json'));counts=plan['counts']
pw=write(W/'b/population.json',dict(schema='r1-population-v1',complete=True,after_all_filters=True,card_sha256=cardpin['sha256'],counts=counts,
      evidence=[file_pin(W/'CENSUS.json'),file_pin(W/'ROW_PLAN.json')],note='camera/pose/pointing counts are P-admitted values; host intake must replace them'))
cells={};off=collections.Counter()
for c in card['cells']:
    s=c['stream'];cells[c['type']]=list(range(off[s],off[s]+counts[c['type']]));off[s]+=counts[c['type']]
pop=file_pin(W/'b/population.json');iw=write(W/'b/indices.json',dict(population_sha256=pop['sha256'],cells=cells,offsets='synthetic contiguous per stream in card order; host must bind real offsets'))
idx=file_pin(W/'b/indices.json');binding=dict(schema='r1-sampling-v1',card=cardpin,population=pop,indices=idx)
stream_counts=dict(off)
draws=collections.Counter();rep=collections.Counter();owner={(c['stream'],i):c['type'] for c in card['cells'] for i in cells[c['type']]}
perstep=collections.Counter();n=0
for step,p in enumerate(plans(binding,stream_counts,1000)):
    sizes=collections.Counter()
    for s,o in p:
        sizes[s]+=len(o)
        for i in o:draws[owner[(s,i)]]+=1;rep[(s,i)]+=1
    if step==0:first=sizes
    n+=1
res=dict(binding=binding,stream_counts=stream_counts,steps=n,per_step=dict(first),draws=dict(draws),largest_repeat=max(rep.values()),
         draws_equal_allocation=dict(draws)=={k:v for k,v in plan['allocation']['draws'].items() if v},plan_sha256=digest(binding))
json.dump(res,open(W/'PLAN_RUN.json','w'),indent=1);print(json.dumps({k:v for k,v in res.items() if k!='binding'}))
