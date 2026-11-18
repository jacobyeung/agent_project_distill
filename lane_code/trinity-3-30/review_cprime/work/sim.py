# review_cprime: replay the shipped sampler (type_mix.allocate + plans) on my own census populations
import json,collections,sys,sqlite3
sys.path.insert(0,'/scratch/jjyeung/orch_n30/r1_ops6/cp/work/tree')
from student_pilot.type_mix import family,allocate,plans
exec(open('census.py').read().split("c=sqlite3.connect")[0].split("from student_pilot.type_mix import family")[1])
cls=json.load(open('../out/MY_COUNTING_CLASSES.json'))
cfg=json.load(open('/scratch/jjyeung/orch_n30/review_cprime/arc_cp/config.json'))
spec=cfg['type_mix'];pol=spec['streams']['vqa'];steps=cfg['recipe']['steps']
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?immutable=1&mode=ro',uri=True)
buckets=collections.defaultdict(list);qid={}
for i,r,t in c.execute("select i,row,target from rows"):
    d=json.loads(r);k=row_keys(d)
    if k&base or k&N or k&B or d['qid'] in xq or f"{d.get('dataset')}/{d.get('scene')}" in sc or d.get('scene') in sc: continue
    buckets[family(d,'vqa')].append(i);qid[i]=d['qid']
eff,table=allocate(pol,{n:len(v) for n,v in buckets.items()},steps,4)
print('effective==config cells (nonzero):',eff=={n:v for n,v in pol['cells'].items() if v['cents']})
value=dict(spec=spec,effective={'vqa':eff},populations={'vqa':{n:buckets[n] for n in eff}})
slots=sum(v['cents'] for v in eff.values())//100
base_plan=[[('vqa',[0]*slots)] for _ in range(steps)]
fam={i:n for n,v in buckets.items() for i in v}
win=collections.Counter();tot=collections.Counter();per=collections.Counter();form=collections.Counter()
for s,plan in enumerate(plans(base_plan,value,cfg['recipe']['seed'])):
    for st,idx in plan:
        for i in idx:
            per[i]+=1;tot[fam[i]]+=1
            if 200<=s<600: win[fam[i]]+=1
            if fam[i]=='counting': form[cls[qid[i]]]+=1
res=dict(steps=steps,slots_per_step=slots,seed=cfg['recipe']['seed'],table=table,draws_steps_201_600=win,draws_1000=tot,max_draws_per_row=max(per.values()),
         max_by_family={n:max(per[i] for i in v) if any(per[i] for i in v) else 0 for n,v in buckets.items()},counting_draw_forms=form)
json.dump(res,open('../out/SIM_MINE.json','w'),indent=1,default=dict)
print(json.dumps({k:res[k] for k in ('steps','slots_per_step','draws_steps_201_600','max_draws_per_row','max_by_family','counting_draw_forms')},default=dict))
