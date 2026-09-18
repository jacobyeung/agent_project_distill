"""CPU checks against the authenticated first-scene assets, without network mocks."""
import os
import unittest
from pathlib import Path
import numpy as np
from gt_scene_assets import DATA_ROOT, read_json, sha, validate_scene, load_arrays, verify

TASK = DATA_ROOT / 'runtime_control/gt_teacher_r1313'
RECEIPT = TASK / 'scene104acbf7d2_v1/scene_receipt.json'


class GTTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import time
        import gt_tool_bindings
        cls.tools = gt_tool_bindings
        cls.receipt = validate_scene(read_json(RECEIPT), load_dense=True)
        cls.root = TASK / 'tool_fixtures' / str(time.time_ns())
        cls.root.mkdir(parents=True, exist_ok=False)
        os.environ.update(R1313_SCENE_RECEIPT=str(RECEIPT), R1313_SCENE_RECEIPT_SHA256=sha(RECEIPT),
                          REQ73_RUN_OUTPUT_ROOT=str(cls.root))
        cls.scene = cls.receipt['runtime_scene_id']
        cls.proof = cls.receipt['rendering_proof'][0]
        cls.label = cls.proof['label']
        from gt_training_r1313 import grounding_provider
        cls.provider = grounding_provider()

    def test_fixed_donor_routes(self):
        scene, label = self.scene, self.label
        found = self.tools.find_frames_with_object.invoke({'scene_id': scene, 'object_label': label, 'num_frames': 'all'})
        self.assertEqual(found, self.provider.find_frames(scene, label, 'all'))
        self.assertIn(1, found)
        args = {'scene_id': scene, 'frame_index': 1, 'object_label': label}
        self.assertEqual(self.tools.predict_2d_bounding_box.invoke(args), self.provider.boxes(scene, 1, label))
        points = self.tools.predict_2d_points.invoke({'scene_id': scene, 'frame_index': 1, 'query': label})
        primitive = self.provider.points(scene, 1, label)
        self.assertEqual([{k: p[k] for k in ('instance_id', 'label', 'pixel_norm')} for p in points], primitive)
        self.assertTrue(all(np.isfinite(p['world']).all() for p in points))
        masks = self.tools.predict_2d_segmentation_masks.invoke(args)
        self.assertTrue(masks)
        reference = load_arrays(self.proof['arrays'])['mask']
        target = next(row for row in masks if row['instance_id'] == self.proof['instance_id'])
        self.assertTrue(np.array_equal(np.load(target['mask_handle'], allow_pickle=False), reference))
        self.assertEqual(target['mask_dense_shape'], [480, 640])
        self.assertEqual(target['mask_handle'], target['mask_dense_handle'])
        video = self.tools.predict_2d_segmentation_masks_video.invoke({'scene_id': scene, 'object_label': label, 'frame_indices': [1, 17]})
        self.assertEqual(sorted(video['frames']), [1, 17])
        self.assertEqual(video['frames'][1][0]['instance_id'], masks[0]['instance_id'])
        self.assertEqual(video['max_instances_in_any_frame'], max(map(len, video['frames'].values())))

    def test_invalid_scene_label_and_frame(self):
        from gt_training_r1313 import load_selected_dense
        with self.assertRaises(ValueError):
            load_selected_dense('scannetppv2__not_registered')
        with self.assertRaises(ValueError):
            load_selected_dense(self.scene, 'mapanything')
        refusal = self.tools.predict_2d_bounding_box.invoke({'scene_id': self.scene, 'frame_index': 1, 'object_label': 'zz_unmapped_fixture_label_zz'})
        self.assertEqual(refusal['status'], 'refused')
        for index in (0, 33):
            with self.assertRaises(ValueError):
                self.tools.predict_2d_bounding_box.invoke({'scene_id': self.scene, 'frame_index': index, 'object_label': self.label})

    def test_all_camera_correspondences_and_canonical_geometry(self):
        from gt_training_r1313 import load_selected_dense
        source = load_arrays(self.receipt['dense'])
        canonical = load_selected_dense(self.scene)
        alignment = read_json(verify(self.receipt['alignment']))
        self.assertEqual(alignment['validated_slots'], 32)
        self.assertEqual(alignment['pose_field'], 'aligned_pose')
        self.assertTrue(np.allclose(canonical['camera_poses'][0, :3, 3], 0, atol=1e-6))
        forward = canonical['camera_poses'][0, :3, 2]
        self.assertAlmostEqual(float(forward[0]), 0, places=6)
        self.assertGreater(forward[1], 0)
        for slot, row in enumerate(alignment['frames']):
            expected_k = np.asarray(row['vsi_to_target_resize_crop']) @ np.asarray(row['source_to_vsi']) @ np.asarray(row['source_intrinsic'])
            self.assertTrue(np.allclose(source['intrinsics'][slot], expected_k))
            self.assertTrue(np.allclose(source['camera_poses'][slot], row['aligned_pose']))
            self.assertEqual(source['indices'][slot], row['ordinal'])
            self.assertTrue(row['selected_png_matches_vsi_decode'])
            self.assertGreaterEqual(row['raw_to_vsi_correlation'], .99)
            ys, xs = np.where(source['mask'][slot])
            ys, xs = ys[::1000], xs[::1000]
            a, b = source['camera_poses'][slot], canonical['camera_poses'][slot]
            local_a = (source['pts3d_world'][slot, ys, xs] - a[:3, 3]) @ a[:3, :3]
            local_b = (canonical['pts3d_world'][slot, ys, xs] - b[:3, 3]) @ b[:3, :3]
            self.assertTrue(np.allclose(local_a, local_b, atol=2e-5))
        self.assertTrue(np.array_equal(source['mask'], canonical['mask']))
        self.assertTrue(np.array_equal(source['conf'], source['mask'].astype(np.float32)))


if __name__ == '__main__':
    unittest.main()
