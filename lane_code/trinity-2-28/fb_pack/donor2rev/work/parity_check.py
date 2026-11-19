"""Field-absent parity: identical native chain without scale_donor; hashes with run-root paths normalized.

Usage: python parity_check.py <tree>  ->  PARITY_<tree>.json ; compare base vs new with parity_compare.py
"""
import copy, hashlib, json, os, sys, tempfile, types
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

W = Path(__file__).resolve().parent; NAME = sys.argv[1]; T = W / NAME
OUT = W / 'parity_run'; OUT.mkdir(exist_ok=False)  # same absolute path for every tree; renamed afterwards
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
from tests.test_tower_read import tower_state, tower_batch
from student_pilot import carrier_c1_run as run, full_ft
from student_pilot.carrier_c1 import parameter_groups, RECIPE
from student_pilot.carrier_c1_decode import HeadState
from student_pilot.r1_handover import trainable_group_table
from student_pilot.p3_provenance import file_pin, load, sha256, write
from student_pilot.trace_version import bind, metadata

R = {}
norm = lambda s: s.replace(str(OUT), '<OUT>')
jh = lambda v: hashlib.sha256(norm(json.dumps(v, sort_keys=True, default=str)).encode()).hexdigest()
th = lambda t: hashlib.sha256(t.detach().contiguous().view(-1).view(torch.uint8).numpy().tobytes()).hexdigest()
ah = lambda a: hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
fh = lambda p: hashlib.sha256(norm(Path(p).read_text()).encode()).hexdigest()

FX, BATCH, TARGETS = final_fixture()
BASE_CONFIG = copy.deepcopy(FX.config)
DEPTH = dict(weight=.05, d_proj=16, mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1, 2, 3])
CAMERA = copy.deepcopy(FX.auxiliary_heads.pose.settings)
COMMIT = 'f' * 40
def tiny_base(*a, **k):
    torch.manual_seed(31)
    return Qwen3_5ForConditionalGeneration(copy.deepcopy(BASE_CONFIG)).float()
tok = Tokenizer(); tok.get_vocab = lambda: {'fixture': 10, '<|fim_middle|>': 5}
PROC = SimpleNamespace(tokenizer=tok, video_processor=SimpleNamespace(image_mean=[.5] * 3, image_std=[.25] * 3),
                       _routing_tokens=dict(ids={'fixture': 10}, constituents={'fixture': [10]}))
IN = OUT / 'inputs'; IN.mkdir()

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
    s.enter_context(mock.patch('student_pilot.students.get_student', return_value=dict(snapshot=IN / 'snapshot', config_sha256=SNAP)))
    s.enter_context(mock.patch.object(Qwen3_5ForConditionalGeneration, 'from_pretrained', side_effect=tiny_base))
    return s

stage1_src, _, _ = final_fixture(); sd = stage1_src.auxiliary_heads.depth; torch.manual_seed(9)
with torch.no_grad():
    for p in sd.auxiliary_heads.camera.point_depth.parameters():
        p.normal_(std=.2)
save_file({k: v.detach().clone().contiguous() for k, v in sd.model.visual.state_dict().items()}, str(IN / 'encoder.safetensors'))
save_file({'camera.point_depth.' + k: v.detach().clone().contiguous() for k, v in sd.auxiliary_heads.camera.point_depth.state_dict().items()},
          str(IN / 'heads.safetensors'))
write(IN / 'stage1.json', dict(schema='p3-head-artifact-v1', feature_backing='decoupled_vc', weights=file_pin(IN / 'heads.safetensors'),
                               encoder_copy=dict(weights=file_pin(IN / 'encoder.safetensors')), camera=dict(point_depth=DEPTH)))
(IN / 'snapshot').mkdir(); (IN / 'snapshot/config.json').write_text(BASE_CONFIG.to_json_string()); SNAP = sha256(IN / 'snapshot/config.json')
write(IN / 'model.json', dict(kind='base', base_identity='fixture', root=str(IN / 'snapshot'), files={'config.json': SNAP}))
write(IN / 'division.json', dict(train_scenes=['d/s'], heldout_scenes=[])); (IN / 'pose.db').write_bytes(b'fixture-db')
write(IN / 'pose.json', dict(schema='decoupled-v-preparation-v1', count=321152, database=file_pin(IN / 'pose.db'),
                             model=file_pin(IN / 'model.json'), inputs=dict(division=file_pin(IN / 'division.json')),
                             settings=dict(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames',
                                           camera=dict(CAMERA, point_depth=DEPTH))))
write(IN / 'exclusions.json', ['heldout/scene']); write(IN / 'code.json', dict(schema='fixture-no-seal'))
cfg = dict(schema='carrier-c1-run-v1', trace_program_version='3.13', base_identity='fixture', training_mode='final',
           carrier_placement=FX.carrier_placement, recipe=copy.deepcopy(FX.recipe), depth_enabled=True, depth_fov_source='pose_head',
           depth_init=file_pin(IN / 'stage1.json'), streams=dict(pose=file_pin(IN / 'pose.json')), exclusions=file_pin(IN / 'exclusions.json'),
           preparation_output=str(OUT / 'prep'), code=file_pin(IN / 'code.json'))
