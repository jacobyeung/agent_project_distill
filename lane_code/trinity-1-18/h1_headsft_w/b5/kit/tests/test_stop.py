import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import torch
from student_pilot import carrier_c1_run as r
from student_pilot.carrier_c1_sweep import recipe_for

class Stop(unittest.TestCase):
    def test_native_stop_exports_and_keeps_lr_horizon(self):
        cfg=json.loads(Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/kit07ca49df_meta/m/k/b02e4385.json').read_text())
        out=Path(tempfile.mkdtemp(dir=Path(__file__).resolve().parents[1]/'tmp'))
        cfg.update(output=str(out),h1={'stop_after_step':200})
        cfg['first_step_admission']=None
        model=SimpleNamespace(depth_stage1=False)
        calls=[]
        def optimize(*args):
            calls.append(args[7]);return {'wall_seconds':.001,'head_metrics':{}},None
        def export(directory,*args,**kw):
            directory.mkdir();(directory/'artifact.json').write_text('{}')
        with patch.object(r,'optimize_step',side_effect=optimize),patch.object(r,'checkpoint') as checkpoint, \
             patch.object(r,'export',side_effect=export) as exported,patch.object(r,'existing_export',return_value=None):
            report=r.run_steps(model,model,None,SimpleNamespace(),dict(pose=8,vqa=8,routing=8,pointing=8),out,cfg,{},
                               torch.device('cpu'),start_step=199,distributed=False)
        self.assertEqual(report['last_step'],200)
        self.assertEqual(report['stop_reason'],'h1_stop_after_step')
        self.assertEqual(exported.call_count,1);self.assertEqual(checkpoint.call_count,1)
        self.assertTrue((out/'m200/artifact.json').is_file())
        stop=json.loads((out/'h1_stop_000200.json').read_text())
        self.assertEqual(stop['lr_horizon'],1000)
        self.assertEqual(recipe_for(cfg)['steps'],1000)

    def test_resume_at_stop_executes_no_more_updates(self):
        cfg=json.loads(Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/kit07ca49df_meta/m/k/b02e4385.json').read_text())
        out=Path(tempfile.mkdtemp(dir=Path(__file__).resolve().parents[1]/'tmp'))
        cfg.update(output=str(out),h1={'stop_after_step':200})
        model=SimpleNamespace(depth_stage1=False)
        with patch.object(r,'optimize_step') as optimize,patch.object(r,'export') as exported,patch.object(r,'existing_export',return_value=True):
            report=r.run_steps(model,model,None,SimpleNamespace(),dict(pose=8,vqa=8,routing=8,pointing=8),out,cfg,{},torch.device('cpu'),start_step=200,distributed=False)
        optimize.assert_not_called();exported.assert_not_called()
        self.assertEqual(report['last_step'],200);self.assertEqual(report['steps'],[])
        self.assertEqual(report['stop_reason'],'h1_stop_after_step')
