"""EAT-1 adapter: the b04 end-to-end reader on a tiny CPU fixture with the two TRAINED heads.

Model under test (every module registered on `reader.model`, every weight in one artifact):
  ''              tiny random Qwen3 causal LM (lm)            program_policy  fixed token program (lm role)
  g3t             frozen G3T stand-in: one K1 capture's tower output as buffers (tower)
  sam3            frozen SAM 3 stand-in: that capture's detections as a byte buffer (tower)
  gravity_head    G1: mean camera up of the tower's anchor poses, fixed math (head)
  scale_head      trained ScaleHead a90b5216 behind ScaleHeadCall (head)
  selector_head   trained SelectorHead run_iso 6d97c524 (head)
  call_hook       e2e_reader CallHook (call_handler)
The LM is untrained, so `ProgramPolicy` (a forward hook on lm_head) sets the logits to the program's next SAMPLED
token; it never writes a response token. The two stand-in towers and this file are the fixture (eat1_fixture_roots).
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
LANE = HERE.parent  # code root (the lane folder, or a code-only staging copy for the A5 sandbox)
DATA = Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/design/b04_inputs/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook')  # build-time inputs only
TREE = '/scratch/jjyeung/orch_n30/tree_rebuild_w/w10/work/tree_r1'
TOK = DATA / 'work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
K1 = Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/design/b04_inputs/scratch/jjyeung/k1/run_tower_sam_2/3912542710353e09')
SCALE = DATA / 'heads/scale/work/run1'
SELECTOR = DATA / 'heads/selector/work/run_iso'
for p in (str(LANE), TREE, str(LANE / 'heads/scale'), str(LANE / 'heads/selector'), str(LANE / 'heads/selector/sl118')):
    if p not in sys.path:
        sys.path.insert(0, p)

PROGRAMS = {
    'move': '<move from=1 to=9> so 1.2',
    'turn': '<turn from=2 to=17> so 30',
    'pose': '<pose frame=3> so 1',
    'ground': '<ground obj="door" mode="box"> so 2.0',
    'gap': '<ground obj="door" mode="box"> and <ground obj="tv" mode="box"> <gap a="door" b="tv" rule="box_grid_5cm"> so 2.0',
    'unseen': '<ground obj="cutting board" mode="box"> so 1.0',
    'direct': 'so 3.0',
}
# gravity_head here is parameter-free G1 math on the g3t stand-in's poses, so responses cite g3t for it.
FIELDS = {'move': ['g3t', 'scale_head'], 'turn': ['g3t'], 'pose': ['g3t', 'scale_head'],
          'ground': ['sam3', 'selector_head', 'g3t', 'scale_head'], 'gap': ['sam3', 'selector_head', 'g3t', 'scale_head']}
MODULES = {'': dict(role='lm', name='lm'), 'program_policy': dict(role='lm', name='program_policy'),
           'g3t': dict(role='tower', name='g3t'), 'sam3': dict(role='tower', name='sam3'),
           'gravity_head': dict(role='head', name='gravity_head'), 'scale_head': dict(role='head', name='scale_head'),
           'selector_head': dict(role='head', name='selector_head'), 'call_hook': dict(role='call_handler', name='call_hook')}
CODE_ROOTS = dict(reader=LANE / 'e2e_reader', tree=Path(TREE), scale=LANE / 'heads/scale', selector=LANE / 'heads/selector')
TOWER_KEYS = ('raw_pose', 'anchor_slots', 'frame_indices', 'depth_grid', 'depth_conf_grid', 'points_grid', 'grid_uv')


class FixtureG3T(nn.Module):
    """Stand-in for the frozen G3T tower: returns one capture's recorded output for any frames."""

    def __init__(self, tower=None, source_hw=(480, 640)):
        super().__init__()
        for k in TOWER_KEYS:
            self.register_buffer(k, torch.as_tensor(tower[k]) if tower is not None else torch.zeros(0))
        self.register_buffer('source_hw', torch.as_tensor(list(source_hw)))

    def forward(self, frames):
        return dict(raw_pose9=self.raw_pose.double().numpy(), anchor_slots=self.anchor_slots.numpy(),
                    frame_indices=self.frame_indices.numpy(), depth_grid=self.depth_grid.numpy(),
                    depth_conf_grid=self.depth_conf_grid.numpy(), points_grid=self.points_grid.numpy(),
                    grid_uv=self.grid_uv.numpy(), source_hw=tuple(int(v) for v in self.source_hw))


