#!/usr/bin/env python3
"""Exclusion test for R0: fails if any R0 capture or room appears in any training-stream or benchmark/dev authority.

Independent of census.py's resolver: every authority file is flattened to its full text (all keys and string
leaves, gz decoded) and searched for (a) each capture's native id and room id as substrings and (b) every alias
token of the capture. A mutation check proves the test fails on a known trained capture.
Run: python3 code/test_exclusion.py
"""
import gzip, hashlib, json, os, sys, unittest

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(L, 'code'))
import census  # noqa: E402  (alias families only)


def text_of(path):
    raw = gzip.open(path, 'rt').read() if path.endswith('.gz') else open(path).read()
    return raw


def needles(cap_key, rec):
    ds, native = cap_key.split('/', 1)
    out = {native}
    if ds == 'scannet':
        out.add(native[:9])  # room: every rescan
    for a in census.build_universe_aliases(ds, native):
        out.add(a.split('/', 1)[1])
    return out


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r0 = json.load(open(os.path.join(L, 'out', 'R0_SCENES.json')))
        c = json.load(open(os.path.join(L, 'out', 'CENSUS.json')))
        cls.auth = {}
        for name, d in c['inputs'].items():
            h = hashlib.sha256(open(d['path'], 'rb').read()).hexdigest()
            assert h == d['sha256'] == cls.r0['authorities'][name], name
            cls.auth[name] = text_of(d['path'])
        bigs = [os.path.join(L, 'in', 'd0v5_vqa_scenes_raw.txt')]
        for p in bigs:
            cls.auth[os.path.basename(p)] = open(p).read()

    def hits(self, cap_key, rec):
        found = []
        for n in needles(cap_key, rec):
            for name, txt in self.auth.items():
                if n in txt:
                    found.append((name, n))
        return found

    def test_no_r0_capture_in_any_authority(self):
        bad = {k: self.hits(k, v) for k, v in self.r0['captures'].items()}
        bad = {k: v for k, v in bad.items() if v}
        self.assertEqual(bad, {}, json.dumps(dict(list(bad.items())[:10]))[:3000])

    def test_mutation_trained_capture_is_caught(self):
        per = json.load(open(os.path.join(L, 'out', 'CENSUS_PER_CAPTURE.json')))
        for want in ('strict:division_A3_train', 'strict:kit07_frame_map_scenes', 'room:benchmark'):
            for ds in ('scannet', 'scannetpp'):
                k = next(k for k, v in per.items() if v['dataset'] == ds and want in v['reasons'])
                self.assertTrue(self.hits(k, per[k]), (want, k))

    def test_split_disjoint_and_dev_full(self):
        caps = self.r0['captures']
        dev = {c['room'] for c in caps.values() if c['r0_split'] == 'R0-dev'}
        rl = {c['room'] for c in caps.values() if c['r0_split'] == 'R0-rl'}
        self.assertFalse(dev & rl)
        self.assertEqual(len(dev), self.r0['dev_rooms'])
        self.assertTrue(all(c['gt_level'] == 'full' for c in caps.values() if c['r0_split'] == 'R0-dev'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
