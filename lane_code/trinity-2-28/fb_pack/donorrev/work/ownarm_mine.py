"""Own arm with the donor attached equals the own arm without it: decode, two native steps, optimizer state."""
import hashlib, json, os, sys, tempfile, types
from pathlib import Path
import numpy as np
import torch

W = Path(__file__).resolve().parent; T = W / 'new'
os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
out = W / 'ownarm'; out.mkdir(exist_ok=True); os.environ['LANE_TEST_OUTPUT'] = str(out); tempfile.tempdir = str(out)
torch.set_num_threads(8)
from tests.test_carrier_c1_final import final_fixture
from tests.test_tower_read import tower_batch
from student_pilot import scale_donor as D, carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups, RECIPE
from student_pilot.carrier_c1_decode import HeadState
from student_pilot.p3_provenance import digest, file_pin


def h(v):
    v = v.detach().contiguous()
    return hashlib.sha256(v.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()


def arm(variant):
    torch.manual_seed(0)
    m, b, t = final_fixture(); b.update(tower_batch()); depth = m.auxiliary_heads.depth
    depth.model.visual.requires_grad_(False)
    if variant:
        root = Path(tempfile.mkdtemp(prefix='src_', dir=out)); torch.save(m.auxiliary_heads.state_dict(), root / 'heads.pt')
        (root / 'artifact.json').write_text(json.dumps(dict(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm', step=400, heads=file_pin(root / 'heads.pt'))))
        D.attach(m, dict(schema=D.SCHEMA, checkpoint=file_pin(root / 'artifact.json'), fov_source=variant,
                         visual_sha256=D.visual_identity(depth.model.visual), feature_contract_sha256=digest(D.feature_contract(depth))))
    torch.manual_seed(1)
    res = {}
    m.eval()
    with torch.no_grad():
        hid = m.hidden(b); own = HeadState(m, b, hid)
        res['own0'] = [h(torch.as_tensor(own.pose9)), h(torch.as_tensor(own.depth(4, [[100, 900], [500, 500]])))]

    class Rows:
        def count(self, s): return 1
        def get(self, s, i): return {k: v for k, v in b.items() if isinstance(v, torch.Tensor)}, t, {}
    m.train()
    opt = torch.optim.AdamW(parameter_groups(m), weight_decay=RECIPE['weight_decay'])
    for s in (1, 2):
        run.optimize_step(m, opt, Rows(), [('pose', [0]), ('vqa', [0])], 0, torch.device('cpu'), s, distributed=False)
    res['state'] = {k: h(v) for k, v in m.state_dict().items() if not k.startswith('auxiliary_heads.scale_donor.')}
    res['opt'] = [h(v) for g in opt.param_groups for p in g['params'] for v in opt.state[p].values() if isinstance(v, torch.Tensor)]
    res['rng'] = h(torch.get_rng_state())
    m.eval()
    with torch.no_grad():
        hid = m.hidden(b); own = HeadState(m, b, hid)
        res['own2'] = [h(torch.as_tensor(own.pose9)), h(torch.as_tensor(own.depth(4, [[100, 900], [500, 500]])))]
    return res


base = arm(None)
diffs = {}
for v in ('V1', 'V2'):
    r = arm(v)
    diffs[v] = [k for k in base if base[k] != r[k]] + [f'state:{k}' for k in base['state'] if base['state'][k] != r['state'].get(k)]
print('own arm with donor == without donor:', diffs)
(W / 'OWNARM_MINE.json').write_text(json.dumps(dict(status='PASS' if not any(diffs.values()) else 'FAIL', diffs=diffs,
                                                    state_tensors=len(base['state']), optimizer_tensors=len(base['opt'])), indent=1))
