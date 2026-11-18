import offline_guard
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate_chain',ROOT/'kit/reader/chain.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)


class ChainTests(unittest.TestCase):
    def run_case(self, failure=None):
        root=ROOT/'evidence'/('test_chain_'+uuid.uuid4().hex)
        root.mkdir()
        import isolated_fixture as isolated
        payload = isolated.package(root)
        run = root/'run'
        config=dict(spec=dict(run=str(run),step=100,
                    interpreters=dict(vllm=str(payload/'vllm_isolated.sh'))),
                    admission={},families=['main','away','forward'],plan_sha256='a'*64,
                    fixture_failure=failure)
        config_path = root/'CONFIG.json'; config_path.write_text(json.dumps(config))
        result = isolated.launch(root, payload/'vllm_isolated.sh', 'chain',
                                 payload/'reader/chain.py', '--config', config_path)
        if failure:
            self.assertNotEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('Family process failed: '+failure+' 7', result.stderr)
        else:
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        calls = [f for f in config['families'] if (run/'logs'/(f+'.hex')).exists()]
        for f in calls:
            marker = run/f/'COMPLETE.json'
            if marker.exists(): self.assertTrue(json.loads(marker.read_text())['isolated'])
        root = run
        return root,calls

    def test_serial_success_and_compact_output(self):
        root,calls=self.run_case()
        self.assertEqual(calls,['main','away','forward'])
        self.assertEqual(len((root/'ITEMS.jsonl').read_text().splitlines()),3)
        self.assertEqual(json.loads((root/'SUMMARY.json').read_text())['items'],3)
        self.assertNotIn('private',(root/'logs/main.hex').read_text())

    def test_family_failure_stops_without_retry(self):
        root,calls=self.run_case('away')
        self.assertEqual(calls,['main','away'])
        self.assertTrue((root/'FAILED.json').exists())
        self.assertFalse((root/'COMPLETE.json').exists())
        self.assertFalse(json.loads((root/'SUMMARY.json').read_text())['complete'])


if __name__=='__main__':unittest.main()
