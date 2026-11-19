"""CPU tests for the part 2 scripts on synthetic caches; no SAM 3, no GPU (bash run.sh part2/test_part2.py; out/part2/TESTS_PART2.json)."""
import json, os, subprocess, sys, unittest, tempfile, shutil
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import price as P  # noqa: E402
import sam3_pass as G  # noqa: E402
K, AG = P.K, P.AG


def mask(r0, c0, h=480, w=640):
    m = np.zeros((h, w), bool); m[r0:r0+40, c0:c0+40] = True
    return m


def inst(q, score, src, pres, retention='k1', at=(0, 0)):
    return dict(query=q, score=score, source_prompt=src, source_presence=pres, retention=retention, mask=G.rle_encode(mask(*at)))


def caches():
    """K1 cache: raw heater in frame 0, a stored radiator instance in frame 0. Rerun: radiator alone in frames 0 and 1,
    a raw-call R_cond query in frame 1 and a radiator R_cond query in frame 2."""
    k1 = {str(s): dict(phrases={'heater': dict(presence=.9, instances=[])}) for s in range(32)}
    k1['0']['phrases']['heater']['instances'] = [dict(query=0, score=.8, mask=G.rle_encode(mask(0, 0)), source_prompt='heater', source_presence=.9),
                                                 dict(query=3, score=.6, mask=G.rle_encode(mask(80, 80)), source_prompt='radiator', source_presence=.5)]
    p2 = {str(s): dict(phrases={'heater': dict(presence=.88, instances=[])}) for s in range(32)}
    p2['0']['phrases']['heater']['instances'] = [inst(0, .81, 'heater', .88), inst(5, .7, 'radiator', .6, at=(100, 100))]
    p2['1']['phrases']['heater']['instances'] = [inst(1, .6, 'heater', .04, 'cond', (200, 200)), inst(2, .55, 'heater', .04, 'cond', (300, 300)),
                                                 inst(4, .9, 'radiator', .7, at=(120, 120))]
    p2['2']['phrases']['heater']['instances'] = [inst(6, .52, 'radiator', .05, 'cond', (50, 300))]
    return dict(frames=k1), dict(capture='x', calls={'heater': ['heater', 'radiator']}, frames=p2)


class Format(unittest.TestCase):
    def test_rle_matches_reader_codec(self):
        rng = np.random.default_rng(0)
        for first in (False, True):
            m = rng.random((64, 48)) > .7; m[0, 0] = first
            self.assertEqual(G.rle_encode(m), K.T.F.rle(m))
            self.assertTrue(np.array_equal(G.rle_decode(G.rle_encode(m)), m))
        empty = np.zeros((4, 5), bool)
        self.assertEqual(G.rle_encode(empty), dict(size=[4, 5], counts=[20]))

    def test_frozen_inputs(self):
        self.assertEqual(K.sha(P.NEW), P.NEW_SHA.read_text().split()[0])
        self.assertEqual(K.sha(P.BARS2), P.BARS2_SHA.read_text().split()[0])

    def test_new_phrases_follow_the_rule(self):
        new = json.loads(P.NEW.read_text())['phrases']; table = K.alias_table()
        names = {n for c, calls in G.plan() for n in calls}
        self.assertEqual(len(names), 64)
        self.assertEqual(set(new), {n for n in names if n not in table})
        self.assertTrue(all(1 <= len(v) <= 3 and len(set(v)) == len(v) and n not in v for n, v in new.items()))

    def test_plan(self):
        p = G.plan()
        self.assertEqual(len(p), 209)
        self.assertTrue(all(ws[0] == n and len(set(ws)) == len(ws) for _, calls in p for n, ws in calls.items()))
        heater = {tuple(calls['heater']) for _, calls in p if 'heater' in calls}
        self.assertEqual(heater, {('heater', 'radiator')})
        new = json.loads(P.NEW.read_text())['phrases']
        self.assertTrue(all(ws[1:] == new[n] for _, calls in p for n, ws in calls.items() if n in new))

    def test_part1_code_unchanged(self):
        pins = json.loads((K.OUT/'DECISION.json').read_text())['input_sha256']
        for name in ('kit.py', 'aggregate.py', 'report.py', 'dryrun.py'):
            self.assertEqual(K.sha(K.HERE/name), pins[str(K.HERE/name)], name)
        for name in ('run.sh', 'launch.sh'):
            source = K.WORK/'fixture_sources'/(name+'.txt')
            self.assertEqual(K.sha(source), pins[str(source)], name)
            self.assertIn(str(K.HERE), (K.HERE/name).read_text())

    def test_gpu_modes_refuse_without_go(self):
        env = {k: v for k, v in os.environ.items() if k != 'PART2_GO'}
        for mode in ('step5', 'pass'):
            r = subprocess.run([sys.executable, str(Path(G.__file__)), mode], env=env, capture_output=True, text=True, timeout=60)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('PART2_GO=1 is required', r.stderr)


