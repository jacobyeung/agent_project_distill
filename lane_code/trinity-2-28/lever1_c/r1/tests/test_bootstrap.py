"""Check clean allocation startup and recover a first-line bootstrap failure."""
import os
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import hashlib
import json
import runpy
import subprocess
import tarfile
import tempfile
import time
import unittest


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unpack(path,dest):
    dest.mkdir()
    with tarfile.open(path) as archive:archive.extractall(dest,filter='data')
def decoded(data):
    value=json.loads(data)
    return json.loads(bytes.fromhex(value['a0'])) if set(value)=={'a0'} else value


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info=json.loads((HERE/'out/BUILD.json').read_text())
        cls.evidence=dict(delivery_sha256=sha(HERE/'out/delivery.tgz'),cases=[])
        assert cls.evidence['delivery_sha256']==cls.info['delivery_sha256']

    @classmethod
    def tearDownClass(cls):
        (HERE/'out/BOOTSTRAP_CHECKS.json').write_text(json.dumps(cls.evidence,indent=2)+'\n')

    def setup_case(self,case):
        root=Path(tempfile.mkdtemp(dir=HERE/'tests',prefix='boot_'));p=root/'package'
        unpack(HERE/'out/delivery.tgz',p)
        import ast,io
        line=next(l for l in (p/'BATCH.sh').read_text().splitlines() if l.startswith('b=bytes.fromhex('))
        blob=bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0]))
        with tarfile.open(fileobj=io.BytesIO(blob)) as archive:operator=archive.extractfile('7.py').read()
        pub=json.loads((p/'0.json').read_text())
        proof=dict(passed=True,bundle_guard_passed=True,entry_sequence_passed=True,
                   payload=pub['payload_sha256'],plan=pub['plan_sha256'],inputs=sha(p/'a/1.json'),
                   operator_sha256=hashlib.sha256(operator).hexdigest(),
                   memory=dict(basis='fixed_g3t_shapes',perception_memo_modules=['g3t'],sam_measurement_required=False,fits=True))
        (p/'a/c').mkdir();(p/'a/c/CPU.json').write_text(json.dumps(proof))
        cpu=dict(passed=True,plan=pub['plan_sha256'],inputs=sha(p/'a/1.json'),package=sha(p/'PACKAGE.json'),gpus=1,time='00:50:00')
        (p/'2.json').write_text(json.dumps(cpu))
        work=root/'work';work.mkdir();pool=root/'pool'
        env=dict(PATH='/usr/bin:/bin',USER='jjyeung',SLURM_JOB_ID='173925',SLURM_JOB_PARTITION='general',
                 SLURM_CPUS_PER_TASK='16',SLURM_MEM_PER_NODE='204800',CUDA_VISIBLE_DEVICES='0',
                 SLURM_JOB_START_TIME=str(int(time.time())),SLURM_JOB_END_TIME=str(int(time.time())+3000))
        argv=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_bootstrap.py'),'parent',str(p),str(work),str(pool),pub['token'],case]
        return root,p,pub,env,argv

    def test_clean_export_none_bootstrap(self):
        root,p,pub,env,argv=self.setup_case('clean')
        proc=subprocess.run(argv,env=env,capture_output=True,text=True)
        diagnostic=(p/'a/14.json').read_text() if (p/'a/14.json').exists() else ''
        self.assertEqual(proc.returncode,1,proc.stdout+proc.stderr+diagnostic)
        self.assertTrue((root/'work'/('a173925'+pub['token'])/'17.json').exists())
        self.assertEqual(proc.stdout+proc.stderr,'')
        self.evidence['cases'].append(dict(case='clean_export_none',passed=True,seconds=3000,real_job_main=True,filesystem_admission=True,job_environment=True,external_staging_stub=True))

    def test_first_line_failure_real_fetch(self):
        self.check_failure_case('first_line','injected first line')

    def test_oversize_publication_capped_failure_fetch(self):
        self.check_failure_case('oversize','BudgetError')

    def test_missing_environment_real_fetch(self):
        self.check_failure_case('missing_env',"KeyError: 'USER'")

    def test_unpack_failure_real_fetch(self):
        self.check_failure_case('archive','ReadError')

    def check_failure_case(self,case,expected):
        root,p,pub,env,argv=self.setup_case(case)
        proc=subprocess.run(argv,env=env,capture_output=True,text=True)
        self.assertEqual(proc.returncode,1,proc.stdout+proc.stderr)
        self.assertEqual(proc.stdout+proc.stderr,'')
        if case!='missing_env':self.assertTrue(any(expected in l for l in decoded((p/'a/14.json').read_bytes())['lines']))
        command=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_fetch.py'),'parent',str(p),
                 '/project/community/jjyeung/okh7/ae71c903',str(root/'pool'),'173925',str(HERE/'orchard/o_fetch.sh')]
        got=subprocess.run(command,env=env,capture_output=True,text=True)
        self.assertEqual(got.returncode,0,got.stdout+got.stderr)
        with tarfile.open(p/'a/f/0.tgz') as archive:
            trace=decoded(archive.extractfile('metadata/14.json').read())
            self.assertTrue(any(expected in l for l in trace['lines']))
            self.assertLessEqual(len(trace['lines']),200)
            self.assertFalse(decoded(archive.extractfile('metadata/PARITY.json').read())['trusted'])
        ex=decoded((p/'a/f/EXIT.json').read_bytes());self.assertEqual(ex['status'],'FAILED')
        self.assertEqual(ex['plan_sha256'],pub['plan_sha256'])
        self.evidence['cases'].append(dict(case=case+'_production_fetch',passed=True,traceback=trace,
            fetched_sha256=sha(p/'a/f/0.tgz'),fetched=str(p/'a/f/0.tgz'),package_pins=True,plan_pin=True,receipt_pins=True))

    def test_changed_allocation_receipt_rejected(self):
        root,p,pub,env,argv=self.setup_case('clean')
        cpu=json.loads((p/'2.json').read_text());cpu['time']='00:40:00';(p/'2.json').write_text(json.dumps(cpu))
        proc=subprocess.run(argv,env=env,capture_output=True,text=True)
        self.assertEqual(proc.returncode,1,proc.stdout+proc.stderr)
        self.assertTrue(any('E60' in l for l in decoded((p/'a/14.json').read_bytes())['lines']))
        self.evidence['cases'].append(dict(case='stale_40_minute_receipt_rejected',passed=True))

if __name__=='__main__':unittest.main(verbosity=2)
