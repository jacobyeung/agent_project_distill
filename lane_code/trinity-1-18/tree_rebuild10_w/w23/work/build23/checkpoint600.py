"""Check the native 600 checkpoint with the already audited MINIMAL 400 stores."""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import json,os,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build23';O=D/'proofs/capacity'
sys.path[:0]=[str(D),str(L/'work/build21'),str(L/'work/tree_r1')]
import native23 as N
from student_pilot.p3_provenance import load,pinned,write,file_pin
from student_pilot import r1_persisted as P
from launch_r1 import production_proof as Q,p_opener_witness
root=O/'600/checkpoint_reuse';root.mkdir(parents=True,exist_ok=True)
prior=load(O/'400/q/RESULT.json')
assert prior['status']=='ADMIT'
cfg=deepcopy(load(pinned(prior['config'])))
donor=load(O/'600/request_config.json')
assert load(pinned(donor['r1_training']['handover_receipt']))['step']==600
cfg['init_artifact']=donor['init_artifact']
for key in ('p_run','handover_receipt','persisted_files','proof_mode','donor_config_sha256'):
    cfg['r1_training'][key]=donor['r1_training'][key]
result=dict(status='REFUSE',GO=False,steps=['reuse_400_native_stores_and_population'],
    proof_root=str(root),reused_data=prior['config'],absolute_resume_step=600)
try:
    assert 'STUDENT_R2_FRAME_HOST' not in os.environ and 'Q_E7' not in os.environ
    with ExitStack() as stack:
        stack.enter_context(patch.object(N.C,'processor_for',N.processor))
        stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
        u=os.uname();stack.enter_context(patch.object(os,'uname',return_value=os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))))
        stack.enter_context(P.proof_scope())
        stack.enter_context(P.scope(cfg['r1_training']['persisted_files']))
        cfg['routing_vocabulary']=p_opener_witness.produce(cfg,root/'v.json')
        bound=Q.bind_handover(cfg,root/'h')
        cfg=load(pinned(bound));result['config']=bound
        handover=P.admission(cfg,weights=True)
        assert handover['absolute_resume_step']==600
        result['handover']={k:v for k,v in handover.items() if k!='paths'}
        result['steps'].append('persisted_checkpoint_handover')
        with P.scope(handover['paths']):result['forward']=Q.forward(cfg,root,600,'cpu')
        result['steps'].append('all_rank_full_forward')
        result['audit']=prior['audit']
        result['status']='ADMIT'
except Exception as error:
    import traceback
    result.update(refusal=type(error).__name__+':'+str(error),traceback=traceback.format_exc())
write(root/'RESULT.json',result);N.m.save(root)
summary=dict(status='ADMIT' if result['status']=='ADMIT' else 'PARTIAL',GO=False,
    milestones={'400':prior,'600':result},
    stand_ins=['Synthetic RGB frame host and catalogs','Tiny native model dimensions',
        'PatchGridProcessor HF processor constructor','CPU local publication collectives'],
    checkpoint_scope='600 reuses the completed 400 native store, population and sampler audits; checkpoint handover and all-rank forward run at 600.')
(O/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],refusal=result.get('refusal'),root=str(root))))
raise SystemExit(0 if result['status']=='ADMIT' else 1)
