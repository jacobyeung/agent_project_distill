import unittest
import numpy as np
from student_pilot.carrier_c1_decode import respond,CallError
from trace_format.calculator import PrintedPointRegistry
class Refusals(unittest.TestCase):
    def test_bad_frame_writes_no_response(self):
        class Geometry:
            p=np.zeros((32,9))
        for call in ('<pose frame=40>','<move from=0 to=2>','<turn from=1 to=64>'):
            with self.assertRaisesRegex(CallError,'bad_frame'):
                respond(call,PrintedPointRegistry(),Geometry())
