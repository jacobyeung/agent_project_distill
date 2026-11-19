"""Run the untouched 9fix tree's own fixture and export producer."""
from pathlib import Path
import hashlib,json,os,sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build12';T=L.parent/'w9f/work/tree_r1'
O=B/'proofs/legacy_export';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(T))
from student_pilot import carrier_c1_run as C
from tests.test_carrier_c1 import fixture
from tests.test_carrier_c1_run import RunnerTests
import torch
model,_,_=fixture(4)
mkdir,opened=Path.mkdir,Path.open
def retain(p,mode=0o777,parents=False,exist_ok=False):
    return mkdir(p,mode=mode,parents=parents,exist_ok=True if p.is_relative_to(O) else exist_ok)
def overwrite(p,mode='r',*a,**k):return opened(p,mode.replace('x','w') if p.is_relative_to(O) else mode,*a,**k)
cfg=dict(base_identity='fixture',trace_program_version='3.13')
with RunnerTests().local_collectives(),patch.object(Path,'mkdir',retain),patch.object(Path,'open',overwrite),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
    C.export(O/'m200',model,model,cfg,200)
artifact=json.loads((O/'m200/artifact.json').read_text())
state=torch.load(artifact['heads']['path'],weights_only=True)
assert len(state)==192 and 'readout_config' not in artifact
(O/'RESULT.json').write_text(json.dumps(dict(producer=str(T/'student_pilot/carrier_c1_run.py'),
    producer_sha256=hashlib.sha256((T/'student_pilot/carrier_c1_run.py').read_bytes()).hexdigest(),
    config=cfg,heads=len(state),readout_config_present=False,
    standins='Untouched 9fix native tiny model replaces pretrained GPU weights; local collectives and publication-state boundary only. Owned proof files overwrite in place.'),indent=2))
