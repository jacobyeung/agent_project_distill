"""M4: run READER_REQUEST.md's runtime block verbatim inside the unmodified mdg_runtime.load_runtime.

The function object itself runs (no source rewrite). Substituted: _bundle (returns the native fixture export),
processor_for_receipt (fixture tokenizer), r2_policy.unsupported_entry. Real: _empty_base (from a config.json
written next to the fixture), CarrierC1, routing init, full_ft.load_export, the runtime's own torch.load and strict
head load. The documented block is exec'd at the runtime's torch.load of heads.pt and returns its popped heads, so
runtime line 213 then strict-loads them again.
Usage: python reader_runtime_check.py <tree> <resume_dir> [empty_base=real|train_config]
"""
import copy, json, os, re, shutil, sys, tempfile, types
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from contextlib import ExitStack

W = Path(__file__).resolve().parent; NAME = sys.argv[1]; T = W / NAME; R = W / sys.argv[2]
BASE_MODE = sys.argv[3] if len(sys.argv) > 3 else 'real'
OUT = Path(tempfile.mkdtemp(prefix=f'rt_{NAME}_{BASE_MODE}_', dir=W))
os.environ.update(TMPDIR=str(OUT), CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
tempfile.tempdir = str(OUT); os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
import torch
torch.set_num_threads(8)
from tests.test_carrier_c1 import Tokenizer
from tests.test_carrier_c1_final import final_fixture
from student_pilot import mdg_runtime as runtime, carrier_c1_run as run, scale_donor as D, full_ft
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.p3_provenance import load, sha256

FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
def block(doc):
    text = Path(doc).read_text()
    m = re.search(r'## Separate runtime[^\n]*\n.*?```python\n(.*?)```', text, re.S)
    return m.group(1)
NEW_BLOCK = block(FB / 'donor3/out/READER_REQUEST.md')
OLD_BLOCK = 'from student_pilot import scale_donor\nscale_donor.attach(model, binding)\n' + block(FB / 'donor2/out/READER_REQUEST.md')

M3 = R / 'run_donor/m3'; HEADS = (M3 / 'heads.pt').resolve()
raw_receipt = load(R / 'prep_donor/receipt.json'); ARTIFACT = load(M3 / 'artifact.json')
BINDING = raw_receipt['scale_donor']
FX, _, _ = final_fixture()
assert raw_receipt['recipe'] == FX.recipe and raw_receipt['carrier_placement'] == FX.carrier_placement
RECEIPT = {**raw_receipt, 'align': None, 'init_artifact': None, 'frame_markers': False}
NATIVE = {'trace_program_version': ARTIFACT['trace_program_version']}
ROOT = OUT / 'bundle'; (ROOT / 'base').mkdir(parents=True)
shutil.copyfile(R / 'inputs/snapshot/config.json', ROOT / 'base/config.json')
tok = Tokenizer(); tok.get_vocab = lambda: {'fixture': 10, '<|fim_middle|>': 5}
PROC = SimpleNamespace(tokenizer=tok, video_processor=SimpleNamespace(image_mean=[.5] * 3, image_std=[.25] * 3),
                       _routing_tokens=dict(ids={'fixture': 10}, constituents={'fixture': [10]}))
RAW = torch.load(HEADS, map_location='cpu', weights_only=True)
EXPECTED = {k: v for k, v in RAW.items() if isinstance(v, torch.Tensor)}
VIS = 'depth.model.visual.'
orig_load, orig_export, orig_empty = torch.load, full_ft.load_export, runtime._empty_base

def variant(mode):
    steps, tamper = NEW_BLOCK, None
    def cut(old, new=''):
        nonlocal steps
        assert old in steps, old
        steps = steps.replace(old, new)
    if mode == 'old_order':
        steps = OLD_BLOCK
    elif mode == 'freeze_only':
        cut('visual.load_state_dict({key[len(prefix):]: value for key, value in heads.items()\n'
            '                        if key.startswith(prefix)}, strict=True)\n')
    elif mode == 'load_only':
        cut('visual.requires_grad_(False)\n')
    elif mode == 'non_strict_visual':
        cut('if key.startswith(prefix)}, strict=True)', 'if key.startswith(prefix)}, strict=False)')
    elif mode == 'unmodified_runtime':
        steps = None
    if mode == 'tampered_visual':
        tamper = lambda h: h[next(k for k in h if k.startswith(VIS))].reshape(-1).__setitem__(0, 1.5)
    elif mode == 'missing_visual':
        tamper = lambda h: h.pop(next(k for k in h if k.startswith(VIS)))
    elif mode == 'tampered_donor':
        tamper = lambda h: h[next(k for k in h if k.startswith('scale_donor.point_depth.'))].reshape(-1).__setitem__(0, 1.5)
    elif mode == 'non_strict_visual':
        tamper = lambda h: h.pop(next(k for k in h if k.startswith(VIS)))
    return steps, tamper

def attempt(mode):
    steps, tamper = variant(mode)
    seen = dict(busy=False, block_ran=False)
    def load_export(model, directory):
        vis = model.auxiliary_heads.depth.model.visual
        seen.update(model=model, type_is_CarrierC1=type(model) is CarrierC1,
                    donor_before=hasattr(model.auxiliary_heads, 'scale_donor'),
                    visual_trainable_before=any(p.requires_grad for p in vis.parameters()),
                    visual_dtype=str(next(vis.parameters()).dtype),
                    base_dtype=str(next(p for _, p in full_ft.base_parameters(model)).dtype))
        return orig_export(model, directory)
    def hooked(path, *a, **k):
        if Path(path).resolve() != HEADS:
            return orig_load(path, *a, **k)
        if seen['busy'] or steps is None:
            h = orig_load(path, *a, **k)
            if tamper: tamper(h)
            return h
        seen['busy'] = True
        try:
            ns = dict(torch=torch, heads_path=path, model=seen['model'], artifact=ARTIFACT, binding=BINDING)
            exec(compile(steps, f'<reader-{mode}>', 'exec'), ns)
            seen['block_ran'] = True
            return ns['heads']
        finally:
            seen['busy'] = False
    def empty_base(base_dir):
        if BASE_MODE == 'real':
            return orig_empty(base_dir)
        from transformers import Qwen3_5ForConditionalGeneration
        torch.manual_seed(77)
        return Qwen3_5ForConditionalGeneration(copy.deepcopy(FX.config)).float()
    res = dict(mode=mode)
    try:
        with ExitStack() as s:
            s.enter_context(mock.patch('student_pilot.r2_policy.unsupported_entry'))
            s.enter_context(mock.patch.object(runtime, '_bundle', return_value=(
                ROOT, M3, NATIVE, RECEIPT, {'files': {}}, ARTIFACT, 'fixture-bundle')))
            s.enter_context(mock.patch.object(runtime, '_empty_base', side_effect=empty_base))
            s.enter_context(mock.patch.object(run, 'processor_for_receipt', return_value=PROC))
            s.enter_context(mock.patch.object(full_ft, 'load_export', side_effect=load_export))
            s.enter_context(mock.patch.object(torch, 'load', side_effect=hooked))
            model, _, _ = runtime.load_runtime({'bundle': 'fixture'}, torch.device('cpu'))
        live = model.auxiliary_heads.state_dict()
        donor = model.auxiliary_heads.scale_donor
        res.update(ok=True, block_ran=seen['block_ran'],
                   head_keys_equal=set(live) == set(EXPECTED), n_heads=len(EXPECTED),
                   heads_bytes_equal=D.tensor_pins(live) == D.tensor_pins(EXPECTED),
                   heads_torch_equal=all(torch.equal(live[k], v) for k, v in EXPECTED.items()),
                   visual_identity_matches_binding=D.visual_identity(model.auxiliary_heads.depth.model.visual) == BINDING['visual_sha256'],
                   donor_metadata_equals_artifact=donor.metadata() == ARTIFACT['scale_donor'],
                   trainable_after=sum(p.requires_grad for p in model.parameters()),
                   depth_init_skipped='depth_init' in model.mdg_runtime_report['skipped'],
                   head_tensors_report=model.mdg_runtime_report['head_tensors'])
    except Exception as e:  # noqa: BLE001
        res.update(ok=False, block_ran=seen['block_ran'], error=type(e).__name__, message=str(e)[:220])
    res.update({k: v for k, v in seen.items() if k not in ('model', 'busy')})
    return res

# With the real no_init_weights base, an unrestored visual can hold nonfinite bytes; tensor_pins refuses those first.
UNRESTORED = 'shared visual pin differs|Nonfinite donor tensor'
EXPECT = {'documented': None, 'old_order': 'already frozen', 'freeze_only': UNRESTORED,
          'load_only': 'already frozen', 'tampered_visual': 'shared visual pin differs',
          'missing_visual': 'Missing key', 'non_strict_visual': UNRESTORED,
          'tampered_donor': 'changed since initialization', 'unmodified_runtime': 'Unexpected key'}
cases, fails = {}, []
for mode, pattern in EXPECT.items():
    r = cases[mode] = attempt(mode)
    if not (r['type_is_CarrierC1'] and not r['donor_before'] and r['visual_trainable_before']):
        fails.append(f'{mode}: model not built as the runtime builds it')
    if pattern is None:
        if not (r['ok'] and r['block_ran'] and r['head_keys_equal'] and r['heads_bytes_equal'] and r['heads_torch_equal']
                and r['visual_identity_matches_binding'] and r['donor_metadata_equals_artifact'] and r['trainable_after'] == 0):
            fails.append(f'{mode}: {r}')
    elif r['ok'] or not re.search(pattern, r.get('message', '')):
        fails.append(f'{mode}: expected refusal {pattern!r}, got {r}')
out = dict(tree=NAME, export=str(M3), heads_sha256=sha256(HEADS), empty_base=BASE_MODE,
           status='PASS' if not fails else 'FAIL', failures=fails, cases=cases,
           new_block=NEW_BLOCK, old_block=OLD_BLOCK,
           inputs={str(p): sha256(p) for p in (Path(__file__), T / 'student_pilot/mdg_runtime.py',
                                              T / 'student_pilot/scale_donor.py', FB / 'donor3/out/READER_REQUEST.md')})
(W / f'RUNTIME_{NAME}_{BASE_MODE}.json').write_text(json.dumps(out, indent=1, default=str))
print(NAME, BASE_MODE, out['status'], json.dumps(fails, default=str)[:3000])
for m, r in cases.items():
    print(m, r.get('ok'), r.get('error'), (r.get('message') or '')[:110])
