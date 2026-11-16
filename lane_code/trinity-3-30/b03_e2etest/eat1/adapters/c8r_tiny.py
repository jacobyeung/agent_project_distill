"""EAT-1 adapter: the C8r routed reader's decode path on the sealed tree's tiny CPU fixture.

C8r's routed read (native/out2/routed.py) decodes each item with
`evalpath.runtime.generate(model, processor, batch, 'routed', 16384, ...)`, which enters
`student_pilot.carrier_c1_decode.generate`. This adapter calls the same entry on the tiny Qwen3.5 +
CarrierC1 model of the tree's own tests (tests/test_batched_routed_decode.fixture), with the sealed
tree imported read-only from `tree`.

The tiny LM is untrained, so a fixed program stands in for trained LM weights: `ProgramPolicy` is a
module registered on the model whose forward hook on `lm_head` sets the logits to the program's next
token (greedy subsequence match over the tokens fed so far). It writes no response token: every
response token comes from the reader's own call path, which is what EAT-1 judges. The policy is part of
the artifact's lm role and is not a finding of the reader.
"""
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

PROGRAMS = {  # question -> token program (FakeTokenizer ids of the tree's fixture)
    'depth_dist': [40, 41, 49, 42, 1],   # <depth_at frame=2 pts=[[500,500],[300,700]]> <dist P1 P2> Next
    'move': [45, 46, 42, 1],             # <move from=2 to=9> Next
    'turn': [47, 48, 42, 1],             # <turn from=4 to=30> Next
    'pose': [33, 42, 1],                 # <pose frame=40> Next
    'ground': [30, 42, 1],               # <ground obj="chair"> Next (no grounding backend bound)
    'direct': [42, 1],                   # Next (no call)
}
# Which declared head each call's response is printed from (C8r: HeadState / OwnGeometry / registry).
FIELDS = {'<depth_at': {'camera_points': ['pose_head', 'depth_head']},
          '<dist': {'distance': ['pose_head', 'depth_head']},
          '<move': {'move': ['pose_head']}, '<turn': {'turn': ['pose_head']}, '<pose': {'pose': ['pose_head']},
          '<ground': {'frames': ['grounding_head']}}
MODULES = {'': dict(role='lm', name='lm'), 'model.visual': dict(role='vit', name='vit'),
           'auxiliary_heads.pose': dict(role='head', name='pose_head'),
           'auxiliary_heads.depth': dict(role='head', name='depth_head'),
           'eat1_program_policy': dict(role='lm', name='program_policy')}


class ProgramPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.program, self.fed = [1], []
        self.anchor = nn.Parameter(torch.zeros(1), requires_grad=False)

    def start(self, program):
        self.program, self.fed = list(program), []

    def see(self, module, args, kwargs):
        ids = kwargs.get('input_ids', args[0] if args else None)
        if ids is not None:
            if kwargs.get('past_key_values') is None or kwargs['past_key_values'].get_seq_length() == 0:
                self.fed = []
            self.fed += ids[0].tolist()

    def forward(self, logits):
        k = 0
        for t in self.fed:
            if k < len(self.program) and t == self.program[k]:
                k += 1
        out = torch.full_like(logits, -1e4)
        out[..., self.program[min(k, len(self.program)-1)]] = 0.
        return out


class C8rTinyReader:
    def __init__(self, tree, workdir):
        tree = str(Path(tree).resolve())
        if tree not in sys.path:
            sys.path.insert(0, tree)
        sys.dont_write_bytecode = True
        from tests.test_batched_routed_decode import fixture
        from eat1.artifact import write_manifest
        model, processor, batch = fixture()
        model.eat1_program_policy = ProgramPolicy()
        art = Path(workdir)/'artifact'
        art.mkdir(parents=True, exist_ok=True)
        if not (art/'ARTIFACT.json').is_file():
            torch.save(model.state_dict(), art/'weights.pt')
            write_manifest(art/'ARTIFACT.json', art, {'weights.pt': 'lm'}, MODULES)
        model.load_state_dict(torch.load(art/'weights.pt'))
        self.model, self.processor, self.batch = model.eval(), processor, batch
        self.tokenizer = processor.tokenizer
        self.artifact_manifest = art/'ARTIFACT.json'
        self.eat1_fixture_roots = [str(Path(tree)/'tests')]  # the tiny fixture's tokenizer and builders
        policy = model.eat1_program_policy
        model.model.register_forward_pre_hook(policy.see, with_kwargs=True)
        model.lm_head.register_forward_hook(lambda m, a, out: policy(out))

    def lm(self):
        return (self.model.model, self.model.lm_head)

    def generate(self, frames, question):
        from evalpath import runtime
        batch = dict(self.batch)
        batch['pixel_values_videos'] = torch.from_numpy(np.load(frames)).float()
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
    return C8rTinyReader(tree, workdir)


def write_items(path, frames_dir, seeds=(0, 1)):
    import json
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for q in PROGRAMS:
        for s in seeds:
            f = frames_dir/f'{q}_{s}.npy'
            np.save(f, np.random.default_rng(100+s).standard_normal((64, 24)).astype(np.float32))
            rows.append(dict(id=f'{q}_{s}', type=q, frames=str(f), question=q))
    Path(path).write_text(''.join(json.dumps(r)+'\n' for r in rows))
