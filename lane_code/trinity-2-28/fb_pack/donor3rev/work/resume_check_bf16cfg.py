"""S1: a donor-prepared leg resumes from its own checkpoint under the same binding; a pre-donor one refuses.

Native chain: prepare -> prepared -> load_model (attaches the donor from the receipt) -> 2 optimize_step ->
rotating checkpoint -> fresh load_model -> restore -> 1 more step, compared bit-for-bit with an
uninterrupted 3-step reference. Only stream IO (database rows, student registry), collectives, admission
`validate` and `from_pretrained` (tiny native base) are substituted.
Usage: python resume_check.py <tree>  ->  RESUME_<tree>.json
"""
import copy, hashlib, json, os, sys, tempfile, types
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

W = Path(__file__).resolve().parent; NAME = sys.argv[1]; T = W / NAME
OUT = Path(tempfile.mkdtemp(prefix='resume_bf16cfg_' + NAME + '_', dir=W)); 
os.environ.update(LANE_TEST_OUTPUT=str(OUT), TMPDIR=str(OUT), CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
tempfile.tempdir = str(OUT); os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
import numpy as np
import torch
import torch.distributed as dist
torch.set_num_threads(8)
from safetensors.torch import save_file
from transformers import Qwen3_5ForConditionalGeneration
from tests.test_carrier_c1_final import final_fixture
from tests.test_carrier_c1 import Tokenizer
from student_pilot import carrier_c1_run as run, scale_donor as D, full_ft
from student_pilot.carrier_c1 import parameter_groups, RECIPE
from student_pilot.p3_provenance import digest, file_pin, load, sha256, write
from student_pilot.trace_version import bind, metadata

fails, notes = [], {}
def need(ok, msg):
    if not ok:
        fails.append(msg)
    return bool(ok)

def raises(pattern, fn, *a, **k):
    try:
        fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        import re
        return dict(raised=type(e).__name__, message=str(e)[:200], matches=bool(re.search(pattern, str(e))))
    return dict(raised=None, matches=False)

FX, BATCH, TARGETS = final_fixture()
BASE_CONFIG = copy.deepcopy(FX.config)
# Match the config fields that from_pretrained(dtype=bf16, attn_implementation='sdpa') and mdg_runtime._empty_base set.
for _item in (BASE_CONFIG, BASE_CONFIG.text_config, BASE_CONFIG.vision_config):
    _item._attn_implementation = 'sdpa'
    _item.dtype = torch.bfloat16
DEPTH = dict(weight=.05, d_proj=16, mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1, 2, 3])
CAMERA = copy.deepcopy(FX.auxiliary_heads.pose.settings)
COMMIT = 'f' * 40

def tiny_base(*a, **k):
    torch.manual_seed(31)
    return Qwen3_5ForConditionalGeneration(copy.deepcopy(BASE_CONFIG)).float()

tok = Tokenizer(); tok.get_vocab = lambda: {'fixture': 10, '<|fim_middle|>': 5}
PROC = SimpleNamespace(tokenizer=tok, video_processor=SimpleNamespace(image_mean=[.5] * 3, image_std=[.25] * 3),
                       _routing_tokens=dict(ids={'fixture': 10}, constituents={'fixture': [10]}))

def collectives():
    s = ExitStack()
    for n, v in (('get_rank', 0), ('get_world_size', 1), ('get_backend', 'gloo')):
        s.enter_context(mock.patch.object(dist, n, return_value=v))
    for n in ('barrier', 'broadcast', 'broadcast_object_list'):
        s.enter_context(mock.patch.object(dist, n))
    s.enter_context(mock.patch.object(dist, 'all_gather_object', side_effect=lambda o, v, **kw: o.__setitem__(0, v)))
    return s

def io_mocks():
    s = ExitStack()
    conn = mock.MagicMock(); conn.__enter__.return_value = conn
    conn.execute.side_effect = lambda q: SimpleNamespace(fetchone=lambda: (321152, 0, 321151)) if 'count(*)' in q else []
    s.enter_context(mock.patch.object(run, 'validate'))
    s.enter_context(mock.patch.object(run, 'authenticate', return_value=COMMIT))
    s.enter_context(mock.patch.object(run, 'connect', return_value=conn))
    s.enter_context(mock.patch.object(run.routing, 'load_exclusions', side_effect=lambda pin: {'heldout/scene'} if pin else set()))
    s.enter_context(mock.patch('student_pilot.students.get_student',
                               return_value=dict(snapshot=IN / 'snapshot', config_sha256=SNAP_SHA)))
    s.enter_context(mock.patch.object(Qwen3_5ForConditionalGeneration, 'from_pretrained', side_effect=tiny_base))
    return s

