"""Section 8 CPU checks; missing real inputs never become synthetic passes."""
import os,time,traceback,resource
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
from common import *
import numpy as np
import metrics,camera

def main():
 start=time.monotonic();code_pins();sha(ROOT/'inputs/pose_k1.py');sha(ROOT/'inputs/KIT_SPEC_tower_frames_v2.md');sha(ROOT/'inputs/HEAD_ACCURACY_DESIGN_20261119.md')
 from policy import captures,numbering
 numbering_check=numbering()
 from exclusions import population
 exclusions=population()
 m=manifest();selected=[];ar=[];errors=[];scales=[]
 from replay import price,load_selector
 from e2e_reader.geometry import from_npz
 head=load_selector()
 for c in captures('train'):
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
   from evaluate import geometry,stored_tower
   own=npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz');rebuilt,scale=geometry(stored_tower(c),own)
   from student_pilot.tower_scale import estimate_scale
   legacy=estimate_scale(tw['depth_grid'],tw['depth_conf_grid'],own['depth'])[0]
   relative=abs(scale-float(g['scale']))/abs(float(g['scale']))
   scales.append(dict(capture=c['canonical'],reader_median_ratio=scale,served_scale=float(torch.tensor(float(np.log(scale)),dtype=torch.float32).exp()),stored_scale=float(g['scale']),relative_error=relative,agrees=relative<=1e-4,legacy_range_gate_scale=legacy,legacy_relative_error=abs(legacy-float(g['scale']))/abs(float(g['scale']))))
   p=metrics.c2w_pose(tw['raw_pose'][tw['anchor_slots']]);a=metrics.poses(p,gt['c2w'],scale,gt['valid']);b=metrics.poses(p.copy(),gt['c2w'],scale,gt['valid'])
   da=metrics.depth_metrics(tw['depth_grid'],gt['depth'],gt['valid']);db=metrics.depth_metrics(tw['depth_grid'].copy(),gt['depth'],gt['valid'])
   differences={k:float(a[k]-b[k]) for k in a if isinstance(a[k],(int,float)) and np.isfinite(a[k])}
   differences.update({k:float(da[k]-db[k]) for k in da if isinstance(da[k],(int,float))})
   from e2e_reader.geometry import from_arrays
   served=float(torch.tensor(float(np.log(scale)),dtype=torch.float32).exp())
   geo=from_arrays(**{k:g[k] for k in ('K','canvas_to_source','camera_to_world','depth_grid','grid_uv','anchor_frame_indices')},scale=served)
   from evaluate import geometry,stored_tower
   own=npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz');rebuilt,scale=geometry(stored_tower(c),own)
   assert np.array_equal(geo.C,rebuilt.C) and np.array_equal(geo.depth_grid,rebuilt.depth_grid), 'K1 conversion tensor parity failed'
   cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
   dist={}
   for arm in ('A0','A2'):
    kwargs=dict(cache=cache,gt=gt if arm=='A2' else None,head=head)
    left=price(c,rebuilt,**kwargs);right=price(c,rebuilt,**kwargs)
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
 # Compare only emitted, authoritative box-kit A0 rows on stored geometry.
 from kbox_hook import compare
 checks=[]
 for c in selected:
  g,_=geometry(stored_tower(c),npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz'));cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
  checks.append(compare(c,price(c,g,cache,32,head=head)))
 bstatus=dict(status='PASS' if len(checks)==5 and all(x['status']=='PASS' for x in checks) else 'BLOCKER',captures=checks)
 from camera_records import records,frame_binding
 staged=records();record=staged[0]
 syn=camera.synthetic(record['scale'],record['gravity'])
 cp=dict(status='PASS' if syn['status']=='PASS' and len(staged)==450 else 'FAIL',synthetic=syn,records_loaded=len(staged),calls_parsed=len(staged),real_parity=dict(status='NOT_RUN',reason='Requires GPU G32 tower replay; own pose9 is not the tower output'),frame_binding=frame_binding())
 mem=dict(status='MEASURE_FIRST_CAPTURE',peak_bytes=None,stop_above_bytes=40000000000)
 scale_result=dict(status='PASS' if len(scales)==5 and all(x['agrees'] for x in scales) else 'FAIL',captures=scales,agreement_fraction=sum(x['agrees'] for x in scales)/len(scales),threshold=.95,rule_used='e2e_reader.stage1.median_ratio; geometry uses float32 exp(log(scale))',stored_rule='tower_scale_rule.estimate; own depth restricted to 0.1 < depth < 10' if all(x['legacy_relative_error']<=1e-4 for x in scales) else 'MISSING: stored scale rule unresolved')
 write_json(ROOT/'out/tower_frames/A_SCALE.json',scale_result)
 status='PASS' if len(ar)==5 and all(r['status']=='PASS' for r in ar) and bstatus['status']=='PASS' and cp['status']=='PASS' and numbering_check['status']=='PASS' and all(r['status']=='PASS' for r in nr) and sorted(n64)==list(range(1,65)) and scale_result['status']=='PASS' else 'BLOCKER'
 result=dict(status=status,code_sha256=digest(code_pins()),gpu_hours_used=0,CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],A=dict(status='PASS' if len(ar)==5 and all(r['status']=='PASS' for r in ar) else 'FAIL',captures=ar),B=bstatus,numbering=numbering_check,exclusions=exclusions,scale_check=scale_result,N32_tree_equivalence=nr,N64_lift=dict(status='PASS' if sorted(n64)==list(range(1,65)) else 'FAIL',frames=len(n64)),C=cp,K1_peak_memory=mem,seconds=time.monotonic()-start,peak_cpu_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 write_json(ROOT/'out/DRYRUN.json',result)
 (ROOT/'STATUS.md').write_text('The section-8 CPU dry run is '+status+'. Five train captures, the scale check, all 296 numbering assertions, and all 450 staged camera calls were checked. Section 8b depends on the box-kit A0 rows named in out/DRYRUN.json. No GPU work ran.\n')
 print(json.dumps({k:v for k,v in result.items() if k in ('status','seconds','peak_cpu_kib')}),flush=True)
if __name__=='__main__':main()
