#!/usr/bin/env python3
"""Check PATCH_PRIOR against authenticated native prepared rows, or an explicit test fixture.

Real mode requires the final bind_prepared config and receipt, all stream receipts,
all post-reader-filter indices/order tables, and their transitive pinned row stores.
It does not manufacture a production population or accept launch placeholders.
"""
import argparse,collections,hashlib,importlib.util,json,os,resource,shlex,sys
from pathlib import Path

N_CARD='c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8'
N_LAUNCH='0e78d7f86f85cf6090db94bb4916fbd1c57b9fa2aff04dd0a8428a414a4a5f5f'
N_VQA='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
# Exact inventories: N's sealed tree, or its authenticated HOST24J update, plus PATCH_PRIOR.
SEALED_PAIRS={
 '31c8f6b8c28c8213ff78a65df6f0fce23a99c24f56945359dade50d394a6236c':
 '57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7',
 '35a4753f97906fcf7d84d3e9dea4d2f837f5bfa5a274e261aa7c7530f9597f25':
 '189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'}
SOURCE_DATABASES={
 'pointing':('c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938',),
 'pose':('b32359ce256a567912d6436fac95dcab78bcef3bb2e1154cabdca57bacdc5320',
         '0b95850a2dec57ec6702ca72cd198eb5afdcdcdd5f711a76a878104e30ec3571'),
 'routing':('4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84',),
 'routing_r16':('3d1d2d05bc8d3fed3048618da0c25b330f693e6394c6e2564c3007d64c050001',)}
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
 p.add_argument('--launch-config',type=Path,default=Path(__file__).with_name('N_LAUNCH_CONFIG.json'),
                help='N launch config, authenticated against the fixed 0e78d7f8 pin')
 p.add_argument('--pin',action='append',default=[],metavar='SHA256=PATH',help='Relocate exact bytes without changing a pin')
 return p.parse_args()

class Evidence:
 def __init__(self,P=None):self.P=P;self.inputs={};self.overrides={}
 def track(self,path,expected=None):
  path=Path(path).resolve();s=str(path)
  if not path.is_file():raise FileNotFoundError('MISSING:'+s+('; sha256='+expected if expected else ''))
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
  # The provided local mirror changes location only; every byte retains its pin.
  if not Path(path).is_file():
   for prefix,target in (('/scratch/jjyeung/orch_n30/','/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/'),
                         ('/scratch/jjyeung/n30_mirror/','/scratch/jjyeung/orch_n30/fb_pack/ro/n30_mirror/')):
    if str(path).startswith(prefix):
     candidate=Path(target+str(path)[len(prefix):])
     if candidate.is_file():path=candidate;break
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

def canonical(value):
 return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)

def tree_inventory(root,E):
 """Authenticate all source bytes before importing any project code."""
 root=Path(root).resolve();files={}
 if not root.is_dir():raise FileNotFoundError('MISSING:'+str(root))
 for directory,dirs,names in os.walk(root):
  dirs[:]=sorted(n for n in dirs if n not in ('.git','__pycache__','artifacts'))
  if any((Path(directory)/n).is_symlink() for n in dirs+names):
   raise ValueError('REAL_SOURCE_TREE_LINK:'+str(directory))
  for name in sorted(names):
   path=Path(directory)/name
   if path.stat().st_size>16_000_000:raise ValueError('REAL_SOURCE_TREE_NON_TINY:'+str(path))
   files[str(path.relative_to(root))]=E.pin(path)['sha256']
 return files,hashlib.sha256(canonical(files).encode()).hexdigest()

def require_prior_config(cfg,binding,weights,E):
 """The weights parameter and the sampler offsets are distinct native pins."""
 field=cfg.get('r1_training',{}).get('direction_prior')
 if not field:raise ValueError('MISSING:r1_training.direction_prior')
 if field.get('sha256')!=weights['sha256']:raise ValueError('PRODUCTION_PRIOR_WEIGHTS_MISMATCH')
 E.pinned(field)
 if not binding.get('direction_prior'):raise ValueError('MISSING:r2_sampling.direction_prior')
 E.pinned(binding['direction_prior'])

def production_offsets(binding,recomputed,weights,E):
 """Compare ordered offsets, including their semantic side, before running training's plan."""
 from student_pilot import p3_provenance as P
 actual=P.load(E.pinned(binding['direction_prior']))
 expected=P.load(E.pinned(recomputed))
 for key in ('schema','cells','card_sha256','population_sha256','indices_sha256'):
  if key not in actual or canonical(actual[key])!=canonical(expected[key]):
   raise ValueError('PRODUCTION_PRIOR_OFFSETS_MISMATCH:'+key)
 if actual.get('policy',{}).get('sha256')!=weights['sha256']:
  raise ValueError('PRODUCTION_PRIOR_OFFSETS_MISMATCH:policy.sha256')
 E.pinned(actual['policy'])
 return actual

