"""CPU tests for the official ReVSI 999 at its 32- and 64-frame tiers."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'evaluator'), str(ROOT/'local')]
import subprocess
from unittest.mock import patch
import data
from data import tasks_for
from evalpath.official import build_prompt_context
from media import identity
from merge import merge
from cells import frame_count
from scoring import score_item, benchmark_summary
import bind_vl

INP = ROOT/'inputs'


def pin(p):
    return dict(path=str(p), sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())


META = Path('/scratch/jjyeung/orch_cd/evalx/work/revsi_meta')
ARROW = Path('/scratch/jjyeung/envs/planner_local_v1/bin/python')
CHANGED_64 = ['28', '213', '242', '253', '392', '475', '650', '700', '712', '834', '894']
VID = Path(tempfile.mkdtemp())


def manifest(tier):
    rows = json.loads((INP/f'revsi999_rows_t{tier}.json').read_text())
    files = {s: dict(sha256=hashlib.sha256(s.encode()).hexdigest(), bytes=1) for s in {r['scene'] for r in rows}}
    p = VID/f'videos_t{tier}.json'; p.write_text(json.dumps(dict(tier=tier, files=files)))
    return p


MANIFESTS = {t: manifest(t) for t in (32, 64)}
PINS = patch.dict(data.REVSI999_VIDEOS, {t: pin(p)['sha256'] for t, p in MANIFESTS.items()})


def setUpModule():
    PINS.start()


def tearDownModule():
    PINS.stop()


def spec(tier, revsi_set='official999', rows=None):
    rows = rows or (INP/f'revsi999_rows_t{tier}.json' if revsi_set == 'official999' else INP/'revsi_rows.json')
    members = INP/('revsi999_membership.json' if revsi_set == 'official999' else 'revsi_membership.json')
    s = dict(benchmark='revsi', rows=pin(rows), membership=pin(members), indices=pin(INP/'revsi_indices.json'))
    if revsi_set == 'official999':
        s.update(set=revsi_set, tier=tier, videos=pin(MANIFESTS[tier]))
    return s


ROOTS = dict(revsi_video_root='/nonexistent/revsi')


class Revsi999(unittest.TestCase):
    def test_01_rows_pins_and_cap452_identity(self):
        prov = json.loads((INP/'REVSI999_PROVENANCE.json').read_text())
        for tier in (32, 64):
            self.assertEqual(pin(INP/f'revsi999_rows_t{tier}.json')['sha256'], data.REVSI999_ROWS[tier])
            self.assertEqual(prov['rows'][str(tier)]['sha256'], data.REVSI999_ROWS[tier])
        self.assertEqual(pin(INP/'revsi999_membership.json')['sha256'], data.REVSI999_MEMBERSHIP)
        old = {r['example_id']: r for r in json.loads((INP/'revsi_rows.json').read_text())}
        t32 = {r['example_id']: r for r in json.loads((INP/'revsi999_rows_t32.json').read_text())}
        t64 = {r['example_id']: r for r in json.loads((INP/'revsi999_rows_t64.json').read_text())}
        self.assertEqual((len(t32), len(t64)), (999, 999))
        self.assertEqual(set(t32), set(t64))
        self.assertTrue(set(old) <= set(t32))
        for k, r in old.items():
            for f, v in r.items():
                if f != 'provenance':
                    self.assertEqual(t32[k][f], v, (k, f))
        self.assertEqual(sum(r['cap452'] for r in t32.values()), 452)
        self.assertTrue(all(r['num_frames'] == '64' for r in t64.values()))
        self.assertTrue(all(t64[k]['question'] == t32[k]['question'] for k in t32))

    def test_02_tasks_for_tiers(self):
        for tier in (32, 64):
            ts = tasks_for(spec(tier), ROOTS)
            self.assertEqual(len(ts), 999)
            self.assertTrue(all(len(t['source_frame_indices']) == tier and t['revsi_tier'] == tier for t in ts))
            self.assertTrue(all(t['sidecar_verified'] and t['revsi_set'] == 'official999' for t in ts))
            self.assertTrue(all(t['video_path'] == f'/nonexistent/revsi/{t["scene"]}.mp4' for t in ts))
            self.assertTrue(all(t['video_sha256'] == hashlib.sha256(t['scene'].encode()).hexdigest() for t in ts))
        cap = tasks_for(spec(32, 'cap452'), ROOTS)
        self.assertEqual(len(cap), 452)
        self.assertFalse(any(t['sidecar_verified'] for t in cap))
        a = {t['example_id']: t for t in tasks_for(spec(32), ROOTS)}
        for t in cap:
            self.assertEqual(a[t['example_id']]['source_frame_indices'], t['source_frame_indices'])

    def test_03_refusals(self):
        with self.assertRaises(ValueError):  # the 64-tier rows under the 32 tier
            tasks_for(spec(32, rows=INP/'revsi999_rows_t64.json'), ROOTS)
        with self.assertRaises(ValueError):  # cap452 rows under the official999 set
            tasks_for(spec(32, rows=INP/'revsi_rows.json'), ROOTS)
        s = spec(32); s.pop('videos')
        with self.assertRaises(ValueError):  # no video manifest
            tasks_for(s, ROOTS)
        s = spec(32); s['videos'] = pin(MANIFESTS[64])
        with self.assertRaises(ValueError):  # the other tier's manifest
            tasks_for(s, ROOTS)
        s = spec(64); s['tier'] = 16
        with self.assertRaises(ValueError):
            tasks_for(s, ROOTS)
        s = spec(32); s['sidecar'] = dict(path='/x', sha256='66e0175d')
        with self.assertRaises(ValueError):
            tasks_for(s, ROOTS)
        s = spec(32, 'cap452'); s['tier'] = 64
        with self.assertRaises(ValueError):
            tasks_for(s, ROOTS)

    def test_04_frame_count(self):
        self.assertEqual(frame_count(dict(frames=64, layout='spread', benchmarks=['revsi'])), 64)
        for bad in (dict(frames=64, layout='duplicate', benchmarks=['revsi']),
                    dict(frames=64, layout='spread', benchmarks=['revsi', 'vsi500']),
                    dict(frames=64, layout='spread', benchmarks=['revsi'], frame_set='nested'),
                    dict(frames=96, layout='spread', benchmarks=['revsi'])):
            with self.assertRaises(ValueError):
                frame_count(bad)
        self.assertEqual(frame_count(dict(frames=64, layout='spread', benchmarks=['vsi500'], frame_set='nested')), 64)

    def test_05_decode_tier64(self):
        import av
        from media import decode
        d = Path(tempfile.mkdtemp())
        def video(n):
            p = d/f'{n}.mp4'
            with av.open(str(p), 'w') as c:
                st = c.add_stream('mpeg4', rate=1); st.width = 32; st.height = 32; st.pix_fmt = 'yuv420p'
                for i in range(n):
                    for pk in st.encode(av.VideoFrame.from_ndarray(np.full((32, 32, 3), i*3, dtype=np.uint8), format='rgb24')):
                        c.mux(pk)
                for pk in st.encode():
                    c.mux(pk)
            return p
        source = [k*639//63 for k in range(64)]
        task = dict(benchmark='revsi', video_path=str(video(64)), source_frame_indices=source, revsi_tier=64)
        pixels, audit = decode(task, 'spread', frames=64)
        self.assertEqual(len(pixels), 64)
        self.assertEqual(audit['metadata']['frames_indices'], source)
        self.assertEqual(audit['metadata']['total_num_frames'], 640)
        self.assertEqual(audit['metadata']['fps'], 10.)
        with self.assertRaises(ValueError):  # a 32-frame video under the 64 tier
            decode({**task, 'video_path': str(video(32))}, 'spread', frames=64)
        with self.assertRaises(ValueError):  # the 64 tier read at 32 frames
            decode(task, 'spread')

    def test_06_metric_on_999(self):
        for tier in (32, 64):
            rows = tasks_for(spec(tier), ROOTS)
            recs = [{**t, **score_item(dict(t,thinking=True), 'r\n</think>\n'+str(t['ground_truth']), 5), 'status': 'complete'} for t in rows]
            s = benchmark_summary(recs, rows, True)
            self.assertAlmostEqual(s['overall_score'], 1.)
            self.assertEqual(len(s['per_category']), 7)
            self.assertEqual(s['visible_32']['count'], 350)

    def test_07_bind_round_trip(self):
        d = Path(tempfile.mkdtemp())
        def run(cells, *extra):
            (d/'c.json').write_text(json.dumps(cells))
            a = bind_vl.parser().parse_args(['--preset', 'custom', '--cells', str(d/'c.json'), '--models',
                                             str(INP/'MODELS.example.json'), '--gpu-cap', '8', '--build-only', *extra])
            return bind_vl.bind(a)
        for t in (32, 64):
            if not (INP/f'revsi999_videos_t{t}.json').exists():
                self.skipTest('per-tier video manifests not built yet')
        c64 = [dict(model='base', layout='spread', benchmarks=['revsi'], frames=64)]
        r = run(c64, '--revsi-set', 'official999', '--revsi-tier', '64')
        s = next(x for x in r['datasets'] if x['benchmark'] == 'revsi')
        self.assertEqual((s['set'], s['tier'], s['rows']['sha256']), ('official999', 64, data.REVSI999_ROWS[64]))
        with tarfile.open(ROOT/'kit/k/1.tar') as tf:
            for m in tf.getmembers():
                (d/m.name).write_bytes(tf.extractfile(m).read())
        import importlib.util
        boot = importlib.util.spec_from_file_location('boot1', ROOT/'kit/b/1.py'); boot1 = importlib.util.module_from_spec(boot)
        boot.loader.exec_module(boot1)
        req = dict(datasets=[s]); boot1.resolve_inputs(req, d)  # the shipped bootstrap must resolve every embedded pin
        self.assertTrue(all(not s[k]['path'].startswith('$Q/') for k in ('rows', 'membership', 'indices', 'videos')))
        with patch.dict(data.REVSI999_VIDEOS, {64: s['videos']['sha256']}):
            self.assertEqual(len(tasks_for(s, r['roots'])), 999)
        r = run([dict(model='base', layout='spread', benchmarks=['revsi'])], '--revsi-set', 'official999')
        self.assertEqual(next(x for x in r['datasets'] if x['benchmark'] == 'revsi')['tier'], 32)
        for cells, extra in ((c64, ['--revsi-tier', '64']),
                             (c64, ['--revsi-set', 'official999']),
                             ([dict(model='base', layout='spread', benchmarks=['revsi'])], ['--revsi-set', 'official999', '--revsi-tier', '64'])):
            with self.assertRaises(ValueError):
                run(cells, *extra)

    def test_08_independent_parquet_and_tiny_set(self):
        if not ARROW.exists() or not (META/'32_frame.parquet').exists():
            self.skipTest('pyarrow interpreter or local parquet copies missing')
        prov = json.loads((INP/'REVSI999_PROVENANCE.json').read_text())
        for t in (32, 64):
            self.assertEqual(pin(META/f'{t}_frame.parquet')['sha256'], prov['parquets'][str(t)]['sha256'])
        code = """
