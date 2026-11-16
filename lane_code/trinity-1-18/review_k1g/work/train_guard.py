import sys,json,types
K='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/kc/k1_build/work/kit_k1a/work'
class Reached(Exception):pass
def rows(p):return [json.loads(l) for l in open(p)]
L=types.ModuleType('setlib')
def lload(p):
  rs=rows(p);g={}
  for r in rs:g.setdefault(r['object_id'],[]).append(r)
  return None,g
L.load=lload;L.FEATS={'portable_np':[]};L.PFEATS=[]
fitm=types.ModuleType('fit');fitm.fit_predict=lambda *a,**k:(_ for _ in ()).throw(Reached())
fp=types.ModuleType('fit_pairs');fp.load=lambda p:(rows(p),None,None)
sk=types.ModuleType('sklearn');skm=types.ModuleType('sklearn.metrics');skm.roc_auc_score=skm.average_precision_score=None;sk.metrics=skm;sk.__version__='stub'
p2=types.ModuleType('proof_p2');p2.exported=None
sys.modules.update(setlib=L,fit=fitm,fit_pairs=fp,sklearn=sk,**{'sklearn.metrics':skm},proof_p2=p2)
sys.path[:0]=[K,K+'/refit']
import train as T
T.audit_features=lambda *a,**k:True
F='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/tests_8cc4f9ec/'
def go(name,tab,gs=None,sens=False):
  try:T.train(f't/{tab}/candidates.jsonl',f't/{tab}/pairs.jsonl',F+'inventory.json',f't/train_{name}',gt_set=gs,sensitivity=sens);print(name,'WROTE?')
  except Reached:print(name,'guards passed (reached estimator)')
  except Exception as e:print(name,'REFUSED',type(e).__name__,str(e)[:120])
go('plain','old')
go('subset_ok','subset',F+'subset.json')
go('subset_noset','subset')
go('subset_with_allset','subset',F+'all.json')
go('sens_ok','sens',F+'sensitivity.json',True)
go('sens_noflag','sens',F+'sensitivity.json')
go('sens_as_primary_allset','sens',F+'all.json')
go('plain_table_with_set','old',F+'all.json')
go('all_with_sensflag','all',F+'all.json',True)
