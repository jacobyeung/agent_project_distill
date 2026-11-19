"""dev-S1 diagnosis only; no thresholds or decisions are selected here."""
from common import *
import inputs,programs,geometry
from evaluate import read_pass
from ground import Grounder,PredictedSource,TrackSource
from box_hook import load as box_hook
from scoring import Scorer
from route_stats import paired
from collections import defaultdict,Counter

def run():
 items,skips,table=inputs.devs1();scorer=Scorer();records=[];missing_groups=[]
 write(ROOT/'out/object_route/DEVS1_SKIPS.json',dict(status='MISSING' if not items else 'OK',kept=len(items),skipped=len(skips),counts=dict(Counter(s.get('type','unknown') for s in skips)),items=skips))
 for sid in sorted({r['scene'] for r in items}):
  rr=[r for r in items if r['scene']==sid]
  try:geo,meta=geometry.g3t_s4(read_pass('s1_g3t',sid,'G3T.npz'));cache=read_pass('s1_sam',sid,'SAM3.json.gz')
  except Missing as e:missing_groups.append(dict(scene=sid,reason=str(e)));continue
  for source_name in ('linker','object','track'):
   for rule in ('today','object'):
    try:
     if source_name=='track':
      tracks={n:read_pass('s1_track',sid+'/'+digest(n)[:16],'TRACKS.json.gz')['tracks'] for n in sorted({n for r in rr for n in programs.operands(r)})};source=TrackSource(tracks,geo)
     elif source_name=='object':
      hook,_=box_hook(True)
      if not hasattr(hook,'object_source'):raise Missing('KBOX_RULES_HOOK.object_source(cache, geometry)')
      source=hook.object_source(cache,geo)
     else:source=PredictedSource(cache,geo,rule)
     g=Grounder(geo,source,rule)
     for item in rr:
      typ=item['question_type']
      for form in ('fallback','strict'):
       variants=[form]+(['full'] if typ=='object_rel_distance' and form=='strict' else [])
       for variant in variants:
        result=programs.run(item,g,item['pred'],item['text'],variant)
        if typ=='object_size_estimation' and not meta['s4_available']:result=dict(prediction=item['pred'] if variant=='fallback' else None,refusal_code='S4 unavailable',member_frames={})
        records.append(dict(qid=item['id'],room=item['room'],dataset=item['dataset'],type=typ,subtype=item.get('subtype') or '',source=source_name,box_rule=rule,form=variant,truth=item['gt_released'],direct_prediction=item['pred'],direct_score=scorer(item,item['pred']),head_score=scorer(item,result['prediction']),**result))
        if typ=='object_counting':
         counts=[g(n).get('count_conf') for n in programs.operands(item)]
         pred=sum(counts) if all(c is not None for c in counts) else None
         records.append(dict(records[-1],form=variant+'_conf',prediction=pred,head_score=scorer(item,pred),refusal_code=None if pred is not None else 'confident instance count unavailable'))
    except Missing as e:missing_groups.append(dict(scene=sid,source=source_name,box_rule=rule,reason=str(e)))
 groups=defaultdict(list)
 for r in records:groups[(r['dataset'],r['type'],r['source'],r['box_rule'],r['form'])].append(r)
 result=[]
 for key,rr in groups.items():
  dataset,typ,source,box,form=key;d=dict(dataset=dataset,type=typ,source=source,box_rule=box,form=form,summary=paired(rr),verdict='DIAGNOSTIC_ONLY',treatment='S4 treatment')
  if typ=='object_counting':d['truth_bands']={str(b):paired([r for r in rr if min(int(float(r['truth'])),5)==b]) for b in (2,3,4,5)}
  result.append(d)
 jsonl(ROOT/'out/object_route/DEVS1_PER_ITEM.jsonl',records)
 write(ROOT/'out/object_route/DEVS1_DIAGNOSTICS.json',dict(status='MISSING' if not records else 'PARTIAL' if missing_groups else 'COMPLETE',diagnostic_only=True,rows=result,skipped=len(skips),missing=missing_groups,route_decisions=0))
if __name__=='__main__':run()
