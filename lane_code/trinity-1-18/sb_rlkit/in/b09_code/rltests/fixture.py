"""Tiny native C1 fixture (the tree's own final_fixture) behind the sampler's backend interface."""
import os
import sys
from types import SimpleNamespace

TREE = os.environ.get('RLKIT_TREE', '/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449')
if TREE not in sys.path:
    sys.path.insert(0, TREE)

import torch  # noqa: E402
from tests.test_carrier_c1_final import FakeTokenizer, final_fixture  # noqa: E402  (tree's tests package)


class WordTokenizer(FakeTokenizer):
    """FakeTokenizer whose encode round-trips the scripted words (longest match first)."""
    def encode(self, text, add_special_tokens=False):
        words = sorted(self.words.items(), key=lambda kv: -len(kv[1]))
        out = []
        while text:
            for i, w in words:
                if text.startswith(w):
                    out.append(i)
                    text = text[len(w):]
                    break
            else:
                out.append(50 + ord(text[0]) % 10)
                text = text[1:]
        return out


HEAD_TEXT = '<depth_at frame=2 pts=[[500,500],[300,700]]>'
DIRECT_TEXT = ' Next'
FORCING = {'object_size': {'head': HEAD_TEXT, 'direct': DIRECT_TEXT},
           'counting': {'direct': DIRECT_TEXT}}


class FixtureBackend:
    def __init__(self, batchable=True):
        self.model, batch, _ = final_fixture()
        self.model.eval()
        self.processor = SimpleNamespace(tokenizer=WordTokenizer(),
                                         _routing_tokens=dict(ids={'<depth_at': 40, '<move': 45, '<pose': 39,
                                                                   '<turn': 47, '<box_3d': 38}))
        self.prompt = {k: v[:, :-2] if k in ('input_ids', 'attention_mask', 'mm_token_type_ids') else v
                       for k, v in batch.items() if k != 'labels'}
        self.batchable = batchable
        self.calls = 0

    def eos_id(self):
        return 1

    def prompt_batch(self, prompt):
        return dict(self.prompt)

    def can_batch(self, prompt):
        return self.batchable

    def decode_kwargs(self, prompt, batch, n=1):
        return {}

    def generate(self, batch, choice, **kw):
        from student_pilot import carrier_c1_decode as D
        self.calls += 1
        return D.generate(self.model, self.processor, batch, reference_trace=choice, max_calls=8, **kw)


def prompt(pid, qtype='object_size', **extra):
    base = dict(schema='rlkit-prompt-v1', prompt_id=pid, type=qtype, question='How long is the table?',
                options=None, gt_answer='120', row={}, scene_key='scene_' + pid, source='reserve_r0_rl')
    base.update(extra)
    return base


def sampler_config(**sampling):
    return dict(export='fixture', tree=TREE, forcing=FORCING,
                sampling=dict(dict(draws=4, max_sampled_tokens=10, temperature=1.0, top_p=0.9), **sampling))