def launch_metadata(cfg,launch):
 """Check the immutable launch lineage before opening large stores."""
 value=cfg.get('r1_training',{});source=launch['r1_training']
 stores=value.get('store_hashes')
 # bind_handover may replace the launch map with all final stream identities.
 if not isinstance(stores,dict) or 'vqa' not in stores:
  raise ValueError('REAL_LAUNCH_STORE_HASHES_MISMATCH:vqa')
 if stores!=source['store_hashes'] and set(stores)!={'pose','vqa','routing','pointing'}:
  raise ValueError('REAL_LAUNCH_STORE_HASHES_MISMATCH')
 for key in ('store_parameter','mix','v7_k1_removal'):
  if value.get(key,{}).get('sha256')!=source[key]['sha256']:
   raise ValueError('REAL_LAUNCH_PIN_MISMATCH:r1_training.'+key)
 authority=value.get('room_authority',{})
 if set(authority)!=set(source['room_authority']):raise ValueError('REAL_LAUNCH_PIN_MISMATCH:room_authority')
 for key,pin in source['room_authority'].items():
  if authority[key].get('sha256')!=pin['sha256']:raise ValueError('REAL_LAUNCH_PIN_MISMATCH:room_authority.'+key)
 if value.get('routing_slices')!=source['routing_slices']:
  raise ValueError('REAL_LAUNCH_ROUTING_SLICES_MISMATCH')
 spec=value.get('direction_twins',{})
 for key in ('source_database','rows','binding','aliases'):
  if spec.get(key,{}).get('sha256')!=source['direction_twins'][key]['sha256']:
   raise ValueError('REAL_LAUNCH_PIN_MISMATCH:direction_twins.'+key)
 if source['store_hashes'].get('vqa')!=N_VQA:raise ValueError('REAL_LAUNCH_VQA_PIN_MISMATCH')
 return stores

def launch_identity(cfg,receipt,launch,E):
 """Reject synthetic stores even when all labels and mutable receipts are rewritten."""
 from student_pilot import p3_provenance as P
 stores=launch_metadata(cfg,launch)
 value=cfg['r1_training'];source=launch['r1_training'];spec=value['direction_twins']
 streams=receipt.get('streams',{})
 for stream,expected in SOURCE_DATABASES.items():
  if stream=='routing_r16':continue
  entry=streams.get(stream,{})
  pins=[s.get('database',{}) for s in entry.get('sources',[])] if stream=='pose' else [entry.get('database',{})]
  if tuple(p.get('sha256') for p in pins)!=expected:
   raise ValueError('REAL_SOURCE_DATABASE_MISMATCH:'+stream)
  if stream=='pose' and (entry.get('kind')!='mix' or any(s.get('kind')!='rows' for s in entry['sources'])):
   raise ValueError('REAL_SOURCE_KIND_MISMATCH:pose')
 for stream,entry in streams.items():
  if cfg.get('streams',{}).get(stream,{}).get('sha256')!=entry.get('receipt',{}).get('sha256'):
   raise ValueError('REAL_CONFIG_STREAM_RECEIPT_MISMATCH:'+stream)
 # Pin the launch source receipt and its database, not a reconstructed row store.
 source_receipt=P.load(E.pinned(value['store_parameter']))
 if source_receipt.get('database',{}).get('sha256')!=N_VQA:
  raise ValueError('REAL_SOURCE_DATABASE_MISMATCH:vqa_source')
 E.pinned(source_receipt['database']);E.pinned(spec['source_database'])
 for stream in ('pointing','routing'):
  E.pinned(streams[stream]['database'])
 for part in streams['pose']['sources']:E.pinned(part['database'])
 routing=P.load(E.pinned(streams['routing']['receipt']))
 r16=routing.get('source_scene_exclusions',{}).get('expected',{}).get('r16',{}).get('population',{}).get('database',{})
 if r16.get('sha256')!=SOURCE_DATABASES['routing_r16'][0]:
  raise ValueError('REAL_SOURCE_DATABASE_MISMATCH:routing_r16')
 E.pinned(r16)
 actual=streams['vqa'].get('database',{})
 E.pinned(actual)
 # The native verifier compares every base and appended row with authenticated inputs.
 from student_pilot.r1_direction_twins import verify_augmented
 verify_augmented(cfg,actual)
 if stores!=source['store_hashes']:
  from student_pilot.r1_training import target_identity
  if stores!=target_identity(cfg)['stores']:raise ValueError('REAL_LAUNCH_STORE_HASHES_MISMATCH:handover')
 return dict(launch_sha256=N_LAUNCH,vqa_source_sha256=N_VQA,store_hashes=stores,
             source_databases=SOURCE_DATABASES,augmented_database=actual)

