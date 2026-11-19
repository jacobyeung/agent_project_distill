"""Use the retained native capacity stores; repeat admission and all-rank forward."""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack,nullcontext
from unittest.mock import patch
import sys,os,math,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';T=L/'work/tree_r1';O=L/'work/build24/proofs/capacity';F=D/'proofs/capacity';F.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(T)]
import native24 as N
from student_pilot import r1_persisted as P,r1_coverage as C,r1_rooms as Rooms,r1_direction_twins as Twins,r1_training as Training
from student_pilot.p3_provenance import load,pinned,file_pin,sha256,source_files,digest
from student_pilot.source_seal import inventory,archive,create,binding
from launch_r1 import production_proof as Q,entry
import joblib as J
prior=load(O/'final/400/RESULT.json');assert prior['status']=='ADMIT'
files=inventory(T);archive(T,F/'source.tar',files,compress=True)
closure={str(p.relative_to(T)):sha256(p) for p in source_files([Path(N.C.__file__)])};code=create(T,F/'source.tar',closure,{})
codepin=J.write(F/'code.json',code)
synthetic=load(O/'TWIN_BOUNDARY.json')['pins'];Twins.ROWS=synthetic['rows']['sha256'];Twins.BINDING=synthetic['binding']['sha256'];Twins.ALIASES=synthetic['aliases']['sha256'];Rooms.STORE=synthetic['source_database']['sha256']
summary=dict(GO=False,status='REFUSE',tree_sha256=digest(files),init_milestone=400,kits={},reused_native_preparation=prior['original_producer_result'],
 stand_ins=['Retained synthetic RGB/labels, tiny native model dimensions and processor constructor','Synthetic twin/store constants; native row validators and removal producers retained','Synthetic PASS host and independent-review receipts only for entry.admit; negative mutations check both gates'],new_databases=0)
