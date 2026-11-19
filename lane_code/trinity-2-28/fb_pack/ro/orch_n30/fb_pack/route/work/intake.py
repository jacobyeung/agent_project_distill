import os,sys,json,copy,time,traceback
from pathlib import Path
from collections import Counter
import route as R
from route import ROOT,BASE,TREE,NAMES,INV,load,pin,write,staged,rows,lines,status,resolve
R.COMMAND=R.PREFIX+'work/intake.py'
pin(__file__);pin(ROOT/'work/route.py')
from student_pilot.p3_provenance import digest
from student_pilot.r1_persisted import scope
from student_pilot.r2_intake import intake
from student_pilot.r1_routing import compose_native
idx=load(ROOT/'out/ENVELOPE_INDEX.json');acc=load(ROOT/'out/EXCLUSION_ACCOUNTING.json')
staging=load(ROOT/'out/STAGED_INPUTS.json');R.MAPS.update(staging['paths'])
# Capture every adjacent tree data file read by the real imported functions.
read_paths=set()
def opened(event,args):
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=Path(os.fsdecode(args[0]))
  if p.is_absolute() and p.is_relative_to(TREE):read_paths.add(p)
sys.addaudithook(opened)
def tree_reads():
 for p in list(read_paths):
  if p.is_file():pin(p)
def execute(label,envpath):
 t=time.monotonic()
 try:
  with scope(R.MAPS):items,report=intake(envpath,limit=2000)
  count=len(items);del items
  tree_reads();report['elapsed_seconds']=time.monotonic()-t
  rp=write('out/intake/'+label+'.json',report)
  totals={k:sum(c[k] for c in report['counts'].values()) for k in ('seen','admitted','refused')}
  reasons=Counter()
  for c in report['counts'].values():reasons.update(c['reasons'])
  return dict(report=rp,**totals,reasons=dict(reasons),status='PASS_WITH_EXPLAINED_REFUSALS' if reasons and set(reasons)=={'excluded:eval_rooms'} else ('PASS' if not reasons else 'TREE_FIX_REQUIRED'))
 except Exception as e:
  tree_reads();rp=write('out/intake/'+label+'.json',dict(status='BLOCKED',error=str(e),exception=type(e).__name__,traceback=traceback.format_exc(),envelope=pin(envpath)))
  return dict(report=rp,status='BLOCKED',error=str(e))
result={}
for name in NAMES+['camera_B']:
 e=load(idx['slices'][name]['envelope']['path']);s=acc['slices'][name]
 first=execute(name+'_first2000',idx['slices'][name]['envelope']['path'])
 cov=load(s['coverage']['path']);shards=[];chunk=[]
 def shard(part,chunk):
  d=ROOT/f'out/shards/{name}/{part:03d}';d.mkdir(parents=True,exist_ok=True);rp=d/'rows.jsonl'
  with rp.open('w') as f:
   for line,r in chunk:f.write(line)
  sp=pin(rp);qs={r['qid'] for _,r in chunk}
  cp=write(str((d/'coverage.json').relative_to(ROOT)),dict(rows_sha256=sp['sha256'],exclusions=e['exclusions'],rows={q:cov['rows'][q] for q in qs},source_coverage=s['coverage'],source_population=s['rows']))
  se={k:v for k,v in e.items() if k not in ('inputs','command')}
  se.update(rows=staged(sp),scene_coverage=staged(cp),count=len(chunk))
  # Preserve every other envelope pin, including full-population upstream accounting.
  ep=write(str((d/'envelope.json').relative_to(ROOT)),se)
  check=execute(name+f'_shard{part:03d}',ep['path'])
  return dict(rows=sp,coverage=cp,envelope=ep,row_count=len(chunk),result=check)
 for line,r in lines(s['rows']['path']):
  chunk.append((line,r))
  if len(chunk)==2000:shards.append(shard(len(shards),chunk));chunk=[]
 if chunk:shards.append(shard(len(shards),chunk))
 all_reasons=Counter();totals=Counter()
 for sh in shards:
  check=sh['result'];all_reasons.update(check.get('reasons',{}))
  for k in ['seen','admitted','refused']:totals[k]+=check.get(k,0)
 assert sum(sh['row_count'] for sh in shards)==s['row_count']
 result[name]=dict(first2000=first,shards=shards,aggregate=dict(totals),reasons=dict(all_reasons),every_row_seen=totals['seen']==s['row_count'],status='PASS_WITH_EXPLAINED_REFUSALS' if all(sh['result']['status'] in ('PASS','PASS_WITH_EXPLAINED_REFUSALS') for sh in shards) else 'TREE_FIX_REQUIRED')
 print(name,dict(totals),dict(all_reasons),flush=True)
 write('out/INTAKE_PROGRESS.json',dict(slices=result))
