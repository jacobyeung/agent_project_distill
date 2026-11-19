"""Section 6 CPU checks; missing real inputs never become synthetic passes."""
import os,time,traceback,resource
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
from common import *
import numpy as np
import metrics,camera

def main():
 start=time.monotonic();code_pins();sha(ROOT/'inputs/pose_k1.py');sha(ROOT/'inputs/KIT_SPEC_tower_frames.md');sha(ROOT/'inputs/HEAD_ACCURACY_DESIGN_20261119.md')
 m=manifest();selected=[];ar=[];errors=[]
 from replay import price,load_selector
 from e2e_reader.geometry import from_npz
 head=load_selector()
 for c in m['captures']:
  if c['k1_split']!='train':continue
  folder=capdir(c,'/scratch/jjyeung/k1/run_tower_sam_2');geo=capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz'
  if not (folder/'tower.npz').is_file() or not Path(c['gt']['path']).is_file() or not geo.is_file():continue
  selected.append(c)
  if len(selected)==5:break
 for c in selected:
  print('A_CAPTURE',c['canonical'],flush=True)
  try:
   tw=npz(capdir(c,'/scratch/jjyeung/k1/run_tower_sam_2')/'tower.npz');gt=npz(c['gt']['path']);g=npz(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz')
   assert INPUTS[str(local(c['gt']['path']))]==c['gt']['sha256']
   assert np.array_equal(tw['frame_indices'][tw['anchor_slots']],gt['frame_indices'])
   p=metrics.c2w_pose(tw['raw_pose'][tw['anchor_slots']]);a=metrics.poses(p,gt['c2w'],float(g['scale']),gt['valid']);b=metrics.poses(p.copy(),gt['c2w'],float(g['scale']),gt['valid'])
   da=metrics.depth_metrics(tw['depth_grid'],gt['depth'],gt['valid']);db=metrics.depth_metrics(tw['depth_grid'].copy(),gt['depth'],gt['valid'])
   differences={k:float(a[k]-b[k]) for k in a if isinstance(a[k],(int,float)) and np.isfinite(a[k])}
   differences.update({k:float(da[k]-db[k]) for k in da if isinstance(da[k],(int,float))})
   geo=from_npz(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz')
   from evaluate import geometry,stored_tower
   own=npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz');rebuilt,scale=geometry(stored_tower(c),own)
   assert np.array_equal(geo.C,rebuilt.C) and np.array_equal(geo.depth_grid,rebuilt.depth_grid), 'K1 conversion parity failed'
   cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
   dist={}
   for arm in ('A0','A2'):
    kwargs=dict(cache=cache,gt=gt if arm=='A2' else None,head=head)
    left=price(c,geo,**kwargs);right=price(c,geo,**kwargs)
    dist[arm]=dict(status='PASS' if clean(left)==clean(right) else 'FAIL',rows=len(left),differences=[0. if x['prediction']==y['prediction'] else None for x,y in zip(left,right)],responses=[x['response'] for x in left])
   ar.append(dict(capture=c['canonical'],status='PASS' if clean(a)==clean(b) and clean(da)==clean(db) and all(v==0 for v in differences.values()) and all(v['status']=='PASS' for v in dist.values()) else 'FAIL',differences=differences,pose=a,depth=da,distance=dist))
  except Exception as e:ar.append(dict(capture=c['canonical'],status='FAIL',error=repr(e)));traceback.print_exc()
 # Exercise N=32 against the unmodified routed-candidate source, and N=64 beyond slot 32.
 import importlib.util
 from student_pilot import routed_candidates as RC
 old=Path('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/routed_candidates.py');sha(old)
 spec=importlib.util.spec_from_file_location('original_candidates',old);original=importlib.util.module_from_spec(spec);sys.modules[spec.name]=original;spec.loader.exec_module(original)
 from e2e_reader.geometry import from_npz
 nr=[]
 for c in selected:
  path=capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz';sha(path);g=from_npz(path)
  a=original.lift_grid(g);b=RC.lift_grid(g,n_frames=32)
  eq=a.keys()==b.keys() and all(all(np.array_equal(x,y,equal_nan=True) for x,y in zip(a[k],b[k])) for k in a)
  cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json');name=next(iter(cache['phrases']))
  aa,ra=original.lift(cache,name,g,grids=a,phrase=name);bb,rb=RC.lift(cache,name,g,grids=b,phrase=name,n_frames=32)
  eq=eq and ra==rb and len(aa)==len(bb) and all(x.frame==y.frame and x.index==y.index and np.array_equal(x.points,y.points) for x,y in zip(aa,bb))
  nr.append(dict(capture=c['canonical'],status='PASS' if eq else 'FAIL',proposals=len(bb)))
 from types import SimpleNamespace
 fake=SimpleNamespace(has=lambda k:1<=k<=64,lift=lambda k,uv,mode:(np.column_stack([uv/1000,np.ones(len(uv))]),np.column_stack([uv/1000,np.ones(len(uv))]),np.zeros(len(uv))))
 n64=RC.lift_grid(fake,n_frames=64)
 # Actual A0 output from the parallel lane is required for section 6b.
 kbox=Path('/scratch/jjyeung/orch_n30/sb_kbox/out/box_ladder/PER_ITEM.jsonl')
 bstatus=missing(kbox)
 if kbox.exists():
  sha(kbox);rows=[json.loads(line) for line in kbox.read_text().splitlines()];a0=[r for r in rows if r.get('arm') in ('A0','deployed','A0_deployed')]
  if not a0:bstatus=dict(status='MISSING',expected_path=str(kbox),reason='No A0 rows')
  else:
   from replay import price,load_selector
   head=load_selector();checks=[]
   for c in selected:
    ref=[r for r in a0 if r.get('capture')==c['canonical']]
    if not ref:checks.append(dict(capture=c['canonical'],status='MISSING'));continue
    g=from_npz(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz');cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json');got=price(c,g,cache,32,head=head)
    target={r.get('row_id',r.get('id')):r for r in ref}
    eq=all(r['row_id'] in target and r['prediction']==target[r['row_id']]['prediction'] and r['response']==target[r['row_id']].get('response') for r in got)
    checks.append(dict(capture=c['canonical'],status='PASS' if eq else 'FAIL',rows=len(got)))
   bstatus=dict(status='PASS' if len(checks)==5 and all(x['status']=='PASS' for x in checks) else 'BLOCKER',captures=checks)
 syn=camera.synthetic()
 # The named exports are unjoined masks; no guessed capture digest is admitted.
 cp=missing('/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py');cp.update(synthetic=syn)
 logs=['RUN2.log','RUN2b.log','run_tower_sam_2/worker.log'];evidence=[]
 for name in logs:
  p=Path('/scratch/jjyeung/k1')/name;sha(p)
  evidence.extend([dict(path=str(p),line=i,text=line) for i,line in enumerate(p.read_text().splitlines(),1) if __import__('re').search(r'peak.*(?:memory|alloc|reserv)|max_memory',line,__import__('re').I)])
 mem=dict(status='MISSING',peak_bytes=None,reason='No peak-allocation or peak-reserved value in K1 logs',matches=evidence)
 if evidence:mem['status']='REQUIRES_REVIEW'
 status='PASS' if len(ar)==5 and all(r['status']=='PASS' for r in ar) and bstatus['status']=='PASS' and syn['status']=='PASS' else 'BLOCKER'
 result=dict(status=status,code_sha256=digest(code_pins()),gpu_hours_used=0,CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],A=dict(status='PASS' if len(ar)==5 and all(r['status']=='PASS' for r in ar) else 'FAIL',captures=ar),B=bstatus,N32_tree_equivalence=nr,N64_lift=dict(status='PASS' if sorted(n64)==list(range(1,65)) else 'FAIL',frames=len(n64)),C=cp,K1_peak_memory=mem,seconds=time.monotonic()-start,peak_cpu_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 write_json(ROOT/'out/DRYRUN.json',result)
 (ROOT/'STATUS.md').write_text('Stage 3: The CPU dry run is '+status+'. Five stored K1 captures were checked against themselves; the full N=32 A0 parity gate and real 450-item camera parity remain explicit prerequisites. Details and input hashes are in out/DRYRUN.json. No GPU, network, SSH, Git, or other-lane writes were used.\n')
 print(json.dumps({k:v for k,v in result.items() if k in ('status','seconds','peak_cpu_kib')}),flush=True)
if __name__=='__main__':main()