# ---- pinned inputs -------------------------------------------------------------------------------
IN = OUT / 'inputs'; IN.mkdir()
stage1_src, _, _ = final_fixture()
sd = stage1_src.auxiliary_heads.depth; torch.manual_seed(9)
with torch.no_grad():
    for p in sd.auxiliary_heads.camera.point_depth.parameters():
        p.normal_(std=.2)
save_file({k: v.detach().clone().contiguous() for k, v in sd.model.visual.state_dict().items()}, str(IN / 'encoder.safetensors'))
save_file({'camera.point_depth.' + k: v.detach().clone().contiguous() for k, v in sd.auxiliary_heads.camera.point_depth.state_dict().items()},
          str(IN / 'heads.safetensors'))
write(IN / 'stage1.json', dict(schema='p3-head-artifact-v1', feature_backing='decoupled_vc', weights=file_pin(IN / 'heads.safetensors'),
                               encoder_copy=dict(weights=file_pin(IN / 'encoder.safetensors')), camera=dict(point_depth=DEPTH)))
(IN / 'snapshot').mkdir(); (IN / 'snapshot/config.json').write_text(BASE_CONFIG.to_json_string())
SNAP_SHA = sha256(IN / 'snapshot/config.json')
write(IN / 'model.json', dict(kind='base', base_identity='fixture', root=str(IN / 'snapshot'), files={'config.json': SNAP_SHA}))
write(IN / 'division.json', dict(train_scenes=['d/s'], heldout_scenes=[]))
(IN / 'pose.db').write_bytes(b'fixture-db')
write(IN / 'pose.json', dict(schema='decoupled-v-preparation-v1', count=321152, database=file_pin(IN / 'pose.db'),
                             model=file_pin(IN / 'model.json'), inputs=dict(division=file_pin(IN / 'division.json')),
                             settings=dict(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames',
                                           camera=dict(CAMERA, point_depth=DEPTH))))
write(IN / 'exclusions.json', ['heldout/scene'])
write(IN / 'code.json', dict(schema='fixture-no-seal'))

def base_cfg(prep_dir, donor=None):
    cfg = dict(schema='carrier-c1-run-v1', trace_program_version='3.13', base_identity='fixture', training_mode='final',
               carrier_placement=FX.carrier_placement, recipe=copy.deepcopy(FX.recipe), depth_enabled=True,
               depth_fov_source='pose_head', depth_init=file_pin(IN / 'stage1.json'), streams=dict(pose=file_pin(IN / 'pose.json')),
               exclusions=file_pin(IN / 'exclusions.json'), preparation_output=str(prep_dir), code=file_pin(IN / 'code.json'))
    if donor is not None:
        cfg['scale_donor'] = donor
    return cfg

def prepare_leg(cfg):
    Path(cfg['preparation_output']).mkdir(parents=True, exist_ok=True)
    with io_mocks():
        receipt = run.prepare(cfg)
    cfg = dict(cfg, preparation=file_pin(Path(cfg['preparation_output']) / 'receipt.json'))
    with io_mocks():
        prepared, manifest = run.prepared(cfg)
    return cfg, receipt, prepared, manifest

def build(cfg, prepared, manifest):
    torch.manual_seed(RECIPE['seed']); np.random.seed(RECIPE['seed'])
    with io_mocks():
        model = run.load_model(manifest, prepared, PROC)
    bind(model, metadata(cfg), cfg)
    model.train()
    return model, torch.optim.AdamW(parameter_groups(model), weight_decay=RECIPE['weight_decay'])

class Rows:
    def count(self, s): return 1
    def get(self, s, i): return {k: v for k, v in BATCH.items() if isinstance(v, torch.Tensor)}, TARGETS, {}

def step(model, opt, n):
    return run.optimize_step(model, opt, Rows(), [('pose', [0])], 0, torch.device('cpu'), n, distributed=False)[0]

def bound_of(cfg):
    return dict(config_sha256=run.identity(cfg), preparation=cfg['preparation'], trainer_commit=COMMIT, world_size=1)

