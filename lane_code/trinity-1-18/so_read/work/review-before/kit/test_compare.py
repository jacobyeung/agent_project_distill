"""Synthetic CPU checks of the exact comparison gate; never runs a model."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest
import uuid

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('parity_compare',HERE/'compare.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.sample=json.loads((HERE/'sample50.json').read_text())
        self.root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex
        self.root.mkdir(parents=True)
        self.records=[dict(id=r['id'],type=r['question_type'],arm='tower',mode='none',complete=True,
            seconds=1.,output=dict(text='</think>\n1',tokens=[1],finish='eos',calls={'records':[]},
                                  heads={'pose9':[-0.]},scores={'answer':1.},timings={'total_s':1.}))
                      for r in self.sample['items']]

    def write(self,name,records):
        root=self.root/name;folder=root/'journals/0/0';folder.mkdir(parents=True)
        (folder/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
        return root

    def test_telemetry_different_exact_trace_passes(self):
        a=self.write('left',self.records);changed=copy.deepcopy(self.records)
        for r in changed:r['seconds']=2.;r['output']['timings']['total_s']=3.
        b=self.write('right',changed);result=checker.compare(a,b,self.sample)
        self.assertTrue(result['passed']);self.assertEqual(result['left_sha256'],result['right_sha256'])

    def test_changed_answer_detected_even_when_score_unchanged(self):
        a=self.write('left',self.records);changed=copy.deepcopy(self.records)
        changed[0]['output']['text']='</think>\n1.01'
        b=self.write('right',changed);result=checker.compare(a,b,self.sample)
        self.assertFalse(result['passed']);self.assertTrue(result['differences'][0]['same_score'])

    def test_tokens_calls_heads_and_finish_each_detected(self):
        a=self.write('left',self.records)
        for i,(field,value) in enumerate((('tokens',[2]),('calls',{'records':[{'response':'changed'}]}),
                                         ('heads',{'pose9':[0.]}),('finish','max_calls'))):
            changed=copy.deepcopy(self.records);changed[0]['output'][field]=value
            b=self.write('right'+str(i),changed)
            self.assertFalse(checker.compare(a,b,self.sample)['passed'])

    def test_missing_duplicate_and_partial_tail_rejected(self):
        a=self.write('left',self.records)
        for name,rows in (('missing',self.records[:-1]),('duplicate',self.records+self.records[:1])):
            b=self.write(name,rows)
            with self.assertRaises(ValueError):checker.compare(a,b,self.sample)
        b=self.write('partial',self.records)
        with (b/'journals/0/0/items.jsonl').open('ab') as f:f.write(b'{')
        with self.assertRaises(ValueError):checker.compare(a,b,self.sample)


if __name__=='__main__':unittest.main(verbosity=2)
