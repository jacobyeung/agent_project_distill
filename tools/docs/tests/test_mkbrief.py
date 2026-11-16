"""mkbrief.py: one golden file per role and the successor brief of cont_ops6."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(DOCS))
sys.path.insert(0, DOCS)
import mkbrief  # noqa: E402

FIX = os.path.join(HERE, 'fixtures')
GOLD = os.path.join(HERE, 'golden')
COMMON = ['--lane', 'demo_lane', '--node', 'trinity-3-30', '--events', 'B/events/demo_lane',
          '--cap-gb', '5', '--scratch-floor-gb', '150', '--io-class', 'named-reads',
          '--limit', '2026-11-16T22:30Z', '--limits', 'at most two ssh calls a minute into Trinity']
SUCC = ['successor', '--lane', 'cont_ops7', '--node', 'trinity-1-3', '--events', 'B/events/cont_ops',
        '--cap-gb', '20', '--scratch-floor-gb', '300', '--io-class', 'governed',
        '--limit', '2026-11-17T02:46Z', '--predecessor', os.path.join(FIX, 'cont_ops6_brief.md'),
        '--status', os.path.join(FIX, 'cont_ops_STATUS.md'),
        '--predecessor-cite', 'B/briefs/cont_ops6.md', '--status-cite', 'B/events/cont_ops/STATUS.md']


def read(path):
    with open(path, 'r') as handle:
        return handle.read()


def render(argv):
    args = mkbrief.build_parser().parse_args(argv)
    return mkbrief.render(args.role, args)


class GoldenTest(unittest.TestCase):
    def test_each_role_matches_golden(self):
        for role in ('operator', 'reviewer', 'builder'):
            self.assertEqual(render([role] + COMMON), read(os.path.join(GOLD, role + '.md')), role)

    def test_successor_matches_golden(self):
        self.assertEqual(render(SUCC), read(os.path.join(GOLD, 'successor_cont_ops6.md')))

    def test_rules_are_pointed_at_not_restated(self):
        for role in ('operator', 'reviewer', 'builder'):
            text = render([role] + COMMON)
            self.assertIn(mkbrief.LANE_RULES, text)
            self.assertEqual(text.count('Key Trinity Cluster Rules'), 1)
            for phrase in ('No Git', 'no deletion', 'No deletion', 'rm_guard'):
                self.assertNotIn(phrase, text)
            self.assertIn('TODO(orchestrator)', text)
            self.assertIn('inside these, act without asking', text)
            self.assertIn('Limits: at most two ssh calls a minute into Trinity', text)


class SuccessorTest(unittest.TestCase):
    def setUp(self):
        self.text = render(SUCC)

    def test_names_predecessor_and_its_folders(self):
        self.assertIn('You continue the work of lane cont_ops6.', self.text)
        self.assertIn('- `/scratch/jjyeung/orch_n30/cont_ops`', self.text)
        self.assertIn('orch_n30/events/review_d0r`', self.text)

    def test_quotes_next_step_and_carries_do(self):
        self.assertIn('tmux `cont6_watch`', self.text)
        self.assertIn('The LEG-S1 continuation packet stays unsubmitted', self.text)

    def test_successor_needs_status(self):
        args = mkbrief.build_parser().parse_args(SUCC[:-6] + ['--predecessor',
                                                             os.path.join(FIX, 'cont_ops6_brief.md')])
        with self.assertRaises(ValueError):
            mkbrief.render('successor', args)


class CliTest(unittest.TestCase):
    def test_out_refuses_existing_file(self):
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp, 'brief.md')
        cmd = [sys.executable, os.path.join(DOCS, 'mkbrief.py'), 'builder'] + COMMON + ['--out', out]
        self.assertEqual(subprocess.call(cmd), 0)
        self.assertEqual(read(out), read(os.path.join(GOLD, 'builder.md')))
        self.assertEqual(subprocess.call(cmd, stderr=subprocess.DEVNULL), 2)

    def test_unknown_io_class_refused(self):
        argv = list(COMMON)
        argv[argv.index('named-reads')] = 'fast'
        cmd = [sys.executable, os.path.join(DOCS, 'mkbrief.py'), 'builder'] + argv
        self.assertEqual(subprocess.call(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL), 2)


if __name__ == '__main__':
    unittest.main()
