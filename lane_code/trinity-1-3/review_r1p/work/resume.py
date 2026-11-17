import sys
sys.path[:0]=['fix3/work/tree','fix3/work/tree/generator/derivgen_v7']
from student_pilot import type_mix as m, carrier_c1_data as data
import json
cfg=json.load(open('fix3/out/config.json'));r=cfg['recipe']
pol=cfg['type_mix']['streams']['vqa']
counts={'appearance':27791,'box':3813,'camera_absolute_distance':0,'camera_obj_rel_dist_v1':1951,'camera_obj_rel_dist_v2':1983,'camera_obj_rel_dist_v3':1998,'counting':11366,'direction':49901,'facing':34958,'first_seen':7076,'obj_obj_relative_pos_lr':1998,'obj_obj_relative_pos_nf':2000,'obj_obj_relative_pos_ud':1996,'relative_distance':20665,'room':0,'route':8894,'size':9778,'totals':9303}
eff,table=m.allocate(pol,counts,r['steps'],4)
print('direction',table['direction'])
# small synthetic populations near cap to stress repeats
small={n:(max(1,c//100) if c else 0) for n,c in counts.items()}
sp={'cells':{n:{'cents':v['cents']} for n,v in eff.items()},'refill':['direction']}
for n in sp['cells']:
    cap=small[n]*4*100//r['steps']
    sp['cells'][n]['cents']=min(sp['cells'][n]['cents'],cap)
tot=sum(v['cents'] for v in sp['cells'].values());print('small total',tot)
pos=0;groups={}
for n in sp['cells']:
    groups[n]=list(range(pos,pos+small[n]));pos+=small[n]
value={'spec':{'max_repeats':4},'effective':{'vqa':{n:dict(cents=v['cents']) for n,v in sp['cells'].items() if v['cents']}},'populations':{'vqa':{n:groups[n] for n,v in sp['cells'].items() if v['cents']}}}
mix=['vqa']*(tot//100) if tot%100==0 else None
import itertools
base=lambda: ([('vqa',list(range(tot//100)))] for _ in range(r['steps']))
full=list(m.plans(base(),value,17,0))
for k in (1,137,999):
    tail=list(m.plans(base(),value,17,k))
    print('resume',k,tail==full[k:])
from collections import Counter
c=Counter(i for p in full for s,ids in p for i in ids);print('max repeat',max(c.values()))
