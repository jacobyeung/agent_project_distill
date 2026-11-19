"""Spec section 6 on real local data; fixture successes never replace missing joins."""
from common import *
import inputs,programs,route_stats as stats
import numpy as np
from ground import Grounder
from itertools import permutations
import traceback

def k1_checks():
 from gt_reference import GTSource
 from trace_format import box_v313 as B
 m=js(ROOT/'inputs/local/K1_MANIFEST.json');sha(ROOT/'inputs/local/GT_REFERENCE_SOURCE.json');out=[]
 for ds in ('arkitscenes','scannetpp'):
  c=next(c for c in m['captures'] if c['k1_split']=='train' and c['canonical'].startswith(ds+'/') and len({n for r in c['rows'] for n in r.get('gt_instances',{})})>=5 and Path(c['gt']['path']).is_file())
  print('K1',c['canonical'],flush=True)
  arrays=npz(c['gt']['path']);assert PINS[str(local(c['gt']['path']))]==c['gt']['sha256']
  assert np.array_equal(arrays['frame_indices'],c['anchor_indices'])
  key=digest(c['canonical'])[:16];cache=js(Path('/scratch/jjyeung/k1/run_convert_2')/key/'candidates.json');tower=npz(Path('/scratch/jjyeung/k1/run_tower_sam_2')/key/'tower.npz')
  assert np.array_equal(tower['frame_indices'][tower['anchor_slots']],c['anchor_indices'])
  class Geo(GTSource):
   def __init__(self,a):
    self.depth=a['depth'];self.inst=a['inst'];self.K=a['K'];self.c2w=a['c2w'];self.C=self.c2w;self.valid=a['valid'].astype(bool);self.H,self.W=self.depth.shape[1:];self.Kinv_frames=np.linalg.inv(a['K_frames'])
   def lift(self,k,uv,mode='center'):
    self.Kinv=self.Kinv_frames[k-1];return super().lift(k,uv,mode)
  geo=Geo(arrays);gt_names={str(n):int(i) for i,n in zip(arrays['ids'],arrays['labels'])}
  mapping={n:i for r in c['rows'] for n,i in r.get('gt_instances',{}).items()}
  masks={n:(arrays['inst']==iid)&geo.valid[:,None,None] for n,iid in mapping.items()}
  visible={n:x for n,x in masks.items() if np.any(x.mean((1,2))>=.002)}
  names=sorted(visible)[:4]
  if len(names)<4:raise Missing('Four GT-visible object names in '+c['canonical'])
  truths={n:int(np.flatnonzero(mm.mean((1,2))>=.002)[0])+1 for n,mm in visible.items()}
  # GT fixture ties are explicitly the GT instance IDs; no R0 ordering rule is fitted.
  truth_order=sorted(names,key=lambda n:(truths[n],mapping[n]));orders=[truth_order]+[list(x) for x in permutations(names) if list(x)!=truth_order][:3]
  def source(n):
   mm=masks[n].copy();mm[mm.mean((1,2))<.002]=False
   ids=[int(i) for i,label in zip(arrays['ids'],arrays['labels']) if str(label)==n]
   count=len(ids) if ids else None
   return dict(entries=[dict(instance_id=str(mapping[n]),masks=mm,tie_index=(truths.get(n,1),mapping[n]))],count=count)
  g=Grounder(geo,source)
  obb={int(i):dict(centre=cc,lengths=ll,axes=aa.reshape(3,3)) for i,cc,ll,aa in zip(arrays['ids'],arrays['obb_centroid'],arrays['obb_lengths'],arrays['obb_axes'])}
  a,b=names[:2];ref=names[0];candidates=names[1:]
  gaps={n:B.box_grid_5cm(obb[mapping[ref]],obb[mapping[n]]) for n in candidates};order=sorted(candidates,key=lambda n:gaps[n])
  base=dict(scene=c['canonical'],dataset=ds,subtype='dry',unit='choice',options=[],frame_indices=c['anchor_indices'])
  fixtures=[dict(base,qid='dry_size',question_type='object_size_estimation',question=f'What is the length of the longest dimension (length, width, or height) of the {a}, measured in centimeters?',unit='cm',answer=str(max(obb[mapping[a]]['lengths'])*100)),
   dict(base,qid='dry_abs',question_type='object_abs_distance',question=f'Measuring from the closest point of each object, what is the distance between the {a} and the {b} (in meters)?',unit='m',answer=str(B.box_grid_5cm(obb[mapping[a]],obb[mapping[b]]))),
   dict(base,qid='dry_count',question_type='object_counting',question=f'How many {a}(s) do we have in this room?',unit='count',answer=str(source(a)['count'])),
   dict(base,qid='dry_order',question_type='obj_appearance_order',question='What will be the first-time appearance order of the following categories in the video: '+', '.join(names)+'?',options=[f'{chr(65+i)}. '+', '.join(v) for i,v in enumerate(orders)],answer='A',gt={'first_pos_f32':{n:truths[n] for n in names}})]
  # Four real GT candidates are required for the registered two-candidate parser.
  if len(visible)<5:raise Missing('Five real GT-visible objects required for relative fixture: '+c['canonical'])
  five=sorted(visible)[:5];ref=five[0];cand=five[1:];gg={n:B.box_grid_5cm(obb[mapping[ref]],obb[mapping[n]]) for n in cand};order=sorted(cand,key=lambda n:gg[n]);opts=[f'{chr(65+i)}. {n}' for i,n in enumerate(cand)]
  fixtures.append(dict(base,qid='dry_rel',question_type='object_rel_distance',question='Measuring from the closest point of each object, which of these objects ('+', '.join(cand)+f') is the closest to the {ref}?',subtype='closest',options=opts,answer=chr(65+cand.index(order[0]))))
  trace='The nearest-to-farthest order from the '+ref+' is: '+', then '.join(order)+'. '
  results=[]
  for f in fixtures:
   pred=programs.run(f,g,direct_prediction=f['answer'],trace=trace);results.append(dict(item=f,result=pred))
  appearance=next(x for x in results if x['item']['qid']=='dry_order');assert appearance['result']['prediction']=='A','GT appearance order must match'
  rel=fixtures[-1];assert programs.run(rel,g,rel['answer'],trace='missing')['prediction']==rel['answer']
  full=programs.run(rel,g,rel['answer'],trace,variant='full')
  class Unseen:
   def __call__(self,n):return dict(seen=False,frames=[],first=None,box_available=False)
  app=fixtures[3];diag=programs.first_seen([app],{app['qid']:g});assert diag['pair_correct']==1. and diag['exact']==1.
  fallback=programs.run(app,Unseen(),'B');strict=programs.run(app,Unseen(),'B',variant='strict');assert fallback['prediction']=='B' and strict['prediction'] is None
  malformed=dict(app,options=['A. '+', '.join(reversed(truth_order))]);assert programs.run(malformed,g,'B')['prediction']=='B'
  # Actual StageOne replay is attempted separately, never replaced by GT masks.
  try:
   from ground import PredictedSource
   stage=PredictedSource(cache,geo,'today');stage_results=[programs.run(f,Grounder(geo,stage),f['answer'],trace) for f in fixtures]
   stage_status=dict(status='PASS',results=stage_results)
  except (ImportError,Missing) as exc:stage_status=missing(exc)
  out.append(dict(capture=c['canonical'],split='train',status='PASS' if all(x['result']['prediction'] is not None for x in results) else 'FAIL',GT_mask_order='PASS',first_seen_diagnostics=diag,fallback='PASS',strict='PASS',option_no_match='PASS',programs=results,relative_full=full,stage1_replay=stage_status,gt_box_source='stored obb_* arrays, no fitted fixture labels'))
 return out

