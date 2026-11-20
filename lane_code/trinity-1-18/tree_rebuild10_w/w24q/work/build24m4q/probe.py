import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
n=z.load(kit('n')/'k/n.json'); print('extent',n.get('extent_receipt'))
pin=n['extent_receipt'];p=input_file(pin['sha256']);v=z.load(p)
print('local',p,'size',p.stat().st_size,'top', {k:v for k,v in v.items() if k!='rows'})
print('rows',len(v['rows']),'examples',list(v['rows'].items())[:2])
for key in ('streams','r1_training'):
 print(key,n[key] if key=='streams' else {k:v for k,v in n[key].items() if k in ('wording_exclusion','camera_wording_exclusion','p_run')})
from student_pilot.mdg_parent import model_pin
from student_pilot.r1_persisted import scope
paths={p.name:str(p) for b in ('work/build24m4p/inputs','work/build24m4n/inputs','work/build24m4j/inputs','work/build24m4h/inputs') for p in (L/b).iterdir() if p.is_file() and len(p.name)==64}
for label,cfg in [('n',n),('p',z.load(input_file(n['r1_training']['p_run']['config']['sha256'])))]:
 with scope(paths):
  try:mp=model_pin(cfg)
  except Exception as e:print('model pin error',type(e).__name__,str(e));continue
  m=z.load(input_file(mp['sha256']));print(label,'model',mp,m)
write(D/'PIN_PROBE.json',dict(extent_pin=pin,extent_local=str(p),extent_metadata={k:v for k,v in v.items() if k!='rows'},extent_count=len(v['rows']),config=n))
