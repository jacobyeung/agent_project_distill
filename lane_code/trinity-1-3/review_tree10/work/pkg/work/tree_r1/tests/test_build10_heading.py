import unittest,math
import numpy as np
from student_pilot.fixed_readout import HeadingReadout
from student_pilot.carrier_c1_routing import wrap

class HeadingMath(unittest.TestCase):
    def test_degrees_match_producer(self):
        m=HeadingReadout()
        rng=np.random.default_rng(13)
        for _ in range(2000):
            a,b=rng.normal(size=(2,3,3))
            self.assertEqual(m('yaw',a),round(math.degrees(math.atan2(-a[0,2],a[2,2]))))
            x,y=a[[0,2],2],b[[0,2],2]
            expected=wrap(round(math.degrees(math.atan2(x[0]*y[1]-x[1]*y[0],float(x@y)))))
            self.assertEqual(m('turn',a,b),expected)
        with self.assertRaises(ValueError):m('invalid',np.eye(3))
        self.assertFalse(list(m.parameters()))

    def test_roundtrip(self):
        m=HeadingReadout();n=HeadingReadout();n.load_state_dict(m.state_dict())
        self.assertEqual(m('turn',np.eye(3),np.eye(3)),n('turn',np.eye(3),np.eye(3)))
