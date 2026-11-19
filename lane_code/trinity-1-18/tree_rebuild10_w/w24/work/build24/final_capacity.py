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
from student_pilot.source_seal import inventory,archive,create,binding
from launch_r1 import production_proof as Q
from student_pilot.r1_loader import production_audit
from refusal_twins import twins
F.mkdir(parents=True,exist_ok=True)
prior=load(O/'RESULT.json');assert prior['complete_native_fixture'] and prior['status']=='ADMIT'
files=inventory(T);archive(T,F/'source.tar',files,compress=True)
closure={str(p.relative_to(T)):sha256(p) for p in source_files([Path(N.C.__file__)])}
code=create(T,F/'source.tar',closure,{});codepin=write(F/'code.json',code)
synthetic=load(O/'TWIN_BOUNDARY.json')['pins'];Twins.ROWS=synthetic['rows']['sha256'];Twins.BINDING=synthetic['binding']['sha256'];Twins.ALIASES=synthetic['aliases']['sha256'];Rooms.STORE=synthetic['source_database']['sha256']
summary=dict(GO=False,status='REFUSE',tree_sha256=digest(files),producer_tree=load(O/'code.json')['tree_sha256'],
    reused_native_preparation=True,milestones={},stand_ins=prior.get('stand_ins',[]))
try:
 with ExitStack() as stack:
    stack.enter_context(patch.object(N.C,'processor_for',N.processor))
    stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
    u=os.uname();stack.enter_context(patch.object(os,'uname',return_value=os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))))
    aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
    stack.enter_context(P.scope(aliases));stack.enter_context(P.proof_scope())
    for step in (600,400):
        root=F/str(step);root.mkdir(exist_ok=True);old=prior['milestones'][str(step)]
        cfg=deepcopy(load(pinned(old['config'])));cfg['code']=codepin
        # Data did not change. The native source-binding format authenticates the
        # final N code and its configuration separately from P's donor checkpoint.
        receipt=deepcopy(load(pinned(cfg['preparation'])));receipt['trainer_commit']=code['commit']
        receipt['config_sha256']=N.C.identity(cfg);receipt['source_seal']=binding(code,receipt['config_sha256'])
        cfg['preparation']=write(root/'p.json',receipt)
        with P.scope(cfg['r1_training']['persisted_files']):
            C.deferred(cfg,read_pins=True);C.validate_binding(cfg)
            bound=Q.bind_handover(cfg,root/'h');cfg=load(pinned(bound))
            N.C.prepared(cfg)
            audit=production_audit(cfg,root/'a')
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
            original_producer_result=file_pin(O/str(step)/'q/RESULT.json'),records=len(records))
        write(root/'RESULT.json',result);summary['milestones'][str(step)]=result
        print(step,'ADMIT',result['first_losses'],flush=True)
    summary['status']='ADMIT';summary['complete_native_fixture']=True
except Exception as error:
 import traceback
 summary.update(refusal=type(error).__name__+':'+str(error),traceback=traceback.format_exc());print(summary['traceback'],flush=True)
write(F/'RESULT.json',summary);N.m.save(F)
raise SystemExit(0 if summary['status']=='ADMIT' else 1)
