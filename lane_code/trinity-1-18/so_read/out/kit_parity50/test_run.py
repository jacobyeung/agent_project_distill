"""CPU verification of the production parity worker launch contract."""
import importlib.util
from pathlib import Path
import unittest
import subprocess
import sys
import os
import uuid
import json
import hashlib
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('gpu_kit',HERE/'run.py')
kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)

class LaunchTests(unittest.TestCase):
    def test_original_and_off_do_not_opt_in_to_journaling_or_sharding(self):
        cfg={'export':'/scratch/u0/u1','export_pin':'/scratch/u0/u2','artifact_manifest':'/scratch/u0/u3'}
        for mode in ('ORIGINAL','OFF','OFF_REPEAT','ON'):
            args=kit.launch_args(cfg,Path('/scratch/u0/u4'),Path('/scratch/u0/u5'),Path('/scratch/u0/u6'),
                                 Path('/scratch/u0/u7'),mode,'0/1',False)
            self.assertNotIn('--atomic-journal',args);self.assertNotIn('--scene-shards',args)
            self.assertNotIn('--opaque',args)
        for mode in ('ORIGINAL','OFF','OFF_REPEAT'):
            with self.assertRaises(ValueError):
                kit.launch_args(cfg,Path('/scratch/u0/u4'),Path('/scratch/u0/u5'),Path('/scratch/u0/u6'),
                                Path('/scratch/u0/u7'),mode,'0/1',True)

    def test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes(self):
        output=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex/'u0'
        source=HERE.parents[1]/'work/src'
        command=[sys.executable,'-I','-s','-B',str(source/'u0/a11.py'),'stage-kit',
                 '--source-root',str(source),'--input',str(HERE),'--out',str(output)]
        process=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.assertEqual(process.returncode,0,process.stderr)
        self.assertEqual({p.name for p in output.iterdir()},{'u0.py','u1.py','a9.py','u0.json','u1.json','u2.json','u3.json'})
        sys.path.insert(0,str(HERE))
        from a9 import read_wire
        identity=read_wire(json.loads((output/'u1.json').read_bytes()))
        self.assertEqual(identity['sample_sha256'],hashlib.sha256((output/'u0.json').read_bytes()).hexdigest())
        for path in output.glob('*.json'):
            self.assertEqual(set(json.loads(path.read_bytes())),{'u0'})
            for word in ('vsi','devs1','scannet','qwen','sam'):
                self.assertNotIn(word,path.read_text().lower())

    def test_durable_scene_comparison_requires_explicit_on_arm(self):
        cfg={'export':'/scratch/u0/u1','export_pin':'/scratch/u0/u2','artifact_manifest':'/scratch/u0/u3'}
        args=kit.launch_args(cfg,Path('/scratch/u0/u4'),Path('/scratch/u0/u5'),Path('/scratch/u0/u6'),
                             Path('/scratch/u0/u7'),'ON','0/4',True)
        self.assertIn('--atomic-journal',args);self.assertIn('--scene-shards',args)
        self.assertEqual(args[args.index('--shard')+1],'0/4')

if __name__=='__main__':unittest.main(verbosity=2)
