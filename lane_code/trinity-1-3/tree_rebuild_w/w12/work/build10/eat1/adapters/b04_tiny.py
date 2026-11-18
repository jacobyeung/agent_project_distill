"""EAT-1 adapter: lane b04_e2ehook's end-to-end reader (e2e_reader) on its own tiny CPU kit.

Mirrors b04's tests/test_tiny_e2e.py kit (tiny Qwen3 causal LM with the real Qwen3.5 tokenizer, G3T outputs
of a real K1 capture as the tower fixture, a scale head, a selector head, the CallHook registered on the
model) and calls b04's `generate(...)`. b04's code is imported read-only from its lane folder.

The tiny LM cannot write calls, so `ScriptPolicy` (a module on the model; forward hook on lm_head) sets
the logits to the program's next token. It advances only when the call hook receives a sampled token, so
response tokens never move it. It writes no response token. b04's own test uses a logits processor
instead; EAT-1 would count those tokens as injected.
"""
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

B04 = Path('/scratch/jjyeung/orch_n30/b04_e2ehook')
TREE = '/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/base/tree_b01ce449'  # b04's tree copy (b01ce449), bound in its manifest
TOK = B04/'work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
K1 = Path('/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2/01949c4249271126')
PROGRAMS = {
    'camera': 'I will read the camera.<move from=1 to=9> then <turn from=2 to=17> and <pose frame=3> so the answer is 1.2',
    'ground': 'I will read the objects.<ground obj="chair" mode="box"> and <ground obj="table" mode="box"> '
              '<gap a="chair" b="table" rule="box_grid_5cm"> so the answer is 0.8',
    'room': 'the room <ground mode="room"> so the answer is 12.0',
    'direct': 'so the answer is 3',
}
FIELDS = {'move': ['g3t', 'scale_head'], 'turn': ['g3t'], 'pose': ['g3t', 'scale_head'],
          'ground': ['sam3', 'selector_head', 'g3t', 'scale_head'], 'gap': ['sam3', 'selector_head', 'g3t', 'scale_head']}


class ScriptPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.script, self.k = [0], 0
        self.anchor = nn.Parameter(torch.zeros(1), requires_grad=False)

    def start(self, script):
        self.script, self.k = list(script), 0

    def advance(self, module, args):
        self.k += 1

    def forward(self, logits):
        out = torch.full_like(logits, -1e4)
        out[..., self.script[min(self.k, len(self.script)-1)]] = 0.
        return out


