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
  truth_order=sorted(names,key=lambda n:(truths[n],mapping[n]));orders=[truth_order]+[list(x) for x in permutations(names) if any(truths[a]<truths[b] and x.index(a)>x.index(b) for a in names for b in names)][:3];assert len(orders)==4
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
  malformed=dict(app,options=['A. '+', '.join(orders[1])]);assert programs.run(malformed,g,'B')['prediction']=='B'
  # Actual StageOne replay is attempted separately, never replaced by GT masks.
  try:
   from ground import PredictedSource
   from e2e_reader.geometry import from_npz
   gp=Path('/scratch/jjyeung/k1/run_convert_2')/key/'geometry.npz';sha(gp);stage_geo=from_npz(gp)
   stage=PredictedSource(cache,stage_geo,'today');stage_ground=Grounder(stage_geo,stage)
   stage_results=[programs.run(f,stage_ground,f['answer'],trace) for f in fixtures]
   stage_status=dict(status='PASS',results=stage_results)
  except Exception as exc:stage_status=dict(status='MISSING',error=repr(exc),traceback=traceback.format_exc())
  out.append(dict(capture=c['canonical'],split='train',status='PASS' if all(x['result']['prediction'] is not None for x in results) else 'FAIL',GT_mask_order='PASS',first_seen_diagnostics=diag,fallback='PASS',strict='PASS',option_no_match='PASS',programs=results,relative_full=full,stage1_replay=stage_status,gt_box_source='stored obb_* arrays, no fitted fixture labels'))
 return out

def main():
 import torch
 torch.set_num_threads(8)
 from scoring import Scorer
 from registration import guard_check
 from collections import Counter
 assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
 start=time.monotonic();pins();checks={};scorer=Scorer()
 assert sha(ROOT/'inputs/local/FITS.json')=='592c20480643fc8b3d45ba1a8e71cbee2998e7e02b63296f23c82c8393da9834'
 def check(name,fn):
  try:checks[name]=fn()
  except Exception as e:checks[name]=dict(status='BLOCKER',error=repr(e),traceback=traceback.format_exc())
 items=inputs.r0_items();r0=inputs.direct('R0-dev');s1=inputs.direct('dev-S1')
 def join():
  report=inputs.join_report(items,r0);assert len(r0)==1781
  assert sha(inputs.paths()['r0_items'])=='b4e278f242e143d8ee66fa527449c7e02fad753bbbb528bd0c31fb9e47aea181'
  return dict(status='PASS',joined=len(r0),types=report,identity='source_line',duplicate_qids={q:n for q,n in Counter(r['qid'] for r in items).items() if n>1})
 check('a_direct_join',join)
 def parity():
  result={}
  for split,table,n in [('R0-dev',r0,678),('dev-S1',s1,300)]:
   rr=[r for r in table.values() if r['type'] in ('object_size_estimation','object_counting')]
   bad=[r.get('source_line',r['id']) for r in rr if abs(scorer(r,r['pred'])-float(r['score']))>1e-12]
   assert len(rr)==n and not bad,(split,len(rr),bad[:5])
   result[split]=dict(rows=n,matched=n)
  return dict(status='PASS',splits=result)
 check('b_scorer_parity',parity)
 def programs_check():
  caps=k1_checks();assert len(caps)==2
  return dict(status='PASS' if all(c['status']=='PASS' and c['stage1_replay']['status']=='PASS' for c in caps) else 'BLOCKER',captures=caps)
 check('c_k1_programs',programs_check)
 def parse():
  out={}
  for split,table,expected in [('R0-dev',r0,279),('dev-S1',s1,150)]:
   rr=[r for r in table.values() if r['type']=='object_rel_distance'];assert len(rr)==expected
   n=sum(programs.parse_order(r['text'],programs.options(r).values()) is not None for r in rr)
   out[split]=dict(parsed=n,total=expected)
  assert out['R0-dev']['parsed']>=250
  sha(ROOT/'inputs/pack/designer_evidence/r0rel.py')
  return dict(status='PASS',counts=out,pattern_sha256=digest(programs.parse_order.__code__.co_consts))
 check('d_trace_parser',parse)
 def frames():
  scenes=inputs.r0_scenes(items,open_scene=True)
  write(ROOT/'out/FRAME_LAYOUTS.json',dict(status='PASS',scenes=scenes))
  return dict(status='PASS',scene=scenes[0]['scene'],opened=scenes[0]['opened_verified'],scenes=len(scenes),frames=94)
 check('e_frames',frames);check('f_one_look_guard',guard_check)
 from track_selection import check as track_selection_check
 check('track_featuriser',track_selection_check)
 result=dict(status='PASS' if all(c['status']=='PASS' for c in checks.values()) else 'BLOCKER',sections=checks,seconds=time.monotonic()-start,peak_cpu_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,torch_version=torch.__version__,threads=torch.get_num_threads(),R0_route_looks=0,K1_heldout_reads=0,official_items_read=0,gpu_hours_used=0)
 write(ROOT/'out/DRYRUN.json',result)
 status('Stage 3: specification CPU dry run '+result['status']+'. out/DRYRUN.json records each check, exact input hashes, runtime and memory. No GPU, R0 head outcome, K1 held-out outcome, or official item was read.')
 print(json.dumps({k:v for k,v in result.items() if k!='sections'}),flush=True)
 for k,v in checks.items():print(k,v['status'],v.get('error',''),flush=True)
if __name__=='__main__':main()
