"""Fix 7: admit continuation C' run 6ed2c7aa (deployment x_ee227714) at milestones 400/600 only; nothing else changes."""
import offline_guard
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'kit/launcher'))
import binding as B
import orchard_launcher as L
import export_stage as E

FAMILIES = {'h1read7': (['main', 'a7'], ['away']), 'h1face7': (['away', 'forward'], ['r6']),
            'h1vsti7': (['r6'], ['away'])}[ROOT.name]


class Fix7(unittest.TestCase):
    def test_milestones_bind_x_ee227714(self):
        for step in (400, 600):
            b = B.expected('6ed2c7aa', step)
            self.assertEqual(b['object'], 'q8/8865619b/6ed2c7aa_m%d.tar' % step)
            self.assertEqual(b['done'], '/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m%d.done' % step)
            self.assertEqual(B.validate(b), b)

    def test_other_steps_namespaces_refused(self):
        for step in (100, 200, 300, 500, 601, 0):
            with self.assertRaises(ValueError): B.expected('6ed2c7aa', step)
        with self.assertRaises(ValueError): B.expected('6ed2c7aa', 400, namespace='00000000')
        with self.assertRaises(ValueError): B.expected('6ed2c7ab', 400)
        with self.assertRaises(ValueError): B.expected('6ed2c7aa', 200, 'mstop')
        for gen in B.STOPS:
            for step in (201, 333, 400, 600):
                with self.assertRaises(ValueError): B.expected('6ed2c7aa', step, gen)
        self.assertEqual(B.expected('05b8ac69', 333, 'mstopB')['generation'], 'mstopB')
        self.assertTrue(B.r1_step('6ed2c7aa', 201) and B.r1_step('6ed2c7aa', 600))
        self.assertFalse(B.r1_step('6ed2c7aa', 200) or B.r1_step('6ed2c7aa', 601))

    def test_previous_identities_unchanged(self):
        self.assertEqual(B.RUNS['673bc60f'], 'x_69d2930d'); self.assertEqual(B.RUNS['05b8ac69'], 'x_7f1589c1')
        self.assertEqual(B.R1_RANGES['673bc60f'], (1, 200)); self.assertEqual(B.R1_RANGES['05b8ac69'], (201, 600))
        self.assertEqual(B.expected('673bc60f', 200)['object'], 'q8/8865619b/673bc60f_m200.tar')
        with self.assertRaises(ValueError): B.expected('673bc60f', 400)

    def test_staging_admits_only_registered_paths(self):
        J = E.J
        for step in (400, 600):
            ok = str(J.FSW/'ap/8865619b/runs/6ed2c7aa'/('m%d' % step)/'artifact.json')
            self.assertEqual(E.logical_artifact(None, ok, step), ok)
        with self.assertRaises(ValueError):
            E.logical_artifact(None, str(J.FSW/'ap/8865619b/runs/6ed2c7aa/m200/artifact.json'), 200)
        with self.assertRaises(ValueError):
            E.logical_artifact(None, str(J.FSW/'ap/8865619b/runs/6ed2c7ab/m400/artifact.json'), 400)

    def test_family_gate(self, tmp=None):
        import tempfile
        good, bad = FAMILIES
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                L.prepare('a' + '0' * 10, Path(d)/'x', 400, run='6ed2c7aa', families=bad)


if __name__ == '__main__':
    unittest.main()
