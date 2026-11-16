from collections import deque
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

from transformers import PreTrainedTokenizerFast
from student_pilot.carrier_c1_batch_decode import Row
from student_pilot.p3_printed_calculator import PrintedPointRegistry


class InterceptionTests(unittest.TestCase):
    def test_long_native_tokenized_angle_is_intercepted(self):
        path = Path("/scratch/jjyeung/orch_cd/leg_s1_tree/work/fixture/assets/base_v3/tokenizer.json")
        tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(path))
        call = "<angle S=P1 F=P2 Q=P3 rule=medium>"
        ids = tokenizer.encode(call, add_special_tokens=False)
        self.assertGreater(len(ids), 24)
        self.assertLessEqual(len(ids), 96)
        registry = PrintedPointRegistry()
        for point in ([0., 0., 0.], [1., 0., 0.], [1., 0., 1.]):
            registry.register(camera=point, f1=point, spread=0., requested_frame=1)
        row = Row.__new__(Row)
        row.ids, row.tokenizer, row.registry = ids, tokenizer, registry
        row.active, row.records, row.forced = None, [], deque()
        row.max_calls, row.finish, row.ground_layout = 200, None, False
        row.state = NS(openers=set(), cap=1024, mdg=None, ground_backend=None,
                       verify_session=None, rereader=None, geometry=None, tool_context=NS(),
                       heads=NS(mdg_states=None, mdg_backend=None))
        row._call(ids[-1])
        self.assertEqual([record["call"] for record in row.records], [call])
        self.assertNotEqual(row.records[0]["kind"], "error")
        self.assertTrue(row.forced)


if __name__ == "__main__":
    unittest.main()
