#!/usr/bin/env python3
"""Check PATCH_PRIOR against authenticated native prepared rows, or an explicit test fixture.

Real mode requires the final bind_prepared config and receipt, all stream receipts,
all post-reader-filter indices/order tables, and their transitive pinned row stores.
It does not manufacture a production population or accept launch placeholders.
"""
import argparse,collections,hashlib,importlib.util,json,os,resource,sys
from pathlib import Path

N_CARD='c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8'
TARGETS=('direction','facing_pairs')
CODE_PINS={'student_pilot/r1_direction_prior.py': {'base': None, 'patched': '1e896028aac8b40b5ccd50cfde7eef4f9cb31a1ec4a089c0b96350a317bf3a30'}, 'student_pilot/r1_direction_twins.py': {'base': '6e9f1f4a1c405dbc89881881f109495d6948802e6de44312eb63253b07d9f093', 'patched': 'dce65d1fb15fce4c04045fca86dac5e67426c02d5e6b484bd9bd9b940bba6834'}, 'student_pilot/r1_loader.py': {'base': '4351861953cc559a79fec7ec8d799272a5dc5c42d90c53eb07bcf8bd7fc93595', 'patched': '8dc3ad8b145d2453ce66d91feaff882ca9845ab9cae2d26014bb371e96cbdf63'}, 'student_pilot/r1_mix.py': {'base': '76e9963e443307e064ef653f0b7b9e62450ce80cfc27558c0840141e80fe9fb1', 'patched': 'e005b44bd4f8ac2852c50a0939f75bbdc692b28127ea80772c6289da80a78f1a'}, 'student_pilot/r1_population.py': {'base': '063ed256bc4b6d797bd99c99bdaf4f11c8fe045a2606645a1dfbcef548c6c76a', 'patched': '83136841ef809f189d4aecda9804fddd73d280be404e78e5776cc86a3681c6e0'}}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

def parse_args():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--base-tree',type=Path,required=True)
 p.add_argument('--patched-tree',type=Path,required=True)
 p.add_argument('--weights',type=Path,required=True)
 p.add_argument('--output-dir',type=Path,required=True)
 mode=p.add_mutually_exclusive_group(required=True)
 mode.add_argument('--config',type=Path,help='Final native config containing preparation and r2_sampling pins')
 mode.add_argument('--fixture',type=Path,help='Explicit NONPRODUCTION fixture manifest; never grants production PASS')
 p.add_argument('--prepared-receipt',type=Path)
 p.add_argument('--receipt',action='append',default=[],metavar='STREAM=PATH')
 p.add_argument('--offset-table',action='append',default=[],metavar='STREAM=PATH')
 p.add_argument('--population',type=Path)
 p.add_argument('--indices',type=Path)
 p.add_argument('--pin',action='append',default=[],metavar='SHA256=PATH',help='Relocate exact bytes without changing a pin')
 return p.parse_args()

class Evidence:
 def __init__(self,P):self.P=P;self.inputs={};self.overrides={}
 def track(self,path,expected=None):
  path=Path(path).resolve();s=str(path)
  if s not in self.inputs:self.inputs[s]=dict(path=s,sha256=sha(path),bytes=path.stat().st_size)
  if expected is not None and self.inputs[s]['sha256']!=expected:raise ValueError('HASH_MISMATCH:'+s)
  return path
 def pin(self,path):
  path=self.track(path);return {k:self.inputs[str(path)][k] for k in ('path','sha256')}
 def relocate(self,pin,path):
  self.track(path,pin['sha256']);self.overrides[pin['sha256']]=Path(path)
 def pinned(self,pin):
  if not isinstance(pin,dict) or set(pin)!={'path','sha256'}:raise ValueError('Exact path/SHA256 pin required')
  path=self.overrides.get(pin['sha256'],Path(pin['path']))
  if not Path(path).is_file():raise FileNotFoundError('MISSING:'+str(path)+'; sha256='+pin['sha256'])
  return self.track(path,pin['sha256'])
 def code(self,trees):
  for m in list(sys.modules.values()):
   path=getattr(m,'__file__',None)
   if path and any(Path(path).is_relative_to(t) for t in trees) and Path(path).is_file():self.track(path)
 def write(self,path,value):
  path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
  value=dict(value,inputs=list(self.inputs.values()))
  with path.open('x') as f:f.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
  return self.pin(path)

def key_values(items):
 result={}
 for item in items:
  key,value=item.split('=',1)
  if key in result:raise ValueError('Duplicate override:'+key)
  result[key]=Path(value)
 return result

