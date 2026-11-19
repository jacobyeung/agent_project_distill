import json,os,sys,collections
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg');T=K/'work/tree_r1';sys.path[:0]=[str(T)]
os.environ.update(R2_FIXTURES=str(K/'fixtures'),R2_PROOFS='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n/tmp')
from student_pilot.r1_mix import allocate
from student_pilot.r1_training import STREAMS
from student_pilot.s1_exclusions import Exclusions
from student_pilot.p3_provenance import digest
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n')
CFG=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/n1fix2/inputs/config.json'))
card=json.load(open(CFG['r1_training']['mix']['path']))
c=json.load(open(W/'CENSUS.json'))
v=c['streams']['vqa']['eligible_by_cell'];rs=c['streams']['routing_slices']
counts={x['type']:0 for x in card['cells']}
counts.update({k:n for k,n in v.items() if k in counts})
counts.update(camera_displacement=14020,camera_movement_direction=12260,camera_rotation=9143,  # P-admitted routing store (171377 admission, type_mix.json); N's 544-scene dev list may lower them
              absolute_distance=rs['absolute_distance']['cells']['absolute_distance'],recovery=sum(rs['recovery']['cells'].values()),units=rs['units']['cells']['units'],
              pose=194987,pointing=20239)  # P's prepared receipt counts
a=allocate(card,counts)
rows=[]
for x in card['cells']:
    k=x['type'];req=int(round(float(x['rows_per_step'])*1000))
    rows.append(dict(cell=k,stream=x['stream'],eligible=counts[k],requested=req,ceiling=4*counts[k],draws=a['draws'][k],refill=a['draws'][k]-min(req,4*counts[k]),expected_repeats=round(a['repeats'][k],3)))
res=dict(schema='n-row-plan-v1',card=CFG['r1_training']['mix'],counts=counts,counts_basis=dict(vqa='own census CENSUS.json (full v7, N filters + native reader)',routing_slices='own census (native intake + N filters), cell by row source',camera='P admitted routing store 47,898 (adm171377/type_mix.json); N filter on it not run (store on Orchard)',pose_pointing='P prepared receipt (adm171377)'),
         allocation=a,table=rows,plan_sha256=digest(dict(counts=counts,draws=a['draws'])))
json.dump(res,open(W/'ROW_PLAN.json','w'),indent=1)
for r in rows: print('%-32s %-8s elig %7d req %6d ceil %7d draws %6d refill %+5d rep %.3f'%(r['cell'],r['stream'],r['eligible'],r['requested'],r['ceiling'],r['draws'],r['refill'],r['expected_repeats']))
print('cuts',a['cuts'])
dev=dict(path=CFG['dev_scene_exclusions']['path'],sha256=CFG['dev_scene_exclusions']['sha256'])
d=json.load(open(dev['path']));nat=d['natives'][0]
ex=Exclusions(dev,None);print('dev self-test sample',nat, ex.excluded(dict(dataset=str(nat).split('/')[0],scene=str(nat).split('/',1)[-1])) if isinstance(nat,str) else nat)
