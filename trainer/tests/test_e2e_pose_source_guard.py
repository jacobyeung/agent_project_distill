"""Refuse the audited clean-camera source before opening a pose database."""
from unittest import TestCase, mock

from student_pilot import c1_pose_mix, carrier_c1_run as run
from student_pilot.pose_source_guard import refuse_a4_r_s
from tests.test_e2e_merge import config


class PoseSourceGuard(TestCase):
    def test_known_source_names_and_renamed_receipt_pin_refuse(self):
        for value in ('/data/A4/r_s/receipt.json', {'source': 'A4 r_s'},
                      {'sha256': '521fcc55' + '0' * 56}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'clean camera pool'):
                refuse_a4_r_s(value)
        refuse_a4_r_s({'sources': ['a2v3', 'a3v2', '/a4/r_spp/receipt.json'], 'lm_lr_scale': .6})

    def test_run_validation_refuses_direct_r_s_binding(self):
        cfg = config()
        cfg['streams']['pose'] = dict(path='/a4/r_s/receipt.json', sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'clean camera pool'):
            run.validate(cfg)

    def test_mix_preparation_refuses_hidden_receipt_source_before_database_io(self):
        spec = dict(schema='c1-pose-mix-v1', sources=[dict(kind='rows', frame_prefix=None,
                    receipt=dict(path='/renamed/receipt.json', sha256='0' * 64))])
        receipt = dict(schema='pose-stream-a4-v1', inputs={'source': '/a4/r_s/rows.sqlite'})
        with mock.patch.object(c1_pose_mix, 'pinned', side_effect=lambda p: p), \
                mock.patch.object(c1_pose_mix, 'load', side_effect=[spec, receipt]), \
                mock.patch.object(c1_pose_mix, 'connect') as connect:
            with self.assertRaisesRegex(ValueError, 'clean camera pool'):
                c1_pose_mix.prepare({}, '/unused', set(), set(), None)
            connect.assert_not_called()

    def test_both_variant_pose_pins_remain_the_a2_a3_spec(self):
        for variant in ('E2E-1G', 'E2E-1C'):
            cfg = config(variant)
            self.assertTrue(cfg['streams']['pose']['sha256'].startswith('8957d119'))
