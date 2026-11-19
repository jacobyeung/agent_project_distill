"""Test the native profile's gate, vote limit and depth-unit contracts."""
from pathlib import Path
import unittest,uuid
from types import SimpleNamespace
import numpy as np
from tests.test_ground_r2 import geometry,synthetic,TMP
from student_pilot.ground_profiles import load_geometry
from student_pilot.ground_sources import CachedSAM3
from student_pilot.scene_state import SceneState
from student_pilot.p3_printed_calculator import PrintedPointRegistry
from rk.sam3mask import tower
from rk.programs import load_heads

class NativeProfile(unittest.TestCase):
    def test_live_source_uses_the_archived_cap_five_pool(self):
        from PIL import Image
        from tests.test_sam3_tower import StubBackend
        from student_pilot.sam3_tower import Sam3Tower
        from student_pilot.ground_sources import TowerSAM3
        g=geometry();tower_model=Sam3Tower({'device':'cpu'},backend=StubBackend())
        frames=[Image.new('RGB',(640,480)) for _ in range(32)]
        source=TowerSAM3(tower_model,frames,g.frame_map,'cap-five-fixture',tower())
        candidates=source.selector_candidates('chair')
        self.assertEqual(len(candidates),32*5)
        self.assertTrue(all(c.instance<5 and c.confidence>.5 for c in candidates))
        default=tower_model.detect(source.encoded,'chair')
        self.assertGreater(len(default[0].scores),5)

    def test_metric_tower_depth_does_not_apply_scale_twice(self):
        z=synthetic();p=TMP/f'metric_tower_{uuid.uuid4().hex}.npz';np.savez(p,**z)
        g=load_geometry(p,geometry().frame_map,'tower_scaled');reference=load_heads(p)
        self.assertEqual(g.contract.depth_scale_count,1)
        self.assertEqual(g.contract.profile,'scaled_g3t_metric')
        for k in (1,32):
            for a,b in zip(g.lift(k,np.array([[215.,626.]])),reference.lift(k,np.array([[215.,626.]]))):
                np.testing.assert_array_equal(a,b)
        with self.assertRaisesRegex(ValueError,'depth_source'):load_geometry(p,g.frame_map,'other')

if __name__=='__main__':unittest.main()
