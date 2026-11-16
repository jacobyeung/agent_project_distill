"""GRPO loss (tree copy grpo_tree) and the kit's row bridge, on the tree's tiny native model. CPU only."""
import copy
import os
import tempfile
import unittest

import torch

from rltests.fixture import TREE, FixtureBackend, prompt, sampler_config
from rlkit import grpo, sampler, store as storemod

if not TREE.rstrip('/').endswith('grpo_tree'):
    raise unittest.SkipTest('run with RLKIT_TREE=<lane>/grpo_tree (bash rltests/run_grpo.sh)')

from student_pilot import grpo_loss  # noqa: E402

TEMP = 1.0


def rollouts(tmp, backend, draws=4):
    prompts = [prompt('p1'), prompt('p2')]
    raw = sampler_config(draws=draws, temperature=TEMP)
    sampler.run(raw, prompts, tmp, backend=backend)
    st = storemod.DrawStore(tmp, sampler.SamplerConfig(raw).identity)
    return st.groups(prompts, draws)


def with_grpo(model, **grpo_settings):
    """Production recipes weigh routing 1 (kit b02e4385); the tiny fixture's recipe weighs it 0."""
    model.recipe = {**model.recipe, 'weights': {**model.recipe['weights'], 'routing': 1.}, 'grpo': grpo_settings}
    return model


def pg_batch(backend, rec, adv):
    return grpo.attach(backend.prompt_batch(None), rec, adv,
                       grpo.reserved_ids(backend.processor.tokenizer, backend.model))


class Advantages(unittest.TestCase):
    def test_group_normalisation(self):
        torch.testing.assert_close(grpo_loss.group_advantages([1., 0., 0., 1.]),
                                   torch.tensor([1., -1., -1., 1.], dtype=torch.float64), atol=1e-5, rtol=0)
        self.assertEqual(grpo_loss.group_advantages([.7] * 4).tolist(), [0.] * 4)
        self.assertEqual(grpo_loss.group_advantages([1., 0.], scale_std=False).tolist(), [.5, -.5])
        for r in ([1., .3, 0., .9, .9], [2., 0., 0., 0.]):
            self.assertEqual(grpo.advantages(r), grpo_loss.group_advantages(r).tolist())

    def test_tied_group_dropped(self):
        scored = [dict(draw=d, r=.5) for d in range(3)]
        self.assertEqual(grpo.group_rows(scored, [dict(draw=d) for d in range(3)]), [])


class TokenTerms(unittest.TestCase):
    def test_value_at_ratio_one_and_kl(self):
        s = grpo_loss.settings({'grpo': dict(kl_beta=.1)})
        new = torch.tensor([-1., -2.])
        tok, ratio, kl = grpo_loss.token_terms(new, new.clone(), new - .5, torch.tensor([2., 2.]), s)
        k3 = torch.exp(torch.tensor(-.5)) + .5 - 1
        torch.testing.assert_close(tok, -2. + .1 * k3.expand(2))
        self.assertTrue((kl >= 0).all())

    def test_clip_stops_gradient(self):
        s = grpo_loss.settings({})
        new = torch.tensor([0.], requires_grad=True)
        tok, _, _ = grpo_loss.token_terms(new, torch.tensor([-1.]), new.detach(), torch.tensor([1.]), s)
        (tok.sum() - s['kl_beta'] * 0).backward()
        # ratio e > 1.2 with a positive advantage: the clipped branch is the minimum, so only KL moves it
        torch.testing.assert_close(new.grad, torch.zeros(1), atol=1e-6, rtol=0)

    def test_bad_settings_refused(self):
        with self.assertRaises(ValueError):
            grpo_loss.settings({'grpo': dict(beta=1.)})
        with self.assertRaises(ValueError):
            grpo_loss.settings({'grpo': dict(norm='batch')})


