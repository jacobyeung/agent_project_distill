"""Fresh A1 preparation binds the fixed camera settings and four-hour recipe."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from student_pilot import decoupled_v_run as run
from student_pilot.decoupled_vc import VC_BATCH4H_RECIPE
from student_pilot.p3_provenance import file_pin, write
from tests.test_decoupled_pose_fix import settings


class AllFrameRecipeTests(unittest.TestCase):
    def test_fresh_preparation_and_tampering(self):
        root = Path(tempfile.mkdtemp(dir=os.environ['LANE_TEST_OUTPUT']))
        write(root/'camera.json', {'camera': settings()})
        write(root/'division.json', dict(schema='diagnostic-whole-scene-division-v1',
            training_only=True, train_scenes=['d/s'], heldout_scenes=[]))
        write(root/'bank.json', {})
        row = dict(qid='r', dataset='d', scene='s', category='camera_pose_only', student_input={'frames': []})
        (root/'rows.jsonl').write_text(json.dumps(row)+'\n')
        cfg = dict(schema='decoupled-v-run-v1', mode='decoupled_vc', all_frames=True,
            recipe=copy.deepcopy(VC_BATCH4H_RECIPE), camera_overrides=dict(run.SPATIAL_CAMERA),
            base_identity='fixture', base_root='/unused', init_heads=None,
            camera_source=file_pin(root/'camera.json'), division=file_pin(root/'division.json'),
            bank=file_pin(root/'bank.json'), rows=file_pin(root/'rows.jsonl'),
            preparation_output=str(root/'prepared'), preparation=None, admission=None)
        manifest = dict(kind='base', root='/unused', base_identity='fixture', feature_encoder_sha256='a'*64)
        with patch.object(run, 'base_manifest', return_value=manifest), \
             patch.object(run, 'processor_for'), patch.object(run, 'encode'), \
             patch('student_pilot.compact_label_bank.load_bank_for_rows',
                   return_value=([{}], dict(depth_rows=1, gravity_rows=1))) as bank:
            receipt = run.prepare(cfg)
        self.assertEqual(bank.call_args.args[2]['max_groups'], 32)
        self.assertEqual(receipt['settings']['anchors'], list(range(1, 33)))
        self.assertEqual(receipt['settings']['feature_backing'], 'decoupled_vc')
        for key, value in run.SPATIAL_CAMERA.items():
            self.assertEqual(receipt['settings']['camera'][key], value)
        cfg['preparation'] = file_pin(root/'prepared/receipt.json')
        self.assertEqual(run.prepared(cfg)[0], receipt)
        for key in ('camera_overrides', 'recipe'):
            changed = copy.deepcopy(cfg)
            if key == 'camera_overrides':
                changed.pop(key)
            else:
                from student_pilot.decoupled_vc import VC_RECIPE
                changed[key] = VC_RECIPE
            self.assertNotEqual(run.identity(cfg), run.identity(changed))
            with self.assertRaisesRegex(ValueError, 'CPU preparation differs'):
                run.prepared(changed)
        bad = copy.deepcopy(receipt)
        bad['settings']['camera'].pop('pose_reference')
        write(root/'bad.json', bad)
        with self.assertRaisesRegex(ValueError, 'Prepared camera overrides differ'):
            run.prepared({**cfg, 'preparation': file_pin(root/'bad.json')})


if __name__ == '__main__':
    unittest.main()