write('out/INTAKE_RESULTS.json',dict(slices=result,scope='Unmodified native intake. Full envelopes use limit=2000; disjoint source-order shards each use limit=2000 and together cover every row. PNG raster bytes are not verified by this metadata intake.'))
# Actual production config, including its deferred-first-boundary shape, is tried unchanged.
cfg=load(BASE/'tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json')
base=cfg['streams']['routing']
base_inventory=load(INV/'out/FULL_INVENTORY.json')['routing_base']
staged(base_inventory['local_pin'])
# Stage actual metadata dependencies used before composition without scanning stores.
for p in [cfg['r1_training']['row_sources'],cfg['remove_files'][-1]]:staged(p)
composition={}
def compose_attempt(label,c):
 try:
  with scope(R.MAPS):v=compose_native(c,base,ROOT/'out/compose'/label)
  return dict(status='RETURNED',result=v)
 except Exception as e:
  tree_reads();return dict(status='REFUSED',error=str(e),exception=type(e).__name__,traceback=traceback.format_exc())
composition['supplied_N_config']=compose_attempt('supplied',cfg)
# A concrete first-boundary candidate binds the delivered rows and actual QID catalogs.
old=load(BASE/'tree_rebuild10_w/w21/work/build21/inputs/row_sources.json')
specs={};catalog={};routing_inputs={};row_inputs={}
for name in NAMES:
 s=acc['slices'][name];source=staged(s['rows']);row_inputs[name]=source
 specs[name]=dict(old.get(name,{}),source=source)
 catalog[name]=dict(source=source,qids=[r['qid'] for r in rows(s['rows']['path'])])
 routing_inputs[name]=staged(idx['slices'][name]['envelope'])
specpin=write('out/config/row_sources.json',specs)
catpin=write('out/config/source_membership.json',dict(schema='r1-source-catalog-v1',sources=catalog))
candidate=copy.deepcopy(cfg);candidate['r1_training'].pop('routing_slices',None)
candidate['r1_training'].update(row_sources=staged(specpin),source_membership=staged(catpin),routing_inputs=routing_inputs,row_slice_inputs=row_inputs)
candidate['extent_receipt']=load(idx['slices']['recovery']['envelope']['path'])['extent_receipt']
cp=write('out/config/FIRST_BOUNDARY_CANDIDATE.json',candidate)
composition['first_boundary_candidate']=dict(config=cp,**compose_attempt('first_boundary',candidate))
# Record the genuine full-intake host refusal independently if compose stops earlier.
try:
 with scope(R.MAPS):intake(idx['slices']['recovery']['envelope']['path'],limit=None)
except Exception as e:
 composition['full_intake_host_gate']=dict(status='REFUSED',error=str(e),exception=type(e).__name__,traceback=traceback.format_exc(),hostname=os.uname().nodename,environment={k:os.environ.get(k) for k in ['STUDENT_R2_FRAME_HOST','STUDENT_R2_LOCAL_NODE','Q_E7','Q_E8']})
else:raise AssertionError('Trinity full intake unexpectedly passed')
write('out/COMPOSE_RESULT.json',composition)
write('out/STAGED_INPUTS_FINAL.json',dict(paths=R.MAPS,files=[dict(staged_name='u/'+h,path=p,source_path=str(Path(p).resolve()),sha256=h,bytes=Path(p).stat().st_size) for h,p in sorted(R.MAPS.items())]))
status(5,'All full-envelope prefixes and all 2,000-row shards ran native intake. INTAKE_RESULTS.json lists every reason and count; COMPOSE_RESULT.json records actual composition and full-intake host refusals without spoofing.')
