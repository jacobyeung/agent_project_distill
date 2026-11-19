"""Tests for the fold rule, the pool builders, the reader contract and parity (bash run.sh test_kit.py; out/TESTS.json)."""
import gzip, json, unittest
import numpy as np
import kit as K
import aggregate as G
T = K.T
CAPTURE = 'scannetpp/067e2e4e61'


def obj(fold, raw, **cands):
    return dict(fold=fold, on_target=dict(raw=raw, **cands))


def rle(mask):
    return T.F.rle(mask)


class FoldRule(unittest.TestCase):
    def test_needs_five_fit_objects(self):
        objs = [obj(1, False, a=True) for _ in range(4)]
        self.assertEqual(G.choose(objs, ['a'], 0)[0], 'raw')
        self.assertEqual(G.choose(objs+[obj(2, False, a=True)], ['a'], 0)[0], 'a')

    def test_count_must_be_strictly_larger(self):
        objs = [obj(1, True, a=True) for _ in range(6)]
        self.assertEqual(G.choose(objs, ['a'], 0)[0], 'raw')
        objs[0]['on_target']['raw'] = False
        self.assertEqual(G.choose(objs, ['a'], 0)[0], 'a')

    def test_held_fold_never_enters(self):
        fit = [obj(1, False, a=True) for _ in range(5)]
        held = [obj(0, True, a=False) for _ in range(50)]
        self.assertEqual(G.choose(fit+held, ['a'], 0)[0], 'a')
        v, ev = G.choose(fit+held, ['a'], 0)
        self.assertEqual(ev['fit_objects'], 5)
        self.assertEqual(G.choose(fit+held, ['a'], 1)[0], 'raw')

    def test_held_fold_objects_do_not_count_as_fit(self):
        objs = [obj(0, False, a=True) for _ in range(9)]+[obj(1, False, a=True) for _ in range(4)]
        self.assertEqual(G.choose(objs, ['a'], 0)[0], 'raw')

    def test_best_candidate_and_sorted_tie_order(self):
        objs = [obj(1, False, a=i < 3, b=i < 4, c=i < 4) for i in range(6)]
        self.assertEqual(G.choose(objs, ['a', 'b', 'c'], 0)[0], 'b')
        self.assertEqual(G.choose(objs, ['c', 'b', 'a'], 0)[0], 'c')

    def test_all_rooms_refit(self):
        objs = [obj(k % 5, False, a=True) for k in range(5)]
        self.assertEqual(G.choose(objs, ['a'], None), ('a', dict(fit_objects=5, counts=dict(raw=0, a=5))))
        self.assertEqual(G.choose(objs, ['a'], 0)[0], 'raw')

    def test_missing_variant_counts_as_off_target(self):
        objs = [obj(1, False) for _ in range(6)]
        self.assertEqual(G.choose(objs, ['q:x'], 0)[0], 'raw')

    def test_candidates_and_phrases_per_arm(self):
        self.assertEqual(G.candidates('W1', ['radiator', 'space heater']), ['q:radiator', 'q:space heater'])
        self.assertEqual(G.candidates('W2', ['radiator']), ['fb:radiator'])
        self.assertEqual(G.candidates('W2c', ['radiator']), ['call:radiator'])
        self.assertEqual(G.phrases('q:radiator', 'heater'), ['radiator'])
        self.assertEqual(G.phrases('fb:radiator', 'heater'), ['heater', 'radiator'])
        self.assertEqual(G.phrases('call:radiator', 'heater'), ['heater', 'radiator'])
        self.assertEqual(G.phrases('raw', 'heater'), ['heater'])

    def test_pcf_rule_reads_recall_only(self):
        objs = [dict(fold=1, recall_lift=dict(raw=False, all=True), on_target=dict(raw=True)) for _ in range(5)]
        self.assertEqual(G.choose(objs, ['all'], 0, key='recall_lift')[0], 'all')


