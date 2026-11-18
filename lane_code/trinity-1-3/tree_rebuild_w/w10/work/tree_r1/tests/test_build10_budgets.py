import unittest
from types import SimpleNamespace as NS
from student_pilot.carrier_c1_batch_decode import Row
class Tokens:
    eos_token_id=1
    def convert_tokens_to_ids(self,s):return 2
    def decode(self,ids,**kw):return '<pose frame=1>' if ids==[3] else '<pose '+('x'*len(ids))
    def encode(self,s,**kw):return list(range(len(s)))
class Budgets(unittest.TestCase):
    def row(self,max_calls=1):
        settings=dict(frame_count=32,max_call_tokens=2,max_calls=1)
        return Row(NS(native=NS(generation_config=None),cap=100,openers={3}),NS(tokenizer=Tokens()),
                   NS(readout_config=settings,carrier_id=4),mode='own',pose_source='own',max_calls=max_calls,
                   max_new_tokens=None,logits_processor=None)
    def test_max_calls_refuses(self):
        r=self.row();r.ids=[3];r.records=[{}]
        with self.assertRaisesRegex(ValueError,'call budget'):r._call(3)
        self.assertFalse(r.forced)
        with self.assertRaises(ValueError):self.row(2)
    def test_call_tokens_refuse(self):
        r=self.row();r.active=0;r.ids=[5,5,5]
        with self.assertRaisesRegex(ValueError,'call token'):r._call(5)
        self.assertFalse(r.forced)
