"""v3.14 fixes: one test per fix (fused box, full height, benchmark grid rule, multi-instance minimum, 3D merge
resolver, category vocabulary, multi-instance operand admission)."""
import unittest
import numpy as np
from derivgen import box_v313 as B
from derivgen.ground_v313 import Session, MergedInstances, GTInstances
from derivgen import ground_v313_distance as D
from test_v313 import backend, Geometry, masks, instances


def session(**kw):
    return Session(backend, Geometry(), masks, instances=instances, **kw)


class ByInstance:
    """Analytic provider: one unit box per (name, instance id)."""
    provider_id = 'test_by_instance_v1'
    CENTRES = {('stand', 'a'): [0, 0, 2], ('face', 'b1'): [4, 0, 2], ('face', 'b2'): [1.5, 0, 2],
               ('lamp', 'c'): [0, 0, 6]}

    def __call__(self, name, obj, geo, best):
        return B.box(self.CENTRES[(name, obj['instance_id'])], [1, 1, 1], np.eye(3))


def entry(iid):
    return dict(instance_id=iid, visible=[1], areas={'1': 1.}, frames=[1], points={'1': [[0, 0, 0]] * 4}, first=1)


ENTRIES = {'stand': [entry('a')], 'face': [entry('b1'), entry('b2')], 'lamp': [entry('c')]}


class FusedProvider(unittest.TestCase):
    def test_fused_box_spans_every_lifted_frame(self):
        """Fix 'extent': the box covers the instance's points from all frames, not only the best frame."""
        f1 = [[x, y, z] for x in (0, .5) for y in (0, .5) for z in (0, 1)]
        f2 = [[x, y, z] for x in (2, 2.5) for y in (0, .5) for z in (0, 1)]
        obj = dict(frames=[1, 2], visible=[1, 2], areas={'1': 2., '2': 1.}, points={'1': f1, '2': f2})
        geo = Geometry()
        best = B.FittedBoxProvider(B.fit_gbox)('x', obj, geo, 1)
        fused = B.FusedBoxProvider()('x', obj, geo, 1)
        self.assertLessEqual(max(best['lengths']), 1.0 + 1e-9)
        self.assertAlmostEqual(max(fused['lengths']), 2.5, places=6)
        self.assertEqual(session().box_provider_id, 'fit_gbox_fused_full_v1')

    def test_full_height(self):
        """Fix 'height': fit_gbox_full keeps the full fused height; fit_gbox trims to the 2nd-98th percentiles."""
        rng = np.random.default_rng(0)
        P = np.c_[rng.uniform(0, 1, (500, 2)), rng.uniform(0, 1, 500)]
        P[0, 2], P[1, 2] = -1.0, 2.0
        self.assertAlmostEqual(B.fit_gbox_full(P)['axesLengths'][2], 3.0, places=9)
        self.assertLess(B.fit_gbox(P)['axesLengths'][2], 1.0)


class GridRule(unittest.TestCase):
    def test_benchmark_grid_rule(self):
        """Fix 'grid': box_grid_5cm reproduces the benchmark sampler (grid reaches the box faces exactly)."""
        a = B.box([0, 0, 2], [1, 1, 1], np.eye(3)); b = B.box([2, 0, 2], [1, 1, 1], np.eye(3))
        self.assertAlmostEqual(B.box_grid_5cm(a, b), 1.0, places=12)
        self.assertGreater(B.sampled_box_512(a, b), 1.0)
        g = B.grid_points(a)
        ext = np.array([1., 1., 1.])
        self.assertTrue(np.all(np.any(np.abs(g - [0, 0, 2]) > ext / 4, axis=1)))
        self.assertEqual(len(g), 20 ** 3 - 10 ** 3)


class TiltedAnnotation(unittest.TestCase):
    def test_tilted_box_prints_enclosing_gravity_box(self):
        """Fix 'tilt': a tilted annotation box prints (no 'box unavailable') and keeps its private operand;
        gravity-aligned boxes print as in v3.13."""
        flat = B.box([1, 0, 2], [2, 1, 0.5], np.eye(3))
        self.assertEqual(B.serialize('desk', 'B1', [1], 1, flat).splitlines()[2], 'size 2.00 x 0.50 x 1.00 m')
        c, s = np.cos(np.radians(30)), np.sin(np.radians(30))
        tilt = B.box([1, 0, 2], [2, 1, 0.5], [[c, s, 0], [-s, c, 0], [0, 0, 1]])
        body = B.serialize('desk', 'B1', [1], 1, tilt)
        reg = B.BoxRegistry(); reg.ingest(body, tilt)
        self.assertTrue(np.allclose(reg.records['B1']['value']['axes'], tilt['axes']))
        size = [float(v) for v in body.splitlines()[2].split()[1::2]]
        self.assertAlmostEqual(size[2], 2 * s + 1 * c, places=2)


