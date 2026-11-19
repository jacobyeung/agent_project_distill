"""Recompute reviewer offsets from pinned rows and exercise the production comparator.

This is a labelled NONPRODUCTION component test. It does not bypass launch checks
to issue a real-mode PASS. The CLI test separately checks the real-mode refusals.
"""
import copy,hashlib,importlib.util,json,os,resource,shlex,sqlite3,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];FB=W.parent;OLD=FB/'prior2b'
sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_AS,(36*1024**3,36*1024**3))
sys.path.insert(0,str(OLD/'work/sealed_new'))
spec=importlib.util.spec_from_file_location('checker',W/'out/prove_on_prepared.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
E=G.Evidence();E.track(__file__);E.track(G.__file__)
from student_pilot import p3_provenance as P
P.pinned=E.pinned
from student_pilot.r1_direction_prior import Prior
from student_pilot.r1_population import Membership
from student_pilot import r1_mix as M
import torch
torch.set_num_threads(16)
ROOT=W/'work/offset_tests';ROOT.mkdir(parents=True,exist_ok=True)
REVIEW=FB/'priorrev/work/s5/new_enabled_r2'
replay=P.load(E.track(REVIEW/'REPLAY.json'))
binding=replay['binding'];weights=E.pin(FB/'prior2/out/TOWARD_HARD_WEIGHTS.json')
prior=Prior(weights)
pop=P.load(E.pinned(binding['population']));indices=P.load(E.pinned(binding['indices']))
membership=Membership(pop['source_membership'],minimal=True)
db=E.track(OLD/'work/source/eligible_vqa.sqlite')
con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
try:
 for i,raw in con.execute('SELECT i,row FROM rows ORDER BY i'):
  row=json.loads(raw);prior.observe(row,'vqa',membership.cell(row,'vqa'),i)
finally:con.close()
absent={k:v for k,v in binding.items() if k!='direction_prior'}
fresh=prior.bind(absent,ROOT/'recomputed.json')
v=P.load(fresh['path']);v['inputs']+=list(E.inputs.values());Path(fresh['path']).write_text(P.encoded(v)+'\n')
fresh=E.pin(fresh['path'])
cfg=dict(r1_training=dict(direction_prior=weights),r2_sampling=binding)
records=[]
def check(name,fn,error=None):
 try:fn();actual=None
 except Exception as exc:actual=type(exc).__name__+':'+str(exc)
 ok=(actual is None) if error is None else (actual is not None and error in actual)
 records.append(dict(name=name,status='PASS' if ok else 'FAIL',expected_error=error,actual_error=actual))
 print(name,records[-1]['status'],actual or '',flush=True)

check('genuine_recomputed_offsets',lambda:G.production_offsets(binding,fresh,weights,E))
check('genuine_prior_config',lambda:G.require_prior_config(cfg,binding,weights,E))
for suffix,error in [('swap','cells'),('nontarget','cells'),('card','card_sha256'),('pop','population_sha256'),
                     ('drop','cells'),('dup','cells'),('outside','cells'),('policy','policy.sha256'),('policysha','policy.sha256')]:
 tamper=E.pin(REVIEW/('tamper_'+suffix+'.json'))
 b=dict(binding,direction_prior=tamper)
 check('review_'+suffix,lambda b=b:G.production_offsets(b,fresh,weights,E),'PRODUCTION_PRIOR_OFFSETS_MISMATCH:'+error)
bad=dict(binding,direction_prior=dict(binding['direction_prior'],path=str(REVIEW/'tamper_bytes.json')))
check('review_bytes_changed_pin_kept',lambda:G.production_offsets(bad,fresh,weights,E),'HASH_MISMATCH')

for field in ('indices_sha256','schema'):
 value=P.load(E.pinned(binding['direction_prior']));value[field]='tampered'
 path=ROOT/(field+'.json');E.write(path,value);b=dict(binding,direction_prior=E.pin(path))
 check(field,lambda b=b:G.production_offsets(b,fresh,weights,E),'PRODUCTION_PRIOR_OFFSETS_MISMATCH:'+field)

check('missing_training_field',lambda:G.require_prior_config({},binding,weights,E),'MISSING:r1_training.direction_prior')
check('missing_sampling_field',lambda:G.require_prior_config(cfg,absent,weights,E),'MISSING:r2_sampling.direction_prior')
bad=copy.deepcopy(cfg);bad['r1_training']['direction_prior']=dict(weights,sha256='0'*64)
check('config_weight_sha_mismatch',lambda:G.require_prior_config(bad,binding,weights,E),'PRODUCTION_PRIOR_WEIGHTS_MISMATCH')

# Paths may differ for identical bytes. Membership order must never differ.
value=P.load(E.pinned(binding['direction_prior']))
alternate=ROOT/'weights.json';alternate.write_bytes(Path(weights['path']).read_bytes())
value['policy']=E.pin(alternate);relocated=ROOT/'relocated.json';E.write(relocated,value)
check('identical_policy_bytes_relocated',lambda:G.production_offsets(dict(binding,direction_prior=E.pin(relocated)),fresh,weights,E))
value['cells']['direction']['front'].reverse();ordered=ROOT/'reordered.json';E.write(ordered,value)
check('offset_order_changed',lambda:G.production_offsets(dict(binding,direction_prior=E.pin(ordered)),fresh,weights,E),
      'PRODUCTION_PRIOR_OFFSETS_MISMATCH:cells')

# The production sampler accepts these two original probes: the comparator must reject them.
counts={s:sum(pop['counts'][c['type']] for c in P.load(E.pinned(binding['card']))['cells'] if c['stream']==s)
        for s in ('pose','vqa','routing','pointing')}
for suffix in ('swap','nontarget'):
 b=dict(binding,direction_prior=E.pin(REVIEW/('tamper_'+suffix+'.json')))
 check('native_accepts_review_'+suffix,lambda b=b:list(M.plans(b,counts,1000,start_step=999)))

launch=P.load(E.track(W/'out/N_LAUNCH_CONFIG.json',G.N_LAUNCH))
check('launch_metadata_positive',lambda:G.launch_metadata(launch,launch))
for field in ('store_hashes','store_parameter','mix','v7_k1_removal','room_authority','direction_twins'):
 bad=copy.deepcopy(launch);bad['r1_training'].pop(field)
 check('launch_missing_'+field,lambda bad=bad:G.launch_metadata(bad,launch),'REAL_LAUNCH_')
original_fixture=P.load(E.track(OLD/'work/mix_fixture/receipt.json'))
check('synthetic_databases_with_launch_metadata',lambda:G.launch_identity(launch,original_fixture,launch,E),
      'REAL_SOURCE_DATABASE_MISMATCH:pointing')
# Test each source role without inventing stores: earlier roles use the declared pins only;
# the function must reject the next synthetic hash before any database is opened.
for role in ('pose','routing'):
 receipt=copy.deepcopy(original_fixture)
 receipt['streams']['pointing']['database']['sha256']=G.SOURCE_DATABASES['pointing'][0]
 if role=='routing':
  for source,h in zip(receipt['streams']['pose']['sources'],G.SOURCE_DATABASES['pose']):source['database']['sha256']=h
 check('synthetic_'+role+'_database',lambda receipt=receipt:G.launch_identity(launch,receipt,launch,E),
       'REAL_SOURCE_DATABASE_MISMATCH:'+role)

E.code([OLD/'work/sealed_new'])
E.write(W/'out/OFFSET_TESTS.json',dict(status='PASS' if all(r['status']=='PASS' for r in records) else 'FAIL',
    scope='FIXTURE_ONLY_NOT_PRODUCTION',production_gate='MISSING',records=records,
    recomputed_offsets=fresh,review_binding=binding,command=shlex.join(sys.argv)))
raise SystemExit(0 if all(r['status']=='PASS' for r in records) else 1)
