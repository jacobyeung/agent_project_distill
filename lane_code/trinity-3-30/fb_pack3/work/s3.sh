cd /scratch/jjyeung/orch_n30/sb_own400 && /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json,numpy as np
b=json.load(open('out/BARS_FROZEN.json')); r=b['captures'][0]; print({k:(v if not isinstance(v,dict) else list(v)) for k,v in r.items()})
print('own544',r['own544'])
z=np.load(r['own544']['path']); print('544 keys',{k:z[k].shape for k in z.files})
rec=json.load(open(r['own544']['receipt'])); print('544 receipt keys',list(rec)); 
d='in/own_400/native/probe/'+r['key']; pc=json.load(open(d+'/PHASE_COMPLETE.json')); print('400 receipt keys',list(pc)); print({k:pc[k] for k in pc if k not in ('sources',)})
z4=np.load(d+'/own.npz'); print('400 keys',z4.files)
P
ls kit/ ; grep -rn "frame_indices\|grid_uv" kit/*.py | head
