"""CPU end-to-end tests of the reader on a tiny random causal LM with the real Qwen3.5 tokenizer.

The tiny model cannot write calls on its own, so a script processor overrides the argmax at
SAMPLED positions only (never at forced response positions). Everything else is the product
path: one prefill, call detection inside the hook, responses from in-call towers and heads
(G3T outputs of a real K1 capture, gravity, a scale head, SAM 3-style candidates + a selector
head), forced ids through the same KV cache, audited file access.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

ROOT = Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/b04/b04_e2ehook')
TREE = '/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/p/tree'
sys.path[:0] = [str(ROOT), TREE]
TOK = ROOT / 'work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
K1 = Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/missing_k1/01949c4249271126')
OUT = ROOT / 'out/proofs'
CODE_ROOTS = dict(reader=ROOT / 'e2e_reader', tree=TREE)

from e2e_reader import artifact as A  # noqa: E402
from e2e_reader.callhook import CallHook, install  # noqa: E402
from e2e_reader.generate import Perception, generate  # noqa: E402
from e2e_reader.grounding import StageOneSocket  # noqa: E402

SCRIPT = ('I will read the camera and the objects.<move from=1 to=9> then <turn from=2 to=17> and '
          '<pose frame=3> then <ground obj="chair" mode="box"> and <ground obj="table" mode="box"> '
          '<gap a="chair" b="table" rule="box_grid_5cm"> and the room <ground mode="room"> so the answer is 1.2')


class TinyScaleHead(nn.Module):
    """Stand-in with the scale head's call signature (the trained head replaces it)."""
    def __init__(self):
        super().__init__()
        self.lin = nn.Linear(3, 1)

    def forward(self, tower):
        d = torch.as_tensor(np.asarray(tower['depth_grid']), dtype=torch.float32)
        x = torch.stack([d.log().mean(), d.log().std(), torch.tensor(1.)])
        return self.lin(x).squeeze(-1)


class TinySelector(nn.Module):
    """Stand-in with the selector head's contract: logits over N candidates + 1 null slot."""
    def __init__(self, feat=4):
        super().__init__()
        self.score = nn.Linear(feat, 1)
        self.null = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        return torch.cat([self.score(x).squeeze(-1), self.null])


@pytest.fixture(scope='module')
def kit(tmp_path_factory):
    from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM
    from student_pilot.carrier_c1_routing import add_routing_tokens
    from types import SimpleNamespace as NS
    root = tmp_path_factory.mktemp('artifact')
    tok = AutoTokenizer.from_pretrained(TOK)
    openers = add_routing_tokens(NS(tokenizer=tok))['ids']
    (root / 'tokenizer').mkdir()
    tok.save_pretrained(root / 'tokenizer')
    torch.manual_seed(0)
    cfg = Qwen3Config(vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                      num_attention_heads=2, num_key_value_heads=1, head_dim=16, max_position_embeddings=4096)
    model = Qwen3ForCausalLM(cfg).eval()
    model.save_pretrained(root / 'checkpoint', safe_serialization=True)
    z = np.load(K1 / 'tower.npz')
    from safetensors.torch import save_file
    save_file({k: torch.as_tensor(z[k]) for k in z.files}, str(root / 'g3t_fixture.safetensors'))
    torch.manual_seed(1)
    scale, selector = TinyScaleHead(), TinySelector()
    with torch.no_grad():
        scale.lin.weight.zero_(); scale.lin.bias.fill_(float(np.log(2.5)))
        selector.score.weight.copy_(torch.tensor([[1., 0., 0., 0.]])); selector.null.fill_(-5.)
    save_file(scale.state_dict(), str(root / 'scale_head.safetensors'))
    save_file(selector.state_dict(), str(root / 'selector_head.safetensors'))
    save_file({'masks': torch.zeros(1)}, str(root / 'sam3_fixture.safetensors'))
    tok_files = sorted(str(p.relative_to(root)) for p in (root / 'tokenizer').iterdir())
    ck_files = sorted(str(p.relative_to(root)) for p in (root / 'checkpoint').iterdir())
    manifest = A.build_manifest(root, dict(
        lm=('checkpoint', ck_files), tokenizer=('tokenizer', tok_files), g3t=('g3t', ['g3t_fixture.safetensors']),
        sam3=('sam3', ['sam3_fixture.safetensors']), scale_head=('scale_head', ['scale_head.safetensors']),
        selector_head=('selector_head', ['selector_head.safetensors'])), code_roots=CODE_ROOTS)
    path, digest = A.write_manifest(root, manifest)
    return dict(root=root, digest=digest, tok=tok, openers=openers, cfg=cfg)


