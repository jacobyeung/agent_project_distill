"""CPU imports and plan resolution with external application paths forbidden."""
import hashlib
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
os.environ.update(PART2_STAGED='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')

for name in ('HF_HOME','TORCH_HOME','XDG_CACHE_HOME','TRITON_CACHE_DIR','TMPDIR'):
    p=ROOT/'out/staged_smoke_cache'/name.lower(); p.mkdir(parents=True,exist_ok=True); os.environ[name]=str(p)

def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=os.fsdecode(args[0])
        if p.startswith(('/home/','/data','/scratch/')) and not p.startswith(str(ROOT)+'/'):
            raise RuntimeError('External input forbidden in staged smoke: '+p)
    if event.startswith('socket.connect'):
        raise RuntimeError('Network forbidden')

sys.addaudithook(audit)
sys.path.insert(0,str(ROOT/'sb_mask_phrase/part2'))
import sam3_pass as G
import torch
torch.set_num_threads(8)
sys.path[:0]=[str(G.SOURCE_ROOT),str(G.VENDOR/'vendor'),str(G.BOX/'reader_src'),str(G.TREE)]
from sam3_tower import Sam3Tower
from e2e_reader.stage1 import sam3_detect
from student_pilot import routed_features
from sam3.model.sam3_image_processor import Sam3Processor
import sam3.model_builder
import numpy as np
assert routed_features.resize(np.zeros((4,4),bool),(8,8)).shape == (8,8)
plan=G.plan()
# Decode one complete 32-frame capture to exercise the frozen path mapping and SHA pins.
frames=G.frames_of(plan[0][0])
assert len(frames)==32
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
        if getattr(module,'__file__',None) and Path(module.__file__).is_file()}
external=[p for p in loaded.values() if p.startswith(('/scratch/','/home/','/data')) and not p.startswith(str(ROOT)+'/')]
assert not external,external
inputs={p:G.sha(p) for p in set(loaded.values()) if p.startswith(str(ROOT)+'/')}
for p in [Path(__file__),G.BOX/'pinned_train.json',G.IDS,G.NEW,G.DECISION,ROOT/'out/ENV_RELOCATION.json',ROOT/'out/ENV_SUPPLEMENT.json']:
    inputs[str(p)]=G.sha(p)
for slot in plan[0][0]['anchor_slots']:
    rec=plan[0][0]['dense_frames'][slot]; inputs[str(G.local(rec['path']))]=rec['sha256']
record=dict(status='PASS',captures=len(plan),decoded_frames=len(frames),python_prefix=sys.prefix,
            gpu='NOT RUN',model='NOT LOADED',external_application_imports=external,
            command='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 nice -n 10 payload/environment/bin/python -B verify_staged.py',
            input_sha256=inputs)
(ROOT/'out/STAGED_SMOKE.json').write_text(json.dumps(record,indent=1)+'\n')
print('PASS: staged imports, 209-capture plan, 32 decoded frames; no external application input')
