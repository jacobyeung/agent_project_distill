"""Score donor depth on frozen K1 training folds using read-only scale1/scale2 functions."""
import os,sys
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='8'
os.environ['CUDA_VISIBLE_DEVICES']='';sys.dont_write_bytecode=True
import argparse,importlib.util,time
from collections import defaultdict
import numpy as np
from core import *
S1=pathlib.Path('/scratch/jjyeung/orch_n30/sb_scale1/code/scale_analysis.py')
S2=pathlib.Path('/scratch/jjyeung/orch_n30/sb_scale2/code/scale_drift.py')
def module(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def choose(folds,combined):
 return 544 if all(v['B-A']['ci95'][1]<0 for v in folds+[combined]) else 400
def summarize(s,records):
 room=defaultdict(list)
 for r in records:
  for a,p in r['pred'].items():room[a,r['room']].extend(s.pair_scores(p,r['gt']).tolist())
 arms=sorted({a for a,r in room});out={}
 for a in arms:
  v=[float(np.mean(room[a,r])) for r in sorted({r for aa,r in room if aa==a})]
  out[a]={'mra':float(np.mean(v)),'ci95':s.interval(v),'rooms':len(v)}
 for a,b in [('B','A'),('G','A'),('G','B')]:
  if a not in arms or b not in arms:continue
  rooms=sorted({r for aa,r in room if aa==a}&{r for aa,r in room if aa==b})
  vals=[float(np.mean(room[a,r])-np.mean(room[b,r])) for r in rooms]
  out[a+'-'+b]={'points':float(np.mean(vals)),'ci95':s.interval(vals),'rooms':len(vals)}
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--own-root',type=pathlib.Path);ap.add_argument('--synthetic',action='store_true');ap.add_argument('--out',required=True);ap.add_argument('--displacement-only',action='store_true');a=ap.parse_args()
 if not a.synthetic and a.own_root is None:ap.error('--own-root is required for real scoring')
 out=fresh(a.out);bars=read(ROOT/'out/BARS_FROZEN.json');write_guard(out)
 for var,name in [('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TORCH_HOME','torch')]:
  q=out/name;q.mkdir(exist_ok=True);os.environ[var]=str(q)
 pins={str(ROOT/'out/BARS_FROZEN.json'):sha(ROOT/'out/BARS_FROZEN.json'),str(S1):sha(S1),str(S2):sha(S2),str(pathlib.Path(__file__)):sha(__file__),str(KIT/'core.py'):sha(KIT/'core.py')}
 checked(S1,bars['code_sha256'])
 source=read('/scratch/jjyeung/orch_n30/sb_scale1/out/BARS_FROZEN.json');assert bars['folds']==source['folds']
 # Freeze the fresh run before opening any depth or score payload.
 atomic(out/'BARS_FROZEN.json',{'input_sha256':pins,'bars':bars,'synthetic':a.synthetic,'synthetic_factor':1.014 if a.synthetic else None,'routed_distance':not a.displacement_only})
 s=module(S1,'scale1_own400');d=module(S2,'scale2_own400');d.OUT=out
 if 'torch' in sys.modules:sys.modules['torch'].set_num_threads(8)
 for p,h in bars['input_sha256'].items():checked(p,h);pins[p]=h
 pins.update(d.codepins())
 cs={c['canonical']:c for c in s.training()};records=[];missing=[];scales={};begin=time.monotonic()
 for n,r in enumerate(bars['captures']):
  c=cs[r['canonical']];assert c['k1_split']=='train' and digest(c)==r['capture_sha256']
  if not r['gt_present']:missing.append({'capture':c['canonical'],'expected':c['gt'],'reason':'GT MISSING'});continue
  for arm in ('tower','own544'):
   q=r[arm];checked(q['path'],q['sha256']);pins[q['path']]=q['sha256'];pins[q['receipt']]=sha(q['receipt'])
   rec=read(q['receipt']);assert rec['capture_sha256']==digest(c) and not rec['synthetic']
  gt,tower,hw=s.load_capture(c,(pathlib.Path(r['tower']['path']).parent,read(r['tower']['receipt'])),False)
  pins[c['gt']['path']]=c['gt']['sha256']
  with np.load(r['own544']['path'],allow_pickle=False) as z:depA=z['depth']
  if a.synthetic:
   depB=depA*1.014
   dest=out/'synthetic400'/r['key'];dest.mkdir(parents=True)
   with (dest/'own.npz').open('xb') as f:np.savez_compressed(f,depth=depB)
   atomic(dest/'PHASE_COMPLETE.json',{'synthetic':True,'input_sha256':{r['own544']['path']:r['own544']['sha256']},'factor':1.014,'files':{'own.npz':sha(dest/'own.npz')}})
  else:
   dest=a.own_root/r['key'];rec=read(dest/'PHASE_COMPLETE.json')
   assert not rec['synthetic'] and rec['capture_sha256']==digest(c)
   assert rec['checkpoint']['sha256']==bars['step400']['artifact_sha256']
   checked(dest/'own.npz',rec['files']['own.npz'])
   with np.load(dest/'own.npz',allow_pickle=False) as z:
    depB=z['depth']
    assert np.array_equal(z['frame_indices'],c['anchor_indices'])
    assert np.array_equal(z['grid_uv'],np.linspace(0,1000,51,dtype=np.float32))
  pins[str(dest/'own.npz')]=sha(dest/'own.npz');pins[str(dest/'PHASE_COMPLETE.json')]=sha(dest/'PHASE_COMPLETE.json')
  valid_grid(depA);valid_grid(depB)
  sa,_,_=s.estimate(tower['depth_grid'],tower['depth_conf_grid'],depA);sb,_,_=s.estimate(tower['depth_grid'],tower['depth_conf_grid'],depB)
  scales[c['canonical']]={'A':sa,'B':sb}
  _,centres,_=s.to_gravity_reference_frame(tower['raw_pose'][tower['anchor_slots']],[0.,-1.,0.])
  i,j=np.triu_indices(32,1);truth=np.linalg.norm(gt['c2w'][i,:3,3]-gt['c2w'][j,:3,3],axis=1)
  ok=gt['valid'][i].astype(bool)&gt['valid'][j].astype(bool)&np.isfinite(truth)&(truth>=.1)
  raw=np.linalg.norm(centres[i]-centres[j],axis=1)[ok]
  assert len(raw)>0 and np.isfinite(raw).all()
  records.append({'capture':c['canonical'],'room':c['room'],'gt':truth[ok],'pred':{'A':raw*sa,'B':raw*sb}})
  if (n+1)%40==0:print('Loaded',n+1,flush=True)
 folds=[summarize(s,[r for r in records if r['room'] in f['test_rooms']]) for f in bars['folds']];combined=summarize(s,records);chosen=choose(folds,combined);arm='A' if chosen==544 else 'B';coeff={}
 for f in bars['folds']:
  factor=s.fit(records,set(f['fit_rooms']),arm);coeff[f['name']]={'factor':factor,'fit_rooms':sorted({r['room'] for r in records if r['room'] in f['fit_rooms']})}
  for r in records:
   if r['room'] in f['test_rooms']:r['pred']['G']=r['pred'][arm]*factor;scales[r['capture']]['G']=scales[r['capture']][arm]*factor
 displacement={'folds':[dict(name=f['name'],**summarize(s,[r for r in records if r['room'] in f['test_rooms']])) for f in bars['folds']],'combined':summarize(s,records),'global_fit_report_only':coeff}
 atomic(out/'DISPLACEMENT_RESULT.json',{'input_sha256':dict(pins),'synthetic':a.synthetic,'chosen_donor':chosen,'displacement':displacement,'captures':len(records),'pairs':sum(len(r['gt']) for r in records)})
 distance=[];rowsout=[]
 if not a.displacement_only:
  for n,r in enumerate(bars['captures']):
   if r['canonical'] not in scales:continue
   c=cs[r['canonical']];rows=[x for x in c['rows'] if x['type']=='object_abs_distance']
   if not rows:continue
   gt,tower,hw=s.load_capture(c,(pathlib.Path(r['tower']['path']).parent,read(r['tower']['receipt'])),True);pred={}
   for arm,scale in scales[c['canonical']].items():
    try:geo=d.geometry_npz(c,tower,hw,d.gravities(tower,gt)['G1'],scale,arm);error=None
    except (ValueError,FloatingPointError,np.linalg.LinAlgError) as e:geo=None;error=str(e)
    cache={};values=[]
    for row in rows:
     p,err=(None,error) if geo is None else d.attempt(lambda:d.distance(row,geo,gt,'predicted',cache))
     values.append(np.nan if p is None else p);rowsout.append({'capture':c['canonical'],'row_id':row['id'],'arm':arm,'pred':p,'gt':float(row['gt_value']),'refusal':err})
    pred[arm]=np.array(values)
   distance.append({'room':c['room'],'gt':np.array([float(x['gt_value']) for x in rows]),'pred':pred})
   if (n+1)%40==0:print('Routed distance',n+1,flush=True)
 dist={'status':'MISSING: --displacement-only'} if not distance else {'folds':[dict(name=f['name'],**summarize(s,[r for r in distance if r['room'] in f['test_rooms']])) for f in bars['folds']],'combined':summarize(s,distance)}
 if distance:
  # A selected 544 donor harms B if B-A is significantly positive; converse for selected 400.
  cis=[x['B-A']['ci95'] for x in dist['folds']+[dist['combined']]]
  dist['chosen_donor_harm']=any(ci[0]>0 if chosen==544 else ci[1]<0 for ci in cis)
  dist['guard_action']='REPORT HARM; donor choice remains frozen Q2 rule'
 result={'schema':'sb-own400-score-v1','input_sha256':pins,'command':' '.join(sys.argv),'synthetic':a.synthetic,'chosen_donor':chosen,'displacement':displacement,'routed_distance':dist,'missing':missing,'captures':len(records),'pairs':sum(len(r['gt']) for r in records),'seconds':time.monotonic()-begin,'global_factor_role':'report-only; chosen donor, fit-half rooms'}
 atomic(out/'SCORE_RESULT.json',result);atomic(out/'DISTANCE_ROWS.json',{'input_sha256':pins,'rows':rowsout})
 print(json.dumps({'chosen_donor':chosen,'B-A':displacement['combined']['B-A'],'seconds':result['seconds']}),flush=True)
if __name__=='__main__':main()