def state_hash(model, opt):
    named = dict(full_ft.named_trainable(model))
    t = {n: hashlib.sha256(p.detach().contiguous().view(-1).view(torch.uint8).numpy().tobytes()).hexdigest() for n, p in named.items()}
    o = {}
    for n, p in named.items():
        for k, v in opt.state.get(p, {}).items():
            o[n + '/' + k] = hashlib.sha256(v.detach().contiguous().view(-1).view(torch.uint8).numpy().tobytes()).hexdigest()
    return t, o

# ---- donor source: a native C1 export at step 400 --------------------------------------------------
src_cfg, _, src_prep, src_manifest = prepare_leg(base_cfg(OUT / 'prep_src'))
src_model, _ = build(src_cfg, src_prep, src_manifest)
need(not any(p.requires_grad for p in src_model.auxiliary_heads.depth.model.visual.parameters()), 'depth_init did not freeze visual')
with torch.no_grad():
    g = torch.Generator().manual_seed(123)
    for p in list(src_model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.parameters()) + list(src_model.auxiliary_heads.depth.fov.parameters()):
        p.add_(torch.randn(p.shape, generator=g) * .05)
    src_model.auxiliary_heads.depth.auxiliary_heads.frame_queries.add_(torch.randn(src_model.auxiliary_heads.depth.auxiliary_heads.frame_queries.shape, generator=g) * .05)
with collectives(), mock.patch('student_pilot.fsdp_training.publication_state', side_effect=lambda w: w.state_dict()):
    run.export(OUT / 'm400', src_model, src_model, dict(base_identity='fixture', trace_program_version='3.13'), 400)
SRC_PIN = file_pin(OUT / 'm400/artifact.json'); SRC_HEADS = load(OUT / 'm400/artifact.json')['heads']
src_bytes = {p: sha256(p) for p in (OUT / 'm400/artifact.json', OUT / 'm400/heads.pt')}
src_state = torch.load(OUT / 'm400/heads.pt', weights_only=True)
depth = src_model.auxiliary_heads.depth
BINDING = dict(schema=D.SCHEMA, checkpoint=SRC_PIN, fov_source='V1', visual_sha256=D.visual_identity(depth.model.visual),
               feature_contract_sha256=digest(D.feature_contract(depth)))
del src_model

def donor_matches_source(model):
    donor = model.auxiliary_heads.scale_donor
    for k, v in donor.state_dict().items():
        sk = ('depth.auxiliary_heads.camera.point_depth.' + k[len('point_depth.'):] if k.startswith('point_depth.') else
              'depth.auxiliary_heads.frame_queries' if k == 'frame_queries' else 'depth.' + k)
        if not torch.equal(v, src_state[sk]):
            return False
    return True

# ---- donor leg: prepare with donor --------------------------------------------------------------------
cfg, receipt, prepared, manifest = prepare_leg(base_cfg(OUT / 'prep_donor', BINDING))
need(receipt.get('scale_donor') == BINDING, 'prepare did not record the donor binding')
need(load(cfg['preparation']['path']).get('scale_donor') == BINDING, 'receipt.json lacks the donor binding')
bound = bound_of(cfg)

# Uninterrupted reference: 3 steps.
ref, ref_opt = build(cfg, prepared, manifest)
need(hasattr(ref.auxiliary_heads, 'scale_donor'), 'load_model did not attach the donor from the receipt')
pins0 = ref.auxiliary_heads.scale_donor.initial_pins
for n in (1, 2, 3):
    step(ref, ref_opt, n)
ref_hash = state_hash(ref, ref_opt)
need(D.tensor_pins(ref.auxiliary_heads.scale_donor.state_dict()) == pins0, 'reference: donor changed in training')

# Interrupted leg: 2 steps, checkpoint, fresh process-equivalent reload, restore, step 3.
leg, leg_opt = build(cfg, prepared, manifest)
need(donor_matches_source(leg), 'donor tensors differ from the pinned source export')
need(leg.auxiliary_heads.scale_donor.initial_pins == pins0, 'donor pins differ between loads')
live0 = D.tensor_pins(leg.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.state_dict())
for n in (1, 2):
    step(leg, leg_opt, n)
need(live0 != D.tensor_pins(leg.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.state_dict()), 'live head did not train')
output = OUT / 'run_donor'
with collectives():
    run.bind_output(output, bound)
    ck = run.checkpoint(output / 'checkpoint_000002', leg, leg_opt, bound, 2, rotate=True)
    latest = run.latest_resume(output, bound)
