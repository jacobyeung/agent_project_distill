"""Approved, serial real-return tests with a 1800 MiB address-space ceiling."""
import gzip
import json
import os
import resource
import subprocess
import sys
import unittest

import corpus_score
import ingest_read

BASE = '/scratch/jjyeung/orch_n30'
C15 = BASE + '/cont_ops16/work/c15'
OUT = os.path.join(ingest_read.SCRATCH, 'real', 'validated')


def memory_limit():
    cap = 1800 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))


@unittest.skipUnless(os.environ.get('CORPUS_REAL_TESTS') == '1', 'Enable approved real-return reads with CORPUS_REAL_TESTS=1')
class RealRound1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = []
        cls.headlines = []
        if os.environ.get('CORPUS_REUSE_OUTPUTS') == '1':
            with open(os.path.join(OUT, 'metrics.json')) as f:
                cls.metrics = json.load(f)
            assert len(cls.metrics) == 8
            for metric in cls.metrics:
                path = os.path.join(metric['out'], 'reads', metric['read_id'] + '.jsonl.gz')
                assert ingest_read.fingerprint(path)['sha256'] == metric['sha256']
            return
        cases = [
            ('a8102c3207b', C15 + '/h1read/kit/build/a8102c3207b/fetched', [], 3120),
            ('a8102c3207b', C15 + '/h1read/kit/build/a8102c3207b/fetched/x', [], 3120),
            ('A4', C15 + '/r1route/out3/A4/ret', ['--inputs', C15 + '/r1route/out3/A4'], 636),
            ('B5', C15 + '/r1route/out3/B5/ret', ['--inputs', C15 + '/r1route/out3/B5'], 134),
            ('ret_vsi', BASE + '/b07_offread/in/ret_vsi', [], 4008),
            ('ret_revsi', BASE + '/b07_offread/in/ret_revsi', [], 679),
            ('full_c8r', BASE + '/b04_e2ehook/work/n13/full_c8r/result.tar.gz',
             ['--inputs', C15 + '/r1route/out3/A4/src', '--set', 'dev-S1'], 636),
            ('a4cadd8934b', C15 + '/h1read/readk/kit/build/a4cadd8934b/fetched', [], 1825),
        ]
        for ident, source, extra, expected in cases:
            target = os.path.join(OUT, 'directory') if source.endswith('/fetched/x') else OUT
            cmd = [sys.executable, os.path.join(ingest_read.ROOT, 'ingest_read.py'), 'ingest',
                   '--source', source, '--read-id', ident, '--out', target] + extra
            run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True, preexec_fn=memory_limit)
            if run.returncode:
                raise AssertionError('%s exit %s: %s %s' % (ident, run.returncode, run.stdout, run.stderr))
            metric = json.loads(run.stdout)
            assert metric['item_count'] == expected, metric
            assert metric['max_rss_kib'] < 2 * 1024 * 1024, metric
            metric['source'] = source
            metric['out'] = target
            cls.metrics.append(metric)
            print('INGEST ' + json.dumps(metric, sort_keys=True), flush=True)
            with open(os.path.join(OUT, 'metrics.json'), 'w') as f:
                json.dump(cls.metrics, f, indent=2, sort_keys=True)

    def read_path(self, ident):
        return os.path.join(OUT, 'reads', ident + '.jsonl.gz')

    def record_score(self, label, corpus, reported):
        self.assertAlmostEqual(corpus, reported, places=6)
        row = dict(label=label, corpus_pct=100 * corpus, reported_pct=100 * reported)
        self.headlines.append(row)
        print('HEADLINE ' + json.dumps(row, sort_keys=True), flush=True)
        with open(os.path.join(OUT, 'headlines.json'), 'w') as f:
            json.dump(self.headlines, f, indent=2, sort_keys=True)

    def test_tar_directory_source_drift(self):
        # This real x/ is not an exact extraction: its supplementary ITEMS rows differ.
        # Synthetic tar/directory equality is covered by the original regression suite.
        self.assertNotEqual(self.metrics[0]['sha256'], self.metrics[1]['sha256'])
        directory = os.path.join(OUT, 'directory', 'reads', 'a8102c3207b.jsonl.gz')
        with gzip.open(self.read_path('a8102c3207b'), 'rt') as a, gzip.open(directory, 'rt') as b:
            count = 0
            for left, right in zip(a, b):
                x, y = json.loads(left), json.loads(right)
                self.assertEqual(x['item_id'], y['item_id'])
                self.assertEqual(x['arms'], y['arms'])
                self.assertEqual(x['raw']['arms'], y['raw']['arms'])
                count += 1
            self.assertEqual(count, 3120)
        print('SOURCE_DRIFT tar and x/ supplementary ITEMS rows differ; all 3120 generation records match', flush=True)

    def test_offread_reports(self):
        for name, mean_key in [('vsi', 'six_task_mean'), ('revsi', 'five_category_mean')]:
            report_path = BASE + '/b07_offread/in/ret_' + name + '/report/B2048.json'
            with open(report_path) as f:
                report = json.load(f)
            cmd = [sys.executable, os.path.join(ingest_read.ROOT, 'corpus_score.py'), self.read_path('ret_' + name),
                   '--arm', 'B2048', '--mean-of-types', '--by', 'category', '--compare', report_path,
                   '--key', mean_key + '.score']
            run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True, preexec_fn=memory_limit)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result['comparison']['B2048']['result'], 'MATCH')
            arm = result['arms']['B2048']
            self.record_score(name + ' ' + mean_key, arm['overall']['mean_score'], report[mean_key]['score'])
            for category, expected in report['groups'].items():
                self.record_score(name + ' ' + category, arm['groups'][category]['mean_score'], expected['score'])

    def test_kit_report(self):
        with open(C15 + '/h1read/kit/build/a8102c3207b/fetched/x/main/report/B2048.json') as f:
            report = json.load(f)
        for stratum, expected in [('primary', report['summary']['primary']['released_answer']),
                                  ('missing_released', report['own_gt_by_stratum']['missing_released'])]:
            arm = corpus_score.collect(self.read_path('a8102c3207b'), arm='B2048', by='question_type',
                                       family='main', stratum=stratum)['arms']['B2048']
            self.record_score('kit main ' + stratum, arm['overall']['mean_score'], expected['overall']['score_pct'] / 100)
            for typ, group in expected['per_type'].items():
                if group['score_pct'] is not None:
                    self.assertAlmostEqual(arm['groups'][typ]['mean_score'] * 100, group['score_pct'], places=6)

    def test_routed_and_set(self):
        with open(C15 + '/r1route/out3s/scoresA/scores.json') as f:
            report = json.load(f)
        arm = corpus_score.collect(self.read_path('A4'), arm='tower', by='question_type')['arms']['tower']
        n, total = 0, 0
        for typ, group in report['types'].items():
            expected = group['current']
            self.assertAlmostEqual(arm['groups'][typ]['mean_score'], expected['score'], places=6)
            total += expected['score'] * expected['completed']
            n += expected['completed']
        self.record_score('A4 tower', arm['overall']['mean_score'], total / n)
        with gzip.open(self.read_path('B5'), 'rt') as f:
            rows = [json.loads(line) for line in f]
        self.assertTrue(all(r['set'] == 'room134' for r in rows))
        self.assertEqual(sum(r['reader']['task_join_rule'] == 'room134.bind:answer=ground_truth' for r in rows), 98)

    def test_native_all_calls(self):
        # Compare every paired row's complete decode and calls to the corpus.
        expected = {}
        with open(BASE + '/b04_e2ehook/work/n13/ret/native/paired/results/items.jsonl') as f:
            for line in f:
                r = json.loads(line)
                expected[(r['key'], r['arm'])] = (ingest_read.digest(r), ingest_read.digest(r.get('decode', {}).get('calls')), len(r.get('decode', {}).get('calls', [])))
        calls = 0
        with gzip.open(self.read_path('full_c8r'), 'rt') as f:
            for line in f:
                row = json.loads(line)
                self.assertIsNotNone(row['question'])
                self.assertIsNotNone(row['truth']['scored'])
                for arm, raw in row['raw']['arms'].items():
                    a, b, count = expected.pop((row['item_id'], arm))
                    self.assertEqual(ingest_read.digest(raw), a)
                    self.assertEqual(ingest_read.digest(row['arms'][arm]['tool_calls']), b)
                    calls += count
        self.assertFalse(expected)
        print('NATIVE_CALLS ' + str(calls), flush=True)

    def test_orphan_integrity(self):
        for ident in set(m['read_id'] for m in self.metrics):
            with open(os.path.join(OUT, 'index', ident + '.json')) as f:
                index = json.load(f)
            path = os.path.join(OUT, index['orphans']['path'])
            fp = ingest_read.fingerprint(path)
            self.assertEqual(fp['sha256'], index['orphans']['sha256'])
            with gzip.open(path, 'rt') as f:
                self.assertEqual(sum(1 for line in f), index['orphan_count'])


if __name__ == '__main__':
    unittest.main()
