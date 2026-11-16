import sys,json,importlib.util,random,os,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
KC='/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a'
spec=importlib.util.spec_from_file_location('kp',KC+'/work/k1_pipeline.py'); kp=importlib.util.module_from_spec(spec); spec.loader.exec_module(kp)
F=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_finalize_v2/K1_MANIFEST.finalized.json'))
S=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/K1_MANIFEST.staged.json'))
for ph in ('own','convert','all'):
    try: kp.check_manifest(F,ph); print(ph,'PASS')
    except Exception as e: print(ph,'REFUSED:',e)
try: kp.check_manifest(S,'tower_sam'); print('staged tower_sam PASS (unexpected)')
except Exception as e: print('staged tower_sam REFUSED:',e)
import bindings as B
real=B.checked; random.seed(3); stats=dict(frames=0,hashed=0,other=[])
sample=set()
for c in F['captures']: sample.add(random.choice(c['dense_frames'])['sha256'])
def checked(pin):
    p=Path(pin['path']).resolve()
    if '/k1_frames/' in str(p):
        stats['frames']+=1
        if pin['sha256'] in sample: stats['hashed']+=1; return real(pin)
        if not p.is_file(): raise ValueError('missing '+str(p))
        return p
    stats['other'].append((pin['path'],os.path.getsize(p)))
    if os.path.getsize(p)<50_000_000: return real(pin)
    if not p.is_file(): raise ValueError('missing')
    return p
B.checked=checked
try: kp.check_manifest(F,'tower_sam'); print('tower_sam PASS (sampled hashing)',stats)
except Exception as e: print('tower_sam REFUSED:',e,stats)