def load(kit):
    from transformers import Qwen3ForCausalLM
    art = A.Artifact(kit['root'], 'E2E_MANIFEST.json', kit['digest'], code_roots=CODE_ROOTS).verify()
    model = Qwen3ForCausalLM.from_pretrained(art.path('lm', 'checkpoint/model.safetensors').parent).eval()
    scale = TinyScaleHead(); scale.load_state_dict(A.load_tensors(art.path('scale_head')))
    selector = TinySelector(); selector.load_state_dict(A.load_tensors(art.path('selector_head')))
    model.add_module('scale_head', scale); model.add_module('selector_head', selector)
    hook = install(model, CallHook(kit['tok'], kit['openers'].values()))
    return art, model, hook


def perception(art, model, leak=None):
    def g3t(frames):
        t = A.load_tensors(art.path('g3t'))  # the frozen tower runs inside the call (fixture here)
        if leak is not None:
            open(leak).read()
        return dict(raw_pose9=t['raw_pose'].double().numpy(), anchor_slots=t['anchor_slots'].numpy(),
                    frame_indices=t['frame_indices'].numpy(), depth_grid=t['depth_grid'].numpy(),
                    depth_conf_grid=t['depth_conf_grid'].numpy(), points_grid=t['points_grid'].numpy(),
                    grid_uv=t['grid_uv'].numpy(), source_hw=(480, 640))

    def gravity(prefill):
        return np.array([0., -1., 0.])  # stand-in for the own gravity head (camera y points down)

    def socket(frames, geometry):
        A.load_tensors(art.path('sam3'))

        def propose(name):
            m = np.zeros((480, 640), bool)
            if name == 'chair':
                m[200:300, 100:220] = True
            else:
                m[150:260, 380:560] = True
            cands = [dict(candidate_id=name + ':000', masks={5: m, 6: m}),
                     dict(candidate_id=name + ':001', masks={20: m})]
            feats = torch.tensor([[1., 0, 0, 0], [0.2, 0, 0, 0]])
            return cands, feats

        def select(feats):
            logits = model.selector_head(feats)
            k = int(logits.argmax())
            return -1 if k == len(logits) - 1 else k
        from e2e_reader.geometry import frame_count
        return StageOneSocket(propose, select, (480, 640), frame_count(geometry))
    return Perception(g3t, gravity, model.scale_head, socket, serve_room=False)


def script_processor(tok):
    script = tok.encode(SCRIPT, add_special_tokens=False) + [tok.convert_tokens_to_ids('<|im_end|>')]
    state = dict(i=0)

    def process(ids, logits):
        t = script[state['i']]
        state['i'] += 1
        out = torch.full_like(logits, -1e9)
        out[..., t] = 0
        return out
    return process


def run(kit, leak=None, enforce=True):
    art, model, hook = load(kit)
    tok = kit['tok']
    prompt = tok.encode('<|im_start|>user\nHow far did the camera move?<|im_end|>\n<|im_start|>assistant\n',
                        add_special_tokens=False)
    res = generate(model, hook, perception(art, model, leak), frames=None, prompt_ids=prompt, artifact=art,
                   eos_ids=[tok.convert_tokens_to_ids('<|im_end|>')], max_new_tokens=2048,
                   logits_processor=script_processor(tok), enforce_audit=enforce)
    return art, model, hook, prompt, res


def test_every_call_type_end_to_end(kit):
    art, model, hook, prompt, res = run(kit)
    rep = res['hook']
    assert res['finish'] == 'eos'
    assert rep['calls'] == dict(move=1, turn=1, pose=1, ground=3, gap=1) or rep['calls'] == {
        'move': 1, 'turn': 1, 'pose': 1, 'ground': 2, 'gap': 1, 'room': 1}
    assert rep['unserved'] == {'room': 1}
    served = [r for r in rep['records'] if r['served']]
    assert [r['family'] for r in served] == ['move', 'turn', 'pose', 'ground', 'ground', 'gap']
    assert res['model_prefills'] == 1 and res['audit']['model_entries'] == 1
    assert res['cache_length'] == len(prompt) + len(res['tokens']) - 1
    assert not res['audit']['violations']
    # responses are well-formed v3.14 bodies
    from student_pilot.live_trace313 import parse_response
    for r in served:
        if r['family'] in ('ground', 'gap'):
            parse_response(r['call'], r['response'], '3.14')
    assert served[3]['response'].startswith('chair: frames 5,6 (best 5)')
    assert served[5]['response'].startswith('distance ')
    # cache continuation equals a fresh full forward over the same ids
    full = model(input_ids=torch.as_tensor([prompt + res['tokens'][:-1]])).logits[0, -1]
    ids = torch.as_tensor([prompt]); out = model(input_ids=ids, use_cache=True); cache = out.past_key_values
    out = model(input_ids=torch.as_tensor([res['tokens'][:-1]]), past_key_values=cache, use_cache=True)
    assert torch.allclose(full, out.logits[0, -1], atol=1e-4)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'TINY_E2E.json').write_text(json.dumps(dict(
        calls=rep['calls'], unserved=rep['unserved'], responses=[(r['call'], r['response']) for r in served],
        prefills=res['model_prefills'], steps=res['model_steps'], cache_length=res['cache_length'],
        audit=dict(opens=res['audit']['opens'], data_files=res['audit']['data_files'],
                   violations=res['audit']['violations']), scale=res['scale'], timings=res['timings'],
        text=res['text']), indent=1) + '\n')


