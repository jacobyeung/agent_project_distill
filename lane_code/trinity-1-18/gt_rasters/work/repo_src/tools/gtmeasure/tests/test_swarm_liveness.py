import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

from tools.gtmeasure.swarm_liveness import tick


class LivenessTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ['H5_TEST_OUTPUT']) / ('liveness_' + uuid4().hex)
        self.swarm = self.root / 'swarm'
        self.lane = self.swarm / 'lanes' / 'example'
        self.out = self.lane / 'out'
        self.out.mkdir(parents=True)
        self.state = self.out / 'state.json'
        self.state.write_text(json.dumps({'phase': 'Checking coordinator directives', 'progress': ['- Cards held: None.']}))

    def run_tick(self):
        stream = io.StringIO()
        result = SimpleNamespace(returncode=0, stdout='', stderr='')
        with patch('tools.gtmeasure.swarm_liveness.subprocess.run', return_value=result), patch('sys.stdout', stream):
            self.assertTrue(tick(self.lane, self.root / 'production', self.state))
        return json.loads(stream.getvalue())

    def test_absent_directive_is_recorded_without_creating_one(self):
        value = self.run_tick()
        self.assertIsNone(value['directive_mtime_ns'])
        self.assertFalse((self.lane / 'COORD_DIRECTIVE.md').exists())
        self.assertTrue(value['production_clean'])
        self.assertEqual(len((self.out / 'HEARTBEAT.log').read_text().splitlines()), 1)

    def test_each_heartbeat_observes_current_directive_and_ruling_mtimes(self):
        directive = self.lane / 'COORD_DIRECTIVE.md'
        directive.write_text('Wait for the assigned card relay.\n')
        ruling = self.swarm / 'RULINGS.md'
        ruling.write_text('Check lane directives at every heartbeat.\n')
        first = self.run_tick()
        self.assertEqual(first['directive_mtime_ns'], directive.stat().st_mtime_ns)
        self.assertEqual(first['rulings_mtime_ns'], ruling.stat().st_mtime_ns)
        os.utime(directive, ns=(first['directive_mtime_ns'] + 1000000000,) * 2)
        second = self.run_tick()
        self.assertGreater(second['directive_mtime_ns'], first['directive_mtime_ns'])
        self.assertEqual(directive.read_text(), 'Wait for the assigned card relay.\n')
        self.assertEqual(len((self.out / 'HEARTBEAT.log').read_text().splitlines()), 2)


if __name__ == '__main__':
    unittest.main()
