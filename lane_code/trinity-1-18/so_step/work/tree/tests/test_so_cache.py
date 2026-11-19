import os
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
import torch

from student_pilot import pose_samples, carrier_c1_run as run
from student_pilot.c1_decoded_cache import DecodedRGB
from student_pilot.p3_provenance import file_pin
from tests.so_helpers import root, inputs, TinyProcessor, assert_nested


class CacheTests(unittest.TestCase):
    def test_same_encoded_rows_hits_invalidation_and_mutation_isolation(self):
        torch.set_num_threads(8)
        directory = root()
        receipt = inputs(directory)
        values = []
        for setting in ('0','1'):
            with patch.dict(os.environ,C1_DECODED_CACHE_MIB=setting):
                rows = run.Rows(receipt,TinyProcessor())
                try:
                    values.append([rows.get(stream,0) for stream in receipt['streams']])
                finally:
                    rows.close()
        assert_nested(self,values[0],values[1])
        from student_pilot import c1_decoded_cache
        self.assertGreater(c1_decoded_cache._cache.hits,0)
        pin = file_pin(directory/'rgb.png')
        with patch.dict(os.environ,C1_DECODED_CACHE_MIB='1'):
            first = pose_samples.load_frames({'frames':[pin]})
            first[:] = 0
            self.assertTrue(pose_samples.load_frames({'frames':[pin]}).any())
            Image.new('RGB',(32,32),(200,10,50)).save(directory/'rgb.png')
            with self.assertRaisesRegex(ValueError,'Stale frame pin'):
                pose_samples.load_frames({'frames':[pin]})
            changed = pose_samples.load_frames({'frames':[file_pin(directory/'rgb.png')]})
            self.assertEqual(changed[0,0,0].tolist(),[200,10,50])

    def test_bounded_cache_and_non_rgb_errors(self):
        directory = root()
        cache = DecodedRGB(64*64*3)
        for i in range(3):
            path = directory/f'{i}.png'
            Image.new('RGB',(64,64),(i,0,0)).save(path)
            cache.get(path,str(path))
            self.assertLessEqual(cache.bytes,cache.capacity)
            self.assertEqual(len(cache.values),1)
        path = directory/'gray.png'
        Image.new('L',(32,32),10).save(path)
        with self.assertRaisesRegex(ValueError,'Source is not RGB'):
            cache.get(path,str(path))


if __name__ == '__main__':
    unittest.main()
