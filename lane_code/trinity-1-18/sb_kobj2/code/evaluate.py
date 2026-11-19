"""One registered R0 comparison per invocation; no outcome is read before reservation."""
from common import *
import inputs,programs,geometry,gzip
from registration import primary,reserve,CATEGORIES
from scoring import Scorer
from ground import Grounder,PredictedSource,TrackSource
from route_stats import summary

def read_pass(step,scene,file):
 folder=ROOT/'out/object_route/passes'/step/scene;receipt=js(folder/'DONE.json')
 for f,h in receipt['outputs'].items():assert sha(folder/f)==h
 return npz(folder/file) if file.endswith('.npz') else json.loads(gzip.decompress(read(folder/file)))

def price(category):
 # Reject missing/changed PRIMARY or spent categories before reading any head output.
 d=primary()
 if js(ROOT/'out/DRYRUN.json')['status']!='PASS':raise Missing('CPU dry run not PASS')
 receipt,arm=reserve(category)
 items=[r for r in inputs.r0_items() if r['question_type']==category]
 direct=inputs.direct('R0-dev');scenes=inputs.r0_scenes(inputs.r0_items());scorer=Scorer();records=[];scales={}
 for scene in scenes:
  rr=[r for r in items if r['scene']==scene['scene']]
  if not rr:continue
  sid=scene['scene'];base_tw=read_pass('r0_g3t',sid,'G3T.npz');base_geo,base_meta=geometry.g3t_s4(base_tw)
  base_cache=read_pass('r0_sam',sid,'SAM3.json.gz')
  if arm['frames']==94:
   tw=read_pass('T94_g3t',sid,'G3T.npz');geo,meta=geometry.g3t_s4(tw);cache=read_pass('T94_sam',sid,'SAM3.json.gz');slots=tw['anchor_slots']
  else:geo,meta,cache,slots=base_geo,base_meta,base_cache,None
  scales[sid]=dict(S4_missing=not meta['s4_available'],scale=meta['scale'],ratio94_32=meta['scale']/base_meta['scale'] if arm['frames']==94 and meta['s4_available'] and base_meta['s4_available'] else None)
  rule='object' if arm['source']=='object' or category!='obj_appearance_order' else 'today'
  if arm['source']=='track':
   tracks={n:read_pass('track',sid+'/'+digest(n)[:16],'TRACKS.json.gz')['tracks'] for n in sorted({n for r in rr for n in programs.operands(r)})};source=TrackSource(tracks,geo)
  else:source=PredictedSource(cache,geo,rule)
  g=Grounder(geo,source,rule,slots);baseline=Grounder(base_geo,PredictedSource(base_cache,base_geo,'today'))
  for r in rr:
   direct_row=direct.get(r['source_line']);present=direct_row['pred'] if direct_row else None
   if category=='object_abs_distance':present=programs.run(r,baseline)['prediction'] if base_meta['s4_available'] else None
   if not meta['s4_available'] and category in ('object_size_estimation','object_abs_distance'):
    result=dict(prediction=present,refusal_code='S4 unavailable',member_frames={},fallback=True)
   else:result=programs.run(r,g,present,direct_row['text'] if direct_row else '',variant='fallback')
   truth_item=dict(r,gt_released=direct_row['gt_released']) if direct_row else r
   records.append(dict(source_line=r['source_line'],qid=r['qid'],room=scene['room'],type=category,subtype=r.get('subtype') or '',arm=arm,direct_prediction=present,direct_score=scorer(truth_item,present),head_score=scorer(truth_item,result['prediction']),**result))
 report=summary(category,records,arm)
 report['S4_missing_scenes']=sum(v['S4_missing'] for v in scales.values());report['scales']=scales
 line=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+category+' '+json.dumps(arm,sort_keys=True)+' '+report['verdict']
 write(receipt,dict(status='COMPLETE',category=category,arm=arm,result=report,R0DEV_LOOKS_line=line,primary_sha256=sha(ROOT/'out/object_route/PRIMARY_ARMS.json')))
 jsonl(ROOT/'out/object_route'/f'PER_ITEM_{category}.jsonl',records)
 # Aggregate only already completed immutable category receipts; no prediction reread.
 table=[];allrows=[]
 for typ in CATEGORIES:
  p=ROOT/'out/object_route'/f'LOOK_{typ}.json'
  if p.exists():
   look=js(p)
   if look['status']=='COMPLETE':table.append(look['result']);allrows+=rows(ROOT/'out/object_route'/f'PER_ITEM_{typ}.jsonl')
 write(ROOT/'out/object_route/ROUTE_TABLE.json',dict(rows=table));jsonl(ROOT/'out/object_route/PER_ITEM.jsonl',allrows)
 (ROOT/'out/object_route/ROUTE_TABLE.txt').write_text('\n'.join(json.dumps(clean(r)) for r in table)+'\n')

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--category',required=True,choices=CATEGORIES);a=p.parse_args();pins();price(a.category)
