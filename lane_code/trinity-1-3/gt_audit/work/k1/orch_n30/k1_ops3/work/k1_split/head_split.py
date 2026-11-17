"""K1 head accuracy split portrait vs landscape (ORCH 1527Z). Reuses refit/train.py and k1_report.py unchanged; reads only bound outputs."""
import argparse,collections,json,sys
from pathlib import Path
KIT=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work')
sys.path[:0]=[str(KIT),str(KIT/'refit')]
import train as T
import k1_report as R
import gate
p=argparse.ArgumentParser();p.add_argument('--analysis',required=True);p.add_argument('--inventory',required=True);p.add_argument('--out',required=True);a=p.parse_args()
A=Path(a.analysis);tables=A/'tables';refit=A/'refit'
tr=json.loads((tables/'TABLE_RECEIPT.json').read_text());fr=json.loads((refit/'FIT_RECEIPT.json').read_text())
for n,pin in tr['files'].items():
 if gate.sha(pin['path'])!=pin['sha256'] or fr['inputs'].get(pin['path'])!=pin['sha256']:raise SystemExit('unbound table '+n)
if gate.sha(refit/'MODELS.json')!=fr['models_sha256']:raise SystemExit('MODELS.json differs from FIT_RECEIPT')
inv=json.loads(Path(a.inventory).read_text());split={c['canonical']:c['split'] for c in inv['pilot']}
cmap=tr['gt_canvas_map'];orient=lambda s:'portrait' if cmap.get(s,'identity').startswith('stretch') else 'landscape'
SUBS=('all','portrait','landscape','landscape_arkitscenes')
insub=lambda s,sub:sub=='all' or orient(s)==sub or (sub=='landscape_arkitscenes' and orient(s)=='landscape' and s.startswith('arkitscenes/'))
models=json.loads((refit/'MODELS.json').read_text());current=json.loads((T.gate.ROOT/'devs1_masks/out/kit/work/vendor/MODELS.json').read_text())
_,groups=T.L.load(str(tables/'candidates.jsonl'));cands=[r for g in groups.values() for r in g]
pairs,_,_=T.fit_pairs.load(str(tables/'pairs.jsonl'))
cs,_=T.split_rows(cands,inv['pilot']);ps,_=T.split_rows(pairs,inv['pilot'])
def m(rows,model,key,pair):
 if not rows:return None
 try:return T.metrics(rows,T.probability(model,rows,key),pair)
 except ValueError as e:return dict(error=str(e),n=len(rows))
out=dict(analysis=str(A),table_receipt=T.G.pin(tables/'TABLE_RECEIPT.json'),fit_receipt=T.G.pin(refit/'FIT_RECEIPT.json'),
 orientation_rule="portrait = TABLE_RECEIPT gt_canvas_map value starting 'stretch' (GT 320x240 stretched to the deployed 240x320 canvas); landscape = every other capture; landscape_arkitscenes = the landscape ARKitScenes captures, the dataset control for portrait (all portrait captures are ARKitScenes)",
 captures={},heads={},mra={})
for s in ('train','heldout'):
 c=collections.Counter((orient(k),k.split('/')[0]) for k,v in split.items() if v==s and k in set(r['scene'] for r in cands))
 out['captures'][s]={f'{o}/{d}':n for (o,d),n in sorted(c.items())}
for tag,rows,key,pair in [('accept',cs['heldout'],'features',False),('pairs',ps['heldout'],'f',True)]:
 out['heads'][tag]={}
 for sub in SUBS:
  sel=[r for r in rows if insub(r['scene'],sub)]
  out['heads'][tag][sub]=dict(refit=m(sel,models[tag],key,pair),current=m(sel,current[tag],key,pair),captures=len({r['scene'] for r in sel}))
 if out['heads'][tag]['all']['refit']!=fr['metrics'][tag]['refit'] or out['heads'][tag]['all']['current']!=fr['metrics'][tag]['current']:raise SystemExit('overall '+tag+' metrics do not reproduce FIT_RECEIPT')
rep=A/'REPORT.json';rows_path=A/'render/K1_ANALYSIS_INPUT.jsonl'
if rep.is_file() and rows_path.is_file():
 r=json.loads(rep.read_text());c=r['train_constant'];rows=[json.loads(l) for l in open(rows_path)]
 test=[x for x in rows if x['type']=='object_abs_distance' and split[x['canonical']]=='heldout']
 refused=set(tr.get('geometry_refused',{}))
 for sub in SUBS:
  t=[x for x in test if insub(x['canonical'],sub)];ans=[x for x in t if x['pred'] is not None]
  mean=lambda v:sum(v)/len(v) if v else None
  out['mra'][sub]=dict(heldout_items=len(t),answered_items=len(ans),trust_fallback_share=mean([x['label'] in ('trust','fallback') for x in t]),
   answered_mra=mean([R.mra(x['pred'],x['gt_value']) for x in ans]),constant_mra=mean([R.mra(c,x['gt_value']) for x in ans]),
   refused_heldout_rows=sum(x['canonical'] in refused for x in t))
 if abs(out['mra']['all']['answered_mra']-r['answered_mra'])>1e-12 or out['mra']['all']['heldout_items']!=r['heldout_items']:raise SystemExit('overall MRA does not reproduce REPORT.json')
Path(a.out).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=1))