import json, sys, pyarrow.parquet as pq
meta, inp = sys.argv[1], sys.argv[2]
tiny = {int(l) for l in open(meta+'/tiny_set_question_ids.txt') if l.strip()}
out = {}
for t in (32, 64):
    table = {int(r['id']): r for r in pq.read_table(meta+f'/{t}_frame.parquet').to_pylist()}
    out[t] = {str(i): [str(table[i]['ground_truth']), table[i]['question'], table[i]['question_type'], str(table[i]['scene_id'])] for i in table}
ids = sorted(tiny & {int(k) for k in out[32]})
print(json.dumps(dict(ids=ids, rows=out)))
"""
        got = json.loads(subprocess.run([str(ARROW), '-c', code, str(META), str(INP)], capture_output=True, text=True, check=True).stdout)
        members = [m['qid'] for m in json.loads((INP/'revsi999_membership.json').read_text())]
        self.assertEqual(sorted(map(int, members)), got['ids'])
        self.assertEqual(len(got['ids']), 999)
        for t in (32, 64):
            for r in json.loads((INP/f'revsi999_rows_t{t}.json').read_text()):
                self.assertEqual([r['ground_truth'], r['question'], r['question_type'], r['scene']], got['rows'][str(t)][r['example_id']])

    def test_09_eleven_changed_answers(self):
        a = {r['example_id']: r for r in json.loads((INP/'revsi999_rows_t32.json').read_text())}
        b = {r['example_id']: r for r in json.loads((INP/'revsi999_rows_t64.json').read_text())}
        self.assertEqual(sorted((k for k in a if a[k]['ground_truth'] != b[k]['ground_truth']), key=int), CHANGED_64)
        t64 = {t['example_id']: t for t in tasks_for(spec(64), ROOTS)}
        for k in CHANGED_64:
            t = t64[k]
            self.assertEqual(score_item(dict(t,thinking=True), '</think>\n'+b[k]['ground_truth'], 5)['score'], 1.)
            self.assertLess(score_item(dict(t,thinking=True), '</think>\n'+a[k]['ground_truth'], 5)['score'], 1.)

    def test_10_leakage(self):
        for t in tasks_for(spec(64), ROOTS)[:50]:
            self.assertEqual(build_prompt_context(dict(t), 'ours'), build_prompt_context({**t, 'ground_truth': 'SENTINEL'}, 'ours'))
            self.assertNotIn('ground_truth', identity(t, 'spread', 64))
            self.assertEqual(identity(t, 'spread', 64), identity({**t, 'ground_truth': 'SENTINEL'}, 'spread', 64))

    def test_11_non_perfect_metric(self):
        rows = tasks_for(spec(32), ROOTS)
        recs = []
        for i, t in enumerate(rows):
            ans = str(t['ground_truth']) if i % 2 == 0 else 'Z'
            recs.append({**t, **score_item(dict(t,thinking=True), '</think>\n'+ans, 5), 'status': 'complete'})
        s = benchmark_summary(recs, rows, True)
        self.assertGreater(s['overall_score'], 0.2)
        self.assertLess(s['overall_score'], 0.8)
        for q, v in s['per_type'].items():
            want = [r['score'] for r in recs if r['question_type'] == q]
            self.assertAlmostEqual(v['score'], sum(want)/len(want))
        self.assertEqual(sum(r['score'] for r in recs[1::2]), 0.)

    def merge_case(self, cell_tier, journal):
        d = Path(tempfile.mkdtemp())
        cell = dict(model='base', layout='spread', benchmarks=['revsi'], **({'frames': 64} if cell_tier == 64 else {}))
        cfg = dict(cells=[cell], output=str(d), datasets=[spec(cell_tier)], roots=ROOTS, binding='b', gpus=1, smoke_items=0)
        from evalpath.items import digest
        binding = digest({'request': 'b', 'cell': 0})
        (d/'0').mkdir()
        with (d/'0'/'g0.jsonl').open('w') as f:
            for r in journal:
                f.write(json.dumps({**r, 'binding': binding})+'\n')
        return merge(cfg, 0, 'a')

    def record(self, t, answer, frames):
        r = {k: v for k, v in t.items() if k not in ('text', 'student_input')}
        r.update(score_item(dict(t,thinking=True), '</think>\n'+answer, 5))
        r.update(key='revsi:'+t['example_id'], status='complete', raw_generation='</think>\n'+answer, frames=frames,
                 finish_reason='stop', media=dict(metadata=dict(frames_indices=t['source_frame_indices'])), at_4096={})
        return r

    def test_12_merge_admission(self):
        t32 = {t['example_id']: t for t in tasks_for(spec(32), ROOTS)}
        t64 = {t['example_id']: t for t in tasks_for(spec(64), ROOTS)}
        k = CHANGED_64[0]
        with self.assertRaises(ValueError):  # a 64-tier answer in a 32-tier cell
            self.merge_case(32, [self.record(t64[k], t64[k]['ground_truth'], 32)])
        with self.assertRaises(ValueError):  # a 64-tier record carrying 32-tier ground truth
            self.merge_case(64, [{**self.record(t64[k], t32[k]['ground_truth'], 64), 'ground_truth': t32[k]['ground_truth']}])
        bad = self.record(t32[k], t32[k]['ground_truth'], 32); bad['score'] = 0.
        with self.assertRaises(ValueError):  # a journal score that disagrees with the pinned rescore
            self.merge_case(32, [bad])
        with self.assertRaises(ValueError):  # frames of the other tier
            self.merge_case(32, [{**self.record(t32[k], '1', 32), 'media': dict(metadata=dict(frames_indices=t64[k]['source_frame_indices']))}])
        good = self.record(t32[k], t32[k]['ground_truth'], 32)
        res = self.merge_case(32, [good, good, self.record(t32['14'], '0', 32)])
        s = res['benchmarks']['revsi']
        self.assertEqual((s['completed'], s['missing'], s['numbers_status']), (2, 997, 'do not count'))
        self.assertEqual(s['per_type'][t32[k]['question_type']]['count'], 1 + (t32['14']['question_type'] == t32[k]['question_type']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
