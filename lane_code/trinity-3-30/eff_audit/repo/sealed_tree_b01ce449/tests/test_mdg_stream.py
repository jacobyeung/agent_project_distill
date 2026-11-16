"""Portable native suffix contract for both MDG-A and stage-B source trees."""
import unittest

import torch

from student_pilot import mdg_features as features
from student_pilot.mdg_stream import stream_suffix_states
from tests.test_mdg_features import fixture, small_layers, cache_tensors


class Tokenizer:
    pad_token_id = 0
    def __init__(self):
        chars = sorted(set('<ground obj="chairtable">'))
        self.ids = {c: i+3 for i, c in enumerate(chars)}
        self.words = {i: c for c, i in self.ids.items()}
    def encode(self, text, **kwargs):
        return [self.ids[c] for c in text]
    def decode(self, ids, **kwargs):
        return ''.join(self.words[int(i)] for i in ids)
    def __call__(self, text, **kwargs):
        return dict(input_ids=self.encode(text), offset_mapping=[(i, i+1) for i in range(len(text))])


class NativeSuffix(unittest.TestCase):
    def test_per_label_results_and_prefix_cache_are_exact(self):
        torch.set_num_threads(min(8, torch.get_num_threads()))
        model, batch = fixture()
        model.mdg_tokenizer = Tokenizer()
        with small_layers(), torch.no_grad():
            prefix = features.capture_prefix(model, batch)
            before = cache_tensors(prefix.cache)
            together = stream_suffix_states(model, prefix, batch, ['chair', 'table'])
            for i, name in enumerate(('chair', 'table')):
                alone = stream_suffix_states(model, prefix, batch, [name])
                for key in ('query', 'phrase', 'phrase_mask'):
                    self.assertTrue(torch.equal(getattr(together, key)[i:i+1], getattr(alone, key)))
            after = cache_tensors(prefix.cache)
            self.assertEqual(before.keys(), after.keys())
            self.assertTrue(all(torch.equal(before[k], after[k]) for k in before))
            self.assertEqual(prefix.cache.get_seq_length(), prefix.prefix_len)


if __name__ == '__main__':
    unittest.main()