class FixtureSAM3(nn.Module):
    """Stand-in for the frozen SAM 3 tower: the capture's raw-name detections (alias prompts dropped)."""

    def __init__(self, blob=b''):
        super().__init__()
        self.register_buffer('blob', torch.frombuffer(bytearray(blob or b'{}'), dtype=torch.uint8))

    def forward(self, name):
        from student_pilot import routed_features as F
        data = json.loads(bytes(self.blob.numpy()).decode())
        out = []
        for slot in range(32):
            r = data['frames'][str(slot)]['phrases'].get(name)
            inst = [e for e in (r or {}).get('instances') or [] if e.get('source_prompt', name) == name]
            if not inst:
                out.append([])
                continue
            pres = float(inst[0].get('source_presence', r['presence']))
            out.append([dict(mask=F.resize(_rle(e['mask']), F.SHAPE), score=float(e['score']), presence=pres)
                        for e in sorted(inst, key=lambda e: -float(e['score']))])
        return out


def _rle(m):
    h, w = m['size']
    return np.repeat(np.arange(len(m['counts'])) % 2 == 1, m['counts']).reshape((h, w), order='F')


class GravityG1(nn.Module):
    def forward(self, raw_pose, anchor_slots):
        from student_pilot import camera_targets
        raw = raw_pose.double().numpy()[anchor_slots.numpy()]
        R = np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw])
        v = np.mean(-R[:, :, 1], axis=0)
        return v / np.linalg.norm(v)


class ProgramPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.program, self.hook = [], None

    def forward(self, logits):
        if self.hook is None or not self.program:
            return logits
        forced = sum(r.get('forced_tokens', 0) for r in self.hook.records)
        k = min(len(self.hook.ids) - forced, len(self.program) - 1)
        out = torch.full_like(logits, -1e4)
        out[..., self.program[k]] = 0.
        return out


def build(art):
    """Write the fixture artifact once: checkpoint, tokenizer, towers, heads; both manifests."""
    from safetensors.torch import save_file
    from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM
    from types import SimpleNamespace as NS
    from student_pilot.carrier_c1_routing import add_routing_tokens
    from e2e_reader import artifact as A
    from eat1.artifact import write_manifest
    art.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(TOK)
    add_routing_tokens(NS(tokenizer=tok))
    tok.save_pretrained(art / 'tokenizer')
    torch.manual_seed(0)
    cfg = Qwen3Config(vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                      num_attention_heads=2, num_key_value_heads=1, head_dim=16, max_position_embeddings=4096)
    Qwen3ForCausalLM(cfg).eval().save_pretrained(art / 'checkpoint', safe_serialization=True)
    z = np.load(K1 / 'tower.npz')
    receipt = json.loads((K1 / 'PHASE_COMPLETE.json').read_text())
    g3t = FixtureG3T({k: z[k] for k in TOWER_KEYS}, receipt['source_hw'])
    save_file({k: v.contiguous() for k, v in g3t.state_dict().items()}, str(art / 'g3t_fixture.safetensors'))
    save_file(FixtureSAM3((K1 / 'candidates.json').read_bytes()).state_dict(), str(art / 'sam3_fixture.safetensors'))
    for src, dst in ((SCALE, 'scale_head'), (SELECTOR, 'selector_head')):
        (art / dst).mkdir(exist_ok=True)
        for f in (dst + '.safetensors', dst + '.json'):
            (art / dst / f).write_bytes((src / f).read_bytes())
    rel = lambda d: sorted(str(p.relative_to(art)) for p in (art / d).iterdir())  # noqa: E731
    manifest = A.build_manifest(art, dict(
        lm=('checkpoint', rel('checkpoint')), tokenizer=('tokenizer', rel('tokenizer')),
        g3t=('g3t', ['g3t_fixture.safetensors']), sam3=('sam3', ['sam3_fixture.safetensors']),
        scale_head=('scale_head', rel('scale_head')), selector_head=('selector_head', rel('selector_head'))),
        code_roots=CODE_ROOTS)
    _, digest = A.write_manifest(art, manifest)
    roles = {r: 'lm' for r in rel('checkpoint')}
    roles.update({r: 'tokenizer' for r in rel('tokenizer')})
    roles.update({'g3t_fixture.safetensors': 'tower', 'sam3_fixture.safetensors': 'tower'})
    roles.update({r: 'head' for r in rel('scale_head') + rel('selector_head')})
    write_manifest(art / 'ARTIFACT.json', art, roles, MODULES)
    (art / 'E2E_MANIFEST.sha256').write_text(digest + '\n')