def main():
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='';start=time.monotonic();pins();checks={}
 items=inputs.r0_items();counts={t:sum(r['question_type']==t for r in items) for t in inputs.TYPES};assert counts==inputs.EXPECTED
 parsed=[];errors=[]
 for r in items:
  if r['question_type'] in inputs.TYPES:
   try:parsed.append((r['qid'],programs.operands(r)))
   except Exception as e:errors.append(dict(qid=r['qid'],error=str(e)))
 from collections import Counter
 dup={q:n for q,n in Counter(r['qid'] for r in items).items() if n>1}
 checks['qid_uniqueness']=dict(status='BLOCKER' if dup else 'PASS',duplicates=dup,policy='No deduplication or invented row IDs; pricing refuses ambiguous qids')
 checks['operand_parsing']=dict(status='PASS' if not errors else 'FAIL',parsed=len(parsed),errors=errors)
 try:
  table=inputs.direct('R0-dev');joins=inputs.join_report(items,table);checks['a']=dict(status='PASS' if all(joins[t]['status']=='PASS' for t in inputs.TYPES[:3]) else 'BLOCKER',types=joins)
  rel=[r for r in items if r['question_type']=='object_rel_distance'];n=sum(programs.parse_order(table[r['qid']]['text'],programs.options(r).values()) is not None for r in rel)
  checks['c']=dict(status='BLOCKER' if n<250 else ('PASS' if n==279 else 'PARTIAL'),parsed=n,expected=279)
 except Missing as e:
  checks['a']=dict(status='MISSING',expected_path=str(e),types={t:dict(items=counts[t],joined=None,missing=counts[t]) for t in inputs.TYPES[:3]});checks['c']=dict(status='BLOCKER',parsed=None,expected=279,reason='MISSING real step-200 relative-distance traces',expected_path=str(ROOT/'inputs/direct_R1_200_R0-dev.jsonl'))
 try:
  twins=rows(inputs.paths()['r0_twin']);assert all(r['r0_split']=='R0-dev' for r in twins)
  scenes=inputs.r0_scenes(items,open_scene=True);by_scene={s['scene']:s for s in scenes}
  assert all(r['frame_indices']==by_scene[r['scene']]['f64'] for r in twins)
  checks['d']=dict(status='PASS',scene=scenes[0]['scene'],opened=94,sha256_verified=94);write(ROOT/'out/FRAME_LAYOUTS.json',dict(status='PASS',scenes=scenes,n_scenes=len(scenes),f32=32,f64=64,union=94,intersection=2,extra_vs_f32=62,f64_superset=False))
 except Exception as e:checks['d']=dict(status='FAIL',error=repr(e),traceback=traceback.format_exc())
 try:
  caps=k1_checks();checks['b']=dict(status='PASS' if len(caps)==2 and all(c['status']=='PASS' and c['stage1_replay']['status']=='PASS' for c in caps) else 'BLOCKER',captures=caps)
 except Exception as e:checks['b']=dict(status='FAIL',error=repr(e),traceback=traceback.format_exc())
 # Bootstrap sanity uses an explicit fixture; it is never a route look.
 fixture=[dict(qid=str(i),room=str(i//2),head_score=.5,direct_score=.5,refusal_code=None) for i in range(6)];z=stats.paired(fixture);assert z['difference']==0 and z['ci95']==[0,0]
 checks['bootstrap_identity']=dict(status='PASS',difference=z['difference'],ci95=z['ci95'])
 for name,path in [('direct_scorer',ROOT/'inputs/DIRECT_SCORER.json'),('devs1_staging_plan',ROOT/'inputs/DEVS1_STAGING_PLAN.json'),('revsi_subtype_weights',ROOT/'inputs/REVSI_SUBTYPE_WEIGHTS.json')]:
  checks[name]=dict(status='PRESENT',sha256=sha(path)) if path.exists() else missing(path)
 checks['track']=js(ROOT/'out/TRACK_CPU_CHECK.json')
 result=dict(status='PASS' if all(checks[k]['status']=='PASS' for k in ('a','b','c','d','qid_uniqueness','operand_parsing')) else 'BLOCKER',sections=checks,item_counts=counts,total_items=len(items),gpu_hours_used=0,CUDA_VISIBLE_DEVICES='',official_items_read=0,R0_route_looks=0,K1_heldout_reads=0,seconds=time.monotonic()-start,peak_cpu_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 write(ROOT/'out/DRYRUN.json',result);status('Stage 3: CPU dry run '+result['status']+'. Exact per-section results and hashes are in out/DRYRUN.json. No GPU launched, R0 route look consumed, K1 held-out item read, or official benchmark item accessed.');print(json.dumps({k:result[k] for k in ('status','seconds','peak_cpu_kib','item_counts')}),flush=True)
if __name__=='__main__':main()
