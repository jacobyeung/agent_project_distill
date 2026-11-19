"""Exercise early refusals without rematerializing the capacity-sized VQA store."""
from copy import deepcopy
from pathlib import Path
from student_pilot.p3_provenance import load
from student_pilot import r1_persisted as P
from launch_r1 import production_proof as Q,p_export_receipt as E
import joblib as J

def twins(request,cfg,mp,root):
    records={}
    def invoke(name,n,extra=None,closure=False,components=False):
        r=deepcopy(request);r['config']=J.write(root/(name+'.json'),n);r['staged_pins'][0]=r['config']
        if extra:extra(r)
        if components:
            from student_pilot.r1_training import training_components
            try:
                with P.proof_scope(),P.scope(n['r1_training']['persisted_files']):training_components(n['r1_training']['registry'],n)
            except (ValueError,OSError) as error:record=dict(status='REFUSE',GO=False,refusal=type(error).__name__+':'+str(error))
            else:record=dict(status='ADMIT',GO=False)
            record['reader']='student_pilot.r1_training.training_components'
        elif closure:
            v=n['r1_training']
            try:
                with P.proof_scope():P.verify(v['handover_receipt'],v['p_run'],n['init_artifact']['artifact'],v['persisted_files'],weights=True,proof_mode=v.get('proof_mode'))
            except (ValueError,OSError) as error:record=dict(status='REFUSE',GO=False,refusal=type(error).__name__+':'+str(error))
            else:record=dict(status='ADMIT',GO=False)
            record['reader']='student_pilot.r1_persisted.verify'
        else:record=Q.run(r,root/'twins'/name)
        records[name]=record
    n=deepcopy(cfg);n['r1_training']['handover_receipt']['sha256']='0'*64;invoke('wrong_h_pin',n,closure=True)
    for name,field in (('non_R1','leg'),('non_N','vehicle')):
        n=deepcopy(cfg);card=load(n['r1_training']['mix']['path']);card[field]='other'
        n['r1_training']['mix']=J.write(root/(name+'_card.json'),card);invoke(name,n,components=True)
    invoke('missing_model_manifest',deepcopy(cfg),lambda r:r['staged_pins'].__setitem__(2,dict(mp,path=str(root/'missing_manifest.json'))))
    n=deepcopy(cfg);n['remove_files']=n['remove_files'][:-1];invoke('without_z',n)
    n=deepcopy(cfg);n['r1_training']['routing_inputs']={'units':dict(path=str(root/'unread.json'),sha256='0'*64)};invoke('k1_slice',n)
    receipt=load(cfg['r1_training']['handover_receipt']['path'])
    label=next(k for k in receipt['pins'] if k.startswith('export/') and k.endswith('.safetensors'))
    p=Path(cfg['r1_training']['persisted_files'][receipt['pins'][label]['sha256']]);raw=p.read_bytes()
    p.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    try:invoke('altered_shard',deepcopy(cfg),closure=True)
    finally:p.write_bytes(raw)
    if receipt['step']==400:
        n=deepcopy(cfg);n['r1_training']['proof_mode']='train';invoke('export_in_training_config',n,closure=True)
    else:
        n=deepcopy(cfg);receipt.update(schema=E.SCHEMA,stop_step=600,checkpoint_status=E.NO_CHECKPOINT)
        receipt['pins']={k:v for k,v in receipt['pins'].items() if not k.startswith('checkpoint')}
        n['r1_training']['p_run'].pop('checkpoint');n['r1_training']['persisted_files']={h:p for h,p in n['r1_training']['persisted_files'].items() if h in {v['sha256'] for v in receipt['pins'].values()}}
        n['r1_training']['handover_receipt']=J.write(root/'export_at_stop_receipt.json',receipt)
        invoke('export_at_stop',n,closure=True)
    J.write(root/'TWINS.json',records)
    return records
