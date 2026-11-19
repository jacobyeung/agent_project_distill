"""Separate-runtime reader per READER_REQUEST.md, built the way mdg_runtime.load_runtime builds its model.

Uses the step-3 donor export from resume_check (resume_new_mv08jzq3/run_donor/m3). Constructs CarrierC1 on a
fresh (differently seeded) base, casts base params to bf16, runs full_ft.load_export, then follows the documented
order: attach -> torch.load -> pop/compare -> verify_export -> strict load. Records where it fails and whether
loading+freezing the private visual from heads.pt before attach is sufficient.
Usage: python reader_check.py <tree>
"""
import copy, json, os, sys, tempfile, types
from pathlib import Path

W = Path(__file__).resolve().parent; NAME = sys.argv[1]; T = W / NAME
R = W / 'resume_new_mv08jzq3'; M3 = R / 'run_donor/m3'
OUT = Path(tempfile.mkdtemp(prefix='reader_' + NAME + '_', dir=W))
os.environ.update(TMPDIR=str(OUT), CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
tempfile.tempdir = str(OUT); os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
import torch
torch.set_num_threads(8)
from transformers import Qwen3_5ForConditionalGeneration
from tests.test_carrier_c1_final import final_fixture
from tests.test_carrier_c1 import Tokenizer
from student_pilot import carrier_c1_run as run, scale_donor as D, full_ft
from student_pilot.camera_targets import carrier_id
from student_pilot.p3_provenance import load

FX, _, _ = final_fixture()
receipt = load(R / 'prep_donor/receipt.json'); artifact = load(M3 / 'artifact.json')
BINDING = receipt['scale_donor']
tok = Tokenizer(); tok.get_vocab = lambda: {'fixture': 10, '<|fim_middle|>': 5}
VIS = 'depth.model.visual.'

def runtime_model():
    torch.manual_seed(1234)
    base = Qwen3_5ForConditionalGeneration(copy.deepcopy(FX.config)).float()
    model = run.CarrierC1(base, receipt['camera'], receipt['depth'], carrier_id(tok), receipt['carrier_placement'],
                          receipt['training_mode'], receipt['depth_enabled'], receipt['recipe'],
                          receipt.get('skip_unsupervised_lm'), receipt.get('frame_layout', 'spread'),
                          receipt.get('depth_fov_source', 'private'))
    for _, p in full_ft.base_parameters(model):
        p.data = p.data.to(torch.bfloat16)
    full_ft.load_export(model, M3 / 'full_weights')
    return model

def documented(model):
    D.attach(model, BINDING)
    heads = torch.load(M3 / 'heads.pt', map_location='cpu', weights_only=True)
    metadata = heads.pop('_scale_donor', None)
    if metadata != artifact.get('scale_donor'):
        raise ValueError('Scale donor artifact/head metadata differs')
    D.verify_export(model, heads, metadata)
    model.auxiliary_heads.load_state_dict(heads, strict=True)
    return heads

def attempt(prep):
    model = runtime_model()
    vis = model.auxiliary_heads.depth.model.visual
    state = dict(visual_requires_grad=any(p.requires_grad for p in vis.parameters()))
    try:
        prep(model)
        heads = documented(model)
        live = model.auxiliary_heads.state_dict()
        state.update(ok=True, heads_equal=all(torch.equal(live[k], v) for k, v in heads.items()), n=len(heads))
    except Exception as e:  # noqa: BLE001
        state.update(ok=False, error=type(e).__name__, message=str(e)[:160])
    return state

def from_heads(freeze):
    def prep(model):
        heads = torch.load(M3 / 'heads.pt', map_location='cpu', weights_only=True)
        vis = model.auxiliary_heads.depth.model.visual
        vis.load_state_dict({k[len(VIS):]: v for k, v in heads.items() if k.startswith(VIS)}, strict=True)
        if freeze:
            vis.requires_grad_(False)
    return prep

cases = dict(
    literal_doc=attempt(lambda m: None),
    frozen_only=attempt(lambda m: m.auxiliary_heads.depth.model.visual.requires_grad_(False)),
    visual_from_heads_unfrozen=attempt(from_heads(False)),
    visual_from_heads_frozen=attempt(from_heads(True)),
)
ok = (not cases['literal_doc']['ok'] and not cases['frozen_only']['ok']
      and not cases['visual_from_heads_unfrozen']['ok'] and cases['visual_from_heads_frozen'].get('heads_equal'))
res = dict(tree=NAME, export=str(M3), cases=cases,
           finding='documented order fails unless the private visual is loaded from heads.pt and frozen before attach' if ok else 'unexpected')
(W / f'READER_{NAME}.json').write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