try:
 with ExitStack() as stack:
  stack.enter_context(patch.object(N.C,'processor_for',N.processor));stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
  u=os.uname();stack.enter_context(patch.object(os,'uname',return_value=os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))))
  aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
  stack.enter_context(P.scope(aliases))
  for name in ('n','q'):
   root=F/name;root.mkdir(exist_ok=True);cfg=deepcopy(load(pinned(prior['config'])));cfg['code']=codepin
   v=cfg['r1_training'];v['proof_mode']='train' if name=='n' else 'q'
   if name=='n':v['init_policy']=P.INIT_POLICY
   else:v.pop('init_policy',None)
   receipt=deepcopy(load(pinned(cfg['preparation'])));receipt['trainer_commit']=code['commit'];receipt['config_sha256']=N.C.identity(cfg);receipt['source_seal']=binding(code,receipt['config_sha256']);cfg['preparation']=J.write(root/'p.json',receipt)
   with P.scope(v['persisted_files']), (nullcontext() if name=='n' else P.proof_scope()):
    C.deferred(cfg,read_pins=True);C.validate_binding(cfg)
    from launch_r1 import p_opener_witness
    cfg['routing_vocabulary']=p_opener_witness.produce(cfg,root/'v.json')
    bound=Q.bind_handover(cfg,root/'h');cfg=load(pinned(bound));N.C.prepared(cfg)
    handover=P.admission(cfg,weights=True);step=handover['absolute_resume_step'];assert step==(0 if name=='n' else 400);assert handover['init_milestone']==400
    with P.scope(handover['paths']):
     if name=='n':
      host=dict(status='PASS',config_identity=N.C.identity(cfg),assertions=dict.fromkeys(entry.ASSERTIONS,True),loader_audit=prior['audit'])
      cfg['r1_training']['host_receipt']=J.write(root/'host.json',host)
      cfg['r1_training']['review']=J.write(root/'review.json',dict(verdict='PASS',config_identity=N.C.identity(cfg)))
      assert entry.admit(cfg)==0
      cfg['r1_training']['host_receipt']=J.write(root/'host_bad.json',dict(host,status='FAIL'))
      try:entry.admit(cfg)
      except ValueError as e:assert str(e)=='R1_HOST_ADMISSION_MISSING'
      else:raise AssertionError('invalid host admitted')
      cfg['r1_training']['host_receipt']=file_pin(root/'host.json')
      cfg['r1_training']['review']=J.write(root/'review_bad.json',dict(verdict='FAIL',config_identity=N.C.identity(cfg)))
      try:entry.admit(cfg)
      except ValueError as e:assert str(e)=='INDEPENDENT_REVIEW_PENDING'
      else:raise AssertionError('invalid review admitted')
      # The native preparation records the config before external host/review pins.
      cfg['r1_training'].pop('host_receipt');cfg['r1_training'].pop('review')
      prep,manifest=N.C.prepared(cfg);model=N.C.load_model(manifest,prep,N.C.processor_for_receipt(manifest,prep))
      optimizer=N.torch.optim.AdamW([p for p in model.parameters() if p.requires_grad]);assert len(optimizer.state)==0
      del optimizer,model
     forward=Q.forward(cfg,root,step,'cpu')
   records=load(root/'f.json')['records'];assert len(records)==288 and {r['rank'] for r in records}==set(range(4));assert all(r['finite'] and math.isfinite(r['loss']) for r in records)
   card=load(pinned(cfg['r1_training']['mix']));pop=load(pinned(cfg['r2_sampling']['population']));indices=load(pinned(cfg['r2_sampling']['indices']));C.deferred_card(card,pop['counts'],indices['cells']);assert pop['counts']['direction']==39971
   assert sha256(T/'student_pilot/r1_loader.py')==load(O/'code.json')['files']['student_pilot/r1_loader.py']
   # Refusal twins use the same policy as this kit, so a training-policy refusal cannot mask an altered shard.
   source=(L/'work/build24/refusal_twins.py').read_text().replace("proof_mode=v.get('proof_mode'))", "proof_mode=v.get('proof_mode'),init_policy=P.init_policy(v))")
   source=source.replace("n['r1_training']['proof_mode']='train';invoke('export_in_training_config',n,closure=True)", "n['r1_training']['proof_mode']='train';n['r1_training'].pop('init_policy',None);invoke('export_without_init_policy',n,closure=True)")
   namespace={};exec(compile(source,'refusal_twins24b','exec'),namespace)
   request=load(O/'400/request.json');request['config']=bound;request['staged_pins'][0]=bound
   twins=namespace['twins'](request,cfg,file_pin(O/'model.json'),root);assert len(twins)==8 and all(x['status']=='REFUSE' for x in twins.values())
   assert 'FILE_MISMATCH' in twins['altered_shard']['refusal'],twins['altered_shard']
   value=dict(status='ADMIT',config=bound,init_milestone=400,training_start_step=step,optimizer_state_entries=0 if name=='n' else None,
    no_proof_scope=name=='n',full_forward=forward,records=len(records),first_losses={str(rank):next(r['loss'] for r in records if r['rank']==rank) for rank in range(4)},
    deferred_cells={c['type']:pop['counts'].get(c['type'],0) for c in card['cells'] if c['stream']=='routing' and c['type']!='routing_base'},direction_rows=pop['counts']['direction'],twins=twins,
    audit=prior['audit'],same_prepared_stores=cfg['streams']==load(pinned(prior['config']))['streams'])
   J.write(root/'RESULT.json',value);summary['kits'][name]=value;print(name,'ADMIT',value['first_losses'],flush=True)
  rows=load(O/'vqa/receipt.json')['removals'];named=[r for r in rows if r.get('file',{}).get('sha256','').startswith('d1454a44')];assert named[0]['matched']==109 and named[0]['removed']==107
  summary.update(status='ADMIT',named_removals=named)
except Exception as e:
 import traceback
 summary.update(refusal=type(e).__name__+':'+str(e),traceback=traceback.format_exc());print(summary['traceback'],flush=True)
J.write(F/'RESULT.json',summary);N.m.save(F)
raise SystemExit(summary['status']!='ADMIT')
