"""Tests of pooled_harm_rule_v2.py, ROOM_CROSSWALK.json and the read manifests (python3 -m unittest -v test_pooled_rule_v2)."""
import copy, csv, hashlib, json, os, re, subprocess, sys, tempfile, unittest
import numpy as np
import pooled_harm_rule_v2 as RULE
import build_crosswalk

HERE = os.path.dirname(os.path.abspath(__file__))
C = '/scratch/jjyeung/orch_n30/cont_ops/work'
TMP = tempfile.mkdtemp(prefix='t_', dir=os.path.join(HERE, 'test_tmp'))
READS = dict(D0m200=[C + '/d0/readk/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl', C + '/h1read/kit/build/ae470417b41/fetched/x/ITEMS.jsonl'],
             D0m100=[C + '/h1read/kit/build/af35386aa3e/fetched/x/ITEMS.jsonl'],
             H1m100=[C + '/h1read/kit/build/a24ea1a1936/fetched/x/ITEMS.jsonl'])
V1_OBS = '/scratch/jjyeung/orch_n30/pooled_rule/work/obs/'


def man(arm):
    return {'S': json.load(open(os.path.join(HERE, 'manifests/%s_dev-S1.json' % arm))),
            'R': json.load(open(os.path.join(HERE, 'manifests/%s_R0-dev.json' % arm)))}


def put(name, obj=None, text=None):
    p = os.path.join(TMP, name)
    with open(p, 'w') as f:
        f.write(text if text is not None else json.dumps(obj, indent=1, sort_keys=True) + '\n')
    return p


def rule_rows(path, fam, types):
    return [r for r in (json.loads(l) for l in open(path) if l.strip()) if r['family'] == fam and r['task_type'] in types]


XW = json.load(open(RULE.CROSSWALK))


