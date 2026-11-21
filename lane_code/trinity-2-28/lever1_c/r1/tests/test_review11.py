"""A successful receipt must not conceal a later supervisor sink failure."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'tests'))
import test_bootstrap as B


class Review11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=dict(delivery_sha256=B.sha(HERE/'out/delivery.tgz'),cases=[])

    @classmethod
    def tearDownClass(cls):
        (HERE/'out/REVIEW11_CHECKS.json').write_text(json.dumps(cls.evidence,indent=2)+'\n')

    def check(self,case):
        root,p,pub,env,argv=B.BootstrapTests.setup_case(self,case)
        proc=subprocess.run(argv,env=env,capture_output=True,text=True)
        self.assertEqual(proc.returncode,1,proc.stdout+proc.stderr)
        initial=B.decoded((root/'work'/('a173925'+pub['token'])/'success.json').read_bytes())
        self.assertEqual(initial['status'],'COMPLETE')
        self.assertEqual(initial['returncode'],0)
        command=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_fetch.py'),'parent',str(p),
                 '/project/community/jjyeung/okh7/ae71c903',str(root/'pool'),'173925',str(HERE/'orchard/o_fetch.sh')]
        got=subprocess.run(command,env=env,capture_output=True,text=True)
        self.assertEqual(got.returncode,0,got.stdout+got.stderr)
        ex=B.decoded((p/'a/f/EXIT.json').read_bytes())
        self.assertEqual(ex['status'],'FAILED');self.assertEqual(ex['returncode'],1)
        with tarfile.open(p/'a/f/0.tgz') as archive:
            trace=B.decoded(archive.extractfile('metadata/14.json').read())
            self.assertTrue(any(case.replace('_',' ') in line for line in trace['lines']),trace)
            self.assertEqual(B.decoded(archive.extractfile('FAILED.json').read())['returncode'],1)
            self.assertFalse(B.decoded(archive.extractfile('metadata/PARITY.json').read())['trusted'])
        self.evidence['cases'].append(dict(case=case,passed=True,initial_status=initial['status'],
            child_returncode=initial['returncode'],supervisor_returncode=proc.returncode,
            fetched_status=ex['status'],production_fetch=True,traceback=trace,fetched_sha256=B.sha(p/'a/f/0.tgz')))

    def test_late_drain_failure(self):self.check('late_sink_drain')
    def test_late_drain_timeout(self):self.check('late_sink_timeout')
    def test_late_diagnostic_save_failure(self):self.check('late_sink_save')


if __name__=='__main__':unittest.main(verbosity=2)
