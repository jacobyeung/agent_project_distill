"""Exercise resume and kill handling without launching any subprocess or GPU work."""
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import uuid
import run_arm
from provenance import write_json
from probe_common import ROOT


class ResumeTests(unittest.TestCase):
    def fixture(self):
        root=ROOT/'out/RESUME_TESTS'/uuid.uuid4().hex
        root.mkdir(parents=True)
        weights=root/'weights.json';write_json(weights,{'qwen_vit':{'path':str(root)}})
        manifest=root/'admitted.jsonl';manifest.write_text('{}\n')
        args=NS(arm='A1',train=str(manifest),tuning=str(manifest),weights=str(weights),
                results=str(root/'results'),feature_root=str(root/'features'),labels=None,fusion_rows=None,
                phases='T1',device='cpu',budget_minutes=240.,ledger=str(root/'GPU_TIME.json'))
        return root,args

    def test_resume_checks_outputs_and_shared_ledger(self):
        root,args=self.fixture()
        def completed(*a,**kw):
            write_json(Path(args.results)/'A1/T1.json',{'test':'success'})
            return NS(returncode=0)
        with patch('run_arm.gate.read_manifest',return_value=[]),patch('run_arm.subprocess.run',side_effect=completed) as process:
            run_arm.run(args);run_arm.run(args)
            self.assertEqual(process.call_count,1)
            self.assertTrue(any(k.startswith('A1/T1/') for k in json.loads(Path(args.ledger).read_text())))
            write_json(Path(args.results)/'A1/T1.json',{'test':'changed'})
            with self.assertRaisesRegex(ValueError,'output changed'):run_arm.run(args)
        write_json(args.ledger,{'earlier_arm':{'seconds':240*60}})
        args.results=str(root/'second_results')
        with patch('run_arm.gate.read_manifest',return_value=[]),patch('run_arm.subprocess.run') as process:
            run_arm.run(args);process.assert_not_called()
        self.assertTrue((Path(args.results)/'A1/BUDGET_STOP.json').exists())

    def test_mock_signal_failure_is_never_retried(self):
        _,args=self.fixture()
        with patch('run_arm.gate.read_manifest',return_value=[]),patch('run_arm.subprocess.run',return_value=NS(returncode=-9)) as process:
            with self.assertRaises(SystemExit):run_arm.run(args)
            with self.assertRaisesRegex(RuntimeError,'system-killed'):run_arm.run(args)
            self.assertEqual(process.call_count,1)
        failures=json.loads(Path(args.ledger).read_text())
        self.assertEqual(len(failures),1)
        self.assertEqual(next(iter(failures.values()))['returncode'],-9)


if __name__=='__main__':unittest.main()
