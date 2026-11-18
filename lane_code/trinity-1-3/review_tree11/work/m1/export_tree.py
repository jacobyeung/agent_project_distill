"""usage: export_tree.py TREE DEST  -- export a fixture model with TREE's own export()"""
import sys
from pathlib import Path
from unittest.mock import patch
tree,dest=sys.argv[1],Path(sys.argv[2])
sys.path.insert(0,tree)
from student_pilot import carrier_c1_run as C
from tests.test_carrier_c1 import fixture
model,_,_=fixture(4)
with patch.object(C.dist,'get_rank',return_value=0),patch.object(C.dist,'get_world_size',return_value=1),patch.object(C.dist,'barrier'),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
    C.export(dest,model,model,dict(base_identity='fixture',trace_program_version='3.13'),200)
import json,torch
a=json.load(open(dest/'artifact.json'))
h=torch.load(dest/'heads.pt',weights_only=True)
print('exported',tree[-40:],'readout_config' in a,len(h),sorted(k for k in h if k.startswith(('depth_readout','heading')))[:3])