def identity_gate(reader,binding,weights,base_tree,out,E,cfg):
 from student_pilot import p3_provenance as P,r1_mix as M
 from student_pilot.r1_training import STREAMS
 from student_pilot.r1_population import Membership
 from student_pilot.r1_direction_prior import Prior
 from student_pilot.r1_direction_twins import dimensions
 from student_pilot.r1_loader import DirectionAudit
 from student_pilot.r1_counting import admit
 card,indices,allocation=M.validate_binding(binding)
 if binding['card']['sha256']!=N_CARD or card['seed']!=17:raise ValueError('N_CARD_OR_SEED_MISMATCH')
 pop=P.load(E.pinned(binding['population']))
 membership=Membership(pop['source_membership'],minimal=cfg.get('r1_training',{}).get('routing_slices')=='deferred_first_boundary')
 groups={c['type']:[] for c in card['cells']};streams={c['type']:c['stream'] for c in card['cells']}
 counts={s:reader.count(s) for s in STREAMS};prior=Prior(weights)
 rows={};metadata={};owner={};seen_rows=set()
 row_digests={k:hashlib.sha256() for k in groups}
 for stream in STREAMS:
  for i in range(counts[stream]):
   row,_=reader.row(stream,i);kind=membership.cell(row,stream)
   identity=(stream,row['qid'])
   if identity in seen_rows:raise ValueError('DUPLICATE_PREPARED_ROW:'+stream+':'+row['qid'])
   seen_rows.add(identity)
   if streams.get(kind)!=stream:raise ValueError('UNASSIGNED_CELL:'+kind)
   if card.get('counting_admission')=='procedure_only_v1':admit(row,kind)
   groups[kind].append(i);owner[stream,i]=kind;prior.observe(row,stream,kind,i)
   row_digests[kind].update(P.encoded([i,row['qid'],P.digest(row)]).encode()+b'\n')
   if kind in TARGETS:
    rows[i]=row;metadata[i]=dimensions(row)
 for k,g in groups.items():
  if g!=indices['cells'][k] or len(g)!=pop['counts'][k]:raise ValueError('PREPARED_POPULATION_MISMATCH:'+k)
 absent={k:v for k,v in binding.items() if k!='direction_prior'}
 enabled=dict(absent,direction_prior=prior.bind(absent,out/'direction_prior.json'))
 E.track(enabled['direction_prior']['path'])
 spec=importlib.util.spec_from_file_location('student_pilot.prior_gate_base_mix',base_tree/'student_pilot/r1_mix.py')
 B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);E.track(base_tree/'student_pilot/r1_mix.py')
 plans={name:list(mod.plans(b,counts,card['steps'])) for name,mod,b in [('base',B,absent),('absent',M,absent),('enabled',M,enabled)]}
 sequences={label:{k:[] for k in groups} for label in plans}
 audits={};max_repeats={}
 for label,value in plans.items():
  audit={k:DirectionAudit() for k in TARGETS};repeats=collections.Counter()
  for kind in TARGETS:
   for i in groups[kind]:audit[kind].eligible(rows[i])
  for plan in value:
   for stream,offsets in plan:
    for i in offsets:
     kind=owner[stream,i];sequences[label][kind].append(i);repeats[stream,i]+=1
     if kind in TARGETS:audit[kind].observe(rows[i])
  audits[label]={k:a.result() for k,a in audit.items()};max_repeats[label]=max(repeats.values(),default=0)
 changed=collections.Counter();stable=collections.Counter();position_errors={k:[] for k in groups}
 for old,new in zip(plans['base'],plans['enabled'],strict=True):
  for (s,oi),(t,ni) in zip(old,new,strict=True):
   if s!=t or len(oi)!=len(ni):raise ValueError('PLAN_STRUCTURE_CHANGED')
   for a,b in zip(oi,ni,strict=True):
    k=owner[s,a]
    if owner[t,b]!=k:position_errors[k].append('CELL_CHANGED');continue
    if k in TARGETS and metadata[a][:2]==('toward','hard'):
     if metadata[b][:2]!=('toward','hard'):position_errors[k].append('TARGET_SLOT_CHANGED')
     changed[k]+=a!=b
    elif a!=b:position_errors[k].append('NON_TARGET_POSITION_CHANGED')
    else:stable[k]+=1
 result={}
 for k in groups:
  checks=dict(field_absent_bytes_identical=P.encoded(sequences['base'][k])==P.encoded(sequences['absent'][k]),
              same_draw_count=len(sequences['base'][k])==len(sequences['enabled'][k]),
              same_non_target_positions=not position_errors[k],
              four_draw_cap=max(collections.Counter(sequences['enabled'][k]).values(),default=0)<=4)
  if k not in TARGETS:checks['field_present_bytes_identical']=P.encoded(sequences['base'][k])==P.encoded(sequences['enabled'][k])
  else:
   before={(r['clause'],r['difficulty']):r for r in audits['base'][k]['answer_shares']}
   after={(r['clause'],r['difficulty']):r for r in audits['enabled'][k]['answer_shares']}
   checks['non_target_clause_difficulty_unchanged']=set(before)==set(after) and all(v==after.get(g) for g,v in before.items() if g!=('toward','hard'))
   b=before.get(('toward','hard'));a=after.get(('toward','hard'))
   checks['toward_hard_count_unchanged']=bool(a and b and a['draws']==b['draws'])
   checks['toward_hard_half_back_within_one_draw']=bool(a and abs(2*a['back']['draws']-a['draws'])<=1)
   checks['toward_hard_draws_changed']=changed[k]>0
  result[k]=dict(status='PASS' if all(checks.values()) else 'FAIL',stream=streams[k],eligible=len(groups[k]),draws=len(sequences['base'][k]),checks=checks,
   sequence_sha256={l:P.digest(sequences[l][k]) for l in sequences},ordered_row_identity_sha256=row_digests[k].hexdigest(),changed_toward_hard_draws=changed[k],unchanged_other_positions=stable[k],position_errors=position_errors[k][:10])
 checks=dict(full_absent_plan_bytes_identical=P.encoded(plans['base'])==P.encoded(plans['absent']),max_four_draws=all(v<=4 for v in max_repeats.values()),
  resume_identical=plans['enabled'][723:]==list(M.plans(enabled,counts,1000,start_step=723)))
 return dict(status='PASS' if all(checks.values()) and all(v['status']=='PASS' for v in result.values()) else 'FAIL',cells=result,global_checks=checks,
  seed=card['seed'],steps=card['steps'],allocation=allocation,stream_counts=counts,max_repeats=max_repeats,loader_audits=audits,
  plan_sha256={l:P.digest(v) for l,v in plans.items()},binding=enabled)

