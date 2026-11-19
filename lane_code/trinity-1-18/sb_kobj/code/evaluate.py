"""CPU pricing from sealed scene passes, with one reservation per category."""
from common import *
import inputs,programs,route_stats as statistics,gzip,geometry
from ground import Grounder,PredictedSource,TrackSource
from box_hook import load as box_hook
from scoring import Scorer
from collections import defaultdict,Counter

def read_pass(step,scene,file):
 folder=ROOT/'out/object_route/passes'/step/scene
 receipt=js(folder/'DONE.json')
 for f,h in receipt['outputs'].items():assert sha(folder/f)==h
 p=folder/file
 return npz(p) if file.endswith('.npz') else json.loads(gzip.decompress(read(p)))

def available():
 checks={};items=inputs.r0_items();duplicates={q:n for q,n in Counter(r['qid'] for r in items).items() if n>1}
 checks['qid_uniqueness']=dict(status='BLOCKER' if duplicates else 'PASS',duplicates=duplicates)
 for split,leg in [('R0-dev','R1'),('R0-dev','D0'),('dev-S1','R1')]:
  try:rr=inputs.direct(split,leg);checks[f'{leg}:{split}']=dict(status='PASS',rows=len(rr))
  except Missing as e:checks[f'{leg}:{split}']=missing(e)
 try:Scorer();checks['scorer']=dict(status='PASS')
 except (Missing,ImportError) as e:checks['scorer']=missing(e)
 for name,p in [('kbox_hook',ROOT/'config/KBOX_RULES_HOOK.json'),('dry_run',ROOT/'out/DRYRUN.json')]:
  d=js(p);checks[name]=dict(status=d['status'],path=str(p))
 checks['track']=dict(status=js(ROOT/'out/TRACK_CPU_CHECK.json')['status'],path=str(ROOT/'out/BLOCKER_track.md'))
 write(ROOT/'out/object_route/READINESS.json',dict(status='BLOCKER' if any(x['status'] not in ('PASS','BOUND') for x in checks.values()) else 'PASS',checks=checks))
 return checks

def placeholders(checks):
 # No model inference has run. MISSING is not a refusal scored zero.
 table=[]
 for split,datasets,types in [('R0-dev',['scannetpp'],inputs.TYPES),('dev-S1',['scannet','scannetpp','arkitscenes'],['object_counting','object_size_estimation','object_rel_distance'])]:
  for ds in datasets:
   for typ in types:
    for arm in (['g3t_s4','track','T94','da3_f32'] if typ=='object_abs_distance' else ['g3t_s4','track'] if split=='R0-dev' else ['g3t_s4']):
     for box in ('today','object'):
      variants=['fallback','strict'] if typ=='obj_appearance_order' else ['fallback','full'] if typ=='object_rel_distance' else ['strict']
      for variant in variants:
       table.append(dict(split=split,dataset=ds,category=typ,arm=arm,box_rule=box,variant=variant,status='MISSING',verdict='MISSING',head=None,direct=None,difference=None,ci95=None,refusals=None,reason='GPU pass not run; see READINESS.json',constant_context=29.5 if typ=='object_abs_distance' else None))
 write(ROOT/'out/object_route/ROUTE_TABLE.json',dict(status='MISSING',rows=table,gpu_hours_used=0,route_looks=0))
 (ROOT/'out/object_route/ROUTE_TABLE.txt').write_text('No pricing pass has run. Every arm is MISSING; no route decision was made.\n'+'\n'.join(f"{r['split']} {r['dataset']} {r['category']} {r['arm']} {r['box_rule']} {r['variant']}: MISSING" for r in table)+'\n')
 write(ROOT/'out/object_route/FIRST_SEEN.json',dict(status='MISSING',reason='No R0-dev model proposals or tracks; GT-mask fixture checks are in DRYRUN.json'))
 write(ROOT/'out/object_route/PASS_METRICS.json',dict(status='NOT_RUN',gpu_hours_used=0,seconds=None,peak_gpu_bytes=None,planned_gpu_memory_gib=48))
 jsonl(ROOT/'out/object_route/PER_ITEM.jsonl',[])
 write(ROOT/'out/object_route/PER_ITEM_STATUS.json',dict(status='MISSING',records=0,reason='No GPU pass or real item scoring; empty JSONL is not a successful result'))
 for d in ('G3T','SAM3','TRACKS'):(ROOT/'out/object_route'/d).mkdir(exist_ok=True)

