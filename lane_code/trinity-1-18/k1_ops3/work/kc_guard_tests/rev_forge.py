import json,sys,shutil
from pathlib import Path
WORK=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work')
sys.path.insert(0,str(WORK))
import k1_pipeline as K
K._native();B=K.B
import k1_guard as guard
T=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard_tests')
m=B.load('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json')
c=m['captures'][1];key=B.digest(c['canonical'])[:16]
src=T/'canary_patch2'/key
for variant,evidence in (('a',True),('b',False)):
    d=T/'forge_patch2'/variant/key;d.mkdir(parents=True)
    for n in ('candidates.json','parity_raw.jsonl'):shutil.copyfile(src/n,d/n)
    names=['candidates.json','parity_raw.jsonl']
    if evidence:shutil.copyfile(src/'geometry.npz',d/'REFUSED_GEOMETRY.npz');names.append('REFUSED_GEOMETRY.npz')
    r=B.load(src/'CACHE_COMPLETE.json')
    r.update(geometry=None,geometry_refusal=dict(code=guard.CODE,message=guard.CODE),
             gravity_verdict=dict(sealed_refused=False,reviewed_refused=True),files={n:B.pin(d/n) for n in names})
    B.write(d/'CACHE_COMPLETE.json',r)
    try:
        raw,geo,rr=K.cached(c,d);print(variant,'evidence' if evidence else 'no-evidence','FORGED REFUSAL ACCEPTED geo=',geo)
    except Exception as e:print(variant,'rejected',repr(e))
print(guard.GG.report())