def main():
 args=parse_args();args.output_dir=args.output_dir.resolve();args.output_dir.mkdir(parents=True,exist_ok=True)
 for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='16'
 os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1');sys.dont_write_bytecode=True
 for key in ('XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR','CONDA_PKGS_DIRS','TORCH_HOME','TMPDIR'):
  path=args.output_dir/key;path.mkdir(exist_ok=True);os.environ[key]=str(path)
 resource.setrlimit(resource.RLIMIT_AS,(36*1024**3,36*1024**3))
 sys.path.insert(0,str(args.patched_tree.resolve()))
 from student_pilot import p3_provenance as P
 E=Evidence(P);E.track(__file__);P.pinned=E.pinned
 for h,path in key_values(args.pin).items():E.relocate(dict(sha256=h),path)
 reader=None;card=None;scope='FIXTURE_ONLY_NOT_PRODUCTION' if args.fixture else 'REAL_PREPARED'
 try:
  for name,pins in CODE_PINS.items():
   if pins['base']:E.track(args.base_tree/name,pins['base'])
   E.track(args.patched_tree/name,pins['patched'])
  E.track(args.patched_tree/'student_pilot/r0_scenes.json','f7c458176426e22a13e47908b03abd2c6f5939d3e48eb7c24e7eba45b75ad479')
  weights=E.pin(args.weights)
  if args.fixture:
   fixture=P.load(E.track(args.fixture))
   if fixture.get('scope')!='FIXTURE_ONLY_NOT_PRODUCTION':raise ValueError('EXPLICIT_FIXTURE_LABEL_REQUIRED')
   E.pinned(fixture['source_reconstruction'])
   for pin in fixture['inputs']:E.pinned({k:pin[k] for k in ('path','sha256')})
   args.config=E.pinned(fixture['native_config'])
   args.prepared_receipt=E.pinned(fixture['prepared_receipt'])
   args.receipt=[k+'='+v['path'] for k,v in fixture['stream_receipts'].items()]
   args.offset_table=[k+'='+v['path'] for k,v in fixture['offset_tables'].items()]
  if not args.prepared_receipt:raise ValueError('--prepared-receipt required in real mode')
  cfg=P.load(E.track(args.config));binding=cfg['r2_sampling']
  card=P.load(E.pinned(binding['card']))
  E.relocate(cfg['preparation'],args.prepared_receipt);receipt=P.load(E.pinned(cfg['preparation']))
  if receipt.get('schema')!='c1-preparation-v1' or receipt.get('r2_sampling')!=binding:raise ValueError('PREPARATION_BINDING_MISMATCH')
  if receipt.get('r1_training')!=cfg.get('r1_training'):raise ValueError('PREPARATION_R1_INPUTS_MISMATCH')
  if cfg.get('r1_training',{}).get('row_plan_sha256')!=P.digest(binding):raise ValueError('PREPARATION_PLAN_DIGEST_MISMATCH')
  if not args.fixture and (cfg.get('scope')=='FIXTURE_ONLY_NOT_PRODUCTION' or receipt.get('scope')=='FIXTURE_ONLY_NOT_PRODUCTION'):
   raise ValueError('FIXTURE_CANNOT_BE_USED_AS_REAL_PREPARATION')
  if args.population:E.relocate(binding['population'],args.population)
  if args.indices:E.relocate(binding['indices'],args.indices)
  receipts=key_values(args.receipt);offsets=key_values(args.offset_table)
  if set(receipts)!={'pointing','pose','routing','vqa'} or set(offsets)!=set(receipts):raise ValueError('All four --receipt and --offset-table arguments required')
  for stream in receipts:
   value=receipt['streams'][stream];E.relocate(value['receipt'],receipts[stream]);source_receipt=P.load(E.pinned(value['receipt']))
   if value.get('kind')=='mix':
    if source_receipt.get('schema')!='c1-pose-mix-v1' or len(source_receipt['sources'])!=len(value['sources']):raise ValueError('POSE_SOURCE_COUNT_MISMATCH')
    source_limits=[]
    for original,part in zip(source_receipt['sources'],value['sources'],strict=True):
     if original.get('kind')!='rows' or part.get('kind')!='rows':raise ValueError('R1_POPULATION_POSE_SOURCE_NOT_ROWS')
     if original['receipt']['sha256']!=part['receipt']['sha256']:raise ValueError('POSE_SOURCE_RECEIPT_MISMATCH')
     child=P.load(E.pinned(part['receipt']))
     if child['database']['sha256']!=part['database']['sha256']:raise ValueError('POSE_SOURCE_DATABASE_MISMATCH')
     source_limits.append(child['count'])
   elif source_receipt['database']['sha256']!=value['database']['sha256']:raise ValueError('SOURCE_DATABASE_MISMATCH:'+stream)
   key='order' if value.get('kind')=='mix' else 'indices'
   if key not in value:raise ValueError('MISSING:receipt.streams.'+stream+'.'+key)
   E.relocate(value[key],offsets[stream]);table=P.load(E.pinned(value[key]))
   if len(table)!=value['count']:raise ValueError('OFFSET_COUNT_MISMATCH:'+stream)
   if value.get('kind')=='mix':
    if any(not isinstance(v,list) or len(v)!=2 or any(type(i)!=int or i<0 for i in v) for v in table):raise ValueError('OFFSET_TYPE_MISMATCH:'+stream)
    keys=[tuple(v) for v in table]
    if any(part>=len(source_limits) or i>=source_limits[part] for part,i in keys):raise ValueError('OFFSET_OUT_OF_RANGE:'+stream)
   else:
    if any(type(i)!=int or i<0 for i in table):raise ValueError('OFFSET_TYPE_MISMATCH:'+stream)
    keys=table
    if any(i>=source_receipt['count'] for i in table):raise ValueError('OFFSET_OUT_OF_RANGE:'+stream)
   if len(keys)!=len(set(keys)):raise ValueError('DUPLICATE_SOURCE_OFFSET:'+stream)
  from student_pilot.r1_population import scene_receipt
  scene_receipt(receipt)
  from student_pilot import carrier_c1_run as C,c1_pose_mix as PM
  import sqlite3,torch
  torch.set_num_threads(16)
  # Native connect() does not authenticate the database. Authenticate every opened
  # store and relocate exact bytes here; retain all native row/filter logic.
  def connect(pin):return sqlite3.connect(E.pinned(pin).as_uri()+'?mode=ro&immutable=1',uri=True)
  C.connect=connect;PM.connect=connect
  reader=C.Rows(receipt,None)
  if card is None:card=P.load(E.pinned(binding['card']))
  result=identity_gate(reader,binding,weights,args.base_tree.resolve(),args.output_dir,E,cfg)
 except Exception as exc:
  result=dict(status='FAIL',error=type(exc).__name__+':'+str(exc),cells={c['type']:dict(status='FAIL',reason=str(exc)) for c in (card or {}).get('cells',[])})
 finally:
  if reader is not None:reader.close()
 result.update(scope=scope,production_gate=result['status'] if scope=='REAL_PREPARED' else 'MISSING: fixture cannot establish production identity',command=' '.join(sys.argv))
 E.code([args.patched_tree.resolve(),args.base_tree.resolve()]);E.write(args.output_dir/'RESULT.json',result)
 for name,v in result.get('cells',{}).items():print(v['status']+' '+name)
 print(result['status']+' '+scope+(': '+result['error'] if 'error' in result else ''))
 return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
