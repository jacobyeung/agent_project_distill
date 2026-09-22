import unittest

import numpy as np

from tools.gtmeasure.mesh_membership import instance_faces, validate_memberships


class MembershipTests(unittest.TestCase):
    def test_sparse_memberships_preserve_faces_shared_by_instances(self):
        mesh = {'faces': np.array([[0, 1, 2]]), 'membership_instance_ids': np.array([3, 9]),
                'membership_face_offsets': np.array([0, 1, 2]), 'membership_face_indices': np.array([0, 0]),
                'segment_ids': np.array([44]), 'segment_offsets': np.array([0, 2]), 'segment_instance_ids': np.array([3, 9])}
        validate_memberships(mesh, {3, 9})
        self.assertEqual(instance_faces(mesh, 3).tolist(), [0])
        self.assertEqual(instance_faces(mesh, 9).tolist(), [0])
        self.assertEqual(instance_faces(mesh, 7).tolist(), [])
        mesh['membership_face_indices'] = np.array([0, 1])
        with self.assertRaisesRegex(ValueError, 'outside'):
            validate_memberships(mesh, {3, 9})

    def test_legacy_membership_does_not_count_unassigned_faces(self):
        mesh = {'instance_ids': np.array([-1, 3, 9, 3])}
        self.assertEqual(instance_faces(mesh, 3).tolist(), [1, 3])


if __name__ == '__main__':
    unittest.main()
