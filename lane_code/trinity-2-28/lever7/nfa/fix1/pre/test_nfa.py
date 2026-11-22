"""NF-A tests (local CPU, no model): item rule, order, operator, worker entry, scorer, package."""
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parent
NFA = KIT.parent
PAYLOAD = NFA / 'ref/payload'
PARENT = NFA / 'ref/parent'
RET = NFA / 'ref/ret'
PY = sys.executable
WORK = Path(tempfile.mkdtemp(prefix='t', dir=NFA / 'work'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


for p in (PAYLOAD / 'b', PAYLOAD / 'tree', PAYLOAD):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
SEL = load('select_nfa', KIT / 'select_nfa.py')
SCORE = load('score_nfa', KIT / 'score_nfa.py')
BUILD = load('build_nfa', KIT / 'build_nfa.py')
ITEMS = json.loads((KIT / 'ITEMS_NFA.json').read_text())
OP = load('op_nfa', KIT / '6.py')
FULL = json.loads((PAYLOAD / 'items/devs1_routed.json').read_text())['items']
ORDER = ('camera_displacement', 'camera_rotation', 'camera_movement_direction',
         'object_abs_distance', 'room_size_estimation')


class ItemRule(unittest.TestCase):
    def test_deterministic(self):
        a = SEL.build(PAYLOAD / 'items/devs1_routed.json', RET / 'metadata/reads/0/metadata/journals')
        b = SEL.build(PAYLOAD / 'items/devs1_routed.json', RET / 'metadata/reads/0/metadata/journals')
        self.assertEqual(a, b)
        self.assertEqual(json.dumps(a, indent=1, sort_keys=True) + '\n', (KIT / 'ITEMS_NFA.json').read_text())

    def test_rule_independently(self):
        h = lambda s: hashlib.sha256(s.encode()).hexdigest()
        pool = [r for r in FULL if r['question_type'] in SEL.TYPES]
        self.assertEqual(len(pool), 600)
        # 37.5 each: the two types with the smallest tie hash get 38.
        ranked = sorted(SEL.TYPES, key=lambda t: h('nfa-v1|type|' + t))
        want = {t: 38 if t in ranked[:2] else 37 for t in SEL.TYPES}
        self.assertEqual(ITEMS['per_type'], want)
        chosen = set(ITEMS['forward_ids'])
        for t in SEL.TYPES:
            rows = [r for r in pool if r['question_type'] == t]
            ds = Counter(r['dataset'] for r in rows)
            got = Counter(r['dataset'] for r in rows if r['id'] in chosen)
            for d, n in ds.items():
                quota = n * want[t] / len(rows)
                self.assertTrue(int(quota) <= got[d] <= int(quota) + 1, (t, d))
                stratum = sorted((r for r in rows if r['dataset'] == d), key=lambda r: h('nfa-v1|' + r['id']))
                self.assertEqual({r['id'] for r in stratum[:got[d]]}, {r['id'] for r in stratum if r['id'] in chosen})
            self.assertEqual(sum(got.values()), want[t])

    def test_order_matches_job(self):
        # The job decodes each type of the (id-sorted) list in the read's type sequence.
        sub = [FULL[i] for i in sorted(ITEMS['forward_indices'])]
        job = [r['id'] for t in (3, 0, 1, 2) for r in sub if r['question_type'] == ORDER[t]]
        self.assertEqual(job, ITEMS['forward_ids'])
        self.assertEqual(ITEMS['reverse_ids'], ITEMS['forward_ids'][::-1])
        self.assertEqual(OP.planned(1, sub, OP.SEQUENCES[0]), ITEMS['reverse_ids'])
        self.assertEqual(OP.planned(0, sub, OP.SEQUENCES[0]), ITEMS['forward_ids'])
        rev = [r['id'] for t in OP.SEQUENCES[1] for r in sub[::-1] if r['question_type'] == ORDER[t]]
        self.assertEqual(rev, ITEMS['reverse_ids'])
        # 171253 read 0 executed exactly id-sorted order within each type.
        for t in range(5):
            ids = [json.loads(l)['id'] for l in (RET / f'metadata/reads/0/metadata/journals/{t}/0/items.jsonl').read_text().splitlines()]
            self.assertEqual(ids, sorted(ids))

    def test_counts(self):
        self.assertEqual(len(ITEMS['forward_ids']), 150)
        self.assertEqual(len(set(ITEMS['forward_ids'])), 150)
        self.assertEqual(sum(ITEMS['per_type_dataset'].values()), 150)


def prepared(root):
    """A prepared settings file, an export and an artifact, as prepare.py leaves them."""
    root = Path(root); (root / 'e').mkdir(parents=True); (root / 'e/x.bin').write_bytes(b'x')
    (root / 'artifact.json').write_text('{}')
    (root / 'pin.json').write_text(json.dumps(dict(lineage='SFT', step=544)))
    s = dict(export_dir=str(root / 'e'), perception_memo='off', perception_memo_modules=['g3t'],
             perception_memo_verify_ids=[], stage1_select_rule='null_argmax', arm='own_depth', save_own_depth=False)
    (root / 'settings.json').write_text(json.dumps(s))
    return dict(package=str(PAYLOAD), output=str(root / 'r'), python=PY, export=str(root / 'e'),
                binding=str(root / 'artifact.json'), export_pin=str(root / 'pin.json'),
                settings=str(root / 'settings.json'), plan_sha256='p', inputs_sha256='i', operator_sha256='o',
                types=list(ORDER), stop_margin=1800, return_margin=1200, prefix=[])


class Operator(unittest.TestCase):
    def test_subset_manifest(self):
        from h1eval.items import load_manifest
        path = WORK / 'sub/0.json'
        forward = OP.subset(PAYLOAD, path)
        m = load_manifest(path)
        self.assertEqual(forward, ITEMS['forward_ids'])
        self.assertEqual([r['id'] for r in m['items']], sorted(forward))
        self.assertEqual(m['count'], 150); self.assertEqual(m['name'], 'devs1_routed')
        self.assertEqual(m['per_type'], dict(sorted(ITEMS['per_type'].items())))
        full = {r['id']: r for r in FULL}
        self.assertTrue(all(full[r['id']] == r for r in m['items']))
        self.assertEqual(OP.subset(PAYLOAD, path), forward)  # idempotent

    def test_prepare(self):
        from orchard_h10.runner import worker_args
        cfg = prepared(WORK / 'prep')
        configs, forward = OP.prepare(cfg)
        self.assertEqual(forward, ITEMS['forward_ids'])
        self.assertEqual(configs[0]['types'], ITEMS['forward_type_sequence'])
        self.assertEqual(configs[1]['types'], ITEMS['reverse_type_sequence'])
        for i in (0, 1):
            c = configs[i]
            self.assertEqual(c['q'], i)
            s = json.loads(Path(c['settings']).read_text())
            self.assertEqual((s['stage1_select_rule'], s['perception_memo'], s['perception_memo_verify_ids'],
                              s['perception_memo_modules'], s['save_own_depth']),
                             ('candidates_argmax', 'on', [], ['g3t'], False))
            entry = Path(c['output']) / 'metadata/a/5.py'
            self.assertEqual(entry.read_text(), (KIT / 'src/w.py').read_text())
            t = ORDER.index(c['types'][0])
            args = worker_args(dict(config=c, type=t, index=0, cards=1, stop_at=1, finish_by=2))
            self.assertEqual(args[args.index('--types') + 1], ','.join(c['types']))
            self.assertEqual(Path(args[args.index('--items') + 1]).read_bytes(), Path(c['items']).read_bytes())
            self.assertIn('--type-journals', args)
        ident = json.loads((Path(cfg['output']) / 'metadata/IDENTITY.json').read_text())
        self.assertEqual(ident['items'], 150)
        configs2, _ = OP.prepare(cfg)  # sealed identity accepts the same inputs
        self.assertEqual(configs2[0]['items'], configs[0]['items'])

    def test_run_order_and_stops(self):
        cfg = prepared(WORK / 'run')
        calls = []
        def runner(c, cards, end, prefix=()):
            calls.append(c['q']); return dict(failure=None, complete=True, completed=150)
        s = OP.run(cfg, 10 ** 10, ['0'], runner=runner)
        self.assertEqual(calls, [0, 1]); self.assertTrue(s['complete']); self.assertEqual(s['expected'], 300)
        calls.clear()
        s = OP.run(dict(cfg, output=str(WORK / 'run2' / 'r')), 10 ** 10, ['0'],
                   runner=lambda c, *a, **k: calls.append(c['q']) or dict(failure='x', complete=False, completed=3))
        self.assertEqual(calls, [0]); self.assertEqual(s['failure'], 'x')
        calls.clear()
        s = OP.run(dict(cfg, output=str(WORK / 'run3' / 'r')), 5000, ['0'], runner=runner, clock=lambda: 3199)
        self.assertEqual(calls, [0, 1])
        s = OP.run(dict(cfg, output=str(WORK / 'run4' / 'r')), 5000, ['0'], runner=runner, clock=lambda: 3200)
        self.assertEqual(s['completed'], 0)
        with self.assertRaises(ValueError):
            OP.run(cfg, 10 ** 10, [''], runner=runner)

    def test_memory_and_constants(self):
        m = OP.memory_bound()
        self.assertTrue(m['fits']); self.assertEqual(m['basis'], 'fixed_g3t_shapes')
        self.assertEqual(OP.WRAPPER, (KIT / 'src/w.py').read_text())
        self.assertEqual(OP.IDX, ITEMS['forward_indices'])


def fake_worker(i, first_rows, ids):
    """Stand-in for runner.run in the CPU rehearsal: writes what the worker writes."""
    def execute(cfg, cards, end, prefix=()):
        assert cards == [''] and cfg['q'] == i
        t = ORDER.index(cfg['types'][0])
        d = Path(cfg['output']) / 'metadata/journals' / str(t) / '0'; d.mkdir(parents=True)
        (d / 'environment.json').write_text(json.dumps(dict(binding=dict(
            ids=ids, stage1_select_rule='candidates_argmax', perception_memo='on',
            perception_memo_verify_ids=[], perception_memo_modules=['g3t']))))
        with (d / 'items.jsonl').open('w') as f:
            for r in first_rows:
                f.write(json.dumps(r) + '\n')
        return dict(failure=None, complete=False, completed=len(first_rows))
    return execute


class Rehearsal(unittest.TestCase):
    def run_case(self, name, rev_ids, fwd_ids, rows):
        cfg = prepared(WORK / name)
        seq = iter([fake_worker(1, [], rev_ids), fake_worker(0, rows, fwd_ids)])
        with mock.patch('orchard_h10.runner.run', side_effect=lambda *a, **k: next(seq)(*a, **k)), \
                mock.patch.object(pathlib.Path, 'unlink', lambda self, missing_ok=False: None):
            return OP.rehearsal(cfg, 10 ** 10)

    def first_type(self, ids, kind):
        k = dict(zip(ITEMS['forward_ids'], ITEMS['forward_types']))
        return [x for x in ids if k[x] == kind]

    def test_pass(self):
        rev = self.first_type(ITEMS['reverse_ids'], ITEMS['reverse_type_sequence'][0])
        fwd = self.first_type(ITEMS['forward_ids'], ITEMS['forward_type_sequence'][0])
        row = dict(id=fwd[0], complete=True, seconds=1.0, output=dict(text='t', finish='eos', scores=dict(answer=1)))
        r = self.run_case('reh1', rev, fwd, [row])
        self.assertTrue(r['passed']); self.assertEqual([x['read'] for x in r['reads']], [1, 0])
        self.assertTrue(r['reads'][1]['first']['exact'])
        from orchard_h10.common import opaque
        opaque([json.dumps(r)])  # REHEARSAL.json and 1.log land on the shared filesystem

    def test_wrong_order_fails(self):
        fwd = self.first_type(ITEMS['forward_ids'], ITEMS['forward_type_sequence'][0])
        with self.assertRaises(ValueError) as e:
            self.run_case('reh2', fwd, fwd, [])
        self.assertIn('E72', str(e.exception))

    def test_missing_record_fails(self):
        rev = self.first_type(ITEMS['reverse_ids'], ITEMS['reverse_type_sequence'][0])
        fwd = self.first_type(ITEMS['forward_ids'], ITEMS['forward_type_sequence'][0])
        with self.assertRaises(ValueError):
            self.run_case('reh3', rev, fwd, [])


class WorkerEntry(unittest.TestCase):
    """The real entry bytes and the real launch loop decide the order; only the reader is a stub."""
    def drive(self, name):
        cfg = prepared(WORK / name)
        configs, _ = OP.prepare(cfg)
        (WORK / name / 'b' / 'e2e_reader').mkdir(parents=True)
        (WORK / name / 'b' / 'e2e_reader' / 'x.py').write_text('')
        order = {}
        for i in (0, 1):
            c = dict(configs[i]); c['package'] = str(PAYLOAD)
            from orchard_h10.runner import commands
            argv = commands(c, c['types'][0], 0, ['0'], 10 ** 10, 10 ** 10)
            root = Path(c['output']) / 'metadata/a'
            driver = WORK / name / f'd{i}.py'
            driver.write_text(DRIVER % dict(payload=str(PAYLOAD), reader=str(WORK / name / 'b')))
            out = subprocess.run([PY, '-B', '-I', str(driver), argv[-1]], cwd=root, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr[-2000:])
            ids = []
            for kind in c['types']:
                p = Path(c['output']) / 'metadata/journals' / str(ORDER.index(kind)) / '0/items.jsonl'
                ids += [json.loads(l)['id'] for l in p.read_text().splitlines()]
                env = json.loads((p.parent / 'environment.json').read_text())['binding']['ids']
                self.assertEqual(env, [x for x in ids if x in set(env)])
            order[i] = ids
        return order

    def test_orders(self):
        order = self.drive('entry')
        self.assertEqual(order[0], ITEMS['forward_ids'])
        self.assertEqual(order[1], ITEMS['reverse_ids'])


DRIVER = r'''
import json, runpy, sys
sys.path[:0] = [%(payload)r + '/b', %(payload)r + '/tree', %(payload)r]
from h1eval.h10 import launch
def maker(export, artifact, items, perception_factory=None, device=None):
    return lambda item: dict(text='<answer>A</answer>', finish='eos')
def main(argv):
    args = launch.parser().parse_args(argv)
    args.reader_entry = 'stub:maker'; args.reader_root = %(reader)r
    print(json.dumps(launch.run_types(args, make_real=maker)))
    return 0
launch.main = main
sys.argv = ['5.py', sys.argv[1]]
runpy.run_path('5.py', run_name='__main__')
'''


def journal(root, read, rows_by_type):
    for kind, rows in rows_by_type.items():
        d = Path(root) / 'metadata/reads' / str(read) / 'metadata/journals' / str(ORDER.index(kind)) / '0'
        d.mkdir(parents=True, exist_ok=True)
        (d / 'environment.json').write_text(json.dumps(dict(binding=dict(ids=[r['id'] for r in rows]))))
        with (d / 'items.jsonl').open('w') as f:
            for r in rows:
                f.write(json.dumps(r) + '\n')


def synth(name, change=lambda i, x: None):
    """Both reads in their planned orders; change(i, row) edits read i's rows."""
    root = WORK / name
    kinds = dict(zip(ITEMS['forward_ids'], ITEMS['forward_types']))
    rooms = dict(zip(ITEMS['forward_ids'], ITEMS['forward_rooms']))
    for read, ids in ((0, ITEMS['forward_ids']), (1, ITEMS['reverse_ids'])):
        by = {}
        for x in ids:
            row = dict(id=x, room_key=rooms[x], type=kinds[x], arm='tower', mode='none', complete=True, seconds=1.0,
                       output=dict(text='<answer>B</answer>', finish='eos', scores=dict(answer=1.0)))
            change(read, row)
            by.setdefault(kinds[x], []).append(row)
        journal(root, read, by)
    return root


class Scorer(unittest.TestCase):
    def test_identical(self):
        r = SCORE.score(synth('s0'), KIT / 'ITEMS_NFA.json', WORK / 's0o')
        for kind, v in r['types'].items():
            self.assertEqual(v['difference']['ci95'], [0.0, 0.0]); self.assertEqual(v['changed_answers'], 0)
            self.assertFalse(v['floor_fails']); self.assertTrue(v['complete'])
        for read in ('0', '1'):
            self.assertTrue(all(c['bound_exact'] and c['executed_prefix'] for c in r['order'][read].values()))

    def test_changed_share(self):
        kind = 'camera_rotation'; ids = [x for x, k in zip(ITEMS['forward_ids'], ITEMS['forward_types']) if k == kind]
        two = set(ids[:2])  # 2 of 37 = 5.4% > 5%
        def edit(read, row):
            if read == 1 and row['id'] in two:
                row['output']['text'] = '<answer>C</answer>'
        v = SCORE.score(synth('s1', edit), KIT / 'ITEMS_NFA.json')['types'][kind]
        self.assertEqual(v['changed_answers'], 2); self.assertTrue(v['share_fails']); self.assertTrue(v['floor_fails'])
        self.assertEqual(v['score_changed'], 0)
        one = set(ids[:1])
        def edit1(read, row):
            if read == 1 and row['id'] in one:
                row['output']['text'] = '<answer>C</answer>'
        v = SCORE.score(synth('s2', edit1), KIT / 'ITEMS_NFA.json')['types'][kind]
        self.assertFalse(v['share_fails']); self.assertFalse(v['floor_fails'])

    def test_interval(self):
        kind = 'object_abs_distance'
        def edit(read, row):
            if read == 1 and row['type'] == kind:
                row['output']['scores']['answer'] = 0.9  # every item 10 points lower in reverse
        v = SCORE.score(synth('s3', edit), KIT / 'ITEMS_NFA.json')['types'][kind]
        self.assertAlmostEqual(v['difference']['value'], -10.0)
        self.assertTrue(v['points_fails']); self.assertTrue(v['interval_beyond_margin']); self.assertFalse(v['share_fails'])
        def small(read, row):
            if read == 1 and row['type'] == kind:
                row['output']['scores']['answer'] = 0.997  # -0.3 points: inside the margin
        v = SCORE.score(synth('s4', small), KIT / 'ITEMS_NFA.json')['types'][kind]
        self.assertFalse(v['points_fails']); self.assertFalse(v['interval_beyond_margin'])
        def one(read, row):
            if read == 1 and row['type'] == kind and row['id'] == ITEMS['forward_ids'][ITEMS['forward_types'].index(kind)]:
                row['output']['scores']['answer'] = 0.0  # one item drops a full point: |diff| >= 0.5
        v = SCORE.score(synth('s4b', one), KIT / 'ITEMS_NFA.json')['types'][kind]
        self.assertTrue(v['points_fails'])

    def test_capped_and_missing(self):
        kind = 'camera_displacement'; ids = [x for x, k in zip(ITEMS['forward_ids'], ITEMS['forward_types']) if k == kind]
        def edit(read, row):
            if read == 0 and row['id'] == ids[0]:
                row['output']['finish'] = 'max_calls'
        v = SCORE.score(synth('s5', edit), KIT / 'ITEMS_NFA.json')['types'][kind]
        self.assertEqual(v['capped'], [1, 0]); self.assertEqual(v['changed_answers'], 1)
        self.assertAlmostEqual(v['score_forward'], 100 * 36 / 37)
        root = synth('s6')
        p = root / 'metadata/reads/1/metadata/journals/0/0/items.jsonl'
        lines = p.read_text().splitlines(True); p.write_text(''.join(lines[:-1]))
        v = SCORE.score(root, KIT / 'ITEMS_NFA.json')['types'][kind]
        self.assertEqual(v['paired'], 36); self.assertFalse(v['complete'])

    def test_order_check_detects_swap(self):
        root = synth('s7')
        p = root / 'metadata/reads/1/metadata/journals/2/0/items.jsonl'
        lines = p.read_text().splitlines(True); p.write_text(''.join([lines[1], lines[0], *lines[2:]]))
        r = SCORE.score(root, KIT / 'ITEMS_NFA.json')
        self.assertFalse(r['order']['1']['camera_movement_direction']['executed_prefix'])

    def test_bootstrap_matches_project(self):
        from h1eval import statistics
        vals = [('r%d' % (i % 7), float(i % 3)) for i in range(40)]
        self.assertEqual(SCORE.bootstrap(vals, seed=statistics.SEED), statistics.bootstrap(vals))

    def test_answer_text_matches_project(self):
        from h1eval import scorers
        for o in (dict(text='a</think>\n\n3.00<|im_end|>', finish='eos'), dict(text='<answer> B </answer>', finish='eos'),
                  dict(text='x', finish='max_calls'), dict(text='plain<|x', finish='eos')):
            self.assertEqual(SCORE.answer_text(o), scorers.answer_text(o))

    def test_registered_baselines(self):
        # item_score on 171253 read 0 reproduces the registered tower baselines.
        want = {0: 82.33, 1: 75.60, 2: 94.67, 3: 26.93}
        for t, v in want.items():
            rows = [json.loads(l) for l in (RET / f'metadata/reads/0/metadata/journals/{t}/0/items.jsonl').read_text().splitlines()]
            self.assertAlmostEqual(round(100 * sum(SCORE.item_score(r['output'])[0] for r in rows) / len(rows), 2), v)


class Package(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.token = (KIT / 'TOKEN').read_text().strip()
        cls.placed, cls.public = BUILD.build(PARENT, cls.token, (KIT / '6.py').read_bytes(), (KIT / 'src/c.py').read_bytes(), None)

    def test_payload_only_plan_differs(self):
        def members(raw):
            with tarfile.open(fileobj=io.BytesIO(raw)) as t:
                return {e.name: t.extractfile(e).read() for e in t}
        old, new = members((PARENT / '0.tgz').read_bytes()), members(self.placed['0.tgz'])
        self.assertEqual(set(old), set(new))
        self.assertEqual([n for n in old if old[n] != new[n]], ['9.json'])
        a, b = json.loads(old['9.json']), json.loads(new['9.json'])
        self.assertEqual({k: v for k, v in a.items() if k != 'token'}, {k: v for k, v in b.items() if k != 'token'})
        self.assertEqual(b['token'], self.token)
        from orchard_h10.job import verify_config
        verify_config({**b, **self.public})

    def test_bundle(self):
        batch = self.placed['BATCH.sh'].decode()
        m = re.search(r"bytes\.fromhex\('([0-9a-f]+)'\)", batch)
        with tarfile.open(fileobj=io.BytesIO(bytes.fromhex(m.group(1)))) as t:
            b = {e.name: t.extractfile(e).read() for e in t}
        self.assertEqual(set(b), {'0.py', '0.json', '7.py'})
        self.assertEqual(b['7.py'], self.placed['a/6.py'])
        self.assertEqual(json.loads(b['0.json']), json.loads(self.placed['0.json']))
        self.assertEqual(b['0.py'], (NFA / 'ref/bundle/0.py').read_bytes())
        self.assertIn("('a'+j+'%s')" % self.token, batch)
        self.assertEqual(batch.count('b9ef552934627'), 0)
        old = (PARENT / 'BATCH.sh').read_text()
        strip = lambda s: re.sub(r"fromhex\('[0-9a-f]+'\)", '', s).replace(self.token, 'T').replace('b9ef552934627', 'T')
        self.assertEqual(strip(batch), strip(old))

    def test_pins_and_reuse(self):
        pins = json.loads(self.placed['PACKAGE.json'])['files']
        for n, h in pins.items():
            self.assertEqual(hashlib.sha256(self.placed[n]).hexdigest(), h)
        for n in ('3.py', 'SUBMIT.cmd', 'INPUTS.example.json', 'a/1.json', 'a/export.json'):
            self.assertEqual(self.placed[n], (PARENT / n).read_bytes())
        self.assertLess(sum(len(v) for v in self.placed.values()), 20 * 10 ** 6)

    def test_bundle_guard_locally(self):
        """The CPU check's own bundle guard (a/5.py check_bundle_guard) on the built package."""
        pkg = WORK / 'pkg'
        BUILD.build(PARENT, self.token, (KIT / '6.py').read_bytes(), (KIT / 'src/c.py').read_bytes(), pkg)
        root = WORK / 'guardroot'; root.mkdir()
        c = load('cpu_nfa', pkg / 'a/5.py')
        sys.path.insert(0, str(PAYLOAD / 'orchard_h10/vendor'))
        from orchard_h10.common import install_process_guard
        import subprocess as sp
        kept = sp.Popen
        try:
            install_process_guard(root)
            proof = c.check_bundle_guard(pkg, root)
        finally:
            sp.Popen = kept
        self.assertTrue(proof['passed'])
        self.assertEqual(proof['operator_sha256'], hashlib.sha256((pkg / 'a/6.py').read_bytes()).hexdigest())

    def test_opaque_surfaces(self):
        from orchard_h10.common import opaque, submit_argv
        for n, v in self.placed.items():
            opaque([n])
            if '/' not in n and n != '0.tgz':
                opaque([v.decode()])
        opaque(submit_argv(self.token, 1, '02:30:00'))
        for p in sorted(KIT.glob('o_*.sh')):
            # The placement script's base64 literal is noise, scanned as decoded files above.
            text = re.sub(r"b64decode\('[A-Za-z0-9+/=]+'\)", 'b64decode()', p.read_text())
            opaque([text])
        place = (KIT / 'o_place.sh').read_text()
        self.assertEqual(len(re.findall(r"b64decode\('[A-Za-z0-9+/=]+'\)", place)), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
