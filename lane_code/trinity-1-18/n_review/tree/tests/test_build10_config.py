import unittest
from trace_format.readout_config import load
from trace_format.calculator import PrintedPointRegistry
class Config(unittest.TestCase):
    def test_shape_config_and_decimal(self):
        c=load()
        self.assertEqual(c['frame_count'],32)
        r=PrintedPointRegistry(frame_count=c['frame_count'])
        r.register(camera=[0.,0.,1.],f1=[0.,0.,1.],spread=0.,requested_frame=1)
        self.assertIn('1.00',r.execute('<cam_dist P1>')['text'])
        with self.assertRaises(ValueError):
            r.register(camera=[0.,0.,1.],f1=[0.,0.,1.],spread=0.,requested_frame=33)