def price(split,registration,arms):
 if js(ROOT/'out/DRYRUN.json')['status']!='PASS':raise Missing('CPU dry run not PASS')
 scorer=Scorer();hook,gate=box_hook();table=inputs.direct(split);d0={}
 if split=='R0-dev':
  items=inputs.r0_items();scenes=inputs.r0_scenes(items)
  try:d0=inputs.direct(split,'D0')
  except Missing:pass
 else:
  items,skips,table=inputs.devs1();write(ROOT/'out/object_route/DEVS1_SKIPS.json',dict(skipped=skips));scenes=[]
  seen=set()
  for r in items:
   if r['scene'] not in seen:scenes.append(dict(scene=r['scene'],dataset=r['dataset'],room=r['room'],f32=r['source_frame_indices'],frames=r['frames'],anchor_slots=list(range(32))));seen.add(r['scene'])
 if len({r['qid'] for r in items})!=len(items):raise Missing('Duplicate qids require an authoritative direct-export identity binding')
 types=[t for t in inputs.TYPES if any(r['question_type']==t for r in items)]
 # Verify all selected passes and all required direct rows before consuming any category look.
 for scene in scenes:
  steps=['s1_g3t','s1_sam'] if split=='dev-S1' else ['r0_g3t','r0_sam']
  if 'T94' in arms:steps+=['T94_g3t','T94_sam']
  for step in steps:
   folder=ROOT/'out/object_route/passes'/step/scene['scene'];d=js(folder/'DONE.json')
   for f,h in d['outputs'].items():assert sha(folder/f)==h
 for r in items:
  if r['question_type'] in types and r['question_type']!='object_abs_distance':
   if r['qid'] not in table:raise Missing('direct row '+r['qid'])
 for typ in types:statistics.reserve_look(split,typ,registration)
 allrows=[];first={};start=time.monotonic()
 for scene in scenes:
  sid=scene['scene'];ss=[r for r in items if r['scene']==sid and r['question_type'] in types]
  for arm in arms:
   if split=='dev-S1' and arm!='g3t_s4':continue
   relevant=[r for r in ss if arm not in ('T94','da3_f32') or r['question_type']=='object_abs_distance']
   if not relevant:continue
   if arm=='da3_f32':geo,meta=geometry.da3_f32(sid);anchor_slots=None
   else:
    step='T94_g3t' if arm=='T94' else 's1_g3t' if split=='dev-S1' else 'r0_g3t';tw=read_pass(step,sid,'G3T.npz');geo,meta=geometry.g3t_s4(tw);anchor_slots=tw['anchor_slots'] if arm=='T94' else None
   if arm=='track':
    tracks={}
    for name in sorted({n for r in relevant for n in programs.operands(r)}):
     try:d=read_pass('track',sid+'/'+digest(name)[:16],'TRACKS.json.gz');tracks[name]=d['tracks']
     except Missing:pass
    relevant=[r for r in relevant if all(n in tracks for n in programs.operands(r))]
    write(ROOT/'out/object_route/track_coverage'/f'{sid}.json',dict(priced_qids=[r['qid'] for r in relevant],not_priced_qids=[r['qid'] for r in ss if r not in relevant]))
   else:cache=read_pass('T94_sam' if arm=='T94' else 's1_sam' if split=='dev-S1' else 'r0_sam',sid,'SAM3.json.gz')
   for rule in (['today','object'] if gate['object_exists'] else ['today']):
    source=TrackSource(tracks,geo) if arm=='track' else PredictedSource(cache,geo,rule);g=Grounder(geo,source,rule,anchor_slots)
    appearances=[r for r in relevant if r['question_type']=='obj_appearance_order']
    if appearances:
     # First-seen diagnostics do not depend on the appearance route screen.
     key=f'{split}:{arm}:{rule}:{sid}';first[key]=programs.first_seen(appearances,{r['qid']:g for r in appearances})
    for item in relevant:
     typ=item['question_type'];d=table.get(item['qid']);variants=['fallback','strict'] if typ=='obj_appearance_order' else ['fallback','full'] if typ=='object_rel_distance' else ['strict']
     if typ=='obj_appearance_order' and not gate['first_seen_screen']:continue
     for variant in variants:
      result=programs.run(item,g,d['prediction'] if d else None,d['text'] if d else '',variant)
      if typ=='object_counting' and result['prediction'] is None:raise Missing('sb_kbox count_objects output unavailable')
      score=scorer(item,result['prediction'])
      if d and scorer(item,d['prediction'])!=float(d['score']):raise ValueError('Direct scorer parity differs for '+item['qid'])
      allrows.append(dict(qid=item['qid'],room=scene['room'],dataset=scene['dataset'],split=split,type=typ,subtype=item.get('subtype',''),arm=arm,box_rule=rule,variant=variant,direct_prediction=d['prediction'] if d else None,direct_score=d['score'] if d else None,head_score=score,d0_score=d0.get(item['qid'],{}).get('score'),truth=item['answer'],**result))
 rows=statistics.report(allrows,gate);jsonl(ROOT/'out/object_route/PER_ITEM.jsonl',allrows);write(ROOT/'out/object_route/ROUTE_TABLE.json',dict(rows=rows,registration=registration,seconds=time.monotonic()-start));write(ROOT/'out/object_route/FIRST_SEEN.json',dict(groups=first));(ROOT/'out/object_route/ROUTE_TABLE.txt').write_text('\n'.join(json.dumps(clean(r),sort_keys=True) for r in rows)+'\n')

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--price',action='store_true');p.add_argument('--split',choices=['R0-dev','dev-S1'],default='R0-dev');p.add_argument('--registration');p.add_argument('--arms',nargs='+',choices=['g3t_s4','track','T94','da3_f32'],default=['g3t_s4']);args=p.parse_args();pins()
 if args.price:
  if not args.registration:raise ValueError('A predeclared registration is required')
  price(args.split,args.registration,args.arms)
 else:
  if (ROOT/'out/object_route/looks').exists():raise ValueError('Readiness output must not overwrite a priced run')
  placeholders(available())
if __name__=='__main__':main()
