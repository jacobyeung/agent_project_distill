"""Failure regressions for durable scheduler output and child sinks."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import types
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1];sys.path[:0]=[str(HERE),str(HERE/'tests')]
import test_bootstrap as B
import test_fixes as F

class Review10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=dict(delivery_sha256=hashlib.sha256((HERE/'out/delivery.tgz').read_bytes()).hexdigest(),cases=[])
    @classmethod
    def tearDownClass(cls):
        (HERE/'out/REVIEW10_CHECKS.json').write_text(json.dumps(cls.evidence,indent=2)+'\n')

    def check(self,case,expected,shell=False):
        root,p,pub,env,argv=B.BootstrapTests.setup_case(self,case)
        header=(p/'BATCH.sh').read_text().split('/usr/bin/python3 -I -s -B - ',1)[0]
        header=header.replace('/project/community/jjyeung/'+pub['token']+'/a/',str(p/'a')+'/')
        if shell:argv=[sys.executable,'-I','-s','-B','-c',"raise RuntimeError('injected shell first line')"]
        script=root/'case.sh';script.write_text(header+shlex.join(argv)+'\n')
        proc=subprocess.run(['bash',str(script)],env=env,capture_output=True)
        self.assertNotEqual(proc.returncode,0,proc.stderr)
        fetch=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_fetch.py'),'parent',str(p),
               '/project/community/jjyeung/okh7/ae71c903',str(root/'pool'),'173925',str(HERE/'orchard/o_fetch.sh')]
        got=subprocess.run(fetch,env=env,capture_output=True)
        self.assertEqual(got.returncode,0,got.stderr)
        with tarfile.open(p/'a/f/0.tgz') as archive:
            cause=B.decoded(archive.extractfile('metadata/14.json').read())
        self.assertTrue(any(expected in line for line in cause['lines']),cause)
        self.assertEqual(B.decoded((p/'a/f/EXIT.json').read_bytes())['status'],'FAILED')
        self.evidence['cases'].append(dict(case=case,passed=True,returncode=proc.returncode,cause=cause,production_fetch=True))

    def test_sink_start_failure(self):self.check('sink_start','injected sink start')
    def test_sink_premature_exit(self):self.check('sink_exit','injected sink exit')
    def test_first_line_raise(self):self.check('first_line','injected first line')
    def test_before_supervisor_raise(self):self.check('shell_first','injected shell first line',shell=True)

    def test_numeric_job_does_not_hide_failure(self):
        F.FixTests.setUpClass.__func__(F.FixTests)
        x=F.FixTests
        m=types.ModuleType('submission');m.__file__=str(x.package/'8.py');exec(x.files['8.py'],m.__dict__)
        from orchard_h10 import job
        cfg=json.loads(x.files['9.json']);cfg.update(json.loads((x.package/'0.json').read_bytes()))
        receipt=dict(plan=cfg['plan_sha256'],inputs=m.digest(x.package/'a/1.json'),package=m.digest(x.package/'PACKAGE.json'),gpus=1,time='00:50:00')
        (x.package/'2.json').write_text(json.dumps(receipt))
        result=types.SimpleNamespace(returncode=1,stdout=b'1001\n',stderr=b'E79\n')
        with patch.object(m,'load_helpers',return_value=cfg),patch.object(job,'check_inputs'),patch.object(m.subprocess,'run',return_value=result) as run:
            self.assertEqual(m.submit(x.package,1,'00:50:00'),1)
            self.assertEqual(run.call_count,1)
        self.evidence['numeric_job_failure']=dict(passed=True,returncode=1,job_id='1001')

if __name__=='__main__':unittest.main(verbosity=2)
