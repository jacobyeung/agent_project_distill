"""Heads and prediction mixing under the exact multi-node layout (microbatch = batch / world).

Ranks are simulated in one process: each rank owns a model copy, takes its rank_slots, mixes and
back-propagates with the trainer's world/batch scaling, and DDP's reduction is the mean of the
rank gradients. The result must equal one process training the whole global batch.
"""
import copy
import io
import unittest

import torch

from tests.auxiliary_toys import Toy, ToyTokenizer, category_query, blank_query, encoded_row, install_runner

install_runner()
from student_pilot import auxiliary_config as config  # noqa: E402
from student_pilot import auxiliary_reason as reason  # noqa: E402
from student_pilot import auxiliary_targets as targets  # noqa: E402
from student_pilot.auxiliary_losses import AuxiliaryHeads, attach, mix_microbatch  # noqa: E402
from student_pilot.ddp_core import backward_batch, collate_rows, global_batches, rank_slots  # noqa: E402

Q = reason.QUERY_TOKENS
QUESTION = 'How many chairs are next to the table?'
PIN = {'path': '/fixture/sidecar', 'sha256': '0' * 64}
BATCH, WORLD = 8, 4


def settings(probability=1.0):
    return config.normalize({'count_weight': .2, 'reason_weight': .5, 'reason_mix_prob': probability,
                             'head_width': 16, 'supervision': PIN})


def encoded_rows(tokenizer):
    rows = []
    for index in range(BATCH):
        target = (f'There are {Q["COUNT"]}{index + 1} chairs at {Q["TIME"]}3.5 seconds, {Q["DIST"]}{index}.5 m away, '
                  f'turn {Q["ANGLE"]}{-20 * index:+d} and step {Q["COORD"]}{0.3 * index - 1:+.1f} m.' if index % 3
                  else f'Nothing to measure in row {index}.')
        record = {'queries': [category_query(QUESTION, 'chairs', counts=[index % 4] * 16, scene=index),
                              blank_query(), blank_query(), blank_query()], 'reason': True}
        row, batch, audit = encoded_row(tokenizer, QUESTION, target, qid=f'r{index}', record=record)
        rows.append(targets.add_to_batch(batch, row, tokenizer, audit))
    return rows


def step(model, rows, indices, weights, world, key):
    batch = collate_rows([rows[i] for i in indices], 0)
    batch, stats = mix_microbatch(model, model.auxiliary_heads, batch, weights, key, 0, collective=True)
    losses = backward_batch(model, batch, weights, world, BATCH)
    return losses, stats


class MultiNodeTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        torch.set_num_threads(1)

    def test_exact_microbatch_ranks_match_one_process(self):
        tokenizer = ToyTokenizer()
        rows = encoded_rows(tokenizer)
        model = Toy()
        attach(model, settings(), tokenizer)
        replicas = [copy.deepcopy(model) for _ in range(WORLD)]
        window = next(global_batches(BATCH, 0, BATCH, 17))
        losses, stats = step(model, rows, window['indices'], [1.0] * BATCH, 1, 'single')
        microbatch = BATCH // WORLD
        rank_losses, mixed = [], 0
        for rank, replica in enumerate(replicas):
            slots = rank_slots(window['indices'], rank, WORLD, microbatch)
            self.assertEqual(len(slots), microbatch)
            self.assertTrue(all(weight == 1.0 for _, weight in slots))
            local, local_stats = step(replica, rows, [i for i, _ in slots], [w for _, w in slots], WORLD, f'17:0:{rank}:0')
            rank_losses.append(local)
            mixed += local_stats['rows']
        self.assertEqual(mixed, stats['rows'])
        self.assertEqual(stats['rows'], sum(1 for i in range(BATCH) if i % 3))
        self.assertAlmostEqual(sum(l.sum().item() for l in rank_losses), losses.sum().item(), places=5)
        for name, parameter in model.named_parameters():
            reduced = torch.stack([dict(r.named_parameters())[name].grad for r in replicas]).mean(dim=0)
            self.assertTrue(torch.allclose(reduced, parameter.grad, atol=1e-6, rtol=1e-4), name)
        for name in ('auxiliary_heads.reason_coord.0.weight', 'auxiliary_heads.reason_angle.0.weight',
                     'auxiliary_heads.count_group.0.weight', 'auxiliary_heads.reason_time_key.weight'):
            self.assertGreater(dict(model.named_parameters())[name].grad.abs().sum().item(), 0, name)

    def test_every_rank_runs_one_prediction_forward_per_microbatch(self):
        tokenizer = ToyTokenizer()
        rows = encoded_rows(tokenizer)
        window = next(global_batches(BATCH, 0, BATCH, 17))
        for probability in (0.0, 0.5, 1.0):
            for rank in range(WORLD):
                model = Toy()
                attach(model, settings(probability), tokenizer)
                calls = []
                handle = model.language_model.norm.register_forward_hook(lambda *args: calls.append(1))
                slots = rank_slots(window['indices'], rank, WORLD, 1)
                for chunk_index, (index, weight) in enumerate(slots):
                    step(model, rows, [index], [weight], WORLD, f'17:0:{rank}:{chunk_index}')
                handle.remove()
                # One no-grad prediction forward plus one training forward, whatever the draw.
                self.assertEqual(len(calls), 2 * len(slots), (probability, rank))
                self.assertTrue(model.training)

    def test_head_export_roundtrip_after_a_step(self):
        tokenizer = ToyTokenizer()
        rows = encoded_rows(tokenizer)
        model = Toy()
        heads = attach(model, settings(), tokenizer)
        optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-2)
        step(model, rows, list(range(BATCH)), [1.0] * BATCH, 1, 'k')
        optimizer.step()
        buffer = io.BytesIO()
        torch.save({name: value.detach().cpu() for name, value in heads.state_dict().items()}, buffer)
        buffer.seek(0)
        manifest = heads.manifest()
        loaded = AuxiliaryHeads(12, manifest['settings'])
        loaded.load_state_dict(torch.load(buffer, weights_only=True), strict=True)
        for name, value in heads.state_dict().items():
            self.assertTrue(torch.equal(value, loaded.state_dict()[name]), name)
        self.assertEqual(manifest['query_tokens']['COORD']['token'], '<|fim_prefix|>')
        self.assertEqual(set(manifest['query_tokens']), set(reason.KINDS))
        self.assertTrue(manifest['inference_required'])


if __name__ == '__main__':
    unittest.main()
