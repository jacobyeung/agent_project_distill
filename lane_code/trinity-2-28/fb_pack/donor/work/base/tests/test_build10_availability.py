import unittest
import numpy as np
from student_pilot.fixed_readout import HeadingReadout
class Availability(unittest.TestCase):
    def test_threshold_and_roundtrip(self):
        for threshold in (.2,.3,.4):
            m=HeadingReadout(threshold)
            n=HeadingReadout();n.load_state_dict(m.state_dict())
            for down in ([0,1,0],[0,0,1],[0,.3,.9539392014169457]):
                d=np.asarray(down,float);d/=np.linalg.norm(d)
                expected=bool(np.linalg.norm(d[:2])>=threshold)
                self.assertEqual(m('availability',np.eye(3),down,threshold),expected)
                self.assertEqual(n('availability',np.eye(3),down,threshold),expected)
            with self.assertRaises(ValueError):m('availability',np.eye(3),[0,1,0],.7)
        with self.assertRaises(ValueError):HeadingReadout(0)