class Crosswalk(unittest.TestCase):
    def test_rebuild_equals_pinned(self):
        s = json.dumps(build_crosswalk.build(), indent=1, sort_keys=True) + '\n'
        self.assertEqual(hashlib.sha256(s.encode()).hexdigest(), RULE.CROSSWALK_SHA256)

    def test_every_item_maps_to_exactly_one_room(self):
        for d in 'SR':
            b = RULE.BASE[d]
            cw = XW['sets'][b['name']]
            ids = [r['id'] for r in rule_rows(b['path'], b['family'], tuple(RULE.N_ITEMS[d]))]
            self.assertEqual(len(ids), b['items'])
            self.assertEqual(set(cw['items']), set(ids))
            self.assertEqual(len(cw['room_order']), b['rooms'])
            self.assertEqual(len(set(cw['room_order'])), b['rooms'])
            for i in ids:
                self.assertIn(cw['items'][i], cw['room_order'])          # a dict value: one room per item

    def test_no_physical_room_in_both_sets(self):
        a, b = set(XW['sets']['dev-S1']['room_order']), set(XW['sets']['R0-dev']['room_order'])
        self.assertEqual(a & b, set())
        r0 = set(l.strip() for l in open(build_crosswalk.SRC['r0_rooms']) if l.strip())
        self.assertEqual(a & r0, set())
        self.assertTrue(b <= r0)

    def test_scenes_of_one_room_are_clustered(self):
        venues = {r['video_id']: r['visit_id'] for r in csv.DictReader(open(build_crosswalk.SRC['arkit_metadata']))}
        for d in 'SR':
            b = RULE.BASE[d]
            cw = XW['sets'][b['name']]
            rows = rule_rows(b['path'], b['family'], tuple(RULE.N_ITEMS[d]))
            by_room, by_label = {}, {}
            for r in rows:
                room = cw['items'][r['id']]
                self.assertEqual(cw['scene_to_room'][r['scene']], room)
                self.assertEqual(cw['label_to_room'][r['room']], room)
                by_room.setdefault(room, set()).add(r['room'])
                by_label.setdefault(r['room'], set()).add(room)
            self.assertTrue(all(len(v) == 1 for v in by_room.values()))     # one physical room never spans two labels
            self.assertTrue(all(len(v) == 1 for v in by_label.values()))    # one label never spans two physical rooms
            if d == 'S':
                for r in rows:
                    ds, sid = r['scene'].split('/', 1)
                    lab = r['room']
                    if ds == 'scannet':
                        self.assertEqual(lab, 'd1/' + sid.split('_')[0])
                    elif ds == 'scannetppv2':
                        self.assertEqual(lab, 'd2/' + sid)
                    else:
                        self.assertEqual(lab, 'd3/venue' + venues[sid])
                labs = {}
                for r in rows:
                    if r['scene'].startswith('arkitscenes/'):
                        labs.setdefault(venues[r['scene'].split('/')[1]], set()).add(r['room'])
                self.assertTrue(all(len(v) == 1 for v in labs.values()))
                self.assertEqual(sum(1 for v in by_room if v.startswith('arkitscenes/')), 31)
            else:
                idmap = json.load(open(build_crosswalk.SRC['id_map']))
                native = {v['id']: v['room'] for v in idmap.values()}
                for r in rows:
                    self.assertEqual(cw['items'][r['id']], native[r['id']])

    def test_crosswalk_partition_equals_label_partition(self):
        """The crosswalk changes no cluster: its rooms partition the items exactly as the read's room labels do."""
        for d in 'SR':
            b = RULE.BASE[d]
            cw = XW['sets'][b['name']]
            rows = rule_rows(b['path'], b['family'], tuple(RULE.N_ITEMS[d]))
            p1 = sorted(sorted(i for i in (r['id'] for r in rows) if cw['items'][i] == room) for room in cw['room_order'])
            labels = sorted({r['room'] for r in rows})
            p2 = sorted(sorted(r['id'] for r in rows if r['room'] == lab) for lab in labels)
            self.assertEqual(p1, p2)
            self.assertEqual(cw['room_order'], [cw['label_to_room'][l] for l in labels])

    def _patched(self, edit):
        x = copy.deepcopy(XW)
        edit(x)
        p = put('xw.json', x)
        old = RULE.CROSSWALK_SHA256
        RULE.CROSSWALK_SHA256 = RULE.sha(p)
        try:
            with self.assertRaises(RULE.Refused) as e:
                RULE.prepare(READS['D0m200'], man('D0m200'), 200, True, crosswalk=p)
        finally:
            RULE.CROSSWALK_SHA256 = old
        return str(e.exception)

    def test_unmapped_item_refused(self):
        i = sorted(XW['sets']['dev-S1']['items'])[0]
        self.assertIn('no physical room', self._patched(lambda x: x['sets']['dev-S1']['items'].pop(i)))

    def test_label_of_another_room_refused(self):
        lab = sorted(XW['sets']['R0-dev']['label_to_room'])[0]
        other = XW['sets']['R0-dev']['room_order'][5]
        msg = self._patched(lambda x: x['sets']['R0-dev']['label_to_room'].__setitem__(lab, other))
        self.assertIn('label of another physical room', msg)

    def test_unpinned_crosswalk_refused(self):
        x = copy.deepcopy(XW)
        x['note'] = 'changed'
        with self.assertRaises(RULE.Refused):
            RULE.prepare(READS['D0m200'], man('D0m200'), 200, True, crosswalk=put('xw2.json', x))


