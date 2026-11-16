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

K = Path(__file__).resolve().parents[1]
ROOT = K / 'h1eval/reader_core'
TREE = K / 'tree'
sys.path[:0] = [str(ROOT), str(TREE)]
OUT = K / 'tmp/b4/reader_proofs'
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
    # Reuse the single retained checkpoint; never create a model or kit per test.
    from tests.test_eval import kit as shared_kit
    return shared_kit.__wrapped__(tmp_path_factory)


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
        return StageOneSocket(propose, select, (480, 640))
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
    # One tiny scale-head file exercises checksum rejection without copying the kit.
    root = tmp_path / 'tampered_head'; root.mkdir()
    p = root / 'scale_head.safetensors'
    p.write_bytes((kit['root'] / p.name).read_bytes())
    manifest = A.build_manifest(root, dict(scale_head=('scale_head', [p.name])))
    _, digest = A.write_manifest(root, manifest)
    b = bytearray(p.read_bytes()); b[-1] ^= 1; p.write_bytes(bytes(b))
    with pytest.raises(A.ArtifactError, match='component_file_differs'):
        A.Artifact(root, 'E2E_MANIFEST.json', digest, required_roles=('scale_head',)).verify()
    with pytest.raises(A.ArtifactError, match='manifest_sha256_differs'):
        A.Artifact(root, 'E2E_MANIFEST.json', '0' * 64, required_roles=('scale_head',))


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