class B04TinyReader:
    def __init__(self, workdir):
        from transformers import AutoTokenizer, Qwen3ForCausalLM
        from e2e_reader import artifact as A
        from e2e_reader.callhook import CallHook, install
        from scale_head import ScaleHead
        from selector_head import SelectorHead
        from e2e_reader.stage1 import ScaleHeadCall
        art = Path(workdir) / 'artifact'
        if not (art / 'ARTIFACT.json').is_file():
            build(art)
        digest = (art / 'E2E_MANIFEST.sha256').read_text().strip()
        self.e2e = A.Artifact(art, 'E2E_MANIFEST.json', digest, code_roots=CODE_ROOTS).verify()
        tok = AutoTokenizer.from_pretrained(self.e2e.path('tokenizer', 'tokenizer/tokenizer_config.json').parent)
        model = Qwen3ForCausalLM.from_pretrained(self.e2e.path('lm', 'checkpoint/model.safetensors').parent).eval()
        g3t = FixtureG3T({k: torch.zeros(0) for k in TOWER_KEYS})
        for k, v in A.load_tensors(self.e2e.path('g3t')).items():
            setattr(g3t, k, v)
        sam3 = FixtureSAM3()
        sam3.blob = A.load_tensors(self.e2e.path('sam3'))['blob']
        scale_meta = json.loads(self.e2e.path('scale_head', 'scale_head/scale_head.json').read_text())
        scale = ScaleHead(hidden=scale_meta['config']['hidden'])
        scale.load_state_dict(A.load_tensors(self.e2e.path('scale_head', 'scale_head/scale_head.safetensors')))
        sel_meta = json.loads(self.e2e.path('selector_head', 'selector_head/selector_head.json').read_text())
        selector = SelectorHead(**{k: sel_meta['config'][k] for k in ('hidden', 'name_mode', 'n_hash')})
        selector.load_state_dict(A.load_tensors(self.e2e.path('selector_head', 'selector_head/selector_head.safetensors')))
        for name, mod in (('program_policy', ProgramPolicy()), ('g3t', g3t), ('sam3', sam3), ('gravity_head', GravityG1()),
                          ('scale_head', ScaleHeadCall(scale.eval())), ('selector_head', selector.eval())):
            model.add_module(name, mod)
        from student_pilot.carrier_c1_routing import OPENERS
        openers = [tok.convert_tokens_to_ids(o) for o in OPENERS]
        self.hook = install(model, CallHook(tok, openers))
        model.program_policy.hook = self.hook
        model.lm_head.register_forward_hook(lambda m, a, out: model.program_policy(out))
        self.model, self.tokenizer = model, tok
        self.artifact_manifest = art / 'ARTIFACT.json'
        self.eat1_fixture_roots = [str(HERE)]

    def lm(self):
        return (self.model.model, self.model.lm_head)

    def perception(self):
        from e2e_reader.generate import Perception
        from e2e_reader.grounding import StageOneSocket
        from e2e_reader.stage1 import StageOne
        m = self.model

        def socket(frames, geometry):
            s = StageOne(m.sam3, m.selector_head, geometry)
            from e2e_reader.geometry import frame_count
            return StageOneSocket(s.propose, s.select, (240, 320), frame_count(geometry))
        return Perception(m.g3t, lambda prefill: m.gravity_head(m.g3t.raw_pose, m.g3t.anchor_slots), m.scale_head,
                          socket, serve_room=False)

    @torch.no_grad()
    def generate(self, frames, question):
        from e2e_reader.generate import generate
        tok = self.tokenizer
        end = tok.convert_tokens_to_ids('<|im_end|>')
        self.hook.reset_read()  # the policy reads the hook's per-read state from the prefill on
        self.model.program_policy.program = tok.encode(PROGRAMS[question], add_special_tokens=False) + [end]
        prompt = tok.encode('<|im_start|>user\n' + question + '<|im_end|>\n<|im_start|>assistant\n',
                            add_special_tokens=False)
        res = generate(self.model, self.hook, self.perception(), frames, prompt, artifact=self.e2e, eos_ids=[end],
                       max_new_tokens=2048)
        calls = [dict(call=r['call'], response=r.get('response', ''),
                      fields={} if not r['served'] or r.get('kind') == 'error' else {'value': FIELDS[r['family']]})
                 for r in res['hook']['records']]
        text = res['text']
        return dict(text=text, answer=text.rpartition('</tool_response>')[2].replace('<|im_end|>', '').strip(),
                    calls=calls, finish=res['finish'], audit=res['audit'])


def make_reader(workdir):
    return B04TinyReader(workdir)


def write_items(path, frames_dir):
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for q in PROGRAMS:
        f = frames_dir / f'{q}.npy'
        np.save(f, np.zeros((32, 4), np.float32))
        rows.append(dict(id=q, type=q, frames=str(f), question=q))
    Path(path).write_text(''.join(json.dumps(r) + '\n' for r in rows))
