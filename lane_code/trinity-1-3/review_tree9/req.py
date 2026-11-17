import json,sys,itertools,collections
from copy import deepcopy
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_tree9')
from mutate import intake_check,norm
from student_pilot.routing_requirements import blockers
from student_pilot.r2_mix import table
from student_pilot import b7_inputs
cen=json.load(open('/scratch/jjyeung/orch_n30/review_tree9/proofs/CENSUS.json'))
adm=collections.Counter()
lines=open('/scratch/jjyeung/orch_n30/review_tree9/lane/work/rows_slices/slices_final/a0_units.jsonl').readlines()
for i in range(0,len(lines),200):
    rows=[norm(json.loads(l)) for l in lines[i:i+200]]
    res=intake_check(rows,'a0_units')
    for q,v in res.items():
        if v=='ADMIT':adm[cen['byqid'][q]]+=1
print('units admitted after exclusions',dict(adm))
good=dict(recovery=1458,units=dict(cm=606,ft=666,in_=643));good['units']['in']=good['units'].pop('in_')
m=table(both_path={'minority_count':2000})
def zero(kind):
    t=deepcopy(m)
    for c in t['cells']:
        if c['type']==kind:c['numerator']=0
    return t
cases={'good':(m,good),'mix_recovery_zero':(zero('recovery'),good),'mix_units_zero':(zero('units'),good),
 'counts_recovery_0':(m,{**good,'recovery':0}),'counts_recovery_bool':(m,{**good,'recovery':True}),'counts_recovery_float':(m,{**good,'recovery':1458.0}),
 'counts_recovery_missing':(m,{'units':good['units']}),'units_in_0':(m,{**good,'units':{'cm':606,'ft':666,'in':0}}),
 'units_in_missing':(m,{**good,'units':{'cm':606,'ft':666}}),'units_m_only':(m,{**good,'units':{'m':10}}),'counts_none':(m,None),
 'recovery_negative':(m,{**good,'recovery':-5})}
for k,(mix,c) in cases.items():print(k,blockers(mix,c))
