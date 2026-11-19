import unittest
import torch
from student_pilot.c1_batch_metrics import Components


class MetricsTests(unittest.TestCase):
    def setUp(self):
        from tests.so_helpers import reset_switches
        reset_switches(self)

    def test_python_float_accumulation_order_and_mixed_dtypes(self):
        torch.set_num_threads(8)
        recorder = Components(72)
        expected, streams = {}, {}
        for i in range(72):
            stream = 'pose' if i%3 else 'vqa'
            row = {'pose':torch.tensor((-1.)**i * (i+.125),dtype=torch.float32),
                   'vqa':torch.tensor(i*.01,dtype=torch.bfloat16), 'extra':1e-20}
            recorder.add(stream,row)
            for key,value in row.items():
                expected[key] = expected.get(key,0.) + float(value)/72
            streams[stream] = streams.get(stream,0.) + float(row[stream])
        self.assertEqual(recorder.finish(),(expected,streams))


if __name__ == '__main__':
    unittest.main()
