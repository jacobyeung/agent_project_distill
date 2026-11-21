"""Run the delivered CPU entry, guarded pool subprocess and failure fetch."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'tests'))
import test_bootstrap as B


class WriteReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=dict(delivery_sha256=B.sha(HERE/'out/delivery.tgz'),cases=[],
            substitutions='Tiny stage/boot/settings fixtures and model-work doubles; real BATCH CPU entry, both guards, process guard, pool writer, reservation ledger and authenticated fetch')
    @classmethod
    def tearDownClass(cls):
        cls.evidence['passed']=all(x['passed'] for x in cls.evidence['cases'])
        (HERE/'out/WRITE_RECEIPT_CHECKS.json').write_text(json.dumps(cls.evidence,indent=2)+'\n')

    def run_case(self,case,job='174001',siblings=False):
        root,p,pub,env,argv=B.BootstrapTests.setup_case(self,case)
        (p/'a/c').rename(p/'a/c0')
        env.update(SLURM_JOB_ID=job,CUDA_VISIBLE_DEVICES='')
        before={}
        if siblings:
            for token in ('a6f198d3c7b20','a7e29d4c8f103','a38bd627f901e'):
                placed=root/token;placed.mkdir();(placed/'0').write_bytes(b'spent placement')
                dest=root/'pool'/(token+format(173995,'08x'));dest.mkdir(parents=True)
                (dest/'.wtest').write_bytes(b'prior probe');(dest.parent/(dest.name+'.0')).write_text('00000000000000000000000000131104')
            before={str(f):B.sha(f) for f in root.rglob('*') if f.is_file() and (f.name=='.wtest' or f.name=='0' or f.suffix=='.0')}
        result=subprocess.run(argv,env=env,capture_output=True,text=True)
        self.assertEqual(result.stdout+result.stderr,'')
        for path,digest in before.items():self.assertEqual(B.sha(Path(path)),digest)
        entry=dict(case=case,job=job,sibling_placements=siblings,passed=False,root=str(root))
        self.evidence['cases'].append(entry)
        return root,p,pub,env,result,entry

    def test_cpu_entry_fresh_and_sibling_pools(self):
        for job,siblings in [('174001',False),('194321',True)]:
            root,p,pub,env,result,entry=self.run_case('write_success',job,siblings)
            diagnostic=B.decoded((p/'a/14.json').read_bytes()) if (p/'a/14.json').exists() else {}
            self.assertEqual(result.returncode,0,diagnostic)
            proof=B.decoded((p/'a/c/CPU.json').read_bytes())
            self.assertTrue(proof['passed'] and proof['bundle_guard_passed'] and proof['entry_sequence_passed'])
            guard=proof['bundle_guard'];self.assertEqual(guard['write_test']['bytes'],131072)
            self.assertEqual(Path(guard['pool']).joinpath(guard['token'],'.wtest').stat().st_size,131072)
            self.assertEqual(int(Path(guard['pool']).joinpath(guard['token']+'.0').read_text()),131104)
            self.assertEqual(proof['entry_sequence']['events'],['guard_installed','write_test','operator_dispatch'])
            # o_check_sub.sh runs the sealed receipt check on this CPU.json before the GPU submit.
            checked=self.receipt_check(p,env)
            self.assertEqual((checked.returncode,checked.stdout.strip()),(0,'All CPU receipt checks passed'),checked.stderr)
            # The placed a/9.py pinned 4 MiB and would reject this receipt.
            old=(p/'a/9.py').read_text();start=old.index("with tarfile.open(p/'0.tgz') as archive:\n    sizes=")
            end=old.index('\n',old.index("found=w['bytes'])",start))+1
            (p/'a/9.py').write_text(old[:start]+"assert type(w['bytes']) is int and w['bytes']==4*1024**2\n"+old[end:])
            stale=self.receipt_check(p,env);(p/'a/9.py').write_text(old)
            self.assertEqual(stale.returncode,1);self.assertIn('AssertionError',stale.stderr)
            entry.update(passed=True,proof=proof,receipt_check=checked.stdout.strip(),old_receipt_check_rejects=True)

    def receipt_check(self,p,env):
        return subprocess.run([sys.executable,'-I','-s','-B','a/9.py',str(p)],cwd=p,env=env,capture_output=True,text=True)

    def test_receipt_check_reports_values(self):
        root,p,pub,env,result,entry=self.run_case('write_success','174002',True)
        self.assertEqual(result.returncode,0)
        cpu=B.decoded((p/'a/c/CPU.json').read_bytes())
        for key in ('bundle_guard','entry_sequence'):cpu[key]['write_test']['bytes']=4*1024**2
        (p/'a/c/CPU.json').write_text(json.dumps(cpu))
        checked=self.receipt_check(p,env)
        self.assertEqual(checked.returncode,1)
        self.assertIn("'expected': 131072",checked.stderr);self.assertIn("'found': 4194304",checked.stderr)
        entry.update(passed=True,receipt_check_failure=checked.stderr.strip().splitlines()[-1][:2048])

    def test_old_cpu_guard_reproduces(self):
        root,p,pub,env,result,entry=self.run_case('write_old','173995',True)
        self.assertEqual(result.returncode,1)
        trace=B.decoded((p/'a/14.json').read_bytes())
        self.assertTrue(any('Write-test receipt differs' in s for s in trace['lines']),trace)
        probe=root/'work'/('a173995'+pub['token'])/'34/wpool'/pub['token']/'.wtest'
        self.assertEqual(probe.stat().st_size,131072)
        entry.update(passed=True,expected_bytes=4194304,found_bytes=probe.stat().st_size,traceback=trace)

    def failure(self,case):
        root,p,pub,env,result,entry=self.run_case(case,siblings=True)
        self.assertEqual(result.returncode,1)
        command=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_fetch.py'),'parent',str(p),
                 '/project/community/jjyeung/okh7/ae71c903',str(root/'pool'),env['SLURM_JOB_ID'],str(HERE/'orchard/o_fetch.sh')]
        got=subprocess.run(command,env=env,capture_output=True,text=True)
        self.assertEqual(got.returncode,0,got.stdout+got.stderr)
        with tarfile.open(p/'a/f/0.tgz') as archive:
            data=archive.extractfile('metadata/30.json').read();self.assertLessEqual(len(data),150000)
            value=B.decoded(data)
            self.assertEqual(value,B.decoded((p/'a/30.json').read_bytes()))
            self.assertEqual(value['job'],env['SLURM_JOB_ID']);self.assertEqual(value['plan'],pub['plan_sha256'])
            self.assertIsNotNone(value['expected']);self.assertIsNotNone(value['found'])
            if case=='write_late':
                self.assertEqual(value['expected'],value['found'])
                self.assertIn('injected post-guard',value['error'])
                self.assertIsNone(value['failed_check']);self.assertIn('passed',value['comparison_status'])
            elif case=='write_budget':
                self.assertEqual(value['failed_check'],'Pool subprocess exit status')
                self.assertEqual(value['expected'],dict(returncode=0));self.assertNotEqual(value['found']['returncode'],0)
                self.assertIn('E72',value['found']['stderr'])
            else:
                self.assertNotEqual(value['expected'],value['found'])
                self.assertEqual(value['failed_check'],value['comparisons'][-1]['check'])
                self.assertFalse(value['comparisons'][-1]['passed'])
            self.assertTrue(B.decoded(archive.extractfile('metadata/25.json').read())['passed'])
        self.assertEqual(B.decoded((p/'a/f/EXIT.json').read_bytes())['status'],'FAILED')
        entry.update(passed=True,production_fetch=True,diagnostic=value)

    def test_receipt_tamper(self):self.failure('write_receipt')
    def test_evidence_size_tamper(self):self.failure('write_size')
    def test_evidence_hash_tamper(self):self.failure('write_hash')
    def test_exhausted_budget(self):self.failure('write_budget')
    def test_later_cpu_failure(self):self.failure('write_late')
    def test_settings_mismatch(self):self.failure('write_settings')


if __name__=='__main__':unittest.main(verbosity=2)
