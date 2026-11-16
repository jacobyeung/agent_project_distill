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
        root=ROOT/'evidence'/('chain_'+uuid.uuid4().hex)
        config=dict(spec=dict(run=str(root),step=100,interpreters=dict(vllm='fixture')),
                    admission={},families=['main','away','forward'],plan_sha256='a'*64)
        calls=[]
        class Process:
            def __init__(self,argv,**kwargs):
                self.family=argv[-1];calls.append(self.family)
                self.stdout=io.BytesIO(b'private engine diagnostic\n')
            def wait(self):
                if self.family==failure:return 7
                p=root/self.family;p.mkdir()
                (p/'COMPLETE.json').write_text(json.dumps(dict(items=1)))
                (p/'ITEMS.jsonl').write_text(json.dumps(dict(id=self.family,family=self.family,
                                            task_type='t',score=1))+'\n')
                return 0
        with patch.object(C.subprocess,'Popen',Process),patch.dict(C.os.environ,dict(A_JOB_CONFIG='fixture')):
            if failure:
                with self.assertRaises(RuntimeError):C.run(config)
            else:C.run(config)
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