class Provenance(unittest.TestCase):
    def refused(self, reads, m, step=200, calibration=True):
        with self.assertRaises(RULE.Refused) as e:
            RULE.prepare(reads, m, step, calibration)
        return str(e.exception)

    def test_valid_reads_pass(self):
        for arm in READS:
            d = RULE.prepare(READS[arm], man(arm), 200, True)
            self.assertEqual((d['S']['K'], d['R']['K']), (72, 98))

    def test_missing_manifest_refused(self):
        m = man('D0m200')
        m.pop('R')
        self.assertIn('no manifest', self.refused(READS['D0m200'], m))

    def test_config_differs_from_baseline_refused(self):
        for path, value in ((('arm',), 'tower'), (('reader_package',), '0' * 64), (('selector_rule',), 'candidates_argmax'),
                            (('item_file_sha256',), 'f' * 64), (('decoding', 'max_tokens'), 4096), (('tower_weights',), 'G3T')):
            m = man('D0m200')
            c = m['S']['config']
            for k in path[:-1]:
                c = c[k]
            c[path[-1]] = value
            self.assertIn('differs from the registered step-544 manifest', self.refused(READS['D0m200'], m))

    def test_internally_inconsistent_manifest_refused(self):
        m = man('D0m200')
        m['S']['run']['run_id'] = '673bc60f'
        self.assertIn('artifact path does not name', self.refused(READS['D0m200'], m))
        m = man('D0m200')
        m['S']['run']['orchard_job'] = 999999
        self.assertIn('does not match run.orchard_job', self.refused(READS['D0m200'], m))
        m = man('D0m200')
        m['R']['run']['plan_sha256'] = 'a' * 64
        self.assertIn('run.plan_sha256', self.refused(READS['D0m200'], m))

    def test_mixed_export_refused(self):
        m = {'S': man('D0m200')['S'], 'R': man('H1m100')['R']}
        self.assertIn('different exports', self.refused([READS['D0m200'][0], READS['H1m100'][0]], m))

    def test_read_file_named_by_no_manifest_refused(self):
        self.assertIn('named by no manifest', self.refused(READS['D0m200'] + READS['H1m100'], man('D0m200')))

    def test_read_not_from_fetched_archive_refused(self):
        rows = open(READS['D0m200'][0]).read().splitlines()
        k = next(n for n, l in enumerate(rows) if '"object_counting"' in l and '"main"' in l)
        r = json.loads(rows[k])
        r['score'] = 1.0 - r['score']
        rows[k] = json.dumps(r, sort_keys=True)
        p = put('tampered.jsonl', text='\n'.join(rows) + '\n')
        m = man('D0m200')
        m['S']['read_file']['sha256'] = RULE.sha(p)
        self.assertIn('not the decoded ITEMS.jsonl of the fetched archive', self.refused([p, READS['D0m200'][1]], m))

    def test_decision_read_must_be_r1(self):
        self.assertIn('not of run 673bc60f', self.refused(READS['D0m200'], man('D0m200'), calibration=False))

    def test_type_filter_claim_checked(self):
        m = man('D0m200')
        m['S']['type_filter'] = 'direct'
        self.assertIn('type filter direct', self.refused(READS['D0m200'], m))

    def test_baseline_manifests_describe_real_receipts(self):
        for d, job, step in (('S', 169526, 544), ('R', 171197, 544)):
            m = json.load(open(RULE.BASE[d]['manifest']))
            self.assertEqual(RULE.sha(RULE.BASE[d]['manifest']), RULE.BASE[d]['manifest_sha256'])
            self.assertEqual((m['run']['orchard_job'], m['run']['step'], m['run']['run_id'], m['run']['artifact_sha256']),
                             (job, step, '469ddece', RULE.BASE_ARTIFACT))
            self.assertEqual(m['read_file']['sha256'], RULE.BASE[d]['sha256'])

    def test_one_read_per_boundary_and_arm(self):
        lg = os.path.join(TMP, 'ledger.jsonl')
        e = dict(step=200, arm='direct', set='dev-S1', read_sha256='a' * 64, manifest_sha256='b' * 64)
        self.assertTrue(RULE.ledger_check(lg, e))
        with open(lg, 'a') as f:
            f.write(json.dumps(e) + '\n')
        self.assertFalse(RULE.ledger_check(lg, dict(e)))                          # the same read again: accepted, not logged twice
        with self.assertRaises(RULE.Refused):
            RULE.ledger_check(lg, dict(e, read_sha256='c' * 64))                    # a second, different read of the boundary
        with self.assertRaises(RULE.Refused):
            RULE.ledger_check(lg, dict(e, manifest_sha256='d' * 64))
        self.assertTrue(RULE.ledger_check(lg, dict(e, step=400, read_sha256='c' * 64)))


def synthetic(delta, route_rooms=None):
    """Room matrices with the real room structure of D0 m200 and a constant item difference `delta` on every item."""
    d = RULE.prepare(READS['D0m200'], man('D0m200'), 200, True)
    for k in 'SR':
        d[k]['S'] = d[k]['N'] * delta
        d[k]['SZ'] = d[k]['NZ'] * delta
    if route_rooms is not None:                                    # route planning moved into the first `route_rooms` rooms
        n = d['S']['N'][:, 6].sum()
        col = np.zeros(d['S']['K'])
        col[:route_rooms] = n / route_rooms
        d['S']['N'][:, 6] = col
        d['S']['S'][:, 6] = col * delta
    return d