class Pools(unittest.TestCase):
    def synthetic(self, with_presence=True):
        m = np.zeros((48, 64), bool); m[:10, :10] = True
        n = np.zeros((48, 64), bool); n[20:30, 20:30] = True
        def inst(q, score, src, pres):
            d = dict(query=q, score=score, mask=rle(m if src == 'heater' else n), source_prompt=src)
            if with_presence or src == 'heater':
                d['source_presence'] = pres
            return d
        frames = {str(s): dict(phrases={'heater': dict(presence=.9, instances=[])}) for s in range(32)}
        frames['0']['phrases']['heater']['instances'] = [inst(0, .8, 'heater', .9), inst(1, .6, 'radiator', .5)]
        frames['1']['phrases']['heater']['instances'] = [inst(0, .7, 'radiator', .5), inst(1, .01, 'radiator', .5)]
        return dict(frames=frames)

    def test_single_prompt_variants(self):
        pv = K.pools(self.synthetic(), 'heater', {'heater': ['radiator']}, offline=True)
        count = lambda v: [len(f) for f in pv[v][0][:3]]
        self.assertEqual(count('raw'), [1, 0, 0])
        self.assertEqual(count('q:radiator'), [1, 1, 0])
        self.assertEqual(count('fb:radiator'), [1, 1, 0])
        self.assertEqual(count('all'), [2, 1, 0])
        self.assertEqual(pv['fb:radiator'][0][0][0]['source_prompt'], 'heater')
        self.assertEqual(pv['fb:radiator'][0][1][0]['source_prompt'], 'radiator')
        self.assertEqual([e['presence'] for e in pv['q:radiator'][0][0]], [.5])
        self.assertEqual(pv['cap100'][1], pv['raw'][1])
        self.assertEqual([pv[v][2] for v in ('raw', 'q:radiator', 'fb:radiator')], ['heater', 'radiator', 'heater'])

    def test_priced_pools_have_one_presence_per_frame(self):
        pv = K.pools(self.synthetic(), 'heater', {'heater': ['radiator']}, offline=True)
        for v in ('raw', 'cap100', 'q:radiator', 'fb:radiator'):
            K.uniform(pv[v][0])
        with self.assertRaisesRegex(ValueError, 'mixed_presence_frame'):
            K.uniform(pv['all'][0])
        self.assertNotIn('all', K.pools(self.synthetic(), 'heater', {'heater': ['radiator']}))

    def test_alias_instance_needs_its_own_presence(self):
        with self.assertRaisesRegex(ValueError, 'alias_instance_without_source_presence'):
            K.pools(self.synthetic(with_presence=False), 'heater', {'heater': ['radiator']})

    def test_no_dictionary_entry_keeps_raw(self):
        pv = K.pools(self.synthetic(), 'heater', {}, offline=True)
        self.assertEqual(pv['all'][1], pv['raw'][1])
        self.assertFalse(any(v.startswith(('q:', 'fb:')) for v in pv))


class ReaderContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.caps, cls.ctx = K.setup()
        cls.c = next(c for c in cls.caps if c['canonical'] == CAPTURE)
        cls.geo, cls.cache, *_ = T.R.geometry(cls.c)
        cls.gt, gt_raw = T.R.gt_arrays(cls.c)

    def test_mixed_presence_collapses_in_cache_for(self):
        """Why P_all/P_cf are not priced: cache_for keeps the first entry's presence for the whole frame."""
        m = np.zeros(T.F.SHAPE, bool); m[100:200, 100:200] = True
        frames = [[dict(mask=m, score=.9, presence=.1), dict(mask=m, score=.8, presence=.9)]]+[[] for _ in range(31)]
        rec = T.F.cache_for('x', frames)['frames']['0']['phrases']['x']
        self.assertEqual(rec['presence'], .1)
        self.assertNotIn('presence', rec['instances'][1])
        with self.assertRaises(ValueError):
            K.uniform(frames)

    def test_raw_builder_equals_cache_detect(self):
        table = self.ctx[5]; detect = K.P.cache_detect(self.cache)
        for name in ['heater', 'table', 'trash can']:
            mine = K.pools(self.cache, name, table)['raw'][0]; ref = detect(name)
            for a, b in zip(mine, ref):
                self.assertEqual(len(a), len(b))
                for x, y in zip(a, b):
                    self.assertEqual((x['score'], x['presence']), (y['score'], y['presence']))
                    self.assertTrue(np.array_equal(x['mask'], y['mask']))

    def test_score_and_presence_survive_for_written_phrase_pools(self):
        table = self.ctx[5]; head = self.ctx[4]; producer = self.ctx[6]
        pv = K.pools(self.cache, 'heater', table)
        gt = dict(self.gt)
        for v in ('q:radiator', 'fb:radiator'):
            frames, sig, call = pv[v]
            o = K.ArmObjects(self.c, self.geo, head, gt); o.bind(call, 'heater', K.reader_frames(K.uniform(frames)))
            o.load(call)
            surv = K.survival(o, call)
            self.assertTrue(surv['passed'], surv); self.assertGreater(surv['proposals'], 0)
            props, _ = T.F.candidates.lift(T.F.cache_for(call, o.stage.raw[call]), call, self.geo, floor=.3, grids=o.stage.grids, phrase=call)
            for p in props:
                e = frames[p.frame-1][p.index]
                self.assertEqual((p.score, p.presence, p.joint), (e['score'], e['presence'], e['score']*e['presence']))
            self.assertEqual(o.ref['rows'], [])
            fresh = K.fresh_labels(producer, o, call, self.geo, dict(instances=self.gt['instances'], frame_indices=self.gt['frame_indices']))
            self.assertEqual(set(fresh), {a['candidate_id'] for a in o.data[call]['accepted']})
            o.unbind(call)
            self.assertEqual(o.c['gt_name_ids'].get(call), self.c['gt_name_ids'].get(call))
        presences = {e['presence'] for fr in pv['q:radiator'][0] for e in fr}
        self.assertGreater(len(presences), 1, 'the alias pool should carry several frame presences')


class Outputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = [json.loads(line) for line in (K.OUT/'PER_ITEM.jsonl').open()]
        cls.decision = json.loads((K.OUT/'DECISION.json').read_text())
        cls.a0 = json.loads((K.WORK/'A0_ROWS.json').read_text())['rows']['A0_deployed']

    def test_bars_frozen_and_recorded(self):
        self.assertEqual(K.sha(G.BARS), (K.WORK/'BARS.sha256').read_text().split()[0])
        self.assertEqual(self.decision['bars_file']['sha256'], K.sha(G.BARS))

    def test_parity_all_rows(self):
        p0 = [r for r in self.items if r['arm'] == 'P0']
        self.assertEqual(len(p0), 1037)
        self.assertEqual(sum(r['prediction'] == self.a0[r['row_id']]['prediction'] for r in p0), 1037)
        self.assertEqual(self.decision['parity']['verdict'], 'PASS')

    def test_parity_from_capture_files(self):
        n = 0
        for p in sorted(K.CAPS.glob('*.json.gz')):
            d = json.loads(gzip.decompress(p.read_bytes()))
            for it in d['items']:
                if all(k == d['names'][nm]['variants']['raw'] for nm, k in it['keys'].items()):
                    self.assertEqual(it['prediction'], self.a0[it['row_id']]['prediction']); n += 1
        self.assertEqual(n, 1037)

    def test_mixed_pools_never_priced(self):
        self.assertEqual({r['arm'] for r in self.items}, set(G.PRICED))
        self.assertFalse(any(v == 'all' for r in self.items for v in r['variants'].values()))
        self.assertIsNone(self.decision['arms']['P_cf']['mra'])

    def test_rows_use_own_fold_choice(self):
        for arm in G.SHIPPABLE:
            choice = self.decision['fold_choices'][arm]
            rows = [r for r in self.items if r['arm'] == arm]
            self.assertEqual(len(rows), 1037)
            for r in rows:
                for n, v in r['variants'].items():
                    self.assertEqual(v, choice[str(r['fold'])].get(n, 'raw'))

    def test_alias_rows_call_the_alias(self):
        for r in self.items:
            for n, v in r['variants'].items():
                want = v.split(':', 1)[1] if v.startswith('q:') else (n if v in ('raw', 'cap100') or v.startswith('fb:') else None)
                if want is not None:
                    self.assertEqual(r['calls'][n], want)

    def test_fold_choices_reproduce_without_held_fold(self):
        objs = json.loads((K.OUT/'OBJECTS.json').read_text())['objects']
        by = {}
        for o in objs:
            o['on_target'] = {v: o['keys'][k]['on_target'] for v, k in o['variants'].items()}
            by.setdefault(o['name'], []).append(o)
        for arm in G.SHIPPABLE:
            for k in range(5):
                for n, os_ in by.items():
                    fit = [o for o in os_ if o['fold'] != k]
                    self.assertEqual(G.choose(fit, G.candidates(arm, os_[0]['aliases']), None)[0],
                                     self.decision['fold_choices'][arm][str(k)].get(n, 'raw'))

    def test_folds_disjoint_by_room(self):
        rooms = {}
        for r in self.items:
            rooms.setdefault(r['room'], set()).add(r['fold'])
        self.assertEqual(len(rooms), 192)
        self.assertTrue(all(len(v) == 1 for v in rooms.values()))
        self.assertTrue(all(r['split'] == 'train' for r in self.items))


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    K.OUT.mkdir(exist_ok=True)
    (K.OUT/'TESTS.json').write_text(json.dumps(dict(ran=result.testsRun, failures=[str(t) for t, _ in result.failures],
                                                    errors=[(str(t), e[-800:]) for t, e in result.errors], passed=result.wasSuccessful(),
                                                    input_sha256={str(p): K.sha(p) for p in [K.HERE/'test_kit.py', K.HERE/'kit.py', K.HERE/'aggregate.py']}), indent=1)+'\n')
