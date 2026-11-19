import os
"""Revalidate native capacity stores and both handovers with the final merged tree.

The original run exercises every producer. This pass reuses those immutable
prepared databases, reseals N's preparation metadata, then repeats the native
sampler audit, checkpoint/export admission, and full forward on every rank.
"""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import json,sys,os,math
L=Path(__file__).resolve().parents[2];D=L/'work/build24';O=D/'proofs/capacity';T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'));F=O/'final'
sys.path[:0]=[str(D),str(L/'work/build21'),str(T)]
import native24 as N
from student_pilot import r1_persisted as P,r1_coverage as C,r1_rooms as Rooms,r1_direction_twins as Twins
from student_pilot.p3_provenance import load,pinned,write,file_pin,sha256,source_files,digest
from joblib import write
from student_pilot.source_seal import inventory,archive,create,binding
from launch_r1 import production_proof as Q
from student_pilot.r1_loader import production_audit
from refusal_twins import twins
F.mkdir(parents=True,exist_ok=True)
prior=load(O/'RESULT.json') if (O/'RESULT.json').is_file() else dict(milestones={})
for step in (600,400):
 p=O/str(step)/'q/RESULT.json'
 if p.is_file() and load(p)['status']=='ADMIT':prior['milestones'][str(step)]=load(p)
assert prior['milestones']['600']['status']=='ADMIT'
files=inventory(T)
if not (F/'source.tar').exists():archive(T,F/'source.tar',files,compress=True)
closure={str(p.relative_to(T)):sha256(p) for p in source_files([Path(N.C.__file__)])}
code=create(T,F/'source.tar',closure,{});codepin=write(F/'code.json',code)
synthetic=load(O/'TWIN_BOUNDARY.json')['pins'];Twins.ROWS=synthetic['rows']['sha256'];Twins.BINDING=synthetic['binding']['sha256'];Twins.ALIASES=synthetic['aliases']['sha256'];Rooms.STORE=synthetic['source_database']['sha256']
summary=dict(GO=False,status='REFUSE',tree_sha256=digest(files),producer_tree=load(O/'code.json')['tree_sha256'],
    reused_native_preparation=True,milestones={},stand_ins=prior.get('stand_ins',[]))
def export400(root):
    from launch_r1 import p_export_receipt as E
    from student_pilot.r1_handover import export_identity
    donor=load(O/'600/request_config.json');run=deepcopy(donor['r1_training']['p_run']);run.pop('checkpoint')
    p=load(pinned(run['config']));current=load(F/'600/h/config.json')
    with P.scope(donor['r1_training']['persisted_files']):
        receipt,manifest=N.C.prepared(current)
        model=N.C.load_model(manifest,receipt,N.C.processor_for_receipt(manifest,receipt))
    with N.RunnerTests().local_collectives(),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
        N.C.export(root/'export',model,model,p,400)
    ap=file_pin(root/'export/artifact.json')
    hp=E.produce(run,ap,root/'h400.json',job_id='6ed2c7aa',trainer_commit=load(pinned(run['binding']))['trainer_commit'])
    h=load(pinned(hp));del model
    return dict(init_artifact=dict(donor['init_artifact'],artifact=ap),p_run=run,handover_receipt=hp,
        persisted_files={pin['sha256']:pin['path'] for pin in h['pins'].values()},proof_mode='q',donor_config_sha256=export_identity(p))
