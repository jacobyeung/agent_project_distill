import json,collections,sys
sys.path.insert(0,'/scratch/jjyeung/orch_n30/tree_rebuild_w/work/base/tree_b01ce449')
D='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/slices_final/'
from generator.derivgen_v7.derivgen import box_v313 as boxes
def agrees(a,g): return str(a)==boxes.number(float(g),2) and abs(float(a)-float(g))<=.05*abs(float(g))
u=[json.loads(l) for l in open(D+'a0_units.jsonl')]
c=collections.Counter();cu=collections.Counter()
for r in u:
    g=r['ground_record'];ok=agrees(g['answer'],g['gt_answer']);c[ok]+=1;cu[(g.get('unit'),ok)]+=1
    c['type_'+g['type']]+=1; c['flags_ok']+= (not g.get('not_seen') and g.get('gt_agrees') is True and g.get('training_admitted') is False)
print(len(u),c,cu)
