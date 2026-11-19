import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rltests.fixture import FixtureBackend, prompt, sampler_config, HEAD_TEXT
from rlkit import sampler, store as storemod
from rlkit.forcing import draw_path


def run(tmp, backend, prompts, **kw):
    return sampler.run(sampler_config(**kw.pop('sampling', {})), prompts, tmp, backend=backend, **kw)


def committed(tmp, prompts, draws=4):
    cfg = sampler.SamplerConfig(sampler_config())
    st = storemod.DrawStore(tmp, cfg.identity)
    return st.groups(prompts, draws)


class Paths(unittest.TestCase):
    def test_half_forced_alternating(self):
        self.assertEqual([draw_path(d, 8) for d in range(8)], ['free'] * 4 + ['head', 'direct'] * 2)
        self.assertEqual([draw_path(d, 8, has_head=False) for d in range(8)], ['free'] * 4 + ['free', 'direct'] * 2)


class Sampler(unittest.TestCase):
    def setUp(self):
        self.prompts = [prompt('p1'), prompt('p2'), prompt('p3', qtype='counting')]

    def test_forced_span_then_sampled_and_response_masked(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(tmp, FixtureBackend(), self.prompts)
            g = committed(tmp, self.prompts)
            head = g['p1'][2]
            self.assertEqual(head['path'], 'head')
            self.assertEqual(head['tokens'][:2], [40, 41])
            self.assertTrue(head['kinds'].startswith('ffr'))
            self.assertEqual(head['calls'][0]['call'], HEAD_TEXT)
            self.assertTrue(head['calls'][0]['response'].startswith('P1: cam2'))
            n_resp = head['calls'][0]['forced_tokens']
            self.assertEqual(head['kinds'][2:2 + n_resp], 'r' * n_resp)
            for i, k in enumerate(head['kinds']):
                self.assertEqual(head['logp_raw'][i] is None, k == 'r')
            direct = g['p1'][3]
            self.assertEqual(direct['path'], 'direct')
            self.assertEqual(direct['tokens'][0], 42)
            # counting has no head form: its head slot samples free
            self.assertEqual([r['path'] for r in g['p3']], ['free', 'free', 'free', 'direct'])
            for grp in g.values():
                for r in grp:
                    self.assertLessEqual(r['kinds'].count('s'), 10)
                    self.assertEqual(r['own_tokens'] + r['response_tokens'], len(r['tokens']))
                    self.assertEqual(len(r['prompt_ids_sha256']), 64)
                    self.assertEqual(r['response_sources']['pose_source'], 'own')
                    self.assertFalse(r['response_sources']['donor'])

    def test_batched_equals_sequential_and_seeds_are_per_draw(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            run(a, FixtureBackend(batchable=True), self.prompts)
            run(b, FixtureBackend(batchable=False), self.prompts)
            ga, gb = committed(a, self.prompts), committed(b, self.prompts)
            for pid in ga:
                self.assertEqual([r['tokens'] for r in ga[pid]], [r['tokens'] for r in gb[pid]], pid)
            seeds = {r['seed'] for grp in ga.values() for r in grp}
            self.assertEqual(len(seeds), 12)

    def test_interrupt_and_resume_repeat_only_missing_draws(self):
        with tempfile.TemporaryDirectory() as ref, tempfile.TemporaryDirectory() as tmp:
            run(ref, FixtureBackend(batchable=False), self.prompts)
            original = storemod.DrawStore.commit
            count = [0]

            def flaky(self_, record):
                if count[0] == 5:
                    raise KeyboardInterrupt('simulated kill')
                count[0] += 1
                return original(self_, record)
            with mock.patch.object(storemod.DrawStore, 'commit', flaky):
                with self.assertRaises(KeyboardInterrupt):
                    run(tmp, FixtureBackend(batchable=False), self.prompts)
            failed = list(Path(tmp).glob('FAILED_*'))
            self.assertEqual(failed, [])  # KeyboardInterrupt is not an Exception: no FAILED file, plain stop
            before = {p: p.read_bytes() for p in Path(tmp).glob('draws/*/*/*.json')}
            self.assertEqual(len(before), 5)
            backend = FixtureBackend(batchable=False)
            run(tmp, backend, self.prompts)
            self.assertEqual(backend.calls, 12 - 5)
            for p, data in before.items():
                self.assertEqual(p.read_bytes(), data)  # committed bytes untouched
            gr, gt = committed(ref, self.prompts), committed(tmp, self.prompts)
            for pid in gr:
                self.assertEqual([r['tokens'] for r in gr[pid]], [r['tokens'] for r in gt[pid]])

    def test_changed_config_and_corrupt_commit_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(tmp, FixtureBackend(), self.prompts[:1])
            with self.assertRaises(storemod.StoreError):
                run(tmp, FixtureBackend(), self.prompts[:1], sampling=dict(temperature=0.5))
            f = sorted(Path(tmp).glob('draws/*/*/d000.json'))[0]
            env = json.loads(f.read_text())
            env['record']['tokens'][0] = 7
            f.write_text(json.dumps(env))
            with self.assertRaises(storemod.StoreError):
                committed(tmp, self.prompts[:1])

    def test_benchmark_and_excluded_prompts_refused(self):
        with self.assertRaises(sampler.PromptError):
            sampler.check_prompts([prompt('x', source='ReVSI_official999')], {})
        with self.assertRaises(sampler.PromptError):
            sampler.check_prompts([prompt('x')], {'scene_keys': ['scene_x']})


if __name__ == '__main__':
    unittest.main()
