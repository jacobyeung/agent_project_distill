from common import *
from student_pilot.r1_handover import compare_configs
from student_pilot.b7_inputs import layout
from student_pilot.r1_persisted import scope
import copy,traceback
paths={}
for folder in ('build24m4k','build24m4j','build24m4i','build24m4h','build24m4e','build24m4d'):
 for p in (L/'work'/folder/'inputs').glob('*'):
  if p.is_file() and len(p.name)==64:paths[p.name]=str(p)
ps={p.name:J.load(p) for p in (W/'inputs/p_configs').glob('*.json')}
for n,v in ps.items():J.write(D/'p_configs'/n,v)
records=[]
for n in NAMES:
 for f in ('c','n'):
  cfg=J.load(kit(n)/('k/'+f+'.json'));proposed=copy.deepcopy(cfg);proposed.update(min_pixels=16384,max_pixels=147456,frame_count=32)
  J.write(D/'configs'/n/(f+'.json'),cfg);J.write(D/'candidate'/n/(f+'.json'),proposed)
  pp=cfg['r1_training']['p_run']['config'];p=J.load(input_file(pp['sha256']))
  for tag,v in (('current',cfg),('candidate',proposed)):
   row=dict(kit=n,config=f,variant=tag)
   try:row['layout']=layout(v)
   except Exception as e:row['layout_refusal']=str(e)
   try:
    with scope(paths):compare_configs(p,v,replicas=paths)
    row['compare']='PASS'
   except Exception as e:row['compare_refusal']=str(e);row['traceback']=traceback.format_exc()
   records.append(row);print({k:v for k,v in row.items() if k!='traceback'},flush=True)
replace(D/'CONFIG_TESTS.json',json.dumps(records,indent=2)+'\n')
print('P summaries',{n:{k:v.get(k) for k in ('min_pixels','max_pixels','frame_count','frame_layout','frame_markers')} for n,v in ps.items()})
