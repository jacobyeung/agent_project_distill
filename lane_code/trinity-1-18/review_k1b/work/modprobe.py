import sys,json
KC='/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a'
sys.path[:0]=[KC+'/work',KC+'/native_kit']
import k1_pipeline as K, bindings as B, k1_phases, k1_cli, boundaries, pipeline, sam3_tower
import torch
sys.path.insert(0,'/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src')
import sam3.model_builder, sam3.model.sam3_image_processor
from student_pilot import tower_read, c1r_ref, g3t_online
pins=json.load(open('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/samfix/DEPENDENCIES.json'))
files=sorted({getattr(m,'__file__',None) for m in list(sys.modules.values())} - {None})
mine=[f for f in files if f.startswith('/scratch/jjyeung/') and '/envs/' not in f]
un=[f for f in mine if f not in pins]
import collections
print('scratch modules loaded',len(mine),'unpinned',len(un))
print(collections.Counter(f.split('/')[4]+'/'+f.split('/')[5] if len(f.split('/'))>5 else f for f in un))
for f in un:
    if '/kit_k1a/' in f or 'out2' in f or 'leg_s1_tree' in f: print(' ',f)
