import copy
import os
import random
import sqlite3
import threading
import unittest
from unittest.mock import patch

import numpy as np
import torch

from student_pilot import carrier_c1_run as run
from student_pilot.c1_cpu_prefetch import Producer
from tests.so_helpers import root, inputs, native, plan, TinyProcessor, rng_state, same_rng, assert_nested


class PrefetchTests(unittest.TestCase):
    def test_real_rows_cpu_rng_sqlite_processor_ownership_and_exact_bytes(self):
        torch.set_num_threads(8)
        directory = root()
        receipt = inputs(directory)
        model = native()
        sequences, owners, calls, closes = [], {}, [], []
        original_get, original_close = run.Rows.get, run.Rows.close

        def get(rows, stream, index):
            tid = threading.get_ident()
            owners.setdefault(tid,set()).add(id(rows.processor))
            calls.append((stream,index,index))
            before = rng_state()
            value = original_get(rows,stream,index)
            self.assertTrue(same_rng(before,rng_state()), 'Rows.get consumed a global RNG')
            self.assertEqual(torch.get_num_threads(),8)
            return value

        def close(rows):
            closes.append(threading.get_ident())
            return original_close(rows)

        for enabled in ('0','1'):
            calls.clear()
            with patch.dict(os.environ,C1_CPU_PREFETCH=enabled), patch.object(run.Rows,'get',get), patch.object(run.Rows,'close',close):
                rows = run.Rows(receipt,TinyProcessor())
                main_processor = id(rows.processor)
                try:
                    before = rng_state()
                    values = list(run.fetch_plan(rows,model,plan(),0))
                    self.assertTrue(same_rng(before,rng_state()))
                    sequences.append((copy.deepcopy(calls),values))
                    if enabled == '1':
                        producer = rows._c1_cpu_producer
                        self.assertNotEqual(id(producer.rows.processor),main_processor)
                        with self.assertRaises(sqlite3.ProgrammingError):
                            producer.rows.connections['vqa'].execute('SELECT 1')
                finally:
                    rows.close()
        self.assertEqual(sequences[0][0],sequences[1][0])
        assert_nested(self,sequences[0][1],sequences[1][1])
        self.assertGreaterEqual(len(owners),2)
        self.assertTrue(any(tid != threading.get_ident() for tid in closes))

    def test_one_group_lookahead_and_exception_deferred_to_its_boundary(self):
        torch.set_num_threads(8)
        receipt = inputs(root())
        model = native()
        original = run.Rows.get
        future_failed = threading.Event()
        calls = []
        def get(rows,stream,index):
            calls.append((stream,index))
            if stream == 'vqa' and index == 0:
                future_failed.set()
                raise ValueError('planted future row error')
            return original(rows,stream,index)
        with patch.dict(os.environ,C1_CPU_PREFETCH='1'), patch.object(run.Rows,'get',get):
            rows = run.Rows(receipt,TinyProcessor())
            iterator = run.fetch_plan(rows,model,plan(),0)
            try:
                next(iterator)
                self.assertTrue(future_failed.wait(10))
                next(iterator)  # Remaining admitted pose slice is still valid.
                with self.assertRaisesRegex(ValueError,'Final-mode row failure'):
                    next(iterator)
                self.assertEqual(calls,[('pose',0),('pose',1),('vqa',0),('vqa',1)])
            finally:
                iterator.close()
                rows.close()

    def test_native_tokenizer_and_video_processor_are_private_and_deterministic(self):
        torch.set_num_threads(8)
        from tokenizers import Tokenizer, models, pre_tokenizers
        from transformers import PreTrainedTokenizerFast
        from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
        raw = Tokenizer(models.WordLevel({'[UNK]':0,'hello':1,'world':2},unk_token='[UNK]'))
        raw.pre_tokenizer = pre_tokenizers.Whitespace()
        processor = dict(tokenizer=PreTrainedTokenizerFast(tokenizer_object=raw,unk_token='[UNK]'),
                         video=Qwen3VLVideoProcessor(patch_size=16,temporal_patch_size=2,merge_size=2))
        private = copy.deepcopy(processor)
        self.assertIsNot(processor['tokenizer']._tokenizer,private['tokenizer']._tokenizer)
        pixels = np.full((4,32,32,3),100,dtype=np.uint8)
        def encode(p):
            # Match the repository's CPU video fixture: torchvision is absent,
            # so exercise native rescaling/patch packing, not RGB conversion/resize.
            return (p['tokenizer']('hello world'),p['video'](videos=[pixels],do_sample_frames=False,
                      do_resize=False,do_convert_rgb=False,do_normalize=False,return_tensors='pt'))
        before = rng_state()
        expected = encode(processor)
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(encode,private)
            main = encode(processor)
            actual = future.result()
        self.assertEqual(expected[0]['input_ids'],actual[0]['input_ids'])
        for key in expected[1]:
            self.assertTrue(torch.equal(expected[1][key],actual[1][key]))
            self.assertTrue(torch.equal(expected[1][key],main[1][key]))
        self.assertTrue(same_rng(before,rng_state()))


if __name__ == '__main__':
    unittest.main()
