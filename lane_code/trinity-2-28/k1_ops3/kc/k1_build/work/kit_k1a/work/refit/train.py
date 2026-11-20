"""Gate K1 tables, call unchanged estimators, export both consumer formats."""
import os,sys,json,pickle,collections,argparse
from pathlib import Path
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent),str(HERE)]
import gate
import gt_set as G
SOURCE=gate.ROOT/'grd_selector/work/setsel'
sys.path.insert(0,str(SOURCE))
import fit,fit_pairs,setlib as L
import numpy as np,sklearn
from sklearn.metrics import roc_auc_score,average_precision_score
from proof_p2 import exported
def versions():return dict(python=sys.version,numpy=np.__version__,sklearn=sklearn.__version__,interpreter=sys.executable)
def audit_features(rows,pair=False):
 key='f' if pair else 'features';allowed=set(L.PFEATS if pair else L.FEATS['portable_np'])
 for r in rows:
  if set(r[key])!=allowed:raise ValueError('Unexpected or missing feature columns: '+str(sorted(set(r[key])^allowed)))
  if not np.isfinite([r[key][f] for f in allowed]).all():raise ValueError('Nonfinite feature')
 return True
def split_rows(rows,pilot):
 membership={c['canonical']:c for c in pilot};out={'train':[],'heldout':[]}
 rooms={'train':set(),'heldout':set()}
 for r in rows:
  ds,cap=r['scene'].split('/');canon=gate.canonical(ds,cap)
  if not gate.eligible(ds,cap) or canon not in membership:raise ValueError('Ineligible/non-K1 fit input: '+r['scene'])
  entry=membership[canon];room=gate.verdict(ds,cap)['room']
  if entry['room']!=room:raise ValueError('Room identity differs')
  split=entry['split'];out[split].append(r);rooms[split].add(room)
 if rooms['train']&rooms['heldout']:raise ValueError('Room crosses split')
 return out,rooms
def probability(m,rows,key='features'):
 X=np.array([[r[key][f] for f in m['features']] for r in rows])
 z=((X-np.array(m['mean']))/m['scale'])@np.array(m['coef'])+m['intercept']
 return 1/(1+np.exp(-np.clip(z,-700,700)))
def metrics(rows,p,pair=False):
 y=np.array([r['y'] for r in rows]);ok=y>=0;y=y[ok];p=np.asarray(p)[ok]
 if len(set(y))!=2:raise ValueError('AUC requires both held-out classes')
 groups=collections.defaultdict(list)
 for r,s in zip([r for r in rows if r['y']>=0],p):groups[r['object_id']].append((r,float(s)))
 top=[max(g,key=lambda x:(x[1],x[0].get('features',{}).get('peak',0)))[0]['y'] for g in groups.values()]
 return dict(auc=float(roc_auc_score(y,p)),average_precision=float(average_precision_score(y,p)),
             top1_accept_accuracy=float(np.mean(top)),n=len(y),objects=len(top),top1_definition='highest probability candidate per object; ties by SAM peak')
