"""GRPO rows through the trainer's own stream path: rlkit.grpo.to_row -> sqlite stream database ->
carrier_c1_run.Rows.get / fetch (check_row) -> CarrierC1 forward. CPU, tiny model."""
import copy
import os
import tempfile
import unittest
from unittest import mock

import torch

from rltests.fixture import TREE, FixtureBackend, prompt, sampler_config
from rlkit import grpo, sampler, store as storemod

if not TREE.rstrip('/').endswith('grpo_tree'):
    raise unittest.SkipTest('run with RLKIT_TREE=<lane>/grpo_tree')

from student_pilot import carrier_c1_run as run, grpo_loss, grpo_rows  # noqa: E402


class StreamRows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        be = cls.be = FixtureBackend()
        prompts = cls.prompts = [prompt('p1'), prompt('p2')]
        raw = sampler_config(draws=4, temperature=1.0)
        sampler.run(raw, prompts, os.path.join(cls.tmp.name, 'run'), backend=be)
        groups = storemod.DrawStore(os.path.join(cls.tmp.name, 'run'), sampler.SamplerConfig(raw).identity).groups(prompts, 4)
        cls.reserved = grpo.reserved_ids(be.processor.tokenizer, be.model)
        ref = copy.deepcopy(be.model).eval()
        rows = {'vqa': [], 'routing': []}
        for p in prompts:
            for rec, adv in zip(groups[p['prompt_id']], grpo.advantages([1., 0., 1., 0.])):
                if 's' not in rec['kinds']:
                    continue
                b = grpo.attach(be.prompt_batch(None), rec, adv, cls.reserved)
                lp = grpo_loss.sequence_logprobs(ref, b, 'vqa', 1.0)[0, -len(rec['tokens']):].tolist()
                row = grpo.to_row(p, rec, adv, lp, cls.reserved)
                rows[row['stream']].append(row)
        cls.rows = rows
        cls.dbs = {}
        for stream, rs in rows.items():
            path = os.path.join(cls.tmp.name, f'{stream}.sqlite')
            grpo.write_stream_db(path, rs)
            cls.dbs[stream] = path

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def trainer_rows(self):
        r = run.Rows.__new__(run.Rows)
        r.r2_admission, r.indices, r.mixes, r.mdg, r.validation = None, {}, {}, None, None
        r.connections = {k: run.connect(dict(path=v)) for k, v in self.dbs.items()}
        r.counts = {k: len(self.rows[k]) for k in self.dbs}
        r.processor, r.placement, r.mode, r.layout, r.gap = self.be.processor, None, 'final', 'duplicate', None
        r.geometry_online, r.tool_flag, r.receipt_pointing_weights = None, None, None
        return r

    def model(self):
        m = copy.deepcopy(self.be.model)
        m.recipe = {**m.recipe, 'weights': {**m.recipe['weights'], 'routing': 1.}, 'grpo': dict(kl_beta=.04, temperature=1.0)}
        return m

    def test_trainer_path_equals_kit_path(self):
        self.assertTrue(self.rows['vqa'] and self.rows['routing'])
        trows, model = self.trainer_rows(), self.model().eval()
        with mock.patch.object(grpo_rows, 'prompt_batch', lambda *a, **k: self.be.prompt_batch(None)):
            for stream in ('vqa', 'routing'):
                for i, row in enumerate(self.rows[stream]):
                    batch, targets, audit = run.fetch(trows, stream, i, model)
                    self.assertEqual(audit['index'], i)
                    kit = grpo.attach(self.be.prompt_batch(None), dict(row, logp_tempered=[v if v is not None else 0.
                                      for v in row['old_logp']]), row['advantage'], self.reserved)
                    kit['aux_ref_logp'] = batch['aux_ref_logp']
                    with torch.no_grad():
                        a = model(batch, stream=stream)['components'][stream]
                        b = model(kit, stream=stream)['components'][stream]
                    torch.testing.assert_close(a, b)
                    for k in ('input_ids', 'labels', 'aux_pg_mask'):
                        self.assertTrue(torch.equal(batch[k], kit[k]), k)

    def test_refusals(self):
        trows, model = self.trainer_rows(), self.model()
        row = self.rows['vqa'][0]
        with mock.patch.object(grpo_rows, 'prompt_batch', lambda *a, **k: self.be.prompt_batch(None)):
            bad = dict(row, prompt_ids_sha256='0' * 64)
            with self.assertRaisesRegex(ValueError, 'prompt differs'):
                grpo_rows.encode(self.be.processor, bad, None, 'duplicate', None)
            bad = dict(row, reserved=[self.reserved[2]])
            with self.assertRaisesRegex(ValueError, 'delimiters'):
                grpo_rows.encode(self.be.processor, bad, None, 'duplicate', None)
            bad = dict(row, old_logp=[0.] * len(row['tokens']))
            with self.assertRaisesRegex(ValueError, 'sampled positions'):
                grpo_rows.encode(self.be.processor, bad, None, 'duplicate', None)
            with self.assertRaisesRegex(ValueError, 'outside the artifact'):
                grpo_rows.encode(self.be.processor, dict(row, response_sources=dict(row['response_sources'], donor=True)),
                                 None, 'duplicate', None)
            with self.assertRaisesRegex(ValueError, 'temperature'):
                grpo_rows.encode(self.be.processor, dict(row, temperature=None), None, 'duplicate', None)
            bad = dict(row, stream='routing')
            with self.assertRaisesRegex(ValueError, 'tool responses'):
                grpo_rows.encode(self.be.processor, bad, None, 'duplicate', None)
            batch, _ = grpo_rows.encode(self.be.processor, dict(row, reserved=self.reserved[:2] + [99]), None, 'duplicate', None)
            with self.assertRaisesRegex(ValueError, 'carrier id'):
                model(batch, stream='vqa')
        with self.assertRaises(FileExistsError):
            grpo.write_stream_db(self.dbs['vqa'], [])


