import json,sys
T='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg/work/tree_r1';sys.path.insert(0,T)
from student_pilot import r1_handover as H
P=json.load(open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/config.json'))
N=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/n1fix2/inputs/config.json'))
out={}
try: H.compare_configs(P,N); out['compare_configs']='ADMIT'
except Exception as e: out['compare_configs']='REFUSED '+str(e)
try: out['optimizer_P']=H.optimizer_contract(P); out['optimizer_N']=H.optimizer_contract(N)
except Exception as e: out['optimizer']='ERR '+str(e)[:200]
diff=[]
for k in sorted(set(P)|set(N)):
    if k in H.HANDOVER_VARIABLE_KEYS: continue
    a,b=P.get(k,'<absent>'),N.get(k,'<absent>')
    if k=='recipe': a={x:y for x,y in a.items() if x!='mix'}; b={x:y for x,y in b.items() if x!='mix'}
    if a!=b: diff.append(dict(key=k,P=json.dumps(a)[:160],N=json.dumps(b)[:160]))
out['all_differences_outside_allow_list']=diff
json.dump(out,open('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/cont_real/CFG_COMPARE.json','w'),indent=1,default=str)
print(out['compare_configs']); print(len(diff),[d['key'] for d in diff])
for k in ('optimizer_P','optimizer_N'): print(k,json.dumps(out.get(k),default=str)[:400])