need(latest == ck, 'latest_resume did not select the donor checkpoint')
manifest_ck = load(ck['path'])
need(not any('scale_donor' in name for name in manifest_ck['files']), 'checkpoint stored donor tensors')
del leg, leg_opt
fresh, fresh_opt = build(cfg, prepared, manifest)
with collectives():
    restored = run.restore(latest, fresh, fresh_opt, bound)
    run.bind_output(output, bound, resume=True)
need(restored == 2, f'restore returned {restored}')
step(fresh, fresh_opt, 3)
res_hash = state_hash(fresh, fresh_opt)
need(res_hash[0] == ref_hash[0], 'resumed trainable tensors differ from uninterrupted run')
need(res_hash[1] == ref_hash[1], 'resumed optimizer state differs from uninterrupted run')
need(D.tensor_pins(fresh.auxiliary_heads.scale_donor.state_dict()) == pins0, 'resumed donor changed')
need(donor_matches_source(fresh), 'resumed donor differs from source')
need({p: sha256(p) for p in src_bytes} == src_bytes, 'donor source bytes changed')
# Continue under the same binding: export step 3 and read it back through the pinned reader.
with collectives(), mock.patch('student_pilot.fsdp_training.publication_state', side_effect=lambda w: w.state_dict()):
    run.export(output / 'm3', fresh, fresh, dict(base_identity='fixture', trace_program_version='3.13', scale_donor=BINDING), 3)
art = load(output / 'm3/artifact.json')
need(art.get('scale_donor', {}).get('settings') == BINDING, 'export metadata binding differs')
reader, _ = build(cfg, prepared, manifest)
run.load_artifact(reader, file_pin(output / 'm3/artifact.json'))
need(D.tensor_pins(reader.auxiliary_heads.scale_donor.state_dict()) == pins0, 'reader donor differs')

# ---- pre-donor leg under the donor binding -------------------------------------------------------------
old_cfg, old_receipt, old_prepared, old_manifest = prepare_leg(base_cfg(OUT / 'prep_old'))
need('scale_donor' not in old_receipt, 'pre-donor receipt has a donor')
old, old_opt = build(old_cfg, old_prepared, old_manifest)
need(not hasattr(old.auxiliary_heads, 'scale_donor'), 'pre-donor model has a donor')
for n in (1, 2):
    step(old, old_opt, n)
old_bound = bound_of(old_cfg); old_out = OUT / 'run_old'
with collectives():
    run.bind_output(old_out, old_bound)
    old_ck = run.checkpoint(old_out / 'checkpoint_000002', old, old_opt, old_bound, 2, rotate=True)
refusals = {}
with io_mocks():
    refusals['prepared_old_receipt'] = raises('C1 preparation frame layout/LM lever differs', run.prepared, dict(cfg, preparation=old_cfg['preparation']))
donor_model, donor_opt = build(cfg, prepared, manifest)
with collectives():
    refusals['restore'] = raises('C1 resume binding differs', run.restore, old_ck, donor_model, donor_opt, bound)
    refusals['latest_resume'] = raises('No complete C1 resume state', run.latest_resume, old_out, bound)
    refusals['bind_output'] = raises('Resume output belongs to another run', run.bind_output, old_out, bound, resume=True)
    # Control: the pre-donor leg still resumes under its own binding.
    refusals['old_leg_own_binding_restores'] = dict(step=run.restore(old_ck, old, old_opt, old_bound))
for k, v in refusals.items():
    if k != 'old_leg_own_binding_restores':
        need(v['matches'], f'pre-donor refusal {k}: {v}')
need(refusals['old_leg_own_binding_restores']['step'] == 2, 'pre-donor leg failed under its own binding')
need(bound['config_sha256'] != old_bound['config_sha256'], 'donor does not change the config identity')

out = dict(tree=NAME, status='PASS' if not fails else 'FAIL', failures=fails, checkpoint=ck, restored_step=restored,
           trainable_tensors=len(ref_hash[0]), optimizer_tensors=len(ref_hash[1]), donor_tensors=len(pins0),
           refusals=refusals, source_bytes={str(k): v for k, v in src_bytes.items()},
           inputs={str(p): sha256(p) for p in (Path(__file__), T / 'student_pilot/scale_donor.py', T / 'student_pilot/carrier_c1_run.py')})
(W / f'RESUME_BF16CFG_{NAME}.json').write_text(json.dumps(out, indent=1, default=str))
print(NAME, out['status'], fails, json.dumps(refusals)[:900])
