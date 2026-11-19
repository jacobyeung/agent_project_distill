"""Run the native pre-optimizer gate on the prepared fixture in one CPU process."""
from pathlib import Path
import os,sys,json,subprocess
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';R=D/'rehearsal3'
sys.path[:0]=[str(D),str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
if '--inside' not in sys.argv:
    env={**os.environ,'S1_CPU_REHEARSAL':'1','S1_REHEARSAL_ATTEMPT':'b24f_fresh',
         'CUDA_VISIBLE_DEVICES':'','TMPDIR':str(R/'tmp'),'OMP_NUM_THREADS':'2',
         'MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','NUMEXPR_NUM_THREADS':'2',
         'PYTHONDONTWRITEBYTECODE':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}
    raise SystemExit(subprocess.run(J.load(R/'VIEW.json')+[sys.executable,'-I','-s','-B',
        str(Path(__file__).resolve()),'--inside'],env=env).returncode)
import native24 as N
import tempfile
tempfile.tempdir=str(R/'tmp');N.torch.set_num_threads(2)
from student_pilot import r1_persisted as P,r1_handover as H
from student_pilot.p3_provenance import load,pinned
from rehearsal_model import install
install(N.C)
N.C.processor_for=N.processor
cfg=J.load('/tmp/q_22c714e1/v.json')
aliases=J.load(R/'r2.json')['_paths']
with P.scope(aliases),P.scope(cfg['r1_training']['persisted_files']):
    receipt,manifest=N.C.prepared(cfg,admission=True)
    processor=N.C.processor_for_receipt(manifest,receipt)
    model=N.C.load_model(manifest,receipt,processor)
    tables=H.verify_trainable_groups(cfg,model)
    assert tables and tables['source']==tables['target']
    head=model.lm_head.weight
    model.lm_head.weight=model.get_input_embeddings().weight
    try:H.verify_trainable_groups(cfg,model)
    except ValueError as error:
        assert str(error)=='P_EXPORT_TRAINABLE_GROUP_MISMATCH'
        mutation=str(error)
    else:raise AssertionError('The gate must reject a tied target')
    finally:model.lm_head.weight=head
    assert H.verify_trainable_groups(cfg,model)==tables
    J.write(R/'SINGLE_PROCESS_GROUPS.json',dict(status='PASS',native_gate='verify_trainable_groups',
        source=tables['source'],target=tables['target'],mutation=mutation,
        native_authenticated_load=True,topology_changed_after_load=False,distributed=False,
        training_steps=0))
print('PASS: native authenticated load and verify_trainable_groups; tied-target mutation refuses; no training executed.')
