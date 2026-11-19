"""Tiny round end to end on CPU: sample, score, select, one GRPO optimiser step, export, reload,
sample again from the reloaded export. The fixture's random model never answers right, so the
update plants rewards (draw parity); scoring itself is covered by test_reward and test_select."""
import copy
import tempfile
import unittest

import torch

from rltests.fixture import TREE, FixtureBackend, prompt, sampler_config
from rlkit import grpo, sampler, store as storemod
from rlkit.reward import score_group
from rlkit.round import build_items, export, grpo_update, reload, state_digest
from rlkit.select import select

if not TREE.rstrip('/').endswith('grpo_tree'):
    raise unittest.SkipTest('run with RLKIT_TREE=<lane>/grpo_tree (bash rltests/run_grpo.sh rltests.test_e2e)')

from student_pilot import grpo_loss  # noqa: E402


def with_grpo(model):
    model.recipe = {**model.recipe, 'weights': {**model.recipe['weights'], 'routing': 1.},
                    'grpo': dict(kl_beta=.04, temperature=1.0)}
    return model


class Round(unittest.TestCase):
    def test_round(self):
        backend = FixtureBackend()
        prompts = [prompt('p1'), prompt('p2')]
        raw = sampler_config(draws=4, temperature=1.0)
        with tempfile.TemporaryDirectory() as run, tempfile.TemporaryDirectory() as exp, \
                tempfile.TemporaryDirectory() as run2:
            sampler.run(raw, prompts, run, backend=backend)
            st = storemod.DrawStore(run, sampler.SamplerConfig(raw).identity)
            groups = st.groups(prompts, 4)
            real = {p['prompt_id']: score_group(p, groups[p['prompt_id']]) for p in prompts}
            out, report = select(prompts, groups)
            self.assertEqual(report['counts']['no_winner'], 2)  # random model: nothing right
            planted = {pid: [dict(s, r=float(s['draw'] % 2 == 0)) for s in rows] for pid, rows in real.items()}
            reserved = grpo.reserved_ids(backend.processor.tokenizer, backend.model)
            items = build_items(prompts, groups, planted, lambda p: backend.prompt_batch(p), reserved)
            self.assertEqual({i['stream'] for i in items} <= {'vqa', 'routing'}, True)
            self.assertTrue(any(i['stream'] == 'routing' for i in items))
            ref = copy.deepcopy(backend.model).eval()
            model = with_grpo(copy.deepcopy(backend.model))
            before = state_digest(model)
            opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3, weight_decay=0.)
            stats = grpo_update(model, ref, opt, items, 1.0)
            self.assertTrue(stats['stepped'])
            for m in stats['per_row']:
                self.assertAlmostEqual(m['ratio'], 1.0, places=3)  # the export that sampled is the policy at step 0
            self.assertNotEqual(state_digest(model), before)
            # direction: advantage-weighted log prob of the sampled tokens rises
            model.eval()
            gain = 0.
            for i in items:
                b = i['batch']
                new = grpo_loss.sequence_logprobs(model, b, i['stream'], 1.0)
                m = b['aux_pg_mask']
                gain += float(i['advantage'] * (new[m] - b['aux_old_logp'][m]).sum())
            self.assertGreater(gain, 0.)
            digest = export(model, exp, dict(round='r1', parent='fixture'))
            factory = lambda: with_grpo(FixtureBackend().model)  # noqa: E731
            again, meta = reload(factory, exp)
            self.assertEqual(meta['state_sha256'], digest)
            # sample round 2 from the reloaded export; its log probs match the export's forward
            backend2 = FixtureBackend()
            backend2.model = again.eval()
            sampler.run(raw, prompts, run2, backend=backend2)
            g2 = storemod.DrawStore(run2, sampler.SamplerConfig(raw).identity).groups(prompts, 4)
            rec = g2['p1'][0]
            b = grpo.attach(backend2.prompt_batch(None), rec, 0., reserved)
            lp = grpo_loss.sequence_logprobs(again, b, 'vqa', 1.0)
            torch.testing.assert_close(lp[b['aux_pg_mask']], b['aux_old_logp'][b['aux_pg_mask']], atol=2e-4, rtol=0)


if __name__ == '__main__':
    unittest.main()
