import sys
sys.dont_write_bytecode = True
import json
import unittest
from pathlib import Path
import numpy as np
import scale_analysis as s

class ScaleTests(unittest.TestCase):
    def test_scale_rule_strict_filters(self):
        d = np.ones((32,51,51))*2
        c = np.tile(np.arange(51), (32,51,1)).astype(float)
        v = d*1.7
        v[:,:,30] = .1
        v[:,:,31] = 10
        d[:,:,32] = 0
        c[:,:,33] = np.nan
        scale, mask, threshold = s.estimate(d,c,v)
        self.assertAlmostEqual(scale,1.7)
        self.assertEqual(threshold,24.5)
        self.assertFalse(mask[:,:,30:34].any())
        self.assertFalse(mask[:,:,:25].any())
        with self.assertRaises(ValueError):
            s.estimate(np.ones((2,2)),np.ones((2,2)),np.ones((2,2)))

    def test_room_disjoint_and_deterministic(self):
        rooms=['r1','r1','r2','r3','r4','r5']
        a,b=s.split_rooms(rooms)
        self.assertFalse(set(a)&set(b))
        self.assertEqual(set(a+b),set(rooms))
        self.assertEqual([a,b],s.split_rooms(rooms[::-1]))

    def test_bars_refusal(self):
        # Persistent fixtures avoid deletion commands and stay inside the workspace.
        p=s.ROOT/'test_fixtures'/'scores_exist'
        p.mkdir(parents=True,exist_ok=True)
        (p/'SCALE_RESULT.json').write_text(json.dumps(dict(input_sha256={str(Path(__file__)):s.sha(__file__)},synthetic=True)))
        with self.assertRaisesRegex(RuntimeError,'score file exists'):
            s.refuse_scores(p)

    def test_mra_matches_harness(self):
        gt=np.ones(8)
        pred=np.array([0,.5,.500001,.8,.95,1,1.5,2])
        np.testing.assert_allclose(s.pair_scores(pred,gt),[100*s.mra(p,g) for p,g in zip(pred,gt)])

    def test_pose_translation_decoding(self):
        # Camera 2 has a 180-degree orientation: raw t differences are incorrect.
        cam=np.zeros((2,9));cam[0,6]=1;cam[1,5]=1
        cam[1,:3]=[2,0,0];cam[:,7:]=1
        _, centres,_=s.to_gravity_reference_frame(cam,[0,-1,0])
        self.assertAlmostEqual(np.linalg.norm(centres[1]-centres[0]),2.)

    def test_log_fit_equal_room_weight(self):
        r=[dict(room='a',gt=np.ones(1),pred={'raw':np.ones(1)*2}),
           dict(room='b',gt=np.ones(100),pred={'raw':np.ones(100)*8})]
        self.assertAlmostEqual(s.fit(r,{'a','b'},'raw'),.25)

if __name__=='__main__':
    unittest.main()