def train(candidate_path,pair_path,inventory_path,out,*,fixture=False,gt_set=None,sensitivity=False):
 selection=G.load(gt_set,sensitivity)
 inv=json.loads(Path(inventory_path).read_text())
 meta=G.metadata(selection,[c['canonical'] for c in inv['pilot']])
 if fixture and selection is not None:raise ValueError('GT-set refit requires bound tables')
 if not inv['pilot_complete']:raise ValueError('Incomplete K1 selection')
 if not fixture:
  table_receipt=Path(candidate_path).parent/'TABLE_RECEIPT.json'
  t=json.loads(table_receipt.read_text());G.require(t,meta)
  if t['inventory']['sha256']!=gate.sha(inventory_path):raise ValueError('Table inventory differs')
  for path in [candidate_path,pair_path]:
   if t['files'][Path(path).name]['sha256']!=gate.sha(path):raise ValueError('Unbound fit table')
 _,groups=L.load(candidate_path);cands=[r for g in groups.values() for r in g]
 audit_features(cands);pair_rows,X,y=fit_pairs.load(pair_path);audit_features(pair_rows,True)
 if meta is not None and any(r['scene'] not in selection['entries'] for r in cands+pair_rows):raise ValueError('Fit table contains captures outside GT set')
 cs,rooms=split_rows(cands,inv['pilot']);ps,_=split_rows(pair_rows,inv['pilot'])
 pred,model,_=fit.fit_predict(cs['train'],cs['heldout'],L.FEATS['portable_np'],'logistic')
 ptr=[r for r in ps['train'] if r['y']>=0]
 pm=fit.model('logistic').fit(np.array([[r['f'][k] for k in L.PFEATS] for r in ptr]),[r['y'] for r in ptr])
 models=dict(accept=exported(model,L.FEATS['portable_np']),pairs=exported(pm,L.PFEATS))
 current=json.loads((gate.ROOT/'devs1_masks/out/kit/work/vendor/MODELS.json').read_text())
 report=dict(versions=versions(),fixture_only=fixture,scope='eligible K1 train rooms only',thresholds=dict(count_accept=.15,pair_merge=.2,unique_accept=2.),
   thresholds_source='frozen deployed policy; no answer-dependent threshold fitting',train_rooms=sorted(rooms['train']),heldout_rooms=sorted(rooms['heldout']),
   metrics={tag:dict(refit=metrics(rows,probability(models[tag],rows,key),tag=='pairs'),current=metrics(rows,probability(current[tag],rows,key),tag=='pairs'))
     for tag,rows,key in [('accept',cs['heldout'],'features'),('pairs',ps['heldout'],'f')]},
   inputs={str(p):gate.sha(p) for p in [candidate_path,pair_path,inventory_path]},
   upstream={str(SOURCE/n):gate.sha(SOURCE/n) for n in ['build.py','fit.py','fit_pairs.py','setlib.py']})
 out=Path(out);out.mkdir(parents=True,exist_ok=False)
 (out/'MODELS.json').write_text(json.dumps(models,indent=2)+'\n')
 native=dict(schema='routed-candidate-policy-v1',count_threshold=.15,merge_threshold=.2,depth_erosion=3,
             depth_percentiles=[10,90],depth_margin_m=.15,disjoint_overlap=.2,name_prior=False)
 for dst,src in [('accept','accept'),('pair','pairs')]:
  native[dst]={('coefficient' if k=='coef' else k):v for k,v in models[src].items()}
 (out/'NATIVE_POLICY.json').write_text(json.dumps(native,indent=2)+'\n')
 # Original price2 consumer loads the unchanged sklearn pipeline bundle.
 for name,m,features in [('deploy_portable_np_logistic.pkl',model,L.FEATS['portable_np']),('deploy_pairs_logistic.pkl',pm,L.PFEATS)]:
  with (out/name).open('wb') as f:pickle.dump(dict(model=m,feats=features,prior_names=None),f)
 # Native policy and frozen price_masks consume the portable NumPy fields.
 report['models_sha256']=gate.sha(out/'MODELS.json')
 report['native_policy_sha256']=gate.sha(out/'NATIVE_POLICY.json')
 if meta is None:(out/'FIT_RECEIPT.json').write_text(json.dumps(report,indent=2)+'\n')
 else:
  report['table_receipt']=G.pin(table_receipt)
  G.write(out/'FIT_RECEIPT.json',report,meta)
  report=json.loads((out/'FIT_RECEIPT.json').read_text())
 return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidates',required=True);p.add_argument('--pairs',required=True);p.add_argument('--inventory',required=True);p.add_argument('--out',required=True);p.add_argument('--gt-set');p.add_argument('--sensitivity',action='store_true');a=p.parse_args()
 print(json.dumps(train(a.candidates,a.pairs,a.inventory,a.out,gt_set=a.gt_set,sensitivity=a.sensitivity),indent=2))
if __name__=='__main__':main()
