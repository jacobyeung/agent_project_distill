"""Build an untied tiny base and a native, authenticated step-400 export."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,sys,json,tempfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';R=D/'rehearsal3';old=D/'rehearsal2'
sys.path[:0]=[str(D),str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
assert J.load(R/'PRODUCTION_GROUPS.json')['status']=='PASS'
(R/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(R/'tmp')
os.environ.update(S1_CPU_REHEARSAL='1',CUDA_VISIBLE_DEVICES='',STUDENT_ORCHARD='1',
                  R1_MOUNT=str(R),STUDENT_MODEL_ROOT=str(R/'model'),TMPDIR=str(R/'tmp'),
                  R2_PROOFS=str(R),LANE_TEST_OUTPUT=str(R/'tmp'))
import torch
torch.set_num_threads(2);torch.set_num_interop_threads(1)
from transformers import Qwen3_5ForConditionalGeneration
from student_pilot import carrier_c1_run as C,r1_handover as H,r1_persisted as P
from student_pilot.p3_provenance import file_pin,pinned,load
from native_assets21 import PatchGridProcessor
from rehearsal_model import untie
from tests.test_carrier_c1_run import RunnerTests
from launch_r1 import p_export_receipt as E
cfg=J.load(old/'input.json');prep=J.load(old/'prepared.json');manifest=J.load(prep['model']['path'])
aliases=J.load(old/'r2.json')['_paths'];aliases.update(cfg['r1_training']['persisted_files'])
seen=set()
def local(pin):
    raw=pin['path'].replace('/tmp/q_22c714e1/p/',str(L/'work/build24d/go/p')+'/')
    p=Path(raw.replace('/tmp/q_22c714e1',str(old)))
    if p.exists():
        aliases[pin['sha256']]=str(p)
        if p.is_relative_to(old) and p.suffix=='.json' and p not in seen:
            seen.add(p);walk(J.load(p))
def walk(v):
    if isinstance(v,dict):
        if 'path' in v and 'sha256' in v:local(v)
        for x in v.values():walk(x)
    elif isinstance(v,list):
        for x in v:walk(x)
walk(prep)
live_cfg=J.load(old/'v.json');walk(live_cfg)
with P.scope(aliases):
    source=load(pinned(cfg['r1_training']['p_run']['config']))
    source_table=H.trainable_group_table(source,H.donor_meta_model(source))
    live_prep=deepcopy(prep)
    live_prep['_r1_start_config']=deepcopy(live_cfg)
    live_prep['camera'].update(live_cfg.get('camera_overrides',{}))
    with patch.object(C,'processor_for',PatchGridProcessor):
        processor=C.processor_for_receipt(manifest,live_prep)
    model=C.load_model(manifest,live_prep,processor)
    untie(model)
    bad_table=H.trainable_group_table(cfg,model)
    assert source_table!=bad_table
    try:H.verify_trainable_groups(cfg,model)
    except ValueError as error:assert str(error)=='P_EXPORT_TRAINABLE_GROUP_MISMATCH'
    else:raise AssertionError('Tied donor must refuse the untied target')
    J.write(R/'CAUSE_GROUPS.json',dict(source=source_table,target=bad_table,
        refusal='P_EXPORT_TRAINABLE_GROUP_MISMATCH'))
    # Save the base with independent equal-valued embedding/head parameters.
    base=Qwen3_5ForConditionalGeneration.from_pretrained(manifest['root'],local_files_only=True,
        dtype=torch.float32,attn_implementation='sdpa')
    untie(base);base.save_pretrained(R/'model')
    for name in ('tokenizer.json','tokenizer_config.json'):
        (R/'model'/name).write_bytes((Path(manifest['root'])/name).read_bytes())
    mp=J.write(R/'model.json',dict(manifest,root=str(R/'model'),
        files={p.name:J.sha(p) for p in (R/'model').iterdir() if p.is_file()}))
    # Preserve donor config identity and all prepared row metadata; only its
    # authenticated model manifest changes. Preparation is outside export identity.
    donor_prep=load(pinned(source['preparation']));donor_prep['model']=mp
    pp=J.write(R/'donor/preparation.json',donor_prep)
    donor_cfg=deepcopy(source);donor_cfg['preparation']=pp
    cp=J.write(R/'donor/config.json',donor_cfg)
    bound=load(pinned(cfg['r1_training']['p_run']['binding']));bound['preparation']=pp
    bp=J.write(R/'donor/binding.json',bound)
    artifact=load(pinned(cfg['init_artifact']['artifact']))
    if artifact.get('trained_groups'):model.trained_group_state=deepcopy(artifact['trained_groups'])
    with RunnerTests().local_collectives(),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
        C.export(R/'donor/export',model,model,donor_cfg,400)
    ap=file_pin(R/'donor/export/artifact.json')
    run=dict(config=cp,binding=bp,preparation=pp)
    hp=E.produce(run,ap,R/'donor/receipt.json',job_id='6ed2c7aa',trainer_commit=bound['trainer_commit'])
    receipt=load(hp['path'])
    cfg['init_artifact']['artifact']=ap
    cfg['r1_training'].update(p_run=run,handover_receipt=hp,
        persisted_files={p['sha256']:p['path'] for p in receipt['pins'].values()})
    cfg=H.bind_target(cfg,R/'donor/mapping.json')
    tables=H.verify_trainable_groups(cfg,model)
    J.write(R/'DONOR_GROUPS.json',tables)
    J.write(R/'seed.json',cfg)
    J.write(R/'GENERATION.json',dict(status='PASS',model=mp,artifact=ap,receipt=hp,
        base_untied=base.lm_head.weight is not base.get_input_embeddings().weight,
        donor_untied=model.lm_head.weight is not model.get_input_embeddings().weight))
print('PASS: tied-donor refusal reproduced; untied base/export/receipt and native group check generated.')
