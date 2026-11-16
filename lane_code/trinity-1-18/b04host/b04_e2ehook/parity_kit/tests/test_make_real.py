"""Tiny random Qwen cache forwards through the production hook and audited real loop."""
from pathlib import Path
from types import SimpleNamespace as NS
import sys

import numpy as np
import pytest
import torch

from parity_kit.common import LANE, TREE, module, pin, policy, write
from e2e_reader import artifact as A, parity
from e2e_reader.core import E2EGenerator


@pytest.fixture
def tiny(tmp_path):
    from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM
    from student_pilot.carrier_c1_routing import add_routing_tokens
    tok_path = LANE/'work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
    tok = AutoTokenizer.from_pretrained(tok_path, local_files_only=True)
    proc = NS(tokenizer=tok)
    proc._routing_tokens = add_routing_tokens(proc)
    torch.manual_seed(0)
    cfg = Qwen3Config(vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                      num_attention_heads=2, num_key_value_heads=1, head_dim=16, max_position_embeddings=4096)
    model = Qwen3ForCausalLM(cfg).eval()
    # Prewarm lazy installed-library imports before auditing generate().
    model(torch.tensor([[1]]), use_cache=True)
    (tmp_path/'dummy.bin').write_bytes(b'pinned fixture')
    manifest = A.build_manifest(tmp_path, {n: (n, ['dummy.bin']) for n in ('checkpoint', 'tokenizer', 'g3t')},
                                dict(reader=LANE/'e2e_reader', tree=TREE))
    _, digest = A.write_manifest(tmp_path, manifest)
    spec = dict(root=str(tmp_path), name='E2E_MANIFEST.json', sha256=digest,
                code_roots=dict(reader=str(LANE/'e2e_reader'), tree=str(TREE)))
    return model, proc, spec


def test_make_real_through_generator(tiny, tmp_path, monkeypatch):
    model, proc, spec = tiny
    from PIL import Image
    frame = tmp_path/'rgb.png'
    Image.new('RGB', (4, 4)).save(frame)
    from parity_kit.common import sha
    dense = [dict(index=i, path='rgb.png', sha256=sha(frame)) for i in range(64)]
    slots = list(range(0, 64, 2))
    capture = dict(native='fixture', frames=[dense[i] for i in slots], anchor_indices=slots,
                   timestamps=slots, fps=1, total_num_frames=64)
    settings = dict(arm='own_depth', frames_root=str(tmp_path),
                    frames_json=dict(captures=[capture]),
                    dense_manifest=dict(captures={'fixture': dict(frames=dense, anchor_slots=slots)}))
    task = dict(id='tiny', native='fixture', dataset='fixture', scene='fixture', question_type='camera_displacement',
                question='How far?', options=[], answer='1.2', answer_type='numeric', room='fixture')
    count = dict(load=0, prefill=0, steps=0)

    def load(*a, **kw):
        count['load'] += 1
        return model, proc, dict(config={}, export=dict(frame_layout='duplicate'))
    monkeypatch.setattr(parity, 'load_native', load)
    from evalpath import runtime
    prompt = torch.tensor([proc.tokenizer.encode('Question: How far?\n<think>\n', add_special_tokens=False)])
    monkeypatch.setattr(runtime, 'prompt_batch', lambda *a: dict(input_ids=prompt, attention_mask=torch.ones_like(prompt)))
    from student_pilot import carrier_c1_decode as native

    def prepare(m, p, batch, max_new_tokens=None):
        assert max_new_tokens == 16384
        count['prefill'] += 1
        output = m(input_ids=batch['input_ids'], attention_mask=batch['attention_mask'], use_cache=True)
        return NS(native=m, output=output, cap=max_new_tokens, stream=None,
                  heads=NS(pose9=np.zeros((32, 9)), gravity=np.array([0., -1., 0.])))

    def consume(m, full, mask, cache, observer=None):
        start = cache.get_seq_length()
        for i in range(start, full.shape[1]):
            output = m(input_ids=full[:, i:i+1], attention_mask=mask[:, :i+1], past_key_values=cache, use_cache=True)
            cache = output.past_key_values
            count['steps'] += 1
        return output, cache
    monkeypatch.setattr(native, '_prepare_decode', prepare)
    monkeypatch.setattr(native, 'consume_cache_tokens', consume)

    class Perception:
        def lazy(self, frames, state, timings):
            assert len(frames['native_frames']) == 64
            return {'move': lambda call: ('distance 1.20 m', {'kind': 'head'})}, {}
    factory_calls = []
    def factory(**kw):
        factory_calls.append(kw['item']['id'])
        return Perception()
    gen = parity.make_real(tmp_path, spec, [task], perception_factory=factory, settings=settings)
    assert isinstance(gen.generator, E2EGenerator)
    # Reuse the suite's sampled-token script helper with a short numerical fixture.
    fixture = module(LANE/'tests/test_tiny_e2e.py', '_parity_tiny_fixture')
    monkeypatch.setattr(fixture, 'SCRIPT', '<move from=1 to=2>\n</think>\n\n1.2')
    original_factory = gen.generator.budget_factory
    class Scripted:
        def __init__(self):
            self.guard, self.script = original_factory(), fixture.script_processor(proc.tokenizer)
        def __call__(self, ids, scores):
            return self.guard(ids, self.script(ids, scores))
        def receipt(self, count):
            return self.guard.receipt(count)
    gen.generator.budget_factory = Scripted
    for _ in range(2):
        result = gen(task)
        assert result['scores'] == dict(answer=1.0, released_answer=None)
        assert result['calls']['records'][0]['call'] == '<move from=1 to=2>'
        assert result['calls']['records'][0]['served']
        assert result['audit']['violations'] == []
        assert result['entries']['prefill'] == 1
        assert result['decode_budget']['natural_close']
    assert count['load'] == 1 and count['prefill'] == 2 and count['steps'] > 0
    assert factory_calls == ['tiny', 'tiny']
