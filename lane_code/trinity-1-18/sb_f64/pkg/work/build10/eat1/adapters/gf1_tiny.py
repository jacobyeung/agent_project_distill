"""EAT-1 adapter: the next-leg tree's routed decode with GF-1 on the tree's tiny GF-1 CPU fixture.

Same entry as c8r_tiny (`evalpath.runtime.generate(..., 'routed', 16384)`), on `tests.test_gf1.fixture()`:
tiny Qwen3.5 + CarrierC1 with the frozen tiny G3T tower (`auxiliary_heads.geometry_encoder`) and the GF-1
fusion (`auxiliary_heads.gf1`) registered on the model. GF-1's output layer is zero-initialised, so the
adapter adds small seeded noise to the fusion parameters as a stand-in for trained weights; otherwise a
perturbed tower could not change any response. The fixture has no depth head, so programs use pose calls.
The fixture binds trace version 3.14, whose decode demands a live ground session; the adapter unbinds it
(as in the C8r fixture), so head calls take the same respond() path without a ground backend.
"""
import sys
from pathlib import Path

import numpy as np
import torch

from .c8r_tiny import ProgramPolicy

PROGRAMS = {'move': [45, 46, 42, 1], 'turn': [47, 48, 42, 1], 'direct': [42, 1]}
FIELDS = {'<move': {'move': ['pose_head', 'g3t', 'gf1']}, '<turn': {'turn': ['pose_head', 'g3t', 'gf1']}}
MODULES = {'': dict(role='lm', name='lm'), 'model.visual': dict(role='vit', name='vit'),
           'auxiliary_heads.pose': dict(role='head', name='pose_head'),
           'auxiliary_heads.geometry_encoder': dict(role='tower', name='g3t'),
           'auxiliary_heads.gf1': dict(role='connector', name='gf1'),
           'eat1_program_policy': dict(role='lm', name='program_policy')}


class GF1TinyReader:
    def __init__(self, tree, workdir):
        tree = str(Path(tree).resolve())
        if tree not in sys.path:
            sys.path.insert(0, tree)
        sys.dont_write_bytecode = True
        from types import SimpleNamespace
        from tests.test_gf1 import fixture
        from tests.test_batched_routed_decode import Tokenizer
        from eat1.artifact import write_manifest
        model, batch, _ = fixture()
        model.eat1_program_policy = ProgramPolicy()
        model.trace_program_version = None
        art = Path(workdir)/'artifact'
        art.mkdir(parents=True, exist_ok=True)
        if not (art/'ARTIFACT.json').is_file():
            g = torch.Generator().manual_seed(5)
            with torch.no_grad():
                for p in model.auxiliary_heads.gf1.parameters():
                    if p.is_floating_point():
                        p.add_(0.05*torch.randn(p.shape, generator=g))
            torch.save(model.state_dict(), art/'weights.pt')
            from .build10_manifest import entries
            files,modules=entries(model,tree,art,MODULES)
            write_manifest(art/'ARTIFACT.json', art, files, modules)
        model.load_state_dict(torch.load(art/'weights.pt'))
        self.model, self.batch = model.eval(), batch
        self.processor = SimpleNamespace(tokenizer=Tokenizer(), _routing_tokens={'ids': {
            '<depth_at': 40, '<move': 45, '<turn': 47, '<pose': 33}})
        self.tokenizer = self.processor.tokenizer
        self.artifact_manifest = art/'ARTIFACT.json'
        self.eat1_fixture_roots = [str(Path(tree)/'tests')]
        policy = model.eat1_program_policy
        model.model.register_forward_pre_hook(policy.see, with_kwargs=True)
        model.lm_head.register_forward_hook(lambda m, a, out: policy(out))

    def lm(self):
        return (self.model.model, self.model.lm_head)

    def generate(self, frames, question):
        from evalpath import runtime
        batch = dict(self.batch)
        data = np.load(frames)
        batch['pixel_values_videos'] = torch.from_numpy(data['pixels']).float()
        batch['aux_g3t_images'] = torch.from_numpy(data['g3t']).float()
        self.model.eat1_program_policy.start(PROGRAMS[question])
        decoded = runtime.generate(self.model, self.processor, batch, 'routed', 16384)
        calls = [dict(call=c['call'], response=c['response'],
                      fields={} if c.get('kind') == 'error' else
                      next((f for k, f in FIELDS.items() if c['call'].startswith(k)), {}))
                 for c in decoded['calls']]
        text = decoded['text']
        return dict(text=text, answer=text.rpartition('</tool_response>')[2].strip() or text.strip(), calls=calls,
                    finish=decoded['finish'], errors=decoded['errors'])


def make_reader(tree, workdir):
    return GF1TinyReader(tree, workdir)


def write_items(path, frames_dir, seeds=(0, 1)):
    import json
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for q in PROGRAMS:
        for s in seeds:
            f = frames_dir/f'{q}_{s}.npz'
            rng = np.random.default_rng(200+s)
            np.savez(f, pixels=rng.standard_normal((128, 24)).astype(np.float32),
                     g3t=rng.random((1, 64, 3, 28, 28)).astype(np.float32))
            rows.append(dict(id=f'{q}_{s}', type=q, frames=str(f), question=q))
    Path(path).write_text(''.join(json.dumps(r)+'\n' for r in rows))
