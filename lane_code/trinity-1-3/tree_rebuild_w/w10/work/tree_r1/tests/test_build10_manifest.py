import json,tempfile,unittest
from pathlib import Path
import torch
from student_pilot.fixed_readout import DepthReadout,HeadingReadout
from student_pilot.eat1_export import write_manifest
class Manifest(unittest.TestCase):
    def test_fixed_math_and_tower_files(self):
        model=torch.nn.Module();model.auxiliary_heads=torch.nn.Module()
        model.auxiliary_heads.depth_readout=DepthReadout()
        model.auxiliary_heads.heading=HeadingReadout()
        model.auxiliary_heads.geometry_encoder=torch.nn.Identity()
        root=Path(tempfile.mkdtemp())
        torch.save(model.auxiliary_heads.state_dict(),root/'heads.pt')
        value=write_manifest(root,model,{})
        for name in ('depth_readout','heading'):
            entry=value['modules']['auxiliary_heads.'+name]
            self.assertEqual(entry['role'],'fixed_math')
            self.assertEqual(set(entry['buffers']),set(getattr(model.auxiliary_heads,name).state_dict()))
        files=value['modules']['auxiliary_heads.geometry_encoder']['files']
        self.assertTrue(any(p.endswith('g3t_online.py') for p in files))
        self.assertTrue(any(p.endswith('utils/rotation.py') for p in files))
        self.assertTrue(all(value['files'][p]['role']=='tower' for p in files))