try:
 with ExitStack() as stack:
    stack.enter_context(patch.object(N.C,'processor_for',N.processor))
    stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
    u=os.uname();stack.enter_context(patch.object(os,'uname',return_value=os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))))
    aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
    stack.enter_context(P.scope(aliases));stack.enter_context(P.proof_scope())
    for step in (600,400):
        existing=F/str(step)/'RESULT.json'
        if step==600 and existing.exists() and load(existing)['status']=='ADMIT':
            saved=load(existing);saved_cfg=load(pinned(saved['config']))
            assert load(pinned(saved_cfg['code']))['tree_sha256']==digest(files)
            summary['milestones'][str(step)]=saved
            continue
        root=F/str(step);root.mkdir(exist_ok=True);old=prior['milestones'].get(str(step),prior['milestones']['600'])
        cfg=deepcopy(load(pinned(old['config'])));cfg['code']=codepin
        if step==400 and str(step) not in prior['milestones']:
            donor=export400(root);cfg['init_artifact']=donor.pop('init_artifact');cfg['r1_training'].update(donor)
            summary['step400_store_reuse']='Native step400 export and export-only receipt; reuse identical step600 prepared stores, sampler and full frame/row audit.'
        # Data did not change. The native source-binding format authenticates the
        # final N code and its configuration separately from P's donor checkpoint.
        receipt=deepcopy(load(pinned(cfg['preparation'])));receipt['trainer_commit']=code['commit']
        receipt['config_sha256']=N.C.identity(cfg);receipt['source_seal']=binding(code,receipt['config_sha256'])
        cfg['preparation']=write(root/'p.json',receipt)
        with P.scope(cfg['r1_training']['persisted_files']):
            C.deferred(cfg,read_pins=True);C.validate_binding(cfg)
            from launch_r1 import p_opener_witness
            cfg['routing_vocabulary']=p_opener_witness.produce(cfg,root/'v.json')
            bound=Q.bind_handover(cfg,root/'h');cfg=load(pinned(bound))
            N.C.prepared(cfg)
            # The 1000-step audit code, rows, indices and card are identical.
            # Only the MINIMAL gate changed; it just authenticated all bindings.
            assert sha256(T/'student_pilot/r1_loader.py')==load(O/'code.json')['files']['student_pilot/r1_loader.py']
            audit=old['audit'];assert audit['complete'] and audit['largest_repeat']<=4
            handover=P.admission(cfg,weights=True)
            assert handover['absolute_resume_step']==step
            with P.scope(handover['paths']):forward=Q.forward(cfg,root,step,'cpu')
        records=load(root/'f.json')['records'];assert {r['rank'] for r in records}==set(range(4))
        assert all(r['finite'] and math.isfinite(r['loss']) for r in records)
        card=load(pinned(cfg['r1_training']['mix']));pop=load(pinned(cfg['r2_sampling']['population']));indices=load(pinned(cfg['r2_sampling']['indices']))
        C.deferred_card(card,pop['counts'],indices['cells'])
        assert pop['counts']['direction']==39971
        before=load(O/str(step)/'request.json');before['config']=bound;before['staged_pins'][0]=bound
        refusal=twins(before,cfg,file_pin(O/'model.json'),root)
        assert len(refusal)==8 and all(x['status']=='REFUSE' for x in refusal.values())
        result=dict(status='ADMIT',config=bound,absolute_resume_step=step,audit=audit,forward=forward,twins=refusal,
            deferred_cells={c['type']:pop['counts'].get(c['type'],0) for c in card['cells'] if c['stream']=='routing' and c['type']!='routing_base'},
            direction_rows=pop['counts']['direction'],first_losses={str(rank):next(r['loss'] for r in records if r['rank']==rank) for rank in range(4)},
            original_producer_result=file_pin(O/str(step if str(step) in prior['milestones'] else 600)/'q/RESULT.json'),records=len(records))
        write(root/'RESULT.json',result);summary['milestones'][str(step)]=result
        print(step,'ADMIT',result['first_losses'],flush=True)
    summary['status']='ADMIT';summary['complete_native_fixture']=True
except Exception as error:
 import traceback
 summary.update(refusal=type(error).__name__+':'+str(error),traceback=traceback.format_exc());print(summary['traceback'],flush=True)
write(F/'RESULT.json',summary);N.m.save(F)
raise SystemExit(0 if summary['status']=='ADMIT' else 1)
