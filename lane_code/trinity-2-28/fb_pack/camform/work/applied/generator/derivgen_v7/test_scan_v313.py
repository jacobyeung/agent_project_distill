import unittest
import numpy as np
from derivgen.scan_witness_v313 import scan_target

class Geo:
    K=np.repeat(np.eye(3)[None],32,axis=0)
    depth=np.ones((32,8,8))*2
    def cam(self,k):return np.eye(3),np.zeros(3)
    def lift(self,k,uv,patch=False):
        xy=np.floor(np.asarray(uv)*8/1000)+.5
        p=np.column_stack((xy,np.ones(len(xy))))*2
        return p,p,np.zeros(len(p))

class ScanTests(unittest.TestCase):
    def test_hidden_true_pair_is_unavailable(self):
        mask=np.ones((32,8,8),bool)
        ref=dict(distance_m=2.,closest_pairs_world=[[[6,6,4],[8,6,4]]],authority='synthetic complete scan',complete_tolerance_set=True)
        r=scan_target(ref,Geo(),[mask,mask],[[1],[19]])
        self.assertEqual(r['status'],'unavailable');self.assertIsNone(r['full_surface_distance_m'])

    def test_visible_tied_alternative_and_disjoint_frames(self):
        mask=np.ones((32,8,8),bool)
        ref=dict(distance_m=2.,closest_pairs_world=[[[6,6,4],[8,6,4]],[[3,3,2],[5,3,2]]],authority='synthetic complete scan',complete_tolerance_set=True)
        r=scan_target(ref,Geo(),[mask,mask],[[2],[19]])
        self.assertEqual(r['status'],'ok');self.assertEqual(r['frames'],[2,19]);self.assertEqual(r['full_surface_distance_m'],2.)

    def test_invalid_tie_distance_rejected(self):
        mask=np.ones((32,8,8),bool)
        ref=dict(distance_m=1.,closest_pairs_world=[[[3,3,2],[5,3,2]]],authority='fixture')
        with self.assertRaisesRegex(ValueError,'outside_tolerance'):scan_target(ref,Geo(),[mask,mask],[[2],[19]])

if __name__=='__main__':unittest.main()
