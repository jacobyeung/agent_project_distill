import sys
K='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/kc/k1_build/work/kit_k1a'
sys.path[:0]=[K+'/work',K+'/native_kit']
import bindings as B,k1_pipeline as P
P._sources_verified=True
m=B.load('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
G='/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets/'
for name,gs,sens in [('primary',G+'GT_SET_PRIMARY_296.json',False),('sens_noflag',G+'GT_SET_SENSITIVITY_300.json',False),('sensitivity',G+'GT_SET_SENSITIVITY_300.json',True),('default',None,False)]:
  try:P.check_manifest(m,'downstream',gs,sens);print(name,'PASS')
  except Exception as e:print(name,'REFUSED',str(e)[:150])