class Rows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = FixtureBackend()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.groups = rollouts(cls.tmp.name, cls.backend)
        cls.head = cls.groups['p1'][2]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_masks_forced_and_response_tokens(self):
        rec = self.head
        self.assertIn('r', rec['kinds'])
        self.assertIn('f', rec['kinds'])
        b = pg_batch(self.backend, rec, 1.)
        P = b['input_ids'].shape[1] - len(rec['tokens'])
        for i, k in enumerate(rec['kinds']):
            self.assertEqual(bool(b['aux_pg_mask'][0, P + i]), k == 's', (i, k))
            self.assertEqual(int(b['labels'][0, P + i]) == -100, k == 'r', (i, k))
        self.assertFalse(b['aux_pg_mask'][0, :P].any())
        self.assertTrue((b['labels'][0, :P] == -100).all())

    def test_logprob_parity_with_the_sampler(self):
        model = self.backend.model
        model.eval()
        checked = False
        for grp in self.groups.values():
            for rec in grp:
                b = pg_batch(self.backend, rec, 0.)
                lp = grpo_loss.sequence_logprobs(model, b, 'routing', TEMP)
                m = b['aux_pg_mask']
                if m.any():
                    torch.testing.assert_close(lp[m], b['aux_old_logp'][m], atol=2e-4, rtol=0)
                    checked = True
        self.assertTrue(checked)
        # the unmasked softmax is not the sampling policy: without the reserved mask parity breaks
        b = pg_batch(self.backend, self.groups['p1'][0], 0.)
        lp = grpo_loss.sequence_logprobs(model, b, 'routing', TEMP, reserved=[])
        self.assertGreater(float((lp[b['aux_pg_mask']] - b['aux_old_logp'][b['aux_pg_mask']]).abs().max()), 1e-2)

    def test_forward_hook_uses_pg_loss(self):
        model = with_grpo(copy.deepcopy(self.backend.model), kl_beta=0.)
        rec = next(r for g in self.groups.values() for r in g if 's' in r['kinds'])
        b = pg_batch(self.backend, rec, 1.5)
        model.eval()
        b['aux_old_logp'] = grpo_loss.sequence_logprobs(model, b, 'routing', TEMP)
        b['aux_ref_logp'] = b['aux_old_logp'].clone()
        out = model(b, stream='routing')
        torch.testing.assert_close(out['loss'], torch.tensor(-1.5), atol=1e-5, rtol=0)
        # ratio 1, beta 0, one row: the loss is minus the advantage
        torch.testing.assert_close(out['components']['routing'], torch.tensor(-1.5), atol=1e-5, rtol=0)
        self.assertEqual(out['metrics']['grpo']['pg_tokens'], rec['kinds'].count('s'))
        out['loss'].backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.parameters()))
        # forced and response positions carry no PG term: changing their old/ref log probs changes nothing
        b2 = dict(b)
        off = ~b['aux_pg_mask']
        b2['aux_old_logp'] = torch.where(off, torch.full_like(b['aux_old_logp'], -7.), b['aux_old_logp'])
        b2['aux_ref_logp'] = torch.where(off, torch.full_like(b['aux_ref_logp'], -9.), b['aux_ref_logp'])
        with torch.no_grad():
            torch.testing.assert_close(model(b2, stream='routing')['components']['routing'],
                                       out['components']['routing'])
        # without the fields the routing stream keeps its CE
        plain = {k: v for k, v in b.items() if k not in grpo_loss.FIELDS}
        with torch.no_grad():
            self.assertGreater(float(model(plain, stream='routing')['components']['routing']), 0.)

    def test_mask_outside_labels_refused(self):
        b = pg_batch(self.backend, self.head, 1.)
        b['aux_pg_mask'][0, 3] = True
        with self.assertRaises(ValueError):
            self.backend.model(b, stream='routing')
        partial = dict(b)
        partial.pop('aux_ref_logp')
        with self.assertRaises(ValueError):
            self.backend.model(partial, stream='routing')

    def test_exact_resume(self):
        rows = [r for g in self.groups.values() for r in g if 's' in r['kinds']][:2]
        batches = [pg_batch(self.backend, r, a) for r, a in zip(rows, (1., -1.))]
        ref = copy.deepcopy(self.backend.model).eval()
        for b in batches:
            b['aux_ref_logp'] = grpo_loss.sequence_logprobs(ref, b, 'routing', TEMP)

        def fresh():
            m = with_grpo(copy.deepcopy(ref), kl_beta=.04)
            m.train()
            return m, torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=1e-3, weight_decay=0.)

        def step(m, opt, b):
            torch.manual_seed(5)
            opt.zero_grad(set_to_none=True)
            out = m(b, stream='routing')
            self.assertGreater(out['metrics']['grpo']['pg_tokens'], 0)
            out['loss'].backward()
            self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in m.parameters()))
            opt.step()

        a, oa = fresh()
        for b in batches:
            step(a, oa, b)
        c, oc = fresh()
        step(c, oc, batches[0])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'ck.pt')
            torch.save(dict(model=c.state_dict(), opt=oc.state_dict()), path)
            d, od = fresh()
            ck = torch.load(path, weights_only=False)
            d.load_state_dict(ck['model'])
            od.load_state_dict(ck['opt'])
        step(d, od, batches[1])
        changed = 0
        for (n, pa), pd, p0 in zip(a.named_parameters(), d.parameters(), ref.parameters()):
            self.assertTrue(torch.equal(pa, pd), n)
            changed += int(not torch.equal(pa, p0))
        self.assertGreater(changed, 0)


if __name__ == '__main__':
    unittest.main()