(OUT / 'prep').mkdir()
with io_mocks():
    receipt = run.prepare(cfg)
cfg['preparation'] = file_pin(OUT / 'prep/receipt.json')
with io_mocks():
    prepared, manifest = run.prepared(cfg)
R['identity'] = run.identity(cfg); R['receipt_json'] = fh(OUT / 'prep/receipt.json'); R['prepared'] = jh(prepared)
R['validate_keys_ok'] = run.validate.__name__

def build():
    import random
    torch.manual_seed(RECIPE['seed']); np.random.seed(RECIPE['seed']); random.seed(RECIPE['seed'])
    with io_mocks():
        m = run.load_model(manifest, prepared, PROC)
    bind(m, metadata(cfg), cfg); m.train()
    return m, torch.optim.AdamW(parameter_groups(m), weight_decay=RECIPE['weight_decay'])

def snap(m, o):
    named = dict(full_ft.named_trainable(m))
    return dict(state={k: th(v) for k, v in m.state_dict().items()},
                optimizer={n + '/' + k: th(v) for n, p in named.items() for k, v in o.state.get(p, {}).items()})

TB = dict(BATCH, **tower_batch())
@torch.no_grad()
def decode(m):
    m.eval(); hidden = m.hidden(TB)
    own = HeadState(m, TB, hidden); tower = HeadState(m, TB, hidden, pose_source='tower', tower_state=tower_state())
    out = dict(hidden=th(hidden), own_pose=ah(own.pose9), own_depth=th(own.depth_map), tower_pose=ah(tower.pose9),
               tower_scale=repr(float(tower.tower_scale)), tower_depth=th(tower.depth_map),
               own_q=ah(own.depth(1, [[200, 300], [700, 100]])), tower_q=ah(tower.depth(1, [[200, 300], [700, 100]])),
               tower_head=type(tower.depth_head).__name__)
    m.train(); return out

class Rows:
    def count(self, s): return 1
    def get(self, s, i): return {k: v for k, v in BATCH.items() if isinstance(v, torch.Tensor)}, TARGETS, {}
def step(m, o, n):
    info = run.optimize_step(m, o, Rows(), [('pose', [0])], 0, torch.device('cpu'), n, distributed=False)[0]
    return {k: repr(v) for k, v in info.items() if k in ('loss', 'stream_means', 'grad_norm')}

m, o = build()
R['has_donor'] = hasattr(m.auxiliary_heads, 'scale_donor')
R['groups'] = [(g['name'], len(g['params']), g.get('lr'), g.get('weight_decay')) for g in o.param_groups]
R['group_names'] = jh([[n for n, p in m.named_parameters() if any(p is q for q in g['params'])] for g in o.param_groups])
R['handover_table'] = jh(trainable_group_table({}, m))
R['init'] = snap(m, o); R['decode0'] = decode(m)
R['steps'] = [step(m, o, n) for n in (1, 2)]
R['after2'] = snap(m, o); R['decode2'] = decode(m)
out_dir = OUT / 'run'
with collectives():
    bound = dict(config_sha256=run.identity(cfg), preparation=cfg['preparation'], trainer_commit=COMMIT, world_size=1)
    run.bind_output(out_dir, bound)
    ck = run.checkpoint(out_dir / 'checkpoint_000002', m, o, bound, 2, rotate=True)
cm = load(ck['path'])
R['checkpoint_files'] = {k: v.get('sha256') for k, v in cm['files'].items()}
R['checkpoint_keys'] = sorted(cm)
f, fo = build()
with collectives():
    R['restored'] = run.restore(ck, f, fo, bound)
R['step3'] = step(f, fo, 3); R['after3'] = snap(f, fo)
with collectives(), mock.patch('student_pilot.fsdp_training.publication_state', side_effect=lambda w: w.state_dict()):
    run.export(out_dir / 'm3', f, f, dict(base_identity='fixture', trace_program_version='3.13'), 3)
R['export_heads'] = sha256(out_dir / 'm3/heads.pt')
R['export_artifact'] = fh(out_dir / 'm3/artifact.json')
R['export_artifact_keys'] = sorted(load(out_dir / 'm3/artifact.json'))
R['export_head_tensors'] = len(torch.load(out_dir / 'm3/heads.pt', weights_only=True))
reader, _ = build()
run.load_artifact(reader, file_pin(out_dir / 'm3/artifact.json'))
R['reader'] = {k: th(v) for k, v in reader.state_dict().items()}
R['decode_reader'] = decode(reader)
R['tensor_counts'] = dict(state=len(R['after3']['state']), optimizer=len(R['after3']['optimizer']))
(W / f'PARITY_{NAME}.json').write_text(json.dumps(R, indent=1, default=str))
OUT.rename(W / f'parity2_{NAME}')
print(NAME, 'done', R['tensor_counts'], R['export_head_tensors'], R['has_donor'])