def test_camera_response_equals_tree_formatter_on_same_geometry(kit):
    """Hook camera responses equal the sealed tree respond() on the same tensors."""
    art, model, hook, prompt, res = run(kit)
    from e2e_reader.geometry import from_tower, camera_geometry
    from student_pilot.carrier_c1_decode import respond
    from student_pilot.p3_printed_calculator import PrintedPointRegistry
    t = A.load_tensors(art.path('g3t'))
    g = from_tower(t['raw_pose'].double().numpy(), t['anchor_slots'].numpy(), t['frame_indices'].numpy(),
                   t['depth_grid'].numpy(), t['grid_uv'].numpy(), np.array([0., -1., 0.]), res['scale'], (480, 640))
    own = camera_geometry(g)[0]
    for r in res['hook']['records'][:3]:
        assert respond(r['call'], PrintedPointRegistry(), own)[0] == r['response']


def test_loader_refuses_file_outside_manifest(kit, tmp_path):
    leak = tmp_path / 'scale_rule.json'
    leak.write_text('{"s": 2.587}')
    with pytest.raises(PermissionError, match='e2e_artifact_refuses'):
        run(kit, leak=str(leak))


def test_loader_refuses_changed_file(kit, tmp_path):
    root = tmp_path / 'copy'
    shutil.copytree(kit['root'], root)
    p = root / 'scale_head.safetensors'
    b = bytearray(p.read_bytes()); b[-1] ^= 1; p.write_bytes(bytes(b))
    with pytest.raises(A.ArtifactError, match='component_file_differs'):
        A.Artifact(root, 'E2E_MANIFEST.json', kit['digest'], code_roots=CODE_ROOTS).verify()
    with pytest.raises(A.ArtifactError, match='manifest_sha256_differs'):
        A.Artifact(root, 'E2E_MANIFEST.json', '0' * 64, code_roots=CODE_ROOTS)


def test_perturbing_one_head_changes_only_its_responses(kit):
    """EAT-1 A5(ii) on the tiny kit: scale head -> camera move + boxes change, turn does not;
    selector head -> ground/gap change, camera does not."""
    _, _, _, _, base = run(kit)
    art, model, hook = load(kit)
    resp = lambda res: {r['call']: r.get('response') for r in res['hook']['records']}
    b = resp(base)
    tok = kit['tok']
    prompt = tok.encode('<|im_start|>user\nHow far did the camera move?<|im_end|>\n<|im_start|>assistant\n',
                        add_special_tokens=False)
    with torch.no_grad():
        model.scale_head.lin.bias.add_(0.1)
    r1 = resp(generate(model, hook, perception(art, model), None, prompt, artifact=art,
                       eos_ids=[tok.convert_tokens_to_ids('<|im_end|>')], logits_processor=script_processor(tok)))
    assert r1['<move from=1 to=9>'] != b['<move from=1 to=9>']
    assert r1['<turn from=2 to=17>'] == b['<turn from=2 to=17>']
    art, model, hook = load(kit)
    with torch.no_grad():
        model.selector_head.score.weight.mul_(-1)
    r2 = resp(generate(model, hook, perception(art, model), None, prompt, artifact=art,
                       eos_ids=[tok.convert_tokens_to_ids('<|im_end|>')], logits_processor=script_processor(tok)))
    assert r2['<move from=1 to=9>'] == b['<move from=1 to=9>']
    assert r2['<ground obj="chair" mode="box">'] != b['<ground obj="chair" mode="box">']
