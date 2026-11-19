"""Pose protocol, depth diagnostics and paired cluster bootstrap."""
import importlib.util
from collections import defaultdict
import numpy as np
from common import ROOT
sp=importlib.util.spec_from_file_location('pose_k1_unchanged',ROOT/'inputs/pose_k1.py');K=importlib.util.module_from_spec(sp);sp.loader.exec_module(K)
SEED=20261119

def mean(xs):return float(np.mean(xs)) if xs else None

def c2w_pose(raw):
 from student_pilot.camera_targets import rotation_from_xyzw
 out=np.repeat(np.eye(4)[None],len(raw),0)
 for k,p in enumerate(raw):
  r=rotation_from_xyzw(p[3:7]).T;out[k,:3,:3]=r;out[k,:3,3]=-r@p[:3]
 return out

def poses(pred,gt,scale=1.,valid=None):
 # Same reference frame, thresholds and arithmetic as pose_k1.py; two extra bands.
 valid=np.ones(len(gt),bool) if valid is None else np.asarray(valid,bool)
 if not valid[0]:return {'status':'MISSING','reason':'invalid_GT_origin'}
 p,g=K.rel(pred),K.rel(gt);r=defaultdict(list)
 for k in range(1,len(gt)):
  if not valid[k]:continue
  (rp,tp),(rg,tg)=p[k],g[k];ag=K.ang(rg);dg=float(np.linalg.norm(tg));dp=float(np.linalg.norm(tp))*scale
  r['rot_all'].append(K.ang(rp.T@rg));r['dir_all'].append(K.vang(tp,tg))
  if ag>=10:r['turn_mra'].append(K.mra(K.ang(rp),ag))
  if dg>=.25:
   r['move_mra'].append(K.mra(dp,dg));r['dir_acc'].append(K.dom(tp)==K.dom(tg));r['disp_ratio'].append(dp/dg)
  if .05<=dg<=.25:r['short_displacement_mra'].append(K.mra(dp,dg))
  if 1<=ag<=5:r['short_rotation_mra'].append(K.mra(K.ang(rp),ag))
 out={k:mean(v) for k,v in r.items() if k not in ('rot_all','dir_all','disp_ratio')}
 out.update(rot_med=float(np.median(r['rot_all'])),dir_med=float(np.nanmedian(r['dir_all'])),n_move=len(r['move_mra']),n_turn=len(r['turn_mra']),rot_all=r['rot_all'],dir_all=r['dir_all'],disp_ratio_med=float(np.median(r['disp_ratio'])) if r['disp_ratio'] else None)
 return out

def depth_metrics(grid,gt,valid):
 # Sample GT optical-axis raster at the tower's declared endpoint grid, nearest pixels.
 h,w=gt.shape[1:];ys=np.rint(np.linspace(0,h-1,grid.shape[1])).astype(int);xs=np.rint(np.linspace(0,w-1,grid.shape[2])).astype(int)
 target=gt[:,ys[:,None],xs];raw=[];aligned=[];ratios=[];counts=[]
 for p,t,v in zip(grid,target,valid):
  ok=np.isfinite(p)&np.isfinite(t)&(p>0)&(t>0)&bool(v);counts.append(int(ok.sum()))
  if not ok.any():continue
  s=float(np.median(t[ok]/p[ok]));ratios.append(s)
  raw.append(float(np.mean(abs(p[ok]-t[ok])/t[ok])));aligned.append(float(np.mean(abs(s*p[ok]-t[ok])/t[ok])))
 return dict(absrel_raw=mean(raw),absrel_median_aligned=mean(aligned),per_frame_scale_log_sd=float(np.std(np.log(ratios))) if ratios else None,per_frame_scale=ratios,valid_pixels=counts,sampling='GT nearest at 51x51 raster endpoints')

def paired(rows,field='delta',cluster='room',draws=10000):
 # Item-weighted cluster resampling: resample complete rooms, preserve their row counts.
 groups=defaultdict(list)
 for r in rows:
  if r.get(field) is not None and np.isfinite(r[field]):groups[r[cluster]].append(float(r[field]))
 if not groups:return dict(status='MISSING',n_clusters=0,draws=draws,seed=SEED)
 v=list(groups.values());sums=np.array([sum(x) for x in v]);counts=np.array([len(x) for x in v]);rng=np.random.default_rng(SEED);boot=[]
 for _ in range(draws):
  i=rng.integers(0,len(v),len(v));boot.append(sums[i].sum()/counts[i].sum())
 return dict(status='OK',point=float(sums.sum()/counts.sum()),low=float(np.percentile(boot,2.5)),high=float(np.percentile(boot,97.5)),n_clusters=len(v),n_items=int(counts.sum()),draws=draws,seed=SEED)

def verdict(rows,cluster='room',draws=10000):
 tr=paired(rows,cluster=cluster,draws=draws)
 return dict(train=tr,status='MISSING' if tr['status']=='MISSING' else 'PASS' if tr['low']>0 else 'FAIL')

def a_bars(pose_rows,distance_rows):
 assert all(r['split']=='train' for r in pose_rows+distance_rows),'Decisions accept K1 train only'
 out={}
 for metric in ('move_mra','short_displacement_mra'):
  rr=[dict(capture=r['capture'],delta=100*(r['G64'][metric]-r['G32'][metric])) for r in pose_rows if r['G64'].get(metric) is not None and r['G32'].get(metric) is not None]
  out[metric]=verdict(rr,'capture',5000)
 out['context_pays_pose']='PASS' if any(out[k]['status']=='PASS' for k in out) else 'MISSING' if any(out[k]['status']=='MISSING' for k in out) else 'FAIL'
 out['lifting']=verdict([r for r in distance_rows if r['arm']=='A2'])
 out['reader_C64_licensed']='PASS' if out['context_pays_pose']=='PASS' or out['lifting']['status']=='PASS' else 'MISSING' if out['context_pays_pose']=='MISSING' or out['lifting']['status']=='MISSING' else 'FAIL'
 out['part_B_runs']=True
 return out

def b_bar(rows):
 assert all(r['split']=='train' for r in rows),'Decisions accept K1 train only'
 return verdict(rows)

def c_bar(rows):
 return dict(status='REPORT_ONLY',by_type={t:paired([r for r in rows if r['type']==t]) for t in sorted({r['type'] for r in rows})})
