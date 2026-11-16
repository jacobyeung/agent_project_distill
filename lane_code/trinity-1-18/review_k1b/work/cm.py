import sys,json,time,traceback
KC='/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a'
sys.path[:0]=[KC+'/work',KC+'/native_kit']
import k1_pipeline as K, bindings as B
M='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'
m=B.load(M)
for ph in sys.argv[1:]:
    t=time.time()
    try:K.check_manifest(m,ph);r='PASS'
    except Exception as e:r='REFUSED '+type(e).__name__+': '+str(e)
    print(json.dumps(dict(phase=ph,result=r,seconds=round(time.time()-t,1),kit_k1_pipeline=K.__file__)),flush=True)