class Pools(unittest.TestCase):
    def test_merged_takes_raw_from_k1_and_drops_cond(self):
        k1, p2 = caches()
        m = P.merged(k1, p2)['frames']
        f0 = m['0']['phrases']['heater']
        self.assertEqual([(p['source_prompt'], p['score']) for p in f0['instances']], [('heater', .8), ('radiator', .7)])
        self.assertEqual(f0['presence'], .9)
        self.assertFalse(any(p.get('retention') == 'cond' for s in m for p in m[s]['phrases']['heater']['instances']))

    def test_rerun_pools_and_cond_fill(self):
        k1, p2 = caches()
        with P.swapped(p2):
            pv = K.pools(k1, 'heater', {'heater': ['radiator']})
        count = lambda v: [len(f) for f in pv[v][0][:3]]  # noqa: E731
        self.assertEqual(count('raw'), [1, 0, 0])
        self.assertEqual(count('q:radiator'), [1, 1, 0])
        self.assertEqual(count('fb:radiator'), [1, 1, 0])
        self.assertEqual(count('rc:raw'), [1, 2, 0])
        self.assertEqual(count('rc:radiator'), [1, 1, 1])
        self.assertEqual([e['presence'] for e in pv['rc:raw'][0][1]], [.04, .04])
        self.assertEqual([pv[v][2] for v in ('raw', 'q:radiator', 'rc:raw', 'rc:radiator')], ['heater', 'radiator', 'heater', 'radiator'])
        for v in pv:
            K.uniform(pv[v][0])
        self.assertIs(K.pools, P.ORIG['pools'])
        self.assertIs(K.families, P.ORIG['families'])

    def test_stored_pool_is_unchanged_outside_the_swap(self):
        k1, p2 = caches()
        before = K.pools(k1, 'heater', {'heater': ['radiator']})
        self.assertEqual(len(before['q:radiator'][0][0]), 1)
        self.assertEqual(before['q:radiator'][0][0][0]['score'], .6)
        self.assertNotIn('rc:raw', before)

    def test_families_add_rc_pairs(self):
        va = {'raw': 'k0', 'cap100': 'k0', 'q:a': 'k1', 'fb:a': 'k2', 'rc:raw': 'k3', 'rc:a': 'k4'}
        vb = {'raw': 'k0', 'cap100': 'k0', 'rc:raw': 'k0'}
        fams = list(P.families2(va, vb))
        self.assertEqual(fams[-1], {('k3', 'k0'), ('k4', 'k0')})
        self.assertEqual(len(fams), 4)


class Stops(unittest.TestCase):
    def test_projection(self):
        new = {'heater': ['space heater']}
        remaining = [{'heater': ['heater', 'radiator', 'space heater']}]*50
        timed = [dict(encode=10., detect=30., distinct_calls=3)]*10
        p = G.projection(timed, remaining, new, 400.)
        self.assertAlmostEqual(p['projected_gpu_h'], (400+50*(10+30))/3600)
        self.assertAlmostEqual(p['projected_gpu_h_without_new'], (400+50*(10+20))/3600)
        self.assertFalse(p['drop_new']); self.assertFalse(p['stop'])
        mid = [dict(encode=10., detect=90., distinct_calls=3)]*10
        p = G.projection(mid, remaining, new, 400.)
        self.assertTrue(p['drop_new']); self.assertFalse(p['stop'])
        slow = [dict(encode=10., detect=150., distinct_calls=3)]*10
        p = G.projection(slow, remaining, new, 400.)
        self.assertTrue(p['drop_new']); self.assertTrue(p['stop'])


class Bars(unittest.TestCase):
    def rows(self, shift, n=60):
        return [dict(row_id=f'r{i}', room=f'room{i % 12}', label=1.0, prediction=(1.0 if (i % 10) < shift else 2.5)) for i in range(n)]

    def test_worth_and_safe(self):
        better, base = self.rows(8), self.rows(2)
        safe = P.safe_bar(better, {r['row_id']: r for r in base}, {r['row_id'] for r in base})
        self.assertEqual(safe['verdict'], 'PASS')
        self.assertEqual(P.worth_bar(better, base, safe)['verdict'], 'PASS')
        self.assertEqual(P.worth_bar(base, better, safe)['verdict'], 'FAIL')
        self.assertEqual(P.worth_bar(better, base, dict(verdict='FAIL'))['verdict'], 'FAIL')
        self.assertEqual(P.worth_bar(base, base)['verdict'], 'FAIL')


class Fixture(unittest.TestCase):
    def test_fixture_passed(self):
        f = json.loads((K.WORK/'part2_fixture/FIXTURE.json').read_text())
        self.assertEqual(f['status'], 'PASS')
        source = K.WORK/'fixture_sources/part2/price.py.txt'
        self.assertEqual(f['input_sha256'][str(source)], K.sha(source))
        self.assertTrue(all(c['rc_pairs_priced'] > 0 and c['rc_distinct_from_base'] > 0 for c in f['captures']))

    def test_full_fixture_reproduces_part1(self):
        """Reruns identical to the stored pools must price W_exact exactly as part 1 priced W1."""
        d = json.loads((K.WORK/'part2_fixture/aggregate/DECISION_PART2.json').read_text())
        self.assertIn('FIXTURE', d)
        self.assertEqual(d['w_exact_rows_equal_w_cf'], 1037)
        self.assertEqual(d['arms']['W_exact']['mra'], d['w_cf_mra'])
        source = K.WORK/'fixture_sources/part2/price.py.txt'
        self.assertEqual(d['input_sha256'][str(source)], K.sha(source))
        self.assertEqual(set(d['arms']), {'W_exact', 'W_new', 'R_cond'})
        self.assertTrue(all(d['arms'][a]['rows'] == 1037 for a in d['arms']))