class StopAtZero(unittest.TestCase):
    def test_reviewer_case_unrounded_bounds_decide(self):
        """Every interval lies below zero by less than the display rounding: v1 rounded first and stayed SILENT."""
        d = synthetic(-1e-6)
        res = RULE.decide(d, 200)
        self.assertTrue(res['stop'])
        self.assertEqual(len(res['H1']), 8)
        self.assertTrue(res['H2'])
        shown = RULE.display(res)
        for r in shown['types']:
            self.assertEqual(r['interval_pp'][1], 0.0)                 # the displayed bound rounds to zero ...
            self.assertLess(r['interval_pp_unrounded'][1], 0)        # ... the unrounded one is below zero and decides
            self.assertFalse(r['interval_pp'][1] < 0)                 # the v1 test on the rounded bound would not fire
            self.assertTrue(r['fires'])

    def test_zero_difference_is_silent(self):
        self.assertFalse(RULE.decide(synthetic(0.0), 200)['stop'])


class Reporting(unittest.TestCase):
    def test_size_split(self):
        res = RULE.decide(RULE.prepare(READS['D0m200'], man('D0m200'), 200, True), 200)
        z = {s['part']: s for s in res['size_split']}
        self.assertEqual([z[k]['items'] for k in ('dev-S1 metric', 'dev-S1 imperial', 'R0-dev (cm)')], [72, 78, 293])
        self.assertEqual(round(100 * z['dev-S1 metric']['delta'], 3), -5.833)
        self.assertEqual(round(100 * z['dev-S1 imperial']['delta'], 3), -12.949)
        size = res['types'][RULE.SIZE]
        self.assertAlmostEqual(z['R0-dev (cm)']['delta'], size['r0_dev']['delta'])
        self.assertEqual(z['R0-dev (cm)']['ci95'], size['r0_dev']['ci95'])
        dS = size['dev_s1']['delta']
        self.assertAlmostEqual((72 * z['dev-S1 metric']['delta'] + 78 * z['dev-S1 imperial']['delta']) / 150, dS)

    def test_console_table(self):
        m = man('D0m200')
        out = subprocess.run([sys.executable, os.path.join(HERE, 'pooled_harm_rule_v2.py'), '--step', '200', '--calibration', '--read'] + READS['D0m200'] +
                             ['--manifest-s1', os.path.join(HERE, 'manifests/D0m200_dev-S1.json'), '--manifest-r0',
                              os.path.join(HERE, 'manifests/D0m200_R0-dev.json'), '--output', os.path.join(TMP, 'o.json')],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=True).stdout
        self.assertIn('dev-S1 delta [95%]', out)
        self.assertIn('R0-dev delta [95%]', out)
        line = next(l for l in out.splitlines() if l.startswith('object_size_estimation'))
        self.assertEqual(line.count('['), 3)                           # dev-S1 95%, R0-dev 95%, pooled interval
        for part in ('dev-S1 metric', 'dev-S1 imperial', 'R0-dev (cm)'):
            self.assertIn(part, out)


class Draws(unittest.TestCase):
    def test_draw_missing_a_type_is_redrawn(self):
        d = synthetic(-0.01, route_rooms=2)
        P, DS, DR, ZS, redrawn = RULE.draws(d)
        self.assertGreater(redrawn, 0)
        self.assertEqual(len(P), RULE.DRAWS)
        self.assertTrue(np.isfinite(P).all())

    def test_real_reads_have_no_redraw(self):
        for arm in READS:
            self.assertEqual(RULE.draws(RULE.prepare(READS[arm], man(arm), 200, True))[4], 0)


class Reproduction(unittest.TestCase):
    def test_v2_equals_v1_on_three_reads(self):
        for arm in READS:
            data = RULE.prepare(READS[arm], man(arm), 200, True)
            for step, lv in ((200, 'level200'), (400, 'levelLater')):
                new = RULE.display(RULE.decide(data, step))
                old = json.load(open(V1_OBS + '%s_%s.json' % (arm, lv)))
                for a, b in zip(new['types'], old['types']):
                    self.assertEqual((a['type'], a['pooled_delta_pp'], a['interval_pp'], a['ci95_pp']),
                                     (b['type'], b['pooled_delta_pp'], b['interval_pp'], b['ci95_pp']))
                    for nm in ('dev_s1', 'r0_dev'):
                        if nm in b:
                            self.assertEqual(a[nm]['ci95_pp_printed_only'], b[nm]['ci95_pp_printed_only'])
                self.assertEqual(new['mean_of_eight']['interval_pp'], old['mean_of_eight']['interval_pp'])


if __name__ == '__main__':
    unittest.main()
