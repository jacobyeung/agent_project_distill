"""CPU fixtures for authenticated mesh loading and shared-face rendering."""
import copy
import os
from pathlib import Path
import unittest
import uuid
import numpy as np
from donor_grounding import GTGroundingError, _load_instance_mesh
from gt_scene_assets import DATA_ROOT, save_arrays, write_json
from gt_training_r1313 import TrainingGrounding, donor_pin
from mesh_membership import instance_faces


class SparseGroundingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ['SPARSE_FIXTURE_ROOT']).resolve() / str(uuid.uuid4())
        self.assertTrue(self.root.is_relative_to(DATA_ROOT))
        self.root.mkdir(parents=True)
        # Three separate triangles: a shared center and one exclusive side per ID.
        vertices = [[x + dx, y, 1] for dx in (-.5, 0, .5)
                    for x, y in ((-.12, -.12), (.12, -.12), (0, .12))]
        yy, xx = np.indices((64, 64))
        vertices.extend(np.stack([(xx-32)/50, (yy-32)/50, np.ones_like(xx)], -1).reshape(-1, 3))
        self.arrays = dict(vertices_world=np.asarray(vertices, np.float32),
            faces=np.arange(9, dtype=np.int64).reshape(3, 3),
            membership_instance_ids=np.array([2, 9, 12], np.int32),
            membership_face_offsets=np.array([0, 2, 4, 4], np.int64),
            membership_face_indices=np.array([0, 1, 1, 2], np.int64),
            segment_ids=np.array([10, 20, 30], np.int64),
            segment_offsets=np.array([0, 1, 3, 4], np.int64),
            segment_instance_ids=np.array([2, 2, 9, 9], np.int32))
        groups = [dict(id=i, objectId=i, label=label, segments=[], obb=dict(
            centroid=[0, 0, 1], axesLengths=[.1, .1, .1],
            normalizedAxes=np.eye(3).reshape(-1).tolist()))
            for i, label in ((2, 'fixture_alpha'), (9, 'fixture_beta'), (12, 'fixture_empty'))]
        self.base_receipt = dict(runtime_scene_id='fixture',
            calibration=save_arrays(self.root/'camera.npz',
                camera_poses=np.tile(np.eye(4), (32, 1, 1)),
                intrinsics=np.tile([[50., 0, 32], [0, 50, 32], [0, 0, 1]], (32, 1, 1)),
                raster_hw=np.array([64, 64])),
            instances=write_json(self.root/'instances.json', {'segGroups': groups}),
            annotations=write_json(self.root/'annotations.json',
                {'instances': [{'instance_id': i} for i in (2, 9, 12)]}))

    def receipt(self, arrays):
        return dict(self.base_receipt, instance_mesh=save_arrays(self.root/(str(uuid.uuid4())+'.npz'), **arrays))

    def load(self, arrays):
        receipt = self.receipt(arrays)
        return _load_instance_mesh({'mesh': donor_pin(receipt['instance_mesh']),
                                    'annotations': donor_pin(receipt['annotations'])})

    def test_shared_and_exclusive_faces_masks_boxes_points_frames(self):
        receipt = self.receipt(self.arrays)
        provider = TrainingGrounding(receipt)
        mesh = provider._instance_mesh('fixture')
        self.assertEqual(instance_faces(mesh, 2).tolist(), [0, 1])
        self.assertEqual(instance_faces(mesh, 9).tolist(), [1, 2])
        self.assertEqual(instance_faces(mesh, 12).tolist(), [])
        self.assertEqual(instance_faces(mesh, 999).tolist(), [])
        masks = [provider._render_instance('fixture', 1, i)['mask'] for i in (2, 9)]
        self.assertTrue((masks[0] & masks[1]).any())
        self.assertTrue((masks[0] & ~masks[1]).any())
        self.assertTrue((masks[1] & ~masks[0]).any())
        os.environ['REQ73_RUN_OUTPUT_ROOT'] = str(self.root)
        for iid, label, mask in zip((2, 9), ('fixture_alpha', 'fixture_beta'), masks):
            # Compare to the unchanged dense renderer using the full face set for this ID.
            dense = {k: v for k, v in self.arrays.items() if k in ('vertices_world', 'faces')}
            dense['face_instance_ids'] = np.array([2, 2, -1] if iid == 2 else [-1, 9, 9], np.int32)
            oracle = TrainingGrounding(self.receipt(dense))
            expected = oracle._render_instance('fixture', 1, iid)['mask']
            np.testing.assert_array_equal(mask, expected)
            for method in ('boxes', 'points'):
                self.assertEqual(getattr(provider, method)('fixture', 1, label),
                                 getattr(oracle, method)('fixture', 1, label))
            served = provider.segment_frame('fixture', 1, label, self.root/label)['instances'][0]
            np.testing.assert_array_equal(np.load(served['mask_handle'], allow_pickle=False), mask)
            self.assertEqual(provider.find_frames('fixture', label, 'all'), list(range(1, 33)))
            self.assertEqual(provider.find_frames('fixture', label, '1'), [1, 32])
        self.assertIsNotNone(provider._render_instance('fixture', 1, 12))

    def test_valid_unsigned_memberships(self):
        arrays = {k: v.astype(np.uint64) if k.startswith(('membership_', 'segment_')) else v
                  for k, v in self.arrays.items()}
        self.assertEqual(instance_faces(self.load(arrays), 9).tolist(), [1, 2])

    def test_malformed_csr_is_refused_by_real_loader(self):
        cases = {
            'float_indices': ('membership_face_indices', [0., 1., 1., 2.]),
            'negative_index': ('membership_face_indices', [-1, 1, 1, 2]),
            'out_of_range': ('membership_face_indices', [0, 3, 1, 2]),
            'duplicate_face': ('membership_face_indices', [0, 0, 1, 2]),
            'unordered_faces': ('membership_face_indices', [1, 0, 1, 2]),
            'unsigned_unordered_faces': ('membership_face_indices', np.array([1, 0, 1, 2], np.uint64)),
            'wrong_start': ('membership_face_offsets', [1, 2, 4, 4]),
            'wrong_end': ('membership_face_offsets', [0, 2, 4, 5]),
            'descending_offsets': ('membership_face_offsets', [0, 3, 2, 4]),
            'unsigned_descending_offsets': ('membership_face_offsets', np.array([0, 3, 2, 4], np.uint64)),
            'short_offsets': ('membership_face_offsets', [0, 4]),
            'empty_offsets': ('membership_face_offsets', np.array([], np.int64)),
            'negative_offsets': ('membership_face_offsets', [0, -1, 4, 4]),
            'multidimensional': ('membership_face_indices', [[0, 1], [1, 2]]),
            'duplicate_ids': ('membership_instance_ids', [2, 2, 12]),
            'missing_annotation_id': ('membership_instance_ids', [2, 9, 13]),
            'unsigned_unordered_ids': ('membership_instance_ids', np.array([9, 2, 12], np.uint64)),
            'unordered_segments': ('segment_ids', np.array([20, 10, 30], np.uint64)),
            'duplicate_segments': ('segment_ids', [10, 10, 30]),
            'bad_segment_offsets': ('segment_offsets', [0, 3, 2, 4]),
            'unknown_segment_instance': ('segment_instance_ids', [2, 2, 99, 9]),
            'duplicate_segment_instance': ('segment_instance_ids', [2, 2, 2, 9]),
            'unsigned_unordered_segment_row': ('segment_instance_ids', np.array([2, 9, 2, 9], np.uint64)),
            'float_faces': ('faces', self.arrays['faces'].astype(float)),
            'bad_vertex_reference': ('faces', np.full((3, 3), 999999, np.int64)),
            'nonfinite_geometry': ('vertices_world', np.full((9, 3), np.nan)),
        }
        for name, (key, value) in cases.items():
            with self.subTest(name=name):
                arrays = dict(self.arrays, **{key: np.asarray(value)})
                with self.assertRaises(GTGroundingError):
                    self.load(arrays)
        for name in ('partial_schema', 'mixed_schema'):
            with self.subTest(name=name):
                arrays = copy.copy(self.arrays)
                if name == 'partial_schema':
                    arrays.pop('segment_offsets')
                else:
                    arrays['face_instance_ids'] = np.array([2, 2, 9])
                with self.assertRaises(GTGroundingError):
                    self.load(arrays)


if __name__ == '__main__':
    unittest.main(verbosity=2)
