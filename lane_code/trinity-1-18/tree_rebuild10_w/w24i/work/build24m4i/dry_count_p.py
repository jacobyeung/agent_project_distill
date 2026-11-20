from pathlib import Path
import sys,json,hashlib
from collections import Counter
L=Path(__file__).resolve().parents[2];D=Path(__file__).parent
sys.path.insert(0,str(L/'work/build24m4h/p_tree'))
from student_pilot import type_mix,carrier_c1_data
from student_pilot.p3_provenance import file_pin
cfg=json.loads((D/'P_CONFIG.json').read_text());receipt=json.loads((D/'P_preparation.json').read_text())
path=D/'P_type_mix.json';assert file_pin(path)['sha256']==receipt['type_mix_population']['sha256']
receipt['type_mix_population']=file_pin(path)
value=type_mix.bound(receipt,cfg)
counts={s:v['count'] for s,v in receipt['streams'].items()}
owner={(s,i):k for s,groups in value['populations'].items() for k,ids in groups.items() for i in ids}
count=Counter();steps=[]
for plan in carrier_c1_data.mixed_indices(counts,200,seed=cfg['recipe']['seed'],mix=cfg['recipe']['mix'],world=cfg['recipe']['world_size'],training_mode=cfg['training_mode'],type_mix=value):
 c=Counter()
 for s,ids in plan:
  for i in ids:c[s,owner.get((s,i),s)]+=1
 count.update(c);steps.append({s+'/'+k:n for (s,k),n in sorted(c.items())})
assert len(steps)==200 and sum(count.values())==200*288
result=dict(config_sha256='b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad',steps=200,counts={s+'/'+k:n for (s,k),n in sorted(count.items())},per_step=steps,stream_populations=counts,type_mix_sha256=file_pin(path)['sha256'],allocation_tables=value['tables'],code=dict(sampler='work/build24m4h/p_tree/student_pilot/type_mix.py:229',wrapper='work/build24m4h/p_tree/student_pilot/carrier_c1_data.py:449'))
(D/'P_DRY_COUNT.json').write_text(json.dumps(result,indent=2)+'\n')
print('P native sampler PASS',result['counts'])
