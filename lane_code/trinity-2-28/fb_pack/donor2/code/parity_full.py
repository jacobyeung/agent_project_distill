"""Field-absent parity: decode both arms, groups, handover tables, two native steps, export and reload."""
import hashlib, json, os, sys, tempfile, types
from contextlib import ExitStack
from pathlib import Path
from unittest import mock
import numpy as np
import torch

W = Path(__file__).resolve().parents[1]; T = W / 'work' / sys.argv[1]
os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
out = W / 'work' / ('parity_' + sys.argv[1]); out.mkdir(exist_ok=True)
os.environ['LANE_TEST_OUTPUT'] = str(out); tempfile.tempdir = str(out)
torch.set_num_threads(8)
from tests.test_carrier_c1_final import final_fixture
from tests.test_tower_read import tower_state, tower_batch
from student_pilot import carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups, RECIPE
from student_pilot.carrier_c1_decode import HeadState
from student_pilot.r1_handover import trainable_group_table, compare_configs
from student_pilot.p3_provenance import file_pin


def h(v):
    if isinstance(v, torch.Tensor): v = v.detach().contiguous().reshape(-1).view(torch.uint8).numpy() if v.numel() else v.detach().numpy()
    return hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()


def decode(m, b):
    m.eval()
    with torch.no_grad():
        hidden = m.hidden(b)
        own = HeadState(m, b, hidden); tower = HeadState(m, b, hidden, pose_source='tower', tower_state=tower_state())
        pts = [[200, 300], [500, 500], [990, 10]]
        r = dict(hidden=h(hidden), own_pose=h(own.pose9), own_depth=h(own.depth(2, pts)), own_read=h(own.read_depth(2, [400, 600], own.pose9[1, 7:9])['stencil_depth']),
                 tower_pose=h(tower.pose9), tower_scale=float(tower.tower_scale), tower_depth=h(tower.depth(2, pts)),
                 tower_read=h(tower.read_depth(2, [400, 600], tower.pose9[1, 7:9])['stencil_depth']),
                 tower_depth_head=type(tower.depth_head).__name__)
    return r


res = {}
m, b, t = final_fixture(); b.update(tower_batch()); m.auxiliary_heads.depth.model.visual.requires_grad_(False)
res['decode0'] = decode(m, b)
groups = parameter_groups(m)
names = {id(p): n for n, p in m.named_parameters()}
res['groups'] = [dict(name=g['name'], lr=g['lr'], params=[names[id(p)] for p in g['params']]) for g in groups]
res['handover_table'] = h(np.frombuffer(json.dumps(trainable_group_table({}, m), sort_keys=True, default=str).encode(), np.uint8))
compare_configs({}, {})
res['state0'] = {k: h(v) for k, v in m.state_dict().items()}


class Rows:
    def count(self, s): return 1
    def get(self, s, i): return {k: v for k, v in b.items() if isinstance(v, torch.Tensor)}, t, {}


m.train()
opt = torch.optim.AdamW(groups, weight_decay=RECIPE['weight_decay'])
for s in (1, 2):
    run.optimize_step(m, opt, Rows(), [('pose', [0])], 0, torch.device('cpu'), s, distributed=False)
res['state2'] = {k: h(v) for k, v in m.state_dict().items()}
res['opt2'] = {f'{i}.{j}.{k}': h(v) for i, g in enumerate(opt.param_groups) for j, p in enumerate(g['params'])
               for k, v in opt.state[p].items() if isinstance(v, torch.Tensor)}
res['decode2'] = decode(m, b)
root = out / 'export'
with ExitStack() as st:
    st.enter_context(mock.patch('student_pilot.fsdp_training.publication_state', side_effect=lambda w: w.state_dict()))
    for n_, v_ in (('get_rank', 0), ('get_world_size', 1)):
        st.enter_context(mock.patch.object(run.dist, n_, return_value=v_))
    st.enter_context(mock.patch.object(run.dist, 'barrier'))
    import uuid
    root = out / ('export_' + uuid.uuid4().hex)
    run.export(root, m, m, dict(base_identity='fixture', trace_program_version='3.13'), 2)
heads = torch.load(root / 'heads.pt', weights_only=True)
res['export_heads'] = {k: (h(v) if isinstance(v, torch.Tensor) else repr(v)) for k, v in heads.items()}
art = json.loads((root / 'artifact.json').read_text())
res['artifact_keys'] = sorted(art)
fresh, _, _ = final_fixture(); fresh.auxiliary_heads.depth.model.visual.requires_grad_(False)
run.load_artifact(fresh, file_pin(root / 'artifact.json'))
res['reloaded'] = {k: h(v) for k, v in fresh.state_dict().items()}
res['decode_reloaded'] = decode(fresh, b)
inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),*T.glob('student_pilot/*.py'),*T.glob('tests/test_carrier_c1*.py'),T/'tests/test_tower_read.py']}
(W / 'out' / ('PARITY_' + sys.argv[1] + '.json')).write_text(json.dumps(dict(input_sha256=inputs,outputs=res,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/parity_full.py '+sys.argv[1]),indent=2)+'\n')
print(sys.argv[1], len(res['state2']), 'tensors')
