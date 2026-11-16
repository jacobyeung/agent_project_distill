"""EAT-1 unit tests: a passing toy reader, one planted violation per clause, and the instruments.

Run: python -m unittest eat1.tests.test_eat1   (CPU, about two minutes)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
EAT1 = HERE.parent
sys.path.insert(0, str(EAT1.parent))

from eat1 import hook as H  # noqa: E402
from eat1 import run as R  # noqa: E402
from eat1 import scan as S  # noqa: E402
from eat1.toy.build import build  # noqa: E402

TOY_ALLOW = str(EAT1/'toy'/'allowlist_toy.json')
EXPECTED = {  # variant -> clauses that must fail (and every other clause must pass)
    'clean': set(),
    'table': {'A1', 'A3', 'A5'},
    'second_entry': {'A2'},
    'threshold': {'A3'},
    'guard': {'A3', 'A4', 'A5'},  # its fallback arm reads response text after decoding and substitutes the answer (A4)
    'cache': {'A1', 'A3', 'A5'},
    'head_method': {'A3'},  # a threshold in a method of a declared module class is not model code
}
STATIC = {  # planted violation -> (rule, function) the static scanner must report
    'table': ('A3.table_load', 'TableHandler.serve'),
    'second_entry': ('A2.entry_after_decode', 'SecondEntryReader.generate'),
    'threshold': ('A3.threshold', 'ThresholdHandler.serve'),
    'guard': ('A4.guard', 'GuardHandler.serve'),
    'cache': ('A5.cache', 'CacheHandler.serve'),
}


class ToyEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix='eat1_test_', dir=os.environ.get('EAT1_TMP')))
        cls.info = build(cls.tmp/'toy')
        cls.results = {}
        for variant in EXPECTED:
            out = cls.tmp/'runs'/variant
            R.main(['--reader', 'eat1.toy.build:make_reader', '--reader-kwargs',
                    json.dumps(dict(variant=variant, workdir=cls.info['work'])), '--items', cls.info['items'],
                    '--out', str(out), '--allowlist-extra', TOY_ALLOW, '--perturb', '--sandbox'])
            cls.results[variant] = json.loads((out/'EAT1_REPORT.json').read_text())

    def test_clean_passes_every_clause(self):
        r = self.results['clean']
        self.assertEqual(r['overall'], 'PASS', json.dumps({k: c['summary'] for k, c in r['clauses'].items()}))
        self.assertEqual(r['clauses']['A5']['parts'], dict(i='PASS', ii='PASS', iii='PASS'))
        for typ in ('move', 'depth'):
            self.assertEqual(r['per_type'][typ]['call_rate'], 1.0)
        self.assertEqual(r['per_type']['move']['heads_behind_fields'], {'distance_m': {'pose': 3}})

    def test_each_planted_violation_fails_its_clause_only(self):
        for variant, expected in EXPECTED.items():
            with self.subTest(variant=variant):
                failed = {k for k, c in self.results[variant]['clauses'].items() if c['status'] == 'FAIL'}
                self.assertEqual(failed, expected)

    def test_offenders_point_at_the_planted_line(self):
        planted = str(EAT1/'toy'/'planted.py')
        a1 = self.results['table']['clauses']['A1']['offenders']
        self.assertTrue(a1[0]['file'].endswith('scale_rule.json'))
        self.assertTrue(a1[0]['opened_at'][0].startswith(planted+':'))
        a2 = self.results['second_entry']['clauses']['A2']['offenders']
        self.assertIn('second_model_entry', {o.get('kind') for o in a2})
        a3 = {(o['rule'], o['line']) for o in self.results['threshold']['clauses']['A3']['offenders']}
        self.assertIn(('A3.threshold', 26), a3)
        hm = {(o['rule'], o['function']) for o in self.results['head_method']['clauses']['A3']['offenders']}
        self.assertIn(('A3.threshold', 'RulePerception.adjust'), hm)
        a4 = {o.get('kind') or o.get('rule') for o in self.results['guard']['clauses']['A4']['offenders']}
        self.assertTrue({'response_without_head', 'answer_not_in_generated_sequence', 'A4.guard'} <= a4)
        a5 = {o.get('kind') or o.get('rule') for o in self.results['cache']['clauses']['A5']['offenders']}
        self.assertTrue({'tower_cited_but_not_run_in_call', 'A5.cache',
                         'response_names_module_but_did_not_change'} <= a5)


class StaticScanner(unittest.TestCase):
    def test_clean_toy_has_no_findings(self):
        allow = S.load_allowlist(extra=[TOY_ALLOW])
        findings, _ = S.scan([EAT1/'toy'/'reader.py'], allow)
        self.assertEqual(findings, [])

    def test_flags_all_five_planted_violations(self):
        allow = S.load_allowlist(extra=[TOY_ALLOW])
        findings, _ = S.scan([EAT1/'toy'/'planted.py'], allow)
        got = {(f['rule'], f['function']) for f in findings}
        for variant, key in STATIC.items():
            with self.subTest(variant=variant):
                self.assertIn(key, got)

    def test_indices_norms_and_printing_pass(self):
        src = ('import torch\n'
               'def fmt(points, k):\n'
               '    d = torch.linalg.norm(points[1]-points[0])\n'
               '    return f"{float(d):.2f}", round(float(d), 2), points[k, 3]\n')
        path = Path(tempfile.mkdtemp())/'ok.py'
        path.write_text(src)
        self.assertEqual(S.scan([path])[0], [])

    def test_unit_conversion_outside_the_model_fails(self):
        cases = ['def f(d):\n    return f"{d*100:.1f} cm"\n',
                 'def f(d):\n    return round(d/0.3048, 2)\n',
                 'def to_feet(d):\n    return d\n',
                 'def f(d):\n    return f"{d:.1f} ft"\n',
                 'def f(a):\n    return a*180/3.141592653589793\n']
        for src in cases:
            with self.subTest(src=src):
                path = Path(tempfile.mkdtemp())/'unit.py'
                path.write_text(src)
                rules = {f['rule'] for f in S.scan([path])[0]}
                self.assertTrue(rules & {'A3.unit_conversion', 'A3.constant'}, rules)

    def test_fitted_constant_and_config_threshold_fail(self):
        src = ('def cut(depth, cfg):\n'
               '    if depth > cfg["tau"]:\n'
               '        return depth*0.85\n'
               '    return depth\n')
        path = Path(tempfile.mkdtemp())/'bad.py'
        path.write_text(src)
        rules = {f['rule'] for f in S.scan([path])[0]}
        self.assertEqual(rules, {'A3.threshold', 'A3.constant'})

    def test_raise_only_validation_passes_but_caught_error_response_fails(self):
        ok = 'def f(k):\n    if not 1 <= k <= 64:\n        raise ValueError(k)\n    return k\n'
        bad = ('def f(k):\n    try:\n        return g(k)\n    except ValueError as e:\n'
               '        return f"error: {e}"\n')
        root = Path(tempfile.mkdtemp())
        (root/'ok.py').write_text(ok)
        (root/'bad.py').write_text(bad)
        self.assertEqual(S.scan([root/'ok.py'])[0], [])
        self.assertIn('A4.except_substitute', {f['rule'] for f in S.scan([root/'bad.py'])[0]})
        (root/'empty.py').write_text('def f(k):\n    try:\n        return g(k)\n    except KeyError:\n        return []\n')
        self.assertNotIn('A4.except_substitute', {f['rule'] for f in S.scan([root/'empty.py'])[0]})

    def test_suppression_is_reported(self):
        path = Path(tempfile.mkdtemp())/'s.py'
        path.write_text('X = 0.7\n')
        allow = S.load_allowlist()
        allow['suppress'] = [dict(rule='A3.constant', file='s.py', line=1, reason='test')]
        findings, suppressed = S.scan([path], allow)
        self.assertEqual((len(findings), len(suppressed)), (0, 1))


class Instruments(unittest.TestCase):
    def ev(self, ids, past, argmax):
        return ('forward', dict(ids=ids, past=past, stack=['f.py:1 x'], embeds=False), argmax)

    def test_provenance_classifies_tokens(self):
        events = [self.ev([5, 6], 0, [9, 7]), self.ev([7], 2, [8]), ('handler', 'h', [3, 4]),
                  self.ev([8, 3, 4], 3, [1, 1, 2]), self.ev([2], 6, [0])]
        p = H.provenance(events)
        self.assertEqual(p['entries'], 1)
        self.assertEqual(p['violations'], [])
        self.assertEqual([s for s, _ in p['tokens']], ['prompt']*2+['model', 'model', 'handler', 'handler', 'model'])
        self.assertEqual(p['generated'], [7, 8, 3, 4, 2, 0])

    def test_provenance_flags_injection_discontinuity_and_reentry(self):
        events = [self.ev([5], 0, [9]), self.ev([4], 1, [8]), self.ev([8], 5, [1]), self.ev([5, 6], 0, [1, 1])]
        kinds = [v['kind'] for v in H.provenance(events)['violations']]
        self.assertEqual(kinds, ['injected_token', 'cache_discontinuity', 'second_model_entry'])

    def test_parse_strace_windows(self):
        log = Path(tempfile.mkdtemp())/'s.log'
        log.write_text(
            '10 openat(AT_FDCWD, "/a/before.json", O_RDONLY) = 3\n'
            f'10 openat(AT_FDCWD, "{H.MARKER_DIR}/start-0", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file)\n'
            '11 openat(AT_FDCWD, "/a/in.json", O_RDONLY|O_CLOEXEC) = 4\n'
            '11 openat(AT_FDCWD, "/a/out.json", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 5\n'
            '11 openat(AT_FDCWD, "/a/missing", O_RDONLY) = -1 ENOENT (No such file)\n'
            f'10 openat(AT_FDCWD, "{H.MARKER_DIR}/end-0", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file)\n'
            '10 openat(AT_FDCWD, "/a/after.json", O_RDONLY) = 6\n')
        self.assertEqual(H.parse_strace(log), [(0, '/a/in.json', False), (0, '/a/out.json', True)])

    def test_classify_files(self):
        d = Path(tempfile.mkdtemp())
        (d/'art').mkdir()
        (d/'art'/'w.bin').write_bytes(b'w')
        (d/'other.json').write_text('{}')
        (d/'code.py').write_text('x=1\n')
        (d/'inp.npy').write_bytes(b'i')
        (d/'tmp.json').write_text('{}')
        from eat1.artifact import write_manifest, Artifact
        write_manifest(d/'art'/'A.json', d/'art', {'w.bin': 'lm'}, {})
        art = Artifact(d/'art'/'A.json')
        recs = [('open', str(d/'art'/'w.bin'), False), ('open', str(d/'other.json'), False),
                ('open', str(d/'code.py'), False), ('open', str(d/'inp.npy'), False),
                ('open', str(d/'tmp.json'), True), ('open', str(d/'tmp.json'), False),
                ('open', sys.executable, False)]
        c = H.classify_files(recs, art, [d/'inp.npy'])
        self.assertEqual([x['path'] for x in c['outside_data']], [str(d/'other.json')])
        self.assertEqual(len(c['artifact']), 1)
        self.assertEqual(len(c['code']), 1)
        self.assertEqual(len(c['input']), 1)
        self.assertEqual(len(c['self_written']), 1)

    def test_cache_proof_rules(self):
        d = Path(tempfile.mkdtemp())
        def proof(n, differ=0):
            items = [dict(id=i, live='a', cached='a' if i >= differ else 'b') for i in range(n)]
            (d/'p.json').write_text(json.dumps(dict(schema='eat1-cache-proof-v1', items=items)))
            return R.check_cache_proof(d/'p.json')['status']
        self.assertEqual(proof(49), 'FAIL')
        self.assertEqual(proof(50), 'PASS')
        self.assertEqual(proof(60, differ=1), 'FAIL')


@unittest.skipUnless(shutil.which('strace'), 'strace absent')
class StraceSource(unittest.TestCase):
    def test_strace_sees_the_planted_table(self):
        tmp = Path(tempfile.mkdtemp(prefix='eat1_strace_', dir=os.environ.get('EAT1_TMP')))
        info = build(tmp/'toy')
        log = tmp/'strace.log'
        cmd = ['strace', '-f', '-qq', '-e', 'trace=open,openat', '-o', str(log), sys.executable, '-B', '-c',
               'import sys;from eat1 import run;sys.exit(run.main(sys.argv[1:]))',
               '--reader', 'eat1.toy.build:make_reader', '--reader-kwargs',
               json.dumps(dict(variant='table', workdir=info['work'])), '--items', info['items'],
               '--out', str(tmp/'out'), '--allowlist-extra', TOY_ALLOW, '--strace-log', str(log)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(EAT1.parent),
                              env=dict(os.environ, PYTHONPATH=str(EAT1.parent)))
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        windows = H.parse_strace(log)
        self.assertTrue(any(p.endswith('scale_rule.json') for _, p, _ in windows))
        report = json.loads((tmp/'out'/'EAT1_REPORT.json').read_text())
        self.assertTrue(report['clauses']['A1']['strace'])
        self.assertEqual(report['clauses']['A1']['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
