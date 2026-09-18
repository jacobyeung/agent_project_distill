"""CPU fixtures exercise the real serializer, mesh loader, and donor renderer."""
import os
from pathlib import Path
import unittest
import uuid
import numpy as np
from prepare_gt_scene import instance_associations, rendering_proof
from mesh_membership import instance_faces, validate_memberships, mesh_candidate
from gt_training_r1313 import TrainingGrounding
from gt_scene_assets import DATA_ROOT, save_arrays, write_json


def group(iid, segments):
    return {'id': iid, 'objectId': iid, 'label': 'wall', 'segments': segments,
            'obb': {'centroid': [0, 0, 0], 'axesLengths': [3, 3, 3],
                    'normalizedAxes': np.eye(3).reshape(-1).tolist()}}


class MembershipTests(unittest.TestCase):
    def test_vertex_intersection_and_determinism(self):
        v = np.zeros((7, 3), np.float32)
        f = np.array([[0, 1, 2], [1, 2, 3], [3, 4, 5], [4, 5, 6]], np.int32)
        seg = {'segIndices': [10, 20, 30, 40, 50, 50, 99]}
        groups = [group(9, [30, 20, 10]), group(2, [10, 20, 30, 40]), group(7, [40, 50]), group(8, [])]
        m, _, diag = instance_associations(v, f, seg, groups)
        expected = {2: [0, 1], 7: [2], 8: [], 9: [0]}
        for iid, wanted in expected.items():
            self.assertEqual(instance_faces(m, iid).tolist(), wanted)
        self.assertEqual([r['face_count'] for r in diag], [1, 2, 1, 0])
        reordered, _, _ = instance_associations(v, f, seg, list(reversed(groups)))
        for key in m:
            np.testing.assert_array_equal(m[key], reordered[key])
        validate_memberships(dict(m, faces=f), set(expected))
        bad = dict(m, faces=f, membership_face_indices=np.array([0, 0, 2, 0]))
        with self.assertRaises(ValueError):
            validate_memberships(bad, set(expected))

    def test_direct_face_membership(self):
        v = np.zeros((6, 3), np.float32)
        f = np.array([[0, 1, 2], [1, 2, 3], [3, 4, 5]], np.int32)
        m, basis, _ = instance_associations(v, f, {'segIndices': [10, 20, 99]},
                                            [group(9, [10]), group(2, [10, 20]), group(7, [])])
        self.assertEqual(basis, 'face_segIndices')
        self.assertEqual(instance_faces(m, 9).tolist(), [0])
        self.assertEqual(instance_faces(m, 2).tolist(), [0, 1])
        self.assertEqual(m['segment_instance_ids'].tolist(), [2, 9, 2])

    def test_obb_diagnostics_use_all_shared_faces(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [2, 0, 0], [0, 2, 0]], np.float32)
        f = np.array([[0, 1, 2], [0, 3, 4]], np.int32)
        _, _, d = instance_associations(v, f, {'segIndices': [10, 20]},
                                         [group(2, [10, 20]), group(9, [20])])
        self.assertEqual([x['face_count'] for x in d], [2, 1])
        for row in d:
            np.testing.assert_allclose(row['max_axis_ratio_to_source_axesLengths'], [2/3, 2/3, 0])


class RenderTests(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ['PREP_FIXTURE_ROOT']).resolve()
        self.assertTrue(root.is_relative_to(DATA_ROOT))
        self.root = root / str(uuid.uuid4())
        self.root.mkdir(parents=True)

    def provider(self, behind_count=0, overlap=False, invisible=False):
        points, faces, segments, groups = [], [], [], []
        for iid in range(1, behind_count + 2):
            z = 2.0 if iid <= behind_count else (-1.0 if invisible else 1.0)
            start = len(points)
            points.extend([[-.4*z, -.4*z, z], [.4*z, -.4*z, z], [.4*z, .4*z, z], [-.4*z, .4*z, z]])
            faces.extend([[start, start+1, start+2], [start, start+2, start+3]])
            segments.extend([iid, iid])
            groups.append(group(iid, [iid]))
        if overlap:
            groups.append(group(100, [1]))
        # Dense source vertices make the donor's unchanged splat z-buffer complete.
        yy, xx = np.indices((64, 64))
        points.extend(np.stack([(xx-32)/50, (yy-32)/50, np.ones_like(xx)], axis=-1).reshape(-1, 3))
        v, f = np.asarray(points, np.float32), np.asarray(faces, np.int32)
        m, _, _ = instance_associations(v, f, {'segIndices': segments}, groups)
        calibration = save_arrays(self.root/'camera.npz', camera_poses=np.tile(np.eye(4), (32, 1, 1)),
            intrinsics=np.tile([[50.,0,32],[0,50,32],[0,0,1]], (32,1,1)), raster_hw=np.array([64,64]))
        receipt = {'runtime_scene_id': 'fixture', 'calibration': calibration,
            'instances': write_json(self.root/'instances.json', {'segGroups': groups}),
            'instance_mesh': save_arrays(self.root/'mesh.npz', vertices_world=v, faces=f, **m),
            'annotations': write_json(self.root/'annotations.json', {'instances': [{'instance_id': g['id']} for g in groups]})}
        return TrainingGrounding(receipt), receipt

    def proof(self, receipt):
        data = {'depth_z': np.ones((32,64,64), np.float32), 'mask': np.ones((32,64,64), bool)}
        return rendering_proof(self.root, receipt, np.zeros((32,64,64,3), np.uint8), data)

    def test_camera_inside_obb_shared_masks_and_legacy_parity(self):
        p, receipt = self.provider(overlap=True)
        pose, k, h, w = p._camera('fixture', 1)
        self.assertFalse((p._project(p._obb_corners('fixture', 1), pose, k)[2] > .05).all())
        self.assertTrue(mesh_candidate(p, p._instance_mesh('fixture'), 1, pose, k, h, w))
        first, shared = p._render_instance('fixture', 1, 1), p._render_instance('fixture', 1, 100)
        np.testing.assert_array_equal(first['mask'], shared['mask'])
        self.assertGreaterEqual(first['mask_pixel_count'], 32)
        mesh = p._instance_mesh('fixture')
        legacy = dict(receipt, instance_mesh=save_arrays(self.root/'legacy.npz', vertices_world=mesh['vertices'],
             faces=mesh['faces'].astype(np.int32), face_instance_ids=np.ones(len(mesh['faces']), np.int32)))
        old = TrainingGrounding(legacy)
        np.testing.assert_array_equal(old._scene_zbuffer('fixture', 1, pose, k, h, w), p._scene_zbuffer('fixture', 1, pose, k, h, w))
        np.testing.assert_array_equal(old._render_instance('fixture', 1, 1)['mask'], first['mask'])
        self.assertEqual([x['slot_1based'] for x in self.proof(receipt)], [1, 17])

    def test_complete_search_past_16_and_occlusion(self):
        p, receipt = self.provider(behind_count=17)
        for iid in range(1,18):
            result = p._render_instance('fixture', 1, iid)
            self.assertTrue(result is None or result['mask_pixel_count'] == 0)
        self.assertEqual([x['instance_id'] for x in self.proof(receipt)], [18,18])

    def test_no_visible_mesh_still_refuses(self):
        _, receipt = self.provider(invisible=True)
        with self.assertRaisesRegex(ValueError, 'could not find a visible'):
            self.proof(receipt)


if __name__ == '__main__':
    unittest.main(verbosity=2)
