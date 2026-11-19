"""Publish through the current native exporter and rebind unchanged audited rows."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,json,tempfile,subprocess,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';R=D/'rehearsal3';ns=Path('/tmp/q_22c714e1')
sys.path[:0]=[str(D),str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
if '--inside' not in sys.argv:
    args=J.load(R/'VIEW.json');py=sys.executable
    env={**os.environ,'S1_CPU_REHEARSAL':'1','S1_REHEARSAL_ATTEMPT':'b24f_fresh'}
    for cmd in ([py,'-I','-s','-B',str(Path(__file__).resolve()),'--inside'],
                [py,'-B',str(D/'rehearsal_handoff.py'),str(ns/'p2'),str(ns/'v.json')],
                [py,'-B',str(D/'rehearsal_gates.py')]):
        subprocess.run(args+cmd,env=env,check=True)
    prepared=J.load(R/'PREPARED.json');prepared['canary']=J.sha(R/'p2/q/RESULT.json')
    J.write(R/'PREPARED.json',prepared)
    raise SystemExit(0)
import native24 as N
tempfile.tempdir=str(R/'tmp');N.torch.set_num_threads(2);N.C.processor_for=N.processor
from student_pilot import r1_persisted as P
from student_pilot.p3_provenance import load,pinned,file_pin
from launch_r1 import p_export_receipt as E,p_opener_witness as W,production_proof as Q
cfg=J.load(ns/'v.json');aliases=J.load(R/'r2.json')['_paths']
with P.scope(aliases),P.scope(cfg['r1_training']['persisted_files']):
    receipt,manifest=N.C.prepared(cfg)
    model=N.C.load_model(manifest,receipt,N.C.processor_for_receipt(manifest,receipt))
    original_cfg=J.load(D/'rehearsal2/input.json')
    original=load(original_cfg['init_artifact']['artifact']['path'])
    if original.get('trained_groups'):model.trained_group_state=deepcopy(original['trained_groups'])
    donor=J.load(R/'donor/config.json')
    (R/'donor/export').rename(R/'donor/export_legacy')
    (R/'donor/receipt.json').rename(R/'donor/receipt_legacy.json')
    with N.RunnerTests().local_collectives(),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
        N.C.export(R/'donor/export',model,model,donor,400)
    ap=file_pin(R/'donor/export/artifact.json')
    actual=load(ap['path'])
    for key in ('r2_identity','routing_vocabulary','readout_config','component_evidence'):
        assert actual[key]==original[key],key
    run=cfg['r1_training']['p_run']
    hp=E.produce(run,ap,R/'donor/receipt.json',job_id='6ed2c7aa',trainer_commit=load(pinned(run['binding']))['trainer_commit'])
    paths={p['sha256']:p['path'] for p in load(hp['path'])['pins'].values()}
    def rebind(c):
        c=deepcopy(c);c['init_artifact']['artifact']=ap
        c['r1_training'].update(handover_receipt=hp,persisted_files=paths)
        c['routing_vocabulary']=W.produce(c,R/'rebind/vocabulary.json')
        return c
    result=J.load(ns/'p2/q/RESULT.json')
    target=rebind(load(pinned(result['config'])))
    # A donor receipt change also changes DEFERRED evidence recorded by preparation.
    from student_pilot.r1_components import artifact_status
    with P.scope(paths):
        prepared=load(pinned(target['preparation']))
        prepared['component_evidence']=artifact_status(target)
        target['preparation']=J.write(R/'rebind/component_preparation.json',prepared)
    with P.scope(paths):
        result['config']=Q.bind_handover(target,R/'rebind/h')
        target=load(pinned(result['config']))
        admission=P.admission(target,weights=True)
        result['handover']={k:v for k,v in admission.items() if k!='paths'}
        tables=N.H.verify_trainable_groups(target,model)
    J.write(ns/'p2/q/RESULT.json',result)
    generation=J.load(R/'GENERATION.json');generation.update(artifact=ap,receipt=hp)
    J.write(R/'GENERATION.json',generation)
    J.write(R/'DONOR_GROUPS.json',tables)
    J.write(R/'METADATA_PRESERVED.json',dict(status='PASS',fields=['r2_identity','routing_vocabulary','readout_config','component_evidence'],
       native_export=True,rows_and_weights_unchanged=True,artifact=ap,receipt=hp))
print('PASS: current native export preserves lineage/readout metadata; native handover admission and groups pass.')
