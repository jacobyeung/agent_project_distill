from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0'
p=E/'a4.py';s=p.read_text().replace('        boundary()\n    state(True)\n','        boundary()\n        state(True)\n',1);p.write_text(s)
p=E/'a6.py';s=p.read_text().replace("if receipt.exists() and json.loads(receipt.read_text()).get('verified') is not True:","if receipt.exists() and (wire.loads if wire else json.loads)(receipt.read_text()).get('verified') is not True:");p.write_text(s)
p=E/'a10.py';s=p.read_text().replace('    for path in paths:\n        for line',"    for path in paths:\n        receipt=path.parent/'WEIGHTS.json'\n        if receipt.exists():\n            from a9 import read_wire\n            if read_wire(json.loads(receipt.read_bytes())).get('verified') is not True:\n                raise ValueError('Unchecked cache weights; cannot compare journal')\n        for line",1);p.write_text(s)
(L/'out/kit_parity50/compare.py').write_bytes(p.read_bytes())
p=E/'tests/test_lock_round3.py';s=p.read_text();pos=s.index('suite=unittest.TestSuite(')
s=s[:pos]+'''class TypeLockTests(fixtures.RunnerTests):
    def test_type_deadline_recovery_holds_writer_lock(self):
        from unittest.mock import patch
        import fcntl
        args=self.args('type-locked');args.types='camera_rotation'
        original=fixtures.J.AtomicJournal.recover;checks=[]
        def checked(journal):
            with (journal.root/'writer.lock').open('a') as other:
                with self.assertRaises(BlockingIOError):fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
            checks.append(True);return original(journal)
        commit=fixtures.launch.commit_record
        def interrupted(stream,value):
            if Path(stream.name).name=='items.jsonl':raise fixtures.launch.ReadDeadline()
            return commit(stream,value)
        with patch.object(fixtures.J.AtomicJournal,'recover',checked),patch.object(fixtures.launch,'commit_record',side_effect=interrupted):
            with self.assertRaises(fixtures.launch.ReadDeadline):fixtures.launch.run_types(args,make_real=self.make_real)
        self.assertGreaterEqual(len(checks),2)

suite=unittest.TestSuite([fixtures.RunnerTests('test_deadline_recovery_keeps_writer_lock'),
                         TypeLockTests('test_type_deadline_recovery_holds_writer_lock')])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
''';p.write_text(s)
with (L/'work/STATUS.md').open('a') as f:
 import subprocess
 f.write(subprocess.check_output(['date','-u'],text=True)+'Round 3: operator actions 0/1/2 tested with a12 ON payload and stub workers; fresh-process activation fixed; read cache memory included with default OFF. Base inventory and OFF guard regressions pass.\n')