if __name__ == '__main__':
    unittest.main()


class OwnRows(StreamRows):
    """Mode (a) exact-token rows: cross-entropy on own tokens through the trainer's routing stream."""
    def test_own_row_trains_by_ce_with_responses_masked(self):
        from rlkit.select import own_row
        rec_row = self.rows['routing'][0]
        rec = dict(tokens=rec_row['tokens'], kinds=rec_row['kinds'], prompt_ids_sha256=rec_row['prompt_ids_sha256'],
                   response_sources=dict(pose_source='own'), draw=0, seed=1, path='head', calls=[1])
        row = own_row(self.prompts[0], rec, dict(r=1., c=1., n=10, answer='1'), 'r1')
        trows, model = self.trainer_rows(), self.model().eval()
        path = os.path.join(self.tmp.name, 'own.sqlite')
        grpo.write_stream_db(path, [row])
        trows.connections['routing'], trows.counts['routing'] = run.connect(dict(path=path)), 1
        with mock.patch.object(grpo_rows, 'prompt_batch', lambda *a, **k: self.be.prompt_batch(None)):
            batch, _, audit = run.fetch(trows, 'routing', 0, model)
            self.assertFalse(grpo_loss.is_pg_batch(batch))
            P = batch['input_ids'].shape[1] - len(row['tokens'])
            for i, k in enumerate(row['kinds']):
                self.assertEqual(int(batch['labels'][0, P + i]) == -100, k == 'r')
            out = model(batch, stream='routing')
            self.assertGreater(float(out['components']['routing']), 0.)
            with self.assertRaisesRegex(ValueError, 'inside the artifact'):
                grpo_rows.encode(self.be.processor, dict(row, response_policy=None), None, 'duplicate', None)
            with self.assertRaisesRegex(ValueError, 'outside the artifact'):
                grpo_rows.encode(self.be.processor, dict(row, response_sources=dict(pose_source='own', mask_source='gt')),
                                 None, 'duplicate', None)