class B04TinyReader:
    def __init__(self, workdir):
        for p in (str(B04), TREE):
            if p not in sys.path:
                sys.path.insert(0, p)
        sys.dont_write_bytecode = True
        from types import SimpleNamespace as NS
        from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM
        from safetensors.torch import save_file
        from student_pilot.carrier_c1_routing import add_routing_tokens
        from e2e_reader import artifact as A
        from e2e_reader.callhook import CallHook, install
        from tests.test_tiny_e2e import TinyScaleHead, TinySelector, perception
        from eat1.artifact import write_manifest
        self.A, self.perception_fn = A, perception
        root = Path(workdir).resolve()/'artifact'
        code_roots = dict(reader=B04/'e2e_reader', tree=TREE)
        tok = AutoTokenizer.from_pretrained(TOK)
        openers = add_routing_tokens(NS(tokenizer=tok))['ids']
        if not (root/'ARTIFACT.json').is_file():
            root.mkdir(parents=True, exist_ok=True)
            (root/'tokenizer').mkdir(exist_ok=True)
            tok.save_pretrained(root/'tokenizer')
            torch.manual_seed(0)
            cfg = Qwen3Config(vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                              num_attention_heads=2, num_key_value_heads=1, head_dim=16, max_position_embeddings=4096)
            Qwen3ForCausalLM(cfg).eval().save_pretrained(root/'checkpoint', safe_serialization=True)
            z = np.load(K1/'tower.npz')
            save_file({k: torch.as_tensor(z[k]) for k in z.files}, str(root/'g3t_fixture.safetensors'))
            scale, selector = TinyScaleHead(), TinySelector()
            with torch.no_grad():
                scale.lin.weight.zero_(); scale.lin.bias.fill_(float(np.log(2.5)))
                selector.score.weight.copy_(torch.tensor([[1., 0., 0., 0.]])); selector.null.fill_(-5.)
            save_file(scale.state_dict(), str(root/'scale_head.safetensors'))
            save_file(selector.state_dict(), str(root/'selector_head.safetensors'))
            save_file({'masks': torch.zeros(1)}, str(root/'sam3_fixture.safetensors'))
            tf = sorted(str(p.relative_to(root)) for p in (root/'tokenizer').iterdir())
            cf = sorted(str(p.relative_to(root)) for p in (root/'checkpoint').iterdir())
            manifest = A.build_manifest(root, dict(
                lm=('checkpoint', cf), tokenizer=('tokenizer', tf), g3t=('g3t', ['g3t_fixture.safetensors']),
                sam3=('sam3', ['sam3_fixture.safetensors']), scale_head=('scale_head', ['scale_head.safetensors']),
                selector_head=('selector_head', ['selector_head.safetensors'])), code_roots=code_roots)
            _, digest = A.write_manifest(root, manifest)
            (root/'B04_DIGEST').write_text(digest)
            files = {**{f: 'lm' for f in cf}, **{f: 'tokenizer' for f in tf}, 'g3t_fixture.safetensors': 'tower',
                     'sam3_fixture.safetensors': 'tower', 'scale_head.safetensors': 'head',
                     'selector_head.safetensors': 'head', 'E2E_MANIFEST.json': 'config', 'B04_DIGEST': 'config'}
            write_manifest(root/'ARTIFACT.json', root, files, {
                '': dict(role='lm', name='lm'), 'scale_head': dict(role='head', name='scale_head'),
                'selector_head': dict(role='head', name='selector_head'),
                'call_hook': dict(role='call_handler', name='call_hook'),
                'eat1_script_policy': dict(role='lm', name='script_policy')})
        digest = (root/'B04_DIGEST').read_text()
        self.art = A.Artifact(root, 'E2E_MANIFEST.json', digest, code_roots=code_roots).verify()
        model = Qwen3ForCausalLM.from_pretrained(self.art.path('lm', 'checkpoint/model.safetensors').parent).eval()
        scale = TinyScaleHead(); scale.load_state_dict(A.load_tensors(self.art.path('scale_head')))
        selector = TinySelector(); selector.load_state_dict(A.load_tensors(self.art.path('selector_head')))
        model.add_module('scale_head', scale); model.add_module('selector_head', selector)
        self.hook = install(model, CallHook(tok, openers.values()))
        model.add_module('eat1_script_policy', ScriptPolicy())
        policy = model.eat1_script_policy
        self.hook.register_forward_pre_hook(policy.advance)
        model.lm_head.register_forward_hook(lambda m, a, out: policy(out))
        self.model, self.tokenizer, self.tok = model, tok, tok
        self.eos = tok.convert_tokens_to_ids('<|im_end|>')
        self.artifact_manifest = root/'ARTIFACT.json'
        self.eat1_fixture_roots = [str(B04/'tests')]

    def lm(self):
        return self.model

    def generate(self, frames, question):
        from e2e_reader.generate import generate
        self.model.eat1_script_policy.start(self.tok.encode(PROGRAMS[question], add_special_tokens=False)+[self.eos])
        prompt = self.tok.encode(f'<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n',
                                 add_special_tokens=False)
        res = generate(self.model, self.hook, self.perception_fn(self.art, self.model), frames=None, prompt_ids=prompt,
                       artifact=self.art, eos_ids=[self.eos], max_new_tokens=2048, enforce_audit=True)
        text = res['text']
        calls = [dict(call=r['call'], response=r.get('response'),
                      fields={r['family']: FIELDS.get(r['family'], [])} if r['served'] else {})
                 for r in res['hook']['records'] if r['served']]
        return dict(text=text, answer=text.rpartition('answer is ')[2].replace('<|im_end|>', '').strip(), calls=calls,
                    unserved=res['hook'].get('unserved'), finish=res['finish'])


def make_reader(workdir):
    return B04TinyReader(workdir)


def write_items(path, frames_dir):
    import json
    Path(frames_dir).mkdir(parents=True, exist_ok=True)
    rows = [dict(id=f'{q}_0', type=q, frames=str(Path(frames_dir)), question=q) for q in PROGRAMS]
    Path(path).write_text(''.join(json.dumps(r)+'\n' for r in rows))
