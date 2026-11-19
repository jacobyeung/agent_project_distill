"""One GPU step per launch, scene receipts, strict dependencies, and cut order."""
from common import *
import inputs,programs,budget,gzip
from collections import defaultdict

def gzread(path):return json.loads(gzip.decompress(read(path)))
def gzwrite(path,value):
 p=local(path);assert p.is_relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(gzip.compress(json.dumps(clean(dict(value,input_sha256=dict(PINS))),allow_nan=False).encode(),mtime=0))

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('step',choices=budget.GROUPS);p.add_argument('--go',required=True);p.add_argument('--cut-level',type=int,choices=range(4),default=0);args=p.parse_args()
 assert os.environ.get('CUDA_VISIBLE_DEVICES'),'GPU pass requires explicit visible device'
 pins();go=js(args.go);assert go['authorized'] and go['kit']=='sb_kobj2' and go['registration'];dry=js(ROOT/'out/DRYRUN.json')
 if dry['status']!='PASS':raise Missing('out/DRYRUN.json is not PASS')
 group=budget.GROUPS[args.step]
 if (args.cut_level>=1 and group in ('dev-S1','S1_track')) or (args.cut_level>=3 and group=='T94'):raise Missing('NOT_PRICED: predeclared budget cut')

 from registration import primary
 frozen=None
 if group in ('R0_f32','track','T94'):
  frozen=primary();active={t:a for t,a in frozen['arms'].items() if a['run']}
  if group in ('track','S1_track'):active={t:a for t,a in active.items() if a['source']=='track'}
  if group=='T94':active={t:a for t,a in active.items() if t=='object_abs_distance' and a['frames']==94}
  if not active:raise Missing('Frozen arms do not authorize this pass')
 if group in ('dev-S1','S1_track'):
  items,skips,_=inputs.devs1();write(ROOT/'out/object_route/DEVS1_SKIPS.json',dict(skipped=skips));scenes={}
  for r in items:
   sid=r['scene'];binding=dict(scene=sid,dataset=r['dataset'],room=r['room'],frames=r['frames'],f32=r['source_frame_indices'],anchor_slots=list(range(32)),split='dev-S1')
   if sid in scenes and scenes[sid]!=binding:raise ValueError('Multiple dev-S1 layouts need an authoritative capture key')
   scenes[sid]=binding
  scenes=list(scenes.values())
 elif group=='K1_track':items=[];scenes=[]
 else:
  items=[r for r in inputs.r0_items() if r['question_type'] in active];scenes=inputs.r0_scenes(inputs.r0_items())
 jobs=[];priority=['obj_appearance_order','object_counting','object_abs_distance','object_size_estimation','object_rel_distance']
 if group in ('track','S1_track'):
  seen=set()
  for typ in priority:
   if args.cut_level>=2 and typ in priority[-2:]:
    if frozen and typ in active:raise Missing('Cannot cut part of a frozen track category; leave its look unspent')
    continue
   for scene in scenes:
    names=sorted({n for r in items if r['scene']==scene['scene'] and r['question_type']==typ for n in programs.operands(r)})
    for name in names:
     key=(scene['scene'],name)
     if key not in seen:jobs.append((scene,[name],typ));seen.add(key)
 else:
  for scene in scenes:
   types=['object_abs_distance'] if group=='T94' else list(active) if frozen else inputs.TYPES
   names=sorted({n for r in items if r['scene']==scene['scene'] and r['question_type'] in types for n in programs.operands(r)});
   if names:jobs.append((scene,names,None))
 if group=='K1_track':
  from k1_track import jobs as k1_jobs
  jobs=k1_jobs()
 if not jobs:raise Missing('No sha-bound jobs available for this part')
 start,seconds=budget.begin(group);normal=False;completed=[]
 try:
  import torch
  torch.set_num_threads(8)
  import gpu_models as M
  import numpy as np
  for scene,names,category in jobs:
   if time.monotonic()-start>=seconds:break
   tag=scene['scene'] if group not in ('track','K1_track','S1_track') else scene['scene']+'/'+digest(names[0])[:16]
   folder=ROOT/'out/object_route/passes'/args.step/tag;folder.mkdir(parents=True,exist_ok=True)
   binding=digest(dict(scene=scene,names=names,step=args.step,registration=go['registration'],primary_sha256=sha(ROOT/'out/object_route/PRIMARY_ARMS.json') if frozen else None,code={k:v for k,v in PINS.items() if '/code/' in k or '/config/' in k}))
   if done_valid(folder,binding):completed.append(dict(scene=scene['scene'],names=names,category=category,status='SKIPPED_VALID'));continue
   t=time.monotonic()
   if args.step.endswith('g3t'):
    data,metric=M.g3t(scene,dense=group=='T94');output=folder/'G3T.npz';np.savez_compressed(output,**data)
   elif args.step.endswith('sam'):
    base=gzread(ROOT/'out/object_route/passes/r0_sam'/scene['scene']/'SAM3.json.gz') if group=='T94' else None
    data,metric=M.sam(scene,names,dense=group=='T94',base=base);output=folder/'SAM3.json.gz';gzwrite(output,data)
   else:
    if group=='K1_track' and not completed:
     import signal
     def minute_limit(signum,frame):raise TimeoutError('First GPU minute tracker check failed')
     old=signal.signal(signal.SIGALRM,minute_limit);signal.alarm(60)
     try:data,metric=M.track(scene,names[0])
     except Exception as exc:
      write(ROOT/'out/object_route/K1_TRACK_CHOICE.json',dict(status='COMPLETE',selection_split='K1-train',box_source='linker',first_seen_pair_rates={},tracker_status='BLOCKER',reason=repr(exc)))
      normal=True
      return
     finally:signal.alarm(0);signal.signal(signal.SIGALRM,old)
    else:data,metric=M.track(scene,names[0])
    output=folder/'TRACKS.json.gz';gzwrite(output,dict(name=names[0],tracks=data,category=category))
   family='G3T' if args.step.endswith('g3t') else 'SAM3' if args.step.endswith('sam') else 'TRACKS'
   suffix='.npz' if family=='G3T' else '.json.gz'
   alias=ROOT/'out/object_route'/family/(scene['scene']+suffix) if group=='R0_f32' else ROOT/'out/object_route'/family/group/(tag+suffix)
   alias.parent.mkdir(parents=True,exist_ok=True)
   if not alias.exists():alias.symlink_to(output)
   write(folder/'METRICS.json',metric);finish(folder,binding,[output,folder/'METRICS.json'],time.monotonic()-t,metric['peak_gpu_bytes']);completed.append(dict(scene=scene['scene'],names=names,category=category,status='DONE'))
  normal=True
 finally:
  if normal:budget.end(group,start)
  write(ROOT/'out/object_route'/f'{args.step}_PASS.json',dict(completed=completed,normal_exit=normal,seconds=time.monotonic()-start,cut_level=args.cut_level,budget_group=group))
if __name__=='__main__':main()
