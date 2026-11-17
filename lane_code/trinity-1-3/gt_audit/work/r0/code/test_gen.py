"""CPU tests for r0lib + gen_questions on a synthetic ScanNet++-format scene with known geometry.

Room 6 x 4 m (floor + 4 walls, z up). Objects (axis boxes): chair x3, table, sofa, lamp, tv, plant, fridge.
A camera orbit at 1.4 m looks outward from the room centre. Checks: PLY/segment parsing, camera-convention resolution
against the colmap file, layout rule, visibility, counting, size, distance, room area, direction labels, determinism.
Each run writes a new folder under work/test_scene/.
"""
import json, math, os, sys, time, unittest
import numpy as np
from scipy.spatial.transform import Rotation
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r0lib, gen_questions  # noqa: E402
T = os.path.join(os.path.dirname(HERE), 'work', 'test_scene', 'synth_%d_%d' % (int(time.time()), os.getpid()))

OBJ = [('chair', (1.0, 1.0, 0.0), (0.5, 0.5, 0.9)), ('chair', (1.0, 3.0, 0.0), (0.5, 0.5, 0.9)),
       ('chair', (5.0, 3.0, 0.0), (0.5, 0.5, 0.9)), ('table', (3.0, 2.0, 0.0), (1.6, 0.8, 0.75)),
       ('sofa', (5.0, 1.0, 0.0), (2.0, 0.9, 0.8)), ('lamp', (0.5, 2.0, 0.0), (0.3, 0.3, 1.6)),
       ('tv', (3.0, 3.8, 0.8), (1.2, 0.1, 0.7)), ('plant', (5.6, 2.2, 0.0), (0.4, 0.4, 1.0)),
       ('refrigerator', (2.0, 0.4, 0.0), (0.7, 0.7, 1.8))]


def box_pts(c, s, step=0.04):
    pts = []
    xs = np.arange(0, s[0] + 1e-9, step); ys = np.arange(0, s[1] + 1e-9, step); zs = np.arange(0, s[2] + 1e-9, step)
    for X, Y in [(a, b) for a in xs for b in ys]:
        pts += [(X, Y, 0), (X, Y, s[2])]
    for X, Z in [(a, b) for a in xs for b in zs]:
        pts += [(X, 0, Z), (X, s[1], Z)]
    for Y, Z in [(a, b) for a in ys for b in zs]:
        pts += [(0, Y, Z), (s[0], Y, Z)]
    p = np.unique(np.round(np.array(pts), 4), axis=0)
    return p + np.array([c[0] - s[0] / 2, c[1] - s[1] / 2, c[2]])


