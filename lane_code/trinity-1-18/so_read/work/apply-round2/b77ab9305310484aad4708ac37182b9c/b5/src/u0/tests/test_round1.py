"""Independent review regressions; READ_REVIEW_BEFORE=1 selects reviewed code."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import uuid
from contextlib import nullcontext
import types
import unittest
from unittest.mock import patch
import numpy as np
import torch
torch.set_num_threads(8)
SRC=Path(__file__).resolve().parents[2]
L=SRC.parent.parent
BEFORE=os.environ.get('READ_REVIEW_BEFORE')=='1'
E=SRC/'u0'
BASE=Path(os.environ.get('READ_REVIEW_BEFORE_ROOT',str(SRC.parent/'review-before/src')))
INPUT=Path(os.environ['READ_INPUT_SRC'])

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

C=load('review_cache',BASE/'b/e2e_reader/read_cache.py' if BEFORE else E/'a0.py')
checker=load('review_compare',L/'work/review-before/kit/compare.py' if BEFORE else E/'a10.py')

class Qwen3_5VisionModel(torch.nn.Module):
    def __init__(self):
        super().__init__();self.weight=torch.nn.Parameter(torch.tensor(2.));self.config=types.SimpleNamespace(to_dict=lambda:{})
    def forward(self,x):return x*self.weight

class ReviewRegressions(unittest.TestCase):
    def test_f1_nested_mapping_boundaries_and_stale_processor(self):
        a={'a':{'b':1},'c':2};b={'a':{'b':1,'c':2}}
        self.assertNotEqual(C.digest(a),C.digest(b))
        class Processor:
            def to_dict(self):return {}
            def __call__(self,x):return json.dumps(x)
        proxy=C.VideoProcessorCache(Processor(),C.ReadCache(1000000))
        self.assertNotEqual(proxy(a),proxy(b))

    def test_f2_absent_hits_and_incomplete_trace_cannot_pass(self):
        sample=json.loads((E/'tests/u0.json').read_text())
        with nullcontext(Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex) as temp:
            roots=[]
            for name in ('a','b'):
                root=Path(temp)/name;folder=root/'journals/0/0';folder.mkdir(parents=True);roots.append(root)
                records=[dict(id=r['id'],type=r['question_type'],arm='tower',mode='none',complete=True,seconds=1.,
                              output=dict(text='',tokens=[],finish='eos',calls={'records':[]},heads={},scores={})) for r in sample['items']]
                (folder/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
            with self.assertRaisesRegex(ValueError,'^Missing required trace field: scale$'):
                checker.compare(*roots,sample)

    def test_f3_original_files_and_hash_tree_have_no_off_changes(self):
        root=BASE if BEFORE else SRC
        for rel in ('b/e2e_reader/parity.py','b/e2e_reader/real.py','b/e2e_reader/stage1.py','h1eval/h10/launch.py'):
            self.assertEqual((INPUT/rel).read_bytes(),(root/rel).read_bytes(),rel)
        for rel in ('b/e2e_reader/read_cache.py','h1eval/h10/atomic_journal.py'):
            self.assertFalse((root/rel).exists(),rel)

    def test_f4_replaced_parameter_cannot_reuse_old_value(self):
        v=Qwen3_5VisionModel().eval().requires_grad_(False)
        cache=C.ReadCache(1000000);C.install_vision_cache(types.SimpleNamespace(model=types.SimpleNamespace(visual=v)),cache)
        with torch.no_grad():
            self.assertEqual(v(torch.tensor(1.)).item(),2.)
            self.assertEqual(v(torch.tensor(1.)).item(),2.)
            self.assertEqual(cache.stats['vision']['hits'],1)
            v.weight=torch.nn.Parameter(torch.tensor(9.),requires_grad=False)
            try:actual=v(torch.tensor(1.)).item()
            except ValueError:return
            self.assertEqual(actual,9.)

    def test_f5_deadline_handler_does_not_repair_after_lock_unwinds(self):
        p=BASE/'h1eval/h10/launch.py' if BEFORE else E/'a4.py'
        text=p.read_text();handler=text.split('def run_types')[1].split('except ReadDeadline')[1].split('                    raise')[0]
        self.assertNotIn('.recover()',handler)

    def test_f6_public_configuration_has_no_descriptive_paths(self):
        path=BASE.parent/'kit/array_config.example.json' if BEFORE else E/'tests/u1.json'
        cfg=json.loads(path.read_text())
        import sys
        sys.path.insert(0,str(E))
        from a9 import validate_config
        try:validate_config(cfg)
        except ValueError as error:self.fail(str(error))

    def test_f7_key_overhead_prevents_unbounded_retention(self):
        cache=C.ReadCache(1000000)
        key='x'*2000000
        cache.call('processor',key,lambda:1)
        self.assertEqual(len(cache.entries),0)

    def test_f7_eviction_precedes_snapshot_allocation(self):
        cache=C.ReadCache(400000)
        cache.call('processor','first',lambda:np.zeros(30000,np.uint8))
        original=C.snapshot;observed=[]
        def snapshot(value):
            observed.append(cache.held_bytes)
            return original(value)
        with patch.object(C,'snapshot',side_effect=snapshot):
            cache.call('processor','second',lambda:np.zeros(30000,np.uint8))
        self.assertTrue(observed)
        self.assertEqual(observed[0],0)

def load_tests(loader, tests, pattern):
    if not BEFORE:
        # Exercise bytes, public transport, and lock ownership in this suite.
        journal=load('round1_journal_tests',E/'tests/test_read_journal.py')
        public=load('round1_public_tests',E/'tests/test_public.py')
        off=load('round1_off_tests',E/'tests/test_off.py')
        tests.addTest(journal.RunnerTests('test_deadline_recovery_keeps_writer_lock'))
        tests.addTests(loader.loadTestsFromTestCase(public.PublicTests))
        tests.addTests(loader.loadTestsFromTestCase(off.OffContractTests))
    return tests

if __name__=='__main__':unittest.main(verbosity=2)
