"""Small mutations for archive, job-surface and write-limit admission."""
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import signal
import sys
import tarfile
import unittest
from unittest.mock import patch
from launch_r2 import bootstrap, build as B, host as H
from student_pilot.p3_provenance import file_pin, load, write
from student_pilot.source_seal import archive
from student_pilot.r2_materialize import materialize
from tests.test_r2_data_path import directory, fixture, manifest, LANE


class Edges(unittest.TestCase):
    def test_archive_mutations_and_raw_archive(self):
        root=directory();(root/'k').mkdir();src=root/'src';src.mkdir();(src/'a.py').write_text('x=1\n')
        files={'a.py':file_pin(src/'a.py')['sha256']}
        archive(src,root/'k/a.tar',files)
        seal=dict(archive={'path':'k/a.tar','sha256':file_pin(root/'k/a.tar')['sha256']},files=files)
        def put(value):(root/'k/7.json').write_text(json.dumps(value))
        put(seal);self.assertEqual((bootstrap.stage(root,root/'s')/'a.py').read_text(),'x=1\n')
        put({**seal,'archive':dict(path='k/a.tar',sha256='0'*64)})
        with self.assertRaisesRegex(ValueError,'archive sha256'):bootstrap.stage(root,root/'b')
        put({**seal,'files':{}})
        with self.assertRaisesRegex(ValueError,'inventory'):bootstrap.stage(root,root/'c')
        put({**seal,'files':{'a.py':'0'*64}})
        with self.assertRaisesRegex(ValueError,'member sha256'):bootstrap.stage(root,root/'d')
        with patch.object(sys,'argv',['e',str(root),'p',str(root/'e')]):
            with self.assertRaises(SystemExit):
                runpy.run_path(str(B.TREE/'launch_r2/bootstrap.py'),run_name='__main__')
        self.assertEqual(set(load(root/'o/ee000007.json')), {'code','sha256'})

    def test_real_store_limit_and_watchdog(self):
        root=directory();row=fixture(root);mp=manifest(root/'m',[row])
        env={'STUDENT_FRAME_ROOT_MAP':json.dumps({'/logical/r2':str(root/'frames')})}
        with patch.dict(os.environ,env):
            with self.assertRaisesRegex(ValueError,'Store over'):
                materialize([mp],root/'a',limits={'vqa':1,'membership':10000})
            with self.assertRaisesRegex(ValueError,'membership'):
                materialize([mp],root/'b',limits={'vqa':1000000,'membership':1})
        now=[0.];guard=H.Guard(root,wall=20,idle=1,clock=lambda:now[0])
        with H.watchdog(guard):
            now[0]=2
            with self.assertRaisesRegex(ValueError,'Stalled'):
                signal.getsignal(signal.SIGALRM)(signal.SIGALRM,None)

    def test_job_surface_and_cpu_entry(self):
        from launch_r2.entry import main
        root=directory();(root/'b').mkdir();(root/'k').mkdir()
        (root/'b/wh.json').write_bytes((B.TREE/'launch_s1/b/wh.json').read_bytes())
        (root/'job.sh').write_text('#!/bin/bash\nexit 1\n')
        script=root/'b/f.sh';script.write_text('#!/bin/bash\n#SBATCH --gpus=1\n')
        with self.assertRaisesRegex(ValueError,'GPU'):B.scan(root)
        script.write_text('#!/bin/bash\nexec python3 k/qwen\n')
        with self.assertRaisesRegex(ValueError,'Forbidden'):B.scan(root)
        script.write_text('#!/bin/bash\nexit 1\n')
        runtime=root/'o/ee000001/student_pilot';runtime.mkdir(parents=True);(runtime/'x.py').write_text('')
        with self.assertRaisesRegex(ValueError,'Forbidden staged path'):B.scan(root)
        root=directory();(root/'b').mkdir();(root/'k').mkdir()
        (root/'b/wh.json').write_bytes((B.TREE/'launch_s1/b/wh.json').read_bytes())
        (root/'job.sh').write_text('#!/bin/bash\nexit 1\n')
        write(root/'k/a.json',{})
        launch={'config':{'file':'k/a.json'},'inputs':None}
        write(root/'k/launch.json',launch)
        with patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':''},clear=True),patch.object(sys,'argv',['b/e.py','.','h','a']):
            with self.assertRaisesRegex(ValueError,'Missing frame-host'):main(root,'h')
            write(root/'k/f.json',{})
            (root/'k/launch.json').write_text(json.dumps({**launch,'inputs':{'path':'k/f.json','sha256':file_pin(root/'k/f.json')['sha256']}}))
            with self.assertRaisesRegex(ValueError,'Missing pose'):main(root,'h')

    def test_deferred_patch_hash_context_and_heading(self):
        namespace=runpy.run_path(str(LANE/'work/build3/apply_contracts.py'))
        plan,apply=namespace['plan'],namespace['apply_text']
        root=directory();tree=root/'t';tree.mkdir();(tree/'a.py').write_text('x=1\n')
        report=root/'report.md';report.write_text('Contract report.\n')
        patch_path=root/'PATCH_a_r2.diff'
        raw='--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x=1\n+x=2\n'
        patch_path.write_text(raw)
        meta=dict(sha256=file_pin(patch_path)['sha256'],report={'path':'report.md','sha256':file_pin(report)['sha256']},
                  base_hashes={'a.py':file_pin(tree/'a.py')['sha256']},tests=['tests.test_r2_build3_edges'])
        sidecar=patch_path.with_suffix('.json');sidecar.write_text(json.dumps(meta))
        changes,tests=plan(root,tree);self.assertEqual(changes['a.py'],'x=2\n')
        sidecar.write_text(json.dumps({**meta,'base_hashes':{'a.py':'0'*64}}))
        with self.assertRaisesRegex(ValueError,'base hash'):plan(root,tree)
        patch_path.write_text(raw.replace('x=2','level_basis=2'))
        sidecar.write_text(json.dumps({**meta,'sha256':file_pin(patch_path)['sha256']}))
        with self.assertRaisesRegex(ValueError,'Heading'):plan(root,tree)
        with self.assertRaisesRegex(ValueError,'context'):apply('x=3\n',raw.split('+++ b/a.py\n')[1])
        with self.assertRaisesRegex(ValueError,'absent'):plan(tree,tree)
