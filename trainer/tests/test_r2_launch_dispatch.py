"""Test native distributed command construction without starting a worker."""
from copy import deepcopy
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from launch_r2 import distributed as D
from student_pilot.carrier_c1_run import identity
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_r2_data_path import directory, LANE


class Dispatch(unittest.TestCase):
    def fixture(self):
        root=directory();(root/'k').mkdir();(root/'o/ee000001').mkdir(parents=True)
        cfg=dict(world_size=4,recipe={'world_size':4},preparation={'path':'unused','sha256':'a'*64})
        review=dict(verdict='PASS',reviewer='CPU fixture',config_sha256=identity(cfg),preparation=cfg['preparation'])
        write(root/'r.json',review);cfg['admission']=file_pin(root/'r.json')
        write(root/'a.json',dict(config_sha256=identity(cfg),new_gpus=4,job_id='123',verdict='GO'))
        cfg['authorization']=file_pin(root/'a.json')
        auth=dict(allow_until_utc='2099-01-01T00:00:00Z',modes=['p','t','u'],production_go_granted=True,
            source_revision='sha256:'+'a'*64,config_sha256=identity(cfg),new_gpus={'t':4,'u':4},other_running_and_pending_gpus=0,gpu_cap=4)
        write(root/'k/4.json',auth)
        launch=dict(production_authorized=True,source_revision=auth['source_revision'])
        write(root/'k/launch.json',launch)
        env=dict(S1_CPU_REHEARSAL='0',SLURM_JOB_NUM_NODES='1',SLURM_GPUS_ON_NODE='4',SLURM_JOB_ID='123')
        return root,cfg,auth,launch,env

    def test_authorized_command_and_mutations(self):
        root,cfg,auth,launch,env=self.fixture()
        command=D.authorized(root,launch,cfg,'t',env)
        self.assertIn('--nproc-per-node=4',command)
        self.assertEqual(command[-4:],[str(root/'b/w.py'),str(root),'t','0'])
        for changed,mode,environment,reason in [({**launch,'production_authorized':False},'t',env,'GO'),
            (launch,'p',env,'GO'),(launch,'t',{**env,'SLURM_GPUS_ON_NODE':'1'},'allocation'),
            (launch,'u',env,'Resume')]:
            with self.assertRaisesRegex(ValueError,reason):D.authorized(root,changed,cfg,mode,environment)
        with self.assertRaisesRegex(ValueError,'review'):D.authorized(root,launch,{k:v for k,v in cfg.items() if k!='admission'},'t',env)
        with self.assertRaisesRegex(ValueError,'allocation'):D.authorized(root,launch,{k:v for k,v in cfg.items() if k!='authorization'},'t',env)
        with patch.dict(os.environ,env),patch.object(D.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as boundary:
            D.launch(root,cfg,'t',launch)
            self.assertEqual(boundary.call_args.args[0],command)
        write(root/'k/7.json',{'files':{}})
        with (patch.dict(os.environ,{**env,'K1':file_pin(root/'o/ee000006.json')['sha256']}),
              patch('student_pilot.carrier_c1_run.train',return_value='GPU boundary') as forward):
            self.assertEqual(D.worker(root,'t','0'),'GPU boundary')
            self.assertEqual(forward.call_args.args[0],cfg)
        with self.assertRaisesRegex(ValueError,'arm'):D.worker(root,'t','1')
        (root/'o/ee000001/a.py').write_text('x=1\n')
        with self.assertRaisesRegex(ValueError,'source'):D.worker(root,'t','0')
        from launch_r2.worker import main
        with self.assertRaisesRegex(ValueError,'arm'):main(root,'t','1')
        (LANE/'out/B3_DISTRIBUTED_COMMAND_PROOF.json').write_text(json.dumps(dict(command=command,
            executed=False,stand_ins=['subprocess.run at GPU worker creation','carrier_c1_run.train at GPU training boundary'],
            parent_function='launch_s1.b.i.launcher',authorization_fixture=True),indent=2)+'\n')

    def test_parent_dependencies_are_isolated(self):
        sentinels={name:object() for name in ('v','q0')}
        with patch.dict(sys.modules,sentinels):
            native=D.parent_launcher()
            self.assertEqual(native.checked.__module__,'launch_s1.b.v')
            self.assertEqual(native.enabled.__module__,'launch_s1.b.q0')
            for name,value in sentinels.items():self.assertIs(sys.modules[name],value)
