"""Replay production metadata readers on unchanged real step-400 bytes, on CPU."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import datetime,json,sys,traceback
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e';E=L.parent/'ext/m400real'
if not E.exists():E=D/'inputs/m400real'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from student_pilot import r1_persisted as P,r1_handover as H,r1_training as T,carrier_c1_run as C
from student_pilot.p3_provenance import file_pin,load,pinned
from student_pilot.source_seal import check_binding
from launch_r1 import production_proof as Q,p_opener_witness as W,p_export_receipt as X
import torch
torch.set_num_threads(8);torch.set_num_interop_threads(1)
O=D/'proofs/replay';O.mkdir(parents=True,exist_ok=True)
original_open=Path.open
def retained_open(p,mode='r',*args,**kwargs):
    return original_open(p,mode.replace('x','w') if p.is_relative_to(O) else mode,*args,**kwargs)
Path.open=retained_open
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
receipt=load(E/'e.json');run=load(E/'r.json');allpaths={}
for p in (E/'files').rglob('*.json'):allpaths[J.sha(p)]=str(p)
for entry in load(B/'UPLOADS.json')['files']:
    if entry['opaque_name'].startswith('u/'):allpaths.setdefault(entry['sha256'],entry['local_path'])
paths={pin['sha256']:allpaths.get(pin['sha256'],str(O/'absent'/pin['sha256'])) for pin in receipt['pins'].values()}
allpaths.update(paths);allpaths[J.sha(E/'e.json')]=str(E/'e.json')
cfg=load(D/'proofs/real/resolved.json')['config'];value=cfg['r1_training']
value.update(handover_receipt=file_pin(E/'e.json'),persisted_files=paths)
rows=[]
def call(name,fn,summary=lambda value:None):
    try:
        result=fn();row=dict(reader=name,status='PASS',result=summary(result))
    except Exception as error:
        row=dict(reader=name,status='REFUSE',error=type(error).__name__+':'+str(error));result=None
        row['traceback']=traceback.format_exc()
    rows.append(row);print(name,row['status'],row.get('error',''),flush=True)
    J.write(D/'REPLAY.json',dict(rows=rows,GO=False))
    return result

with P.scope(allpaths),P.proof_scope():
    source=call('p3_provenance.pinned/load: config',lambda:load(pinned(run['config'])),lambda c:dict(export_identity=H.export_identity(c)))
    artifact=call('p3_provenance.pinned/load: artifact',lambda:load(pinned(cfg['init_artifact']['artifact'])),lambda a:dict(config_sha256=a['config_sha256'],step=a['step']))
    prep=call('p3_provenance.pinned/load: preparation',lambda:load(pinned(run['preparation'])),lambda p:dict(config_sha256=p['config_sha256']))
    call('p3_provenance.pinned/load: binding',lambda:load(pinned(run['binding'])),lambda b:b)
    for label,record in (('artifact',artifact),('preparation',prep)):
        call('source_seal.check_binding:'+label,lambda record=record:check_binding(record.get('source_seal'),load(pinned(source['code'])),H.export_identity(source)))
    closure=call('r1_persisted.verify: e.json/r.json',lambda:P.verify(value['handover_receipt'],run,cfg['init_artifact']['artifact'],paths,proof_mode='q'),
        lambda c:dict(verified=len(c['verified']),absent=sorted(c['absent']),export_bytes_verified=c['export_bytes_verified']))
    call('r1_handover.donor',lambda:H.donor(cfg,artifact),lambda d:dict(runtime_identity=H.export_identity(d[0]),continuation=d[2]))
    call('r1_handover.compare_configs',lambda:H.compare_configs(source,cfg))
    call('r1_training.training_components',lambda:T.training_components(value['registry'],cfg),lambda v:{k:x.get('status','VERIFIED') for k,x in v.items()})
    bound=call('r1_handover.bind_target',lambda:H.bind_target(cfg,O/'mapping.json'),lambda c:dict(donor_config_sha256=c['r1_training']['donor_config_sha256']))
    call('p_opener_witness.prepared_vocabulary',lambda:W.prepared_vocabulary(source))
    call('p_opener_witness.produce',lambda:W.produce(cfg,O/'v.json'))
    if bound is not None:
        call('r1_training.start',lambda:T.start(bound),lambda step:step)
        call('r1_persisted.admission(weights=False)',lambda:P.admission(bound),lambda c:dict(status=c['status'],step=c['absolute_resume_step']))
        call('production_proof.bind_handover',lambda:Q.bind_handover(bound,O/'h'))
    call('r1_persisted.admission(weights=True)',lambda:P.admission(bound or cfg,weights=True))
    # No model tensors are constructed. The namespace supplies only attributes read before tensor I/O.
    model=SimpleNamespace(carrier_placement=artifact['placement'],frame_layout=artifact.get('frame_layout','spread'),
        carrier_position_policy=artifact.get('carrier_position_policy','native_v1'),geometry_online=None,
        auxiliary_heads=SimpleNamespace(pose=SimpleNamespace(projector_fp32=False)))
    call('r1_handover.donor_meta_model',lambda:H.donor_meta_model(source))
    call('r1_handover.verify_trainable_groups',lambda:H.verify_trainable_groups(bound or cfg,model))
    call('carrier_c1_run.prepared:N',lambda:C.prepared(bound or cfg,admission=True))
    for part in ('lm','heads'):
        call('carrier_c1_run.init_from_artifact:'+part,lambda part=part:C.init_from_artifact(model,cfg['init_artifact'],part=part))
    call('p_export_receipt.collect',lambda:X.collect(run,cfg['init_artifact']['artifact']))
    for name in ('config','binding','preparation'):
        assert J.sha(Path(allpaths[run[name]['sha256']]))==run[name]['sha256']
    bad=deepcopy(bound or cfg);bad['r1_training']['donor_config_sha256']=J.load(B/'kits/q/k/p.json')['p_kit_identity']
    call('mutation: donor receives kit identity',lambda:H.donor(bad,artifact))
    with P.scope({}),P.proof_scope():
        call('mutation: unbound export-only mode',lambda:P.verify(value['handover_receipt'],run,cfg['init_artifact']['artifact'],paths,proof_mode='train'))

J.write(D/'REPLAY.json',dict(GO=False,rows=rows,real_receipt=file_pin(E/'e.json'),real_run=file_pin(E/'r.json'),
    runtime_identity=H.export_identity(source),kit_identity=J.load(B/'kits/q/k/p.json')['p_kit_identity'],
    limitations=['No production weights, base tokenizer metadata, databases or RGB are present.',
        'init_from_artifact receives only model metadata attributes and stops at real missing tensor I/O; no forward is claimed.',
        'N native preparation and population production are not replaced with fake success. Their absent outputs may refuse final binding.']))