class Admission(unittest.TestCase):
    def exercise(self, condition):
        parent = K.WORK/'gate_tests'
        parent.mkdir(exist_ok=True)
        # Retain refusal fixtures for review; no deletion or temporary cleanup.
        for entry in ('launcher', 'capture', 'aggregate', 'step5', 'pass', 'run_relative', 'run_absolute', 'run_aggregate', 'run_option'):
            root = Path(tempfile.mkdtemp(prefix=condition+'_'+entry+'_', dir=parent))
            (root/'part2').mkdir()
            for name in ('gate.py', 'price.py', 'sam3_pass.py', 'launch_part2.sh'):
                shutil.copyfile(P.PART2/name, root/'part2'/name)
            (root/'run.sh').write_text((K.HERE/'run.sh').read_text().replace(str(K.HERE), str(root)))
            if condition != 'missing':
                (root/'part2/BARS_PART2.json').write_bytes(P.BARS2.read_bytes() + (b' ' if condition == 'altered' else b''))
            if condition in ('per_item', 'per_capture'):
                dest = root/('out/part2/PER_ITEM_PART2.jsonl' if condition == 'per_item' else 'out/part2/captures/example.json')
                dest.parent.mkdir(parents=True); dest.write_text('{}\n')
            if condition == 'capture_work':
                dest = root/'work/part2_caps/example.json.gz'
                dest.parent.mkdir(parents=True); dest.write_bytes(b'planted')
                if entry in ('aggregate', 'run_aggregate'):
                    continue  # Capture files are aggregate inputs, not its destination.
            if condition == 'killed':
                dest = root/'out/pool_part2/KILLED.json'
                dest.parent.mkdir(parents=True); dest.write_text('{}\n')
            def snapshot():
                return {str(p.relative_to(root)): (K.sha(p) if p.is_file() else 'DIRECTORY', p.stat().st_mtime_ns)
                        for p in root.rglob('*')}
            before = snapshot()
            if entry == 'launcher':
                cmd = ['bash', str(root/'part2/launch_part2.sh'), 'capture']
            elif entry.startswith('run_'):
                script = str(root/'part2/price.py') if entry == 'run_absolute' else './part2/price.py'
                cmd = ['bash', str(root/'run.sh'), script, 'aggregate' if entry == 'run_aggregate' else 'capture', '0', '1']
                if entry == 'run_option':
                    cmd.insert(2, '-B')
            else:
                script = 'price.py' if entry in ('capture', 'aggregate') else 'sam3_pass.py'
                cmd = [sys.executable, '-B', str(root/'part2'/script), entry]
                if entry == 'capture':
                    cmd += ['0', '1']
            result = subprocess.run(cmd, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                                    capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0, (condition, entry))
            self.assertIn('REFUSED:', result.stderr, (condition, entry, result.stderr))
            self.assertEqual(before, snapshot(), (condition, entry, 'refusal wrote files'))

    def test_planted_per_item_refused_without_writes(self):
        self.exercise('per_item')

    def test_missing_bars_refused_without_writes(self):
        self.exercise('missing')

    def test_altered_bars_refused_without_writes(self):
        self.exercise('altered')

    def test_per_capture_refused_without_writes(self):
        self.exercise('per_capture')

    def test_capture_work_refused_without_writes(self):
        self.exercise('capture_work')

    def test_killed_never_rerun(self):
        self.exercise('killed')


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    P.OUT2.mkdir(parents=True, exist_ok=True)
    (P.OUT2/'TESTS_PART2.json').write_text(json.dumps(dict(ran=result.testsRun, failures=[str(t) for t, _ in result.failures],
                                                           errors=[(str(t), e[-800:]) for t, e in result.errors], passed=result.wasSuccessful(),
                                                           role='CPU tests of the part 2 scripts on synthetic caches and a fixture; part 2 has not run',
                                                           input_sha256={str(p): K.sha(p) for p in [P.PART2/'test_part2.py', P.PART2/'price.py',
                                                                                                     P.PART2/'sam3_pass.py', P.PART2/'gate.py', P.PART2/'launch_part2.sh', P.NEW, P.BARS2, K.HERE/'kit.py',
                                                                                                     K.WORK/'part2_fixture/FIXTURE.json', K.WORK/'part2_fixture/aggregate/DECISION_PART2.json']}), indent=1)+'\n')
    sys.exit(0 if result.wasSuccessful() else 1)
