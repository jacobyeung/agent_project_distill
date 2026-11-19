"""Real-source integration tests. Set CORPUS_REAL_TESTS=1 after I/O approval."""
import json
import os
import resource
import subprocess
import sys
import unittest

import corpus_score
import ingest_read

BASE = '/scratch/jjyeung/orch_n30/cont_ops16/work/c15'
OUT = os.path.join(ingest_read.SCRATCH, 'out')
KIT = os.path.join(BASE, 'h1read/kit/build/a8102c3207b/fetched')
ENABLED = os.environ.get('CORPUS_REAL_TESTS') == '1'


def memory_limit():
    limit = 1800 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


@unittest.skipUnless(ENABLED, 'Full-source I/O requires approval; enable CORPUS_REAL_TESTS=1')
class RealReturns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = []
        cls.outputs = {}
        cases = [
            ('a8102c3207b', os.path.join(KIT, 'result.tar.gz'), []),
            ('a8102c3207b', os.path.join(KIT, 'x'), []),
            ('a2e46c0504e', os.path.join(BASE, 'h1face/kit/build/a2e46c0504e/fetched/x'), []),
            ('acb2faedd41', os.path.join(BASE, 'h1vsti/kit/build/acb2faedd41/fetched/x'), []),
            ('A4', os.path.join(BASE, 'r1route/out3/A4/ret'),
             ['--inputs', os.path.join(BASE, 'r1route/out3/A4/src')]),
        ]
        for ident, source, extra in cases:
            command = [sys.executable, os.path.join(ingest_read.ROOT, 'ingest_read.py'), 'ingest',
                       '--source', source, '--read-id', ident, '--out', OUT] + extra
            run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True, preexec_fn=memory_limit)
            if run.returncode:
                raise AssertionError('%s: %s\n%s' % (ident, run.stdout, run.stderr))
            metric = json.loads(run.stdout.strip())
            metric['source'] = source
            cls.metrics.append(metric)
            print('INGEST ' + json.dumps(metric, sort_keys=True), flush=True)
            cls.outputs[ident] = os.path.join(OUT, 'reads', ident + '.jsonl.gz')
        with open(os.path.join(ingest_read.SCRATCH, 'real_metrics.json'), 'w') as f:
            json.dump(cls.metrics, f, indent=2, sort_keys=True)

    def test_counts_and_tar_identical(self):
        self.assertEqual([m['item_count'] for m in self.metrics], [3120, 3120, 300, 900, 636])
        self.assertEqual(self.metrics[0]['sha256'], self.metrics[1]['sha256'])
        self.assertEqual(self.metrics[1]['result'], 'SAME')

    def test_kit_report_overall_and_every_type(self):
        with open(os.path.join(KIT, 'x/main/report/B2048.json')) as f:
            report = json.load(f)
        results = {}
        path = self.outputs['a8102c3207b']
        for stratum, expected in [('primary', report['primary']),
                                  ('missing_released', report['own_gt_by_stratum']['missing_released'])]:
            scored = corpus_score.collect(path, arm='B2048', by='question_type', family='main', stratum=stratum)
            arm = scored['arms']['B2048']
            self.assertAlmostEqual(arm['overall']['mean_score'] * 100, expected['overall']['score_pct'], places=6)
            for typ, values in expected['per_type'].items():
                if values['score_pct'] is not None:
                    self.assertAlmostEqual(arm['groups'][typ]['mean_score'] * 100, values['score_pct'], places=6)
            results[stratum] = arm
        print('KIT_REPORT ' + json.dumps(results, sort_keys=True), flush=True)

    def test_routed_report_every_type(self):
        with open(os.path.join(BASE, 'r1route/out3s/scoresA/scores.json')) as f:
            report = json.load(f)
        result = corpus_score.collect(self.outputs['A4'], arm='tower', by='question_type')['arms']['tower']
        weighted, n = 0, 0
        for typ, values in report['types'].items():
            expected = values['current']
            self.assertAlmostEqual(result['groups'][typ]['mean_score'], expected['score'], places=6)
            weighted += expected['score'] * expected['completed']
            n += expected['completed']
        self.assertAlmostEqual(result['overall']['mean_score'], weighted / n, places=6)
        print('ROUTED_REPORT ' + json.dumps(result, sort_keys=True), flush=True)

    def test_score_cli_compare(self):
        cmd = [sys.executable, os.path.join(ingest_read.ROOT, 'corpus_score.py'), self.outputs['a8102c3207b'],
               '--arm', 'B2048', '--family', 'main', '--stratum', 'missing_released',
               '--compare', os.path.join(KIT, 'x/main/report/B2048.json'),
               '--key', 'own_gt_by_stratum.missing_released.overall.score_pct']
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                                preexec_fn=memory_limit)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['comparison']['B2048']['result'], 'MATCH')
