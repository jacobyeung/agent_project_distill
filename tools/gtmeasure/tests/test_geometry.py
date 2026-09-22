import unittest

import numpy as np

from tools.gtmeasure.geometry import camera_object_distance, object_count, object_distance, object_size, room_area


def plane(x, y, z=0., label='floor', iid=1):
    vertices = np.array([[0, 0, z], [x, 0, z], [x, y, z], [0, y, z]], dtype=float)
    return {'id': iid, 'label': label, 'vertices': vertices,
            'triangles': vertices[np.array([[0, 1, 2], [0, 2, 3]])],
            'obb': {'centroid': [x / 2, y / 2, z], 'axesLengths': [x / 2, y / 2, .1],
                    'normalizedAxes': np.eye(3).ravel().tolist()}}


class GeometryTests(unittest.TestCase):
    def test_object_count_uses_distinct_category_instances(self):
        objects = [{'id': 7, 'label': 'chair'}, {'id': 8, 'label': 'chair'}, {'id': 9, 'label': 'stool'}]
        self.assertEqual(object_count(objects, 'chair'), 2)
        self.assertEqual(object_count(objects, 'table'), 0)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            object_count(objects + [objects[0]], 'chair')

    def test_object_size_is_longest_full_box_extent_not_diagonal(self):
        obj = plane(2., 4., label='table')
        self.assertEqual(object_size(obj), 4.)
        angle = np.pi / 4
        obj['obb']['normalizedAxes'] = [np.cos(angle), -np.sin(angle), 0, np.sin(angle), np.cos(angle), 0, 0, 0, 1]
        self.assertEqual(object_size(obj), 4.)

    def test_object_distance_uses_triangle_surfaces_not_centers_or_vertices(self):
        a = plane(10., 10., label='table')
        b = plane(1., 1., 3., label='chair', iid=2)
        b['triangles'] += [4.5, 4.5, 0]
        b['vertices'] += [4.5, 4.5, 0]
        self.assertAlmostEqual(object_distance(a, b), 3., places=10)
        self.assertAlmostEqual(object_distance(b, a), 3., places=10)
        crossing = {'triangles': np.array([[[4., 4., -1.], [6., 4., 1.], [5., 6., 1.]]])}
        self.assertAlmostEqual(object_distance(a, crossing), 0., places=10)

    def test_camera_distance_is_radial_to_nearest_surface(self):
        obj = plane(10., 10., label='table')
        pose = np.eye(4)
        pose[:3, 3] = [5., 5., 2.]
        self.assertAlmostEqual(camera_object_distance(obj, pose), 2., places=10)
        pose[:3, 3] = [-3., -4., 12.]
        self.assertAlmostEqual(camera_object_distance(obj, pose), 13., places=10)
        pose[:3, :3] = [[0., 0., 1.], [0., 1., 0.], [-1., 0., 0.]]
        self.assertAlmostEqual(camera_object_distance(obj, pose), 13., places=10)

    def test_room_area_keeps_concavity_and_unions_overlapping_floor_faces(self):
        a = plane(2., 1.)
        b = plane(1., 2., iid=2)
        chair = plane(100., 100., label='chair', iid=3)
        self.assertAlmostEqual(room_area([a, b, chair]), 3., places=10)
        self.assertAlmostEqual(room_area([a, a]), 2., places=10)
        with self.assertRaisesRegex(ValueError, 'floor'):
            room_area([chair])


if __name__ == '__main__':
    unittest.main()
