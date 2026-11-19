"""Synthetic CPU checks of the exact comparison gate; never runs a model."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest
import uuid

HERE=Path(__file__).resolve().parent
COMPARE=HERE/'compare.py' if (HERE/'compare.py').exists() else HERE.parent/'a10.py'
SAMPLE=HERE/'sample50.json' if (HERE/'sample50.json').exists() else HERE/'u0.json'
spec=importlib.util.spec_from_file_location('parity_compare',COMPARE)
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.sample=json.loads(SAMPLE.read_text())
        self.root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex
        self.root.mkdir(parents=True)
        self.records=[dict(id=r['id'],type=r['question_type'],arm='tower',mode='none',complete=True,
            seconds=1.,output=dict(text='</think>\n1',tokens=[1],finish='eos',calls={'records':[],'calls':{},'unserved':{}},
                                  heads={'pose9':[[-0.]*9],'gravity':[[0.,0.,1.]]},scale=None,
                                  scores={'answer':1.},timings={'total_s':1.},
                                  read_cache={'enabled':['read_processor_cache','read_vision_cache','read_sam_cache'],
                                              'max_bytes':1000000,'held_bytes':1000,'peak_bytes':2000,
                                              'stats':{k:{'hits':1,'misses':1} for k in ('processor','vision','sam_features','sam_detections')}},
                                  audit={'violations':[]},entries={'prefill':1,'steps':1},prompt_tokens=32,
                                  frames={'count':32,'matches_training':True,'layout':'spread'},
                                  decode_budget={'total_tokens':1},id='devrows:'+r['id'],key='devrows:'+r['id'],
                                  room=r.get('room',r['room_key']),question_type=r['question_type'],stratum=None,arm='own_depth',seconds=1.))
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
        for i,(field,value) in enumerate((('tokens',[2]),('calls',{'records':[{'call':'<ground>','family':'ground','served':True,'response':'changed','at_token':1,'forced_tokens':1}],'calls':{'ground':1},'unserved':{}}),
                                         ('heads',{'pose9':[[0.]*9],'gravity':[[0.,0.,1.]]}),('finish','max_calls'))):
            changed=copy.deepcopy(self.records);changed[0]['output'][field]=value
            b=self.write('right'+str(i),changed)
            self.assertFalse(checker.compare(a,b,self.sample)['passed'])

    def test_each_enabled_cache_requires_hits(self):
        a=self.write('left',self.records)
        for index,name in enumerate(('processor','vision','sam_features','sam_detections')):
            changed=copy.deepcopy(self.records)
            for row in changed:row['output']['read_cache']['stats'][name]['hits']=0
            b=self.write('zero'+str(index),changed)
            result=checker.compare(a,b,self.sample)
            self.assertFalse(result['passed']);self.assertEqual(result['cache_failures'],['right:'+name+':no_hits'])
        changed=copy.deepcopy(self.records)
        for row in changed:row['output'].pop('read_cache')
        b=self.write('none',changed)
        with self.assertRaisesRegex(ValueError,'Enabled cache declaration is missing or differs'):checker.compare(a,b,self.sample)
        self.assertTrue(checker.compare(a,b,self.sample,enabled_caches=())['passed'])
        self.assertTrue(checker.compare(a,a,self.sample,cache_sides=('left','right'))['passed'])

    def test_scale_empty_fields_and_nested_served_responses_are_required(self):
        a=self.write('left',self.records)
        changes=[('scale','missing'),('text',''),('tokens',[]),('heads',{}),('scores',{}),
                 ('calls',{'records':[{'call':'<ground>','family':'ground','served':True,'at_token':1}],
                           'calls':{'ground':1},'unserved':{}})]
        for index,(field,value) in enumerate(changes):
            changed=copy.deepcopy(self.records)
            if value=='missing':changed[0]['output'].pop(field)
            else:changed[0]['output'][field]=value
            b=self.write('invalid'+str(index),changed)
            with self.assertRaises(ValueError):checker.compare(a,b,self.sample)

    def test_response_changes_are_detected(self):
        original=copy.deepcopy(self.records)
        call={'call':'<move>','family':'move','served':True,'at_token':1,'response':'dx=1','forced_tokens':1}
        original[0]['output']['calls']={'calls':{'move':1},'unserved':{},'records':[call]}
        a=self.write('served',original);changed=copy.deepcopy(original)
        changed[0]['output']['calls']['records'][0]['response']='dx=2'
        b=self.write('changed',changed)
        self.assertFalse(checker.compare(a,b,self.sample)['passed'])

    def test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map(self):
        import sys
        sys.path.insert(0,str(HERE if (HERE/'a9.py').exists() else HERE.parent))
        from a9 import Codec,PublicJSON
        wire=PublicJSON(Codec(self.sample))
        a=self.write('public-a',self.records);b=self.write('public-b',self.records)
        for root in (a,b):
            path=root/'journals/0/0/items.jsonl'
            path.write_text(''.join(wire.dumps(row)+'\n' for row in self.records))
            self.assertNotIn('vsi',path.read_text());self.assertNotIn('scannet',path.read_text())
        self.assertTrue(checker.compare(a,b,self.sample,codec=wire.codec)['passed'])

    def test_source_hash_gate_rejects_changed_or_missing_hashes(self):
        a=self.write('left',self.records);b=self.write('right',self.records)
        fields=('reader_sha256','maker_sha256','evaluator_code_sha256','expected_calls_sha256','r0_code_sha256','parity_code_sha256')
        binding={field:'a'*64 for field in fields}
        for root in (a,b):(root/'journals/0/0/environment.json').write_text(json.dumps({'binding':binding}))
        self.assertTrue(checker.compare_source_hashes(a,b)['passed'])
        binding['reader_sha256']='b'*64
        (b/'journals/0/0/environment.json').write_text(json.dumps({'binding':binding}))
        self.assertFalse(checker.compare_source_hashes(a,b)['passed'])
        binding.pop('maker_sha256')
        (b/'journals/0/0/environment.json').write_text(json.dumps({'binding':binding}))
        with self.assertRaises(ValueError):checker.compare_source_hashes(a,b)

    def test_missing_duplicate_and_partial_tail_rejected(self):
        a=self.write('left',self.records)
        for name,rows in (('missing',self.records[:-1]),('duplicate',self.records+self.records[:1])):
            b=self.write(name,rows)
            with self.assertRaises(ValueError):checker.compare(a,b,self.sample)
        b=self.write('partial',self.records)
        with (b/'journals/0/0/items.jsonl').open('ab') as f:f.write(b'{')
        with self.assertRaises(ValueError):checker.compare(a,b,self.sample)


if __name__=='__main__':unittest.main(verbosity=2)