def sealed_preparation(cfg,receipt,files,tree_sha,E):
 from student_pilot import p3_provenance as P,source_seal as S
 from student_pilot.carrier_c1_run import identity
 if not cfg.get('code'):raise ValueError('MISSING:config.code')
 seal=P.load(E.pinned(cfg['code']))
 if (seal.get('schema')!=S.SCHEMA or seal.get('tree_sha256')!=tree_sha
     or seal.get('commit')!='sha256:'+tree_sha or seal.get('files')!=files):
  raise ValueError('REAL_PATCHED_SOURCE_SEAL_MISMATCH')
 if receipt.get('config_sha256')!=identity(cfg):raise ValueError('REAL_PREPARATION_CONFIG_IDENTITY_MISMATCH')
 if receipt.get('source_seal')!=S.binding(seal,receipt['config_sha256']):
  raise ValueError('REAL_PREPARATION_SOURCE_SEAL_MISMATCH')
 E.pinned(seal['archive']);S.check_archive(seal['archive'],files)
 return dict(tree_sha256=tree_sha,code=cfg['code'],archive=seal['archive'])

def identity_gate(reader,binding,weights,base_tree,out,E,cfg,*,real=False):
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
 recomputed=prior.bind(absent,out/'direction_prior.json')
 # Preserve the native fields and record the row stores and checker that produced them.
 value=P.load(recomputed['path']);value['inputs']+=list(E.inputs.values())
 Path(recomputed['path']).write_text(canonical(value)+'\n')
 recomputed=E.pin(recomputed['path'])
 # Existing labelled fixtures may omit the field. Any supplied field is checked,
 # and real mode always runs the unchanged production binding.
 if real or 'direction_prior' in binding or 'direction_prior' in cfg.get('r1_training',{}):
  require_prior_config(cfg,binding,weights,E)
  production_offsets(binding,recomputed,weights,E)
  enabled=binding
 else:enabled=dict(absent,direction_prior=recomputed)
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
  plan_sha256={l:P.digest(v) for l,v in plans.items()},binding=enabled,
  enabled_plan_source='production_binding' if enabled is binding else 'fixture_recomputed_binding',
  recomputed_offsets=recomputed)

def main():
 args=parse_args();args.output_dir=args.output_dir.resolve();args.output_dir.mkdir(parents=True,exist_ok=True)
 for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='16'
 os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1');sys.dont_write_bytecode=True
 for key in ('XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR','CONDA_PKGS_DIRS','TORCH_HOME','TMPDIR'):
  path=args.output_dir/key;path.mkdir(exist_ok=True);os.environ[key]=str(path)
 resource.setrlimit(resource.RLIMIT_AS,(36*1024**3,36*1024**3))
 E=Evidence();E.track(__file__)
 reader=None;card=None;scope='FIXTURE_ONLY_NOT_PRODUCTION' if args.fixture else 'REAL_PREPARED'
 try:
  for h,path in key_values(args.pin).items():E.relocate(dict(sha256=h),path)
  if not args.fixture:
   files,tree_sha=tree_inventory(args.patched_tree,E)
   if tree_sha not in SEALED_PAIRS:raise ValueError('REAL_PATCHED_TREE_PIN_MISMATCH:'+tree_sha)
   _,base_sha=tree_inventory(args.base_tree,E)
   if base_sha!=SEALED_PAIRS[tree_sha]:raise ValueError('REAL_BASE_TREE_PIN_MISMATCH:'+base_sha)
  sys.path.insert(0,str(args.patched_tree.resolve()))
  from student_pilot import p3_provenance as P
  P.pinned=E.pinned
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
  if not args.fixture:
   launch=P.load(E.track(args.launch_config,N_LAUNCH))
   # Identity checks precede field checks so an unlabelled fixture receives the
   # specific lineage error even if it also lacks the production prior fields.
   launch_metadata(cfg,launch)
   require_prior_config(cfg,binding,weights,E)
   for stream,path in key_values(args.receipt).items():
    if stream in receipt['streams']:E.relocate(receipt['streams'][stream]['receipt'],path)
   sealed=sealed_preparation(cfg,receipt,files,tree_sha,E)
   identities=launch_identity(cfg,receipt,launch,E)
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
  result=identity_gate(reader,binding,weights,args.base_tree.resolve(),args.output_dir,E,cfg,real=not args.fixture)
  if not args.fixture:result.update(launch_identity=identities,source_seal=sealed)
 except Exception as exc:
  result=dict(status='FAIL',error=type(exc).__name__+':'+str(exc),cells={c['type']:dict(status='FAIL',reason=str(exc)) for c in (card or {}).get('cells',[])})
 finally:
  if reader is not None:reader.close()
 result.update(scope=scope,production_gate=('MISSING' if 'MISSING:' in result.get('error','') else result['status']) if scope=='REAL_PREPARED' else 'MISSING: fixture cannot establish production identity',command=shlex.join(sys.argv))
 E.code([args.patched_tree.resolve(),args.base_tree.resolve()]);E.write(args.output_dir/'RESULT.json',result)
 for name,v in result.get('cells',{}).items():print(v['status']+' '+name)
 print(result['status']+' '+scope+(': '+result['error'] if 'error' in result else ''))
 return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
