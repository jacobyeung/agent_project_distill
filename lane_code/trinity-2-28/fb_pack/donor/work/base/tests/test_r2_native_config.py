"""The native validator accepts both configured arms and each fusion stage."""
import unittest
from student_pilot import carrier_c1_run as R, r2_config as C
from student_pilot import r2_mix as M
from student_pilot.p3_provenance import load
from tests.test_gf1 import fixture
from tests.test_r2_build import dense
from tests.test_r2_data_path import directory, LANE


class NativeConfig(unittest.TestCase):
    def test_native_configuration_validation(self):
        root=directory(); manifest=dense(root)
        parent=load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json')
        for stage in (1,2):
            _,_,native=fixture(stage)
            for connector in ('none','gf1'):
                cfg=C.configure(parent,connector,stage=stage,dense_manifest=manifest if connector=='gf1' else None, init_pin=INIT_PIN)
                cfg=C.apply_native(cfg,native['geometry_online'] if connector=='gf1' else None)
                R.validate(cfg)
                self.assertNotIn('mdg',cfg)
                self.assertEqual(cfg['recipe']['global_batch'],288)
                self.assertEqual(cfg['recipe']['steps'],cfg['steps'])
                self.assertLessEqual(max(cfg['recipe']['milestones']),cfg['steps'])
                self.assertEqual(cfg['recipe']['stream_rows_per_step'],dict(vqa=128,routing=64,pose=64,pointing=32))
                fallback=C.bind_mix(cfg,M.table(True))
                R.validate(fallback)
                self.assertEqual(fallback['recipe']['stream_rows_per_step']['pose'],60)
                self.assertEqual(fallback['recipe']['stream_rows_per_step']['pointing'],36)

from tests.r2_init_fixture import PIN as INIT_PIN