class MultiInstance(unittest.TestCase):
    def make(self, multi):
        s = session(box_provider=ByInstance(), multi_instance=multi)
        s._instances = lambda n: ENTRIES[n]
        return s

    def test_v313_keeps_unresolved(self):
        s = self.make(False)
        self.assertEqual(s.execute('<ground obj="face" mode="box">'), 'face: unresolved')

    def test_minimum_over_instances_and_replay(self):
        """Fix 'instances': every instance is printed, and the gap is the minimum over instance pairs."""
        s = self.make(True)
        s.execute('<ground obj="stand" mode="box">')
        body = s.execute('<ground obj="face" mode="box">')
        self.assertTrue(body.startswith('face: 2 instances\nface: frames 1 (best 1)\nB2: '))
        self.assertIn('\nB3: ', body)
        s.execute('<ground obj="lamp" mode="box">')
        got = s.execute('<gap a="stand" b="face" b="lamp" rule="box_grid_5cm">')
        self.assertEqual(got.splitlines()[0], 'face: 0.50 m')
        self.assertEqual(got.splitlines()[-1], 'min "face" 0.50 m')
        values = B.replay_audit(s.events)
        self.assertAlmostEqual(values[0], 0.5, places=12)
        self.assertAlmostEqual(values[1], 3.0, places=12)
        gap = s.events[-1]['audit']
        self.assertEqual(gap['ordered_box_labels'], ['B1', ['B2', 'B3'], 'B4'])
        self.assertEqual(gap['sampler'], B.SAMPLER_GRID)
        tampered = [dict(e) for e in s.events]
        tampered[1] = dict(tampered[1], audit=dict(tampered[1]['audit'], box_labels=['B3', 'B2']))
        with self.assertRaises(ValueError):
            B.replay_audit(tampered)

    def test_too_many_instances(self):
        s = self.make(True)
        s._instances = lambda n: [entry(f'x{i}') for i in range(B.MAX_INSTANCES + 1)]
        # The cap applies to usable boxes; missing boxes are skipped.
        s.box_provider = lambda name, obj, geo, best: B.box([0, 0, 1], [1, 1, 1], np.eye(3))
        self.assertEqual(s.execute('<ground obj="face" mode="box">'), 'face: unresolved')


class CameraGap(unittest.TestCase):
    def test_camera_box_grid_prefers_instances_in_frame(self):
        """Fix 'camgap': VSTI camera-object distance = camera centre of the asked frame to the 5 cm box grid, using
        the instances supported in that frame."""
        def at(iid, k):
            return dict(instance_id=iid, visible=[k], areas={str(k): 1.}, frames=[k], points={str(k): [[0, 0, 0]] * 4},
                        first=k)
        s = session(box_provider=ByInstance(), multi_instance=True)
        s._instances = lambda n: {'face': [at('b1', 3), at('b2', 1)], 'stand': [at('a', 3)]}[n]
        s.execute('<ground obj="face" mode="box">'); s.execute('<ground obj="stand" mode="box">')
        body = s.execute('<gap camera="3" b="face" b="stand" rule="box_grid_5cm">')
        centre = B.camera_centre_f1(Geometry(), 3)
        self.assertTrue(np.allclose(centre, [0.2, 0, 0]))
        want = B.camera_gap(centre, B.box([4, 0, 2], [1, 1, 1], np.eye(3)))
        self.assertEqual(body.splitlines()[0], 'face: ' + B.number(want, 2) + ' m')
        self.assertTrue(body.splitlines()[-1].startswith('min "stand" '))
        values = B.replay_audit(s.events)
        self.assertAlmostEqual(values[0], want, places=12)
        self.assertEqual(s.execute('<gap camera="3" b="lamp" rule="box_grid_5cm">'), 'not seen')


class Merge(unittest.TestCase):
    def test_merge3d_one_per_frame(self):
        """Fix 'merge': detections within 1.5 m from different frames merge; same-frame detections stay apart."""
        class LiftBackend:
            def lift_object(self, name, stack, prob, geo, tau):
                k = int(np.argmax(prob)) + 1
                ys, xs = np.nonzero(stack[k - 1])
                return dict(points={str(k): [[float(xs.mean()), float(ys.mean()), 0.]]})

        def det(x, y):
            m = np.zeros((10, 10), bool); m[y, x] = True
            return m
        frames = [[] for _ in range(32)]
        frames[0] = [det(1, 1), det(2, 1)]          # two chairs 1 m apart in the same frame
        frames[1] = [det(1, 2)]                     # chair 1 again, 1 m from its first sighting
        frames[2] = [det(8, 8)]                     # a third chair far away
        r = MergedInstances(LiftBackend(), None, lambda n: frames)('chair')
        self.assertEqual(len(r), 3)
        self.assertEqual(sorted(int(e['prob'].sum()) for e in r), [1, 1, 2])
        self.assertEqual(MergedInstances.rule, 'merge3d_1.5m_one_per_frame')


class Vocab(unittest.TestCase):
    def test_vocab_pools_raw_labels(self):
        """Fix 'vocab': a category word pools the raw labels the benchmark counts under it."""
        class Geo:
            ids = [1, 2, 3]; labels = ['table', 'desk', 'chair']
            inst = np.stack([np.full((8, 8), i) for i in (1, 2, 3)] * 11)[:32]
        class Clip:
            geo = Geo()
        plain = GTInstances(Clip())('table')
        pooled = GTInstances(Clip(), vocab={'table': ['table', 'desk', 'coffee table']})('table')
        self.assertEqual([e['instance_id'] for e in plain], [1])
        self.assertEqual([e['instance_id'] for e in pooled], [1, 2])


class Prepare(unittest.TestCase):
    def test_prepare_multi_records_every_instance(self):
        class Geo:
            ids = [1, 2, 3]; labels = ['table', 'chair', 'chair']
            obb = {i: dict(centroid=[i, 0, 0], axesLengths=[1, 1, 1], normalizedAxes=list(np.eye(3).ravel()))
                   for i in (1, 2, 3)}
        class Clip:
            geo = Geo()
        item = dict(type='object_abs_distance', roles=dict(a='table', b='chair'))
        with self.assertRaises(Exception):
            D.prepare(dict(item), Clip())
        D.prepare(item, Clip(), rule=B.RULE_GRID, multi_instance=True)
        self.assertEqual([b['instance_id'] for b in item['independent_ordered_boxes']], [1, 2, 3])
        self.assertEqual(item['trace_revision'], '3.14')


if __name__ == '__main__':
    unittest.main()