def build():
    os.makedirs(T + '/scans'); os.makedirs(T + '/iphone/colmap')
    parts = [('floor', box_pts((3, 2, -0.01), (6, 4, 0.01), 0.05)), ('wall', box_pts((3, -0.05, 0), (6, 0.02, 2.6), 0.05)),
             ('wall', box_pts((3, 4.05, 0), (6, 0.02, 2.6), 0.05)), ('wall', box_pts((-0.05, 2, 0), (0.02, 4, 2.6), 0.05)),
             ('wall', box_pts((6.05, 2, 0), (0.02, 4, 2.6), 0.05))] + [(l, box_pts(c, s)) for l, c, s in OBJ]
    V = np.concatenate([p for _, p in parts]).astype('<f4')
    seg = np.concatenate([np.full(len(p), i) for i, (_, p) in enumerate(parts)])
    F = np.array([[0, 1, 2]], dtype='<i4')
    with open(T + '/scans/mesh_aligned_0.05.ply', 'wb') as f:
        f.write(('ply\nformat binary_little_endian 1.0\nelement vertex %d\nproperty float x\nproperty float y\nproperty float z\n'
                 'property uchar red\nproperty uchar green\nproperty uchar blue\nelement face 1\nproperty list uchar int vertex_indices\nend_header\n' % len(V)).encode())
        dt = np.dtype([('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('r', 'u1'), ('g', 'u1'), ('b', 'u1')])
        a = np.zeros(len(V), dt); a['x'], a['y'], a['z'] = V[:, 0], V[:, 1], V[:, 2]; f.write(a.tobytes())
        f.write(np.array([3], 'u1').tobytes() + F.tobytes())
    json.dump({'segIndices': seg.tolist()}, open(T + '/scans/segments.json', 'w'))
    json.dump({'segGroups': [{'id': i, 'objectId': i, 'label': l, 'segments': [i]} for i, (l, _) in enumerate(parts)]},
              open(T + '/scans/segments_anno.json', 'w'))
    K = [[1425.0, 0, 960.0], [0, 1425.0, 720.0], [0, 0, 1]]
    P = {}; cm = []
    n = 600
    for i in range(n):
        th = 2 * math.pi * i / n
        eye = np.array([3 + 1.2 * math.cos(th), 2 + 0.8 * math.sin(th), 1.4])
        tgt = eye + np.array([math.cos(th), math.sin(th), -0.25])
        z = tgt - eye; z /= np.linalg.norm(z)
        x = np.cross(z, [0, 0, 1.0]); x /= np.linalg.norm(x); y = np.cross(z, x)
        c2w = np.eye(4); c2w[:3, 0], c2w[:3, 1], c2w[:3, 2], c2w[:3, 3] = x, y, z, eye  # OpenCV
        gl = c2w @ r0lib.GL2CV
        P['frame_%06d' % i] = {'timestamp': i / 60, 'pose': gl.tolist(), 'aligned_pose': gl.tolist(), 'intrinsic': K}
        if i % 10 == 0:
            w2c = np.linalg.inv(c2w); R = w2c[:3, :3]; t = w2c[:3, 3]
            qx, qy, qz, qw = Rotation.from_matrix(R).as_quat()
            cm.append('%d %f %f %f %f %f %f %f 1 frame_%06d.jpg\n\n' % (i, qw, qx, qy, qz, t[0], t[1], t[2], i))
    json.dump(P, open(T + '/iphone/pose_intrinsic_imu.json', 'w'))
    open(T + '/iphone/colmap/images.txt', 'w').write('# x\n' + ''.join(cm))
    open(T + '/iphone/colmap/cameras.txt', 'w').write('1 OPENCV 1920 1440 1425 1425 960 720 0 0 0 0\n')


class T1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        cls.out = T + '_q.jsonl'
        gen_questions.main(T, 'R0-dev', 3, cls.out)
        cls.items = [json.loads(l) for l in open(cls.out)]

    def test_layout_rule(self):
        self.assertEqual(r0lib.layout(823, 32)[:5], [0, 26, 53, 79, 106])
        self.assertEqual(r0lib.layout(11738, 32)[-2:], [11358, 11737])

    def test_convention(self):
        total, cams, conv = r0lib.load_cameras(T)
        self.assertEqual(total, 600); self.assertEqual(conv['convention'], 'opengl')
        self.assertLess(conv['median_abs_err_vs_colmap']['opengl'], 1e-4)

    def test_visibility_frame0(self):
        S = r0lib.load_scene(T); total, cams, _ = r0lib.load_cameras(T)
        vc = r0lib.visible_counts(S, cams, [0])[0]
        lab = {S['inst'][k]['label'] for k, c in vc.items() if c >= r0lib.VIS_MIN_PX}
        self.assertIn('plant', lab); self.assertNotIn('lamp', lab)  # frame 0 looks along +x from (4.2, 2)

    def test_types_present(self):
        qts = {i['question_type'] for i in self.items}
        for q in ('object_counting', 'object_size_estimation', 'object_abs_distance', 'room_size_estimation',
                  'object_rel_distance', 'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard'):
            self.assertIn(q, qts)

    def test_counting_chairs(self):
        c = [i for i in self.items if i['question_type'] == 'object_counting' and i['gt'].get('category') == 'chair']
        for i in c:
            self.assertLessEqual(int(i['answer_f32']), 3); self.assertLessEqual(int(i['answer_f64']), 3)

    def test_sizes_and_distances(self):
        size = {l: max(s) * 100 for l, _, s in OBJ}
        for i in self.items:
            if i['question_type'] == 'object_size_estimation':
                self.assertLess(abs(int(i['answer_f32']) - size[i['gt']['category']]), 6, i['question'])
            if i['question_type'] == 'room_size_estimation':
                self.assertLess(abs(float(i['answer_f32']) - 24.0), 2.5)

    def test_direction_geometry(self):
        cen = {l: np.array([c[0], c[1]]) for l, c, s in OBJ if l != 'chair'}
        for i in self.items:
            if i['question_type'].startswith('object_rel_direction'):
                g = i['gt']; a, b, c = cen[g['standing']], cen[g['facing']], cen[g['query']]
                f = (a - b) if g['away'] else (b - a); t = c - a
                cross = f[0] * t[1] - f[1] * t[0]
                ans = dict(zip('ABCD', [o.split('. ', 1)[1] for o in i['options']]))[i['answer_f32']]
                if ans in ('left', 'right'):
                    self.assertEqual(ans, 'left' if cross > 0 else 'right', i['question'])

    def test_mc_letters_valid_and_deterministic(self):
        out2 = T + '_q2.jsonl'
        gen_questions.main(T, 'R0-dev', 3, out2)
        self.assertEqual(open(self.out).read(), open(out2).read())
        for i in self.items:
            if i['options']:
                self.assertIn(i['answer_f32'], 'ABCD'[:len(i['options'])])


if __name__ == '__main__':
    unittest.main(verbosity=2)
