"""CPU admission tests. Fake nvidia-smi and fake pass; never invoke a GPU or terminate a process."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import launch_gpu as L
from watchdog import call_watchdog

ROOT = Path(__file__).resolve().parents[2]
TESTROOT = ROOT/'sb_mask_phrase/work/launcher_tests'
TESTROOT.mkdir(parents=True, exist_ok=True)


def allowed_write(path, out, user):
    path = Path(path)
    return path.is_relative_to(out) or re.fullmatch(r'/tmp/terminator/' + re.escape(user) + r'-[0-9]+', str(path)) is not None


class Launcher(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=TESTROOT))
        self.kit = self.root/'sb_mask_phrase'
        (self.kit/'part2').mkdir(parents=True)
        shutil.copyfile(L.KIT/'part2/BARS_PART2.json',self.kit/'part2/BARS_PART2.json')
        self.out = self.kit/'out/pool_part2'
        self.t = 1000.0
        self.waits=[]; self.commands=[]
        self.smi=self.root/'nvidia-smi'
        self.smi.write_text('#!/usr/bin/env python3\nimport pathlib,sys\np=pathlib.Path(__file__).with_suffix(".xml")\nprint(p.read_text())\n')
        self.smi.chmod(0o755)
        self.xml()
        self.fake=self.root/'fake_pass.py'
        self.fake.write_text('''import hashlib,json,os,pathlib
out=pathlib.Path(os.environ['PART2_OUT'])
for name in ('HF_HOME','TORCH_HOME','XDG_CACHE_HOME','TRITON_CACHE_DIR','TMPDIR','HOME'):
 p=pathlib.Path(os.environ[name]); assert p.is_relative_to(out); p.mkdir(parents=True,exist_ok=True); (p/'test').write_text('ok')
assert os.environ['CUDA_VISIBLE_DEVICES']=='GPU-test'
phase=os.environ['PART2_MODE']
(out/('STEP5.json' if phase=='step5' else 'PASS_COMPLETE.json')).write_text(json.dumps(dict(status='PASS',input_sha256={__file__:hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()})))
(out/'TIMING_RECEIPT.json').write_text(json.dumps(dict(fake=True,input_sha256={__file__:hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()})))
''')

    def xml(self, used=0, processes='', total=49140, cap='8.6', identity='GPU-test'):
        self.smi.with_suffix('.xml').write_text(f'<nvidia_smi_log><gpu><uuid>{identity}</uuid><compute_cap>{cap}</compute_cap><fb_memory_usage><used>{used} MiB</used><total>{total} MiB</total></fb_memory_usage><processes>{processes}</processes></gpu></nvidia_smi_log>')

    def sample(self,card):
        return L.reading(card,str(self.smi))

    def sleep(self,seconds):
        self.waits.append(seconds)

    def fake_run(self,command,**kwargs):
        self.commands.append(command)
        self.assertEqual(command[:2],['timeout','--signal=KILL'])
        self.assertIn(str(self.kit/'part2/vendor/vnice.sh'),command)
        self.assertTrue(kwargs['start_new_session'])
        self.t += 12
        return subprocess.run([sys.executable,'-B',str(self.fake)],**kwargs)

    def launch(self,**kwargs):
        options=dict(kit=self.kit,host='trinity-1-18',sample=self.sample,sleep=self.sleep,
                     run=self.fake_run,prepare=lambda k:{str(self.fake):L.sha(self.fake)},clock=lambda:self.t)
        options.update(kwargs)
        return L.launch(2,**options)

    def test_clean_two_samples_and_remaining_timeout(self):
        self.assertEqual(self.launch(),0)
        self.assertEqual(self.waits,[300])
        self.assertEqual([c[2] for c in self.commands],['4320.000000s','4308.000000s'])
        r=json.loads((self.out/'CLEAN_END.json').read_text())
        self.assertEqual(len(r['readings']),2)
        self.assertEqual(r['spent_seconds'],24)
        self.assertFalse((self.out/'RUNNING').exists())
        self.assertTrue((self.out/'LAST_CLEAN_START.json').exists())

    def test_clean_resume_charges_previous_budget(self):
        self.launch(mode='step5')
        self.commands=[]
        self.launch(mode='pass')
        self.assertEqual(self.commands[0][2],'4308.000000s')

    def test_memory_busy_in_first_reading(self):
        self.xml(used=1025)
        def wait(s): self.sleep(s); self.xml()
        with self.assertRaises(RuntimeError): self.launch(sleep=wait)
        self.assertEqual(self.commands,[])
        self.assertEqual(len(json.loads((self.out/'KILLED.json').read_text())['readings']),2)

    def test_memory_busy_in_second_reading(self):
        def wait(s): self.sleep(s); self.xml(used=1025)
        with self.assertRaises(RuntimeError): self.launch(sleep=wait)
        self.assertEqual(self.commands,[])

    def test_graphics_process_rejected_even_with_zero_memory(self):
        self.xml(processes='<process_info><pid>42</pid><type>G</type></process_info>')
        with self.assertRaises(RuntimeError): self.launch()
        self.assertEqual(self.commands,[])

    def test_process_in_second_reading(self):
        def wait(s): self.xml(processes='<process_info><pid>42</pid></process_info>')
        with self.assertRaises(RuntimeError): self.launch(sleep=wait)

    def test_threshold_1024_accepted(self):
        self.xml(used=1024)
        self.assertEqual(self.launch(),0)

    def test_small_card_refused(self):
        self.xml(total=24000)
        with self.assertRaises(RuntimeError): self.launch()

    def test_placement_refused_before_writes(self):
        for host in ('trinity','trinity-0-13','laptop'):
            with self.assertRaises(RuntimeError): self.launch(host=host)
        self.assertFalse(self.out.exists())

    def test_running_stop_killed_never_resumed(self):
        for name in ('RUNNING','STOP','STOP.json','KILLED','KILLED.json'):
            folder=self.root/name; folder.mkdir(); (folder/name).write_text('interrupted')
            with self.assertRaises(RuntimeError): L.admit_state(folder)

    def test_unmarked_partial_refused(self):
        self.out.mkdir(parents=True); (self.out/'partial').write_text('partial')
        with self.assertRaises(RuntimeError): self.launch()

    def test_failed_pass_preserves_running_and_refuses_retry(self):
        def fail(*args,**kwargs): return subprocess.CompletedProcess(args[0],137)
        with self.assertRaises(RuntimeError): self.launch(run=fail)
        self.assertTrue((self.out/'RUNNING').exists())
        with self.assertRaises((RuntimeError, SystemExit)): self.launch()

    def test_missing_clean_completion_preserves_running(self):
        def fail(*args,**kwargs): return subprocess.CompletedProcess(args[0],0)
        with self.assertRaises(FileNotFoundError): self.launch(run=fail)
        self.assertTrue((self.out/'RUNNING').exists())

    def test_expired_budget_refused(self):
        self.out.mkdir(parents=True)
        (self.out/'CLEAN_END.json').write_text(json.dumps(dict(status='CLEAN',spent_seconds=4320,input_sha256={})))
        with self.assertRaises(RuntimeError): self.launch()

    def test_watchdog_interrupts_stalled_call(self):
        start=time.monotonic()
        with self.assertRaises(TimeoutError):
            with call_watchdog(.03): time.sleep(1)
        self.assertLess(time.monotonic()-start,.5)

    def test_watchdog_uses_remaining_budget(self):
        with patch.dict(os.environ,PART2_DEADLINE_MONOTONIC=str(time.monotonic()+.03)):
            with self.assertRaises(TimeoutError):
                with call_watchdog(300): time.sleep(1)

    def test_bars_first_no_writes(self):
        (self.kit/'part2/BARS_PART2.json').write_text('{}')
        with self.assertRaises(SystemExit): self.launch()
        self.assertFalse(self.out.exists())

    def test_all_writes_confined(self):
        self.launch()
        for p in self.kit.rglob('*'):
            if p.is_file() and p != self.kit/'part2/BARS_PART2.json':
                self.assertTrue(allowed_write(p, self.out, os.environ['USER']),str(p))
        self.assertFalse((self.kit/'out/TIMING_RECEIPT.json').exists())

    def test_only_terminator_control_allowed_outside_pool(self):
        user = os.environ['USER']
        self.assertTrue(allowed_write(f'/tmp/terminator/{user}-123', self.out, user))
        for path in ('/tmp/terminator/other-123', f'/tmp/terminator/{user}-abc',
                     f'/tmp/terminator/{user}-123/nested', '/tmp/other', '/home/test'):
            self.assertFalse(allowed_write(path, self.out, user), path)
        vendor = L.KIT/'part2/vendor'
        self.assertEqual(L.sha(vendor/'terminator.sh'), '19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d')
        self.assertEqual(json.loads((vendor/'PINS.json').read_text())['sha256']['terminator.sh'], L.sha(vendor/'terminator.sh'))

    def test_environment_confines_openssl_and_path(self):
        env = L.environment(self.kit, self.out, 'GPU-test', 4320, 'pass', False)
        self.assertEqual(env['PATH'], '/usr/bin:/bin')
        self.assertEqual(env['OPENSSL_CONF'], str(self.kit.parent/'payload/environment/ssl/openssl.cnf'))

    def test_complete_pass_never_relaunched(self):
        self.launch()
        with self.assertRaisesRegex(RuntimeError, 'already complete'): self.launch()

    def test_card_identity_must_match(self):
        def wait(s): self.xml(identity='GPU-changed')
        with self.assertRaises(RuntimeError): self.launch(sleep=wait)

    def test_watchdog_disarms_after_success(self):
        with call_watchdog(.03): pass
        time.sleep(.04)

    def test_missing_bars_and_scores_refuse_without_writes(self):
        bars=self.kit/'part2/BARS_PART2.json'
        bars.rename(bars.with_suffix('.saved'))
        with self.assertRaises(SystemExit): self.launch()
        self.assertFalse(self.out.exists())
        bars.with_suffix('.saved').rename(bars)
        score=self.kit/'out/part2/PER_ITEM_PART2.jsonl'
        score.parent.mkdir(parents=True); score.write_text('{}')
        before={str(p):p.stat().st_mtime_ns for p in self.kit.rglob('*')}
        with self.assertRaises(SystemExit): self.launch()
        after={str(p):p.stat().st_mtime_ns for p in self.kit.rglob('*')}
        self.assertEqual(before,after)

    def test_pinned_vnice_rejects_tamper(self):
        vendor=self.kit/'part2/vendor'; vendor.mkdir()
        (vendor/'vnice.sh').write_text('tampered')
        (vendor/'PINS.json').write_text(json.dumps(dict(sha256={'vnice.sh':'0'*64},input_sha256={})))
        with self.assertRaisesRegex(RuntimeError,'vendor hash'): L.preflight(self.kit)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Launcher)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    inputs=[Path(__file__),Path(L.__file__),L.KIT/'part2/watchdog.py',L.KIT/'part2/gate.py',L.KIT/'part2/sam3_pass.py', L.KIT/'part2/vendor/PINS.json', L.KIT/'part2/vendor/terminator.sh', L.KIT/'part2/launch_gpu.sh']
    record=dict(status='PASS' if result.wasSuccessful() else 'FAIL',ran=result.testsRun,
                command='bash sb_mask_phrase/run.sh part2/test_launcher.py',gpu='NOT RUN',
                method='fake nvidia-smi executable; fake pass executable; injected timeout runner (no process termination)',
                input_sha256={str(p):L.sha(p) for p in inputs})
    (ROOT/'out/LAUNCHER_TESTS.json').write_text(json.dumps(record,indent=1)+'\n')
    raise SystemExit(not result.wasSuccessful())
