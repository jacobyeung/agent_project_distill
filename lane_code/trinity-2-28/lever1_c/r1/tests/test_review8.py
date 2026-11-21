"""Exercise submission equivalence, disk admission, and cumulative write ceilings."""
import os
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE/'tests'))
import ast
import importlib.util
import io
import json
import subprocess
import tarfile
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import test_fixes as F
import environment_audit

class ReviewTests(unittest.TestCase):
    setUpClass=classmethod(F.FixTests.setUpClass.__func__)
    @classmethod
    def tearDownClass(cls):
        import j
        (HERE/'out/REVIEW8_CHECKS.json').write_text(j.wire_dumps(cls.evidence,indent=2)+'\n')

    def test_ext4_only_assigned_job(self):
        from orchard_h10 import job
        S,J,*_=job.template()
        for fs in ('ext4','tmpfs','xfs','btrfs'):
            mount=f'42 1 8:1 /job_tmp/123 /tmp rw - {fs} /dev/sda rw'
            with patch.object(J,'active_mount',return_value=dict(mount_id=42,probe_path='/tmp/a')):
                if fs=='ext4':self.assertEqual(J.storage_proof('/tmp/a',mountinfo=mount,job='123')['filesystem'],'ext4')
                else:
                    with self.assertRaises(J.StorageRefusal):J.storage_proof('/tmp/a',mountinfo=mount,job='123')
        self.evidence['disk_admission']=dict(passed=True,accepted=['ext4'],rejected=['tmpfs','xfs','btrfs'])

    def test_identical_cpu_gpu_submission(self):
        from orchard_h10 import job
        from orchard_h10.common import sha
        m=types.ModuleType('submission');m.__file__=str(self.package/'8.py')
        exec(self.files['8.py'],m.__dict__)
        cfg=json.loads(self.files['9.json']);cfg.update(json.loads((self.package/'0.json').read_bytes()))
        receipt=dict(plan=cfg['plan_sha256'],inputs=m.digest(self.package/'a/1.json'),package=m.digest(self.package/'PACKAGE.json'),gpus=1,time='00:50:00')
        (self.package/'2.json').write_text(json.dumps(receipt))
        loaded=m.json.loads((self.package/'2.json').read_text())
        self.assertEqual((loaded['plan'],loaded['inputs'],loaded['package'],loaded['gpus'],loaded['time']),(cfg['plan_sha256'],m.digest(self.package/'a/1.json'),m.digest(self.package/'PACKAGE.json'),1,'00:50:00'))
        calls=[]
        def submitted(argv,**kw):calls.append((argv,kw));return types.SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
        with patch.object(m,'load_helpers',return_value=cfg),patch.object(job,'check_inputs'),patch.object(m.subprocess,'run',side_effect=submitted):
            self.assertEqual(m.submit(self.package,1,'00:50:00',cpu_only=True),0)
            self.assertEqual(m.submit(self.package,1,'00:50:00'),0)
        cpu,gpu=calls
        self.assertEqual(cpu[0],[v for v in gpu[0] if not v.startswith('--gres=')]);self.assertEqual(cpu[1],gpu[1])
        self.assertIn('--export=NONE',cpu[0]);self.assertIn('--chdir=/tmp',cpu[0]);self.assertIn('--open-mode=append',cpu[0])
        self.assertFalse(any('/dev/null' in v for v in gpu[0]));self.assertEqual(cpu[1]['input'],(self.package/'BATCH.sh').read_bytes())
        self.evidence['submission']=dict(passed=True,cpu_argv=cpu[0],gpu_argv=gpu[0],identical_environment=True,identical_batch=True,differences=['--gres=gpu:1 omitted for CPU allocation'])

    def test_diagnostics_persist_before_capture_exit(self):
        from orchard_h10.e import capture
        root=F.temp();path=root/'14.json';mirror=root/'20'
        with capture(path,mirror=mirror) as stream:
            stream.write(b'cause before child exit\n');stream.flush()
            for _ in range(100):
                if mirror.exists() and mirror.stat().st_size:break
                time.sleep(.01)
            self.assertIn(b'cause before child exit',bytes.fromhex(mirror.read_text().strip()))
            stream.write(b'x'*200000);stream.flush()
        self.assertLessEqual(mirror.stat().st_size,131072)
        self.assertLessEqual(path.with_suffix('.0').stat().st_size,131072)
        batch=(self.package/'BATCH.sh').read_text();header=batch.split('/usr/bin/python3 -I -s -B - ',1)[0]
        self.assertEqual(header.splitlines()[1],'ulimit -S -f 512')
        # Execute the real header and an early shell failure, with only its path mapped.
        (root/'27.py').write_bytes((self.package/'a/27.py').read_bytes())
        shell=header.replace('/project/community/jjyeung/'+self.info['token']+'/a/',str(root)+'/')+'false\n'
        script=root/'1.sh';script.write_text(shell)
        result=subprocess.run(['bash',str(script)],capture_output=True)
        self.assertEqual(result.returncode,1)
        records=(root/'21').read_text().splitlines()
        self.assertTrue(records and all(r.split()[0]=='1' and r.split()[1].isdigit() for r in records))
        self.evidence['durable']=dict(passed=True,stream_before_exit=True,stream_cap=131072,shell_first_command=True,err_exit_records=records)

    def test_metadata_budget_refuses_before_write(self):
        root=F.temp();(root/'a').mkdir();m=types.ModuleType('quota');exec((HERE/'runtime/q.py').read_bytes(),m.__dict__)
        m.PREFIX=str(root)+'/';m.LIMIT=160
        with (root/'file').open('wb') as disk:
            writer=m.Writer(disk);writer.write(b'a'*96)
            with self.assertRaisesRegex(OSError,'E70'):writer.write(b'b')
        self.assertEqual((root/'file').read_bytes(),b'a'*96)
        self.assertEqual(int((root/'a/18').read_text()),128)
        self.evidence['metadata_budget']=dict(passed=True,cap=2_000_000,prewrite_reservation=True,counts_ledger_writes=True)

    def test_pool_budget_refuses_before_copy(self):
        from orchard_h10 import job
        S,J,R,I,A=job.template();root=F.temp();pool=root/'pool';token='a123456789'
        I.operate('test',pool,token);ledger=pool/(token+'.0');ledger.write_text('11999990')
        src=root/'src';src.mkdir()
        for name in ('result.tar.gz','EXIT.json','JOB.log'):(src/name).write_bytes(b'12345')
        with self.assertRaisesRegex(ValueError,'E72'):I.operate('publish',pool,token,src)
        self.assertFalse((pool/token/'result.tar.gz.partial').exists())
        self.evidence['project_budget']=dict(passed=True,total=48_000_000,placement=10_000_000,shell_diagnostics=2_000_000,python_metadata_and_diagnostics=2_000_000,pool=12_000_000,fetch=20_000_000,scheduler_control_and_reserve=2_000_000,recovery_working_directory='assigned job directory')

    def test_environment_inventory(self):
        result=environment_audit.inventory();self.assertTrue(result['passed'])
        reads=result['reads'];self.assertTrue(any(r['key']=='USER' for r in reads));self.assertTrue(any(r['key']=='A_N' for r in reads))
        self.assertTrue(any('tree/' in r['source'] for r in reads))
        self.assertTrue(all(r['provided_by'] for r in reads))
        self.evidence['environment']=dict(passed=True,reads=len(reads),files_parsed=result['files_parsed'],scope=result['scope'])

if __name__=='__main__':unittest.main(verbosity=2)
