"""Native wrap_model (FSDP FULL_SHARD, use_orig_params, ignored replicated heads) with an attached donor; fake 2-rank PG."""
import json, os, sys, tempfile, types
from pathlib import Path
import torch, torch.distributed as dist

W = Path(__file__).resolve().parent; T = W / 'new'
os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
out = W / 'fsdp'; out.mkdir(exist_ok=True); os.environ['LANE_TEST_OUTPUT'] = str(out); tempfile.tempdir = str(out)
torch.set_num_threads(8)
from torch.testing._internal.distributed.fake_pg import FakeStore
dist.init_process_group('fake', store=FakeStore(), rank=0, world_size=2)
from tests.test_carrier_c1_final import final_fixture
from tests.test_tower_read import tower_state, tower_batch
from student_pilot import scale_donor as D, carrier_c1_run as run, full_ft
from student_pilot.carrier_c1 import parameter_groups, RECIPE
from student_pilot.p3_provenance import digest, file_pin
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

fail = []
for variant in ('V1', 'V2'):
    m, b, t = final_fixture(); b.update(tower_batch()); depth = m.auxiliary_heads.depth
    depth.model.visual.requires_grad_(False)
    root = Path(tempfile.mkdtemp(prefix='src_', dir=out)); torch.save(m.auxiliary_heads.state_dict(), root / 'heads.pt')
    (root / 'artifact.json').write_text(json.dumps(dict(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm', step=544, heads=file_pin(root / 'heads.pt'))))
    cfg = dict(schema=D.SCHEMA, checkpoint=file_pin(root / 'artifact.json'), fov_source=variant,
               visual_sha256=D.visual_identity(depth.model.visual), feature_contract_sha256=digest(D.feature_contract(depth)))
    donor = D.attach(m, cfg)
    with torch.no_grad(): g0 = donor(b, tower_state()).clone()
    pins0 = D.tensor_pins(donor.state_dict())
    m.train()
    wrapped = run.wrap_model(m, torch.device('cpu'), mixed_precision=True)
    flat = [n for n, p in wrapped.named_parameters() if 'scale_donor' in n and (p.requires_grad or type(p).__name__ == 'FlatParameter')]
    if flat: fail.append(f'{variant}: donor parameter flattened/trainable under FSDP {flat[:3]}')
    ignored = getattr(wrapped, '_ignored_params', set())
    if not all(p in ignored for p in donor.parameters()): fail.append(f'{variant}: donor not an ignored replicated state')
    groups = parameter_groups(wrapped, **run.gx_recipe(m))
    gid = {id(p) for g in groups for p in g['params']}
    if gid & ({id(p) for p in donor.parameters()} | {id(p) for p in depth.model.visual.parameters()}):
        fail.append(f'{variant}: donor/visual in FSDP optimizer groups')
    trn = [n for n, _ in full_ft.named_trainable(wrapped) if 'scale_donor' in n]
    if trn: fail.append(f'{variant}: donor in named_trainable (resume shards) {trn[:3]}')
    if any('scale_donor' in n for n, _ in full_ft.named_buffers(wrapped)):
        print(variant, 'note: donor buffers are in resume buffers')
    wd = {g['name']: g.get('weight_decay', RECIPE['weight_decay']) for g in groups}
    wrapped.train()
    if donor.training or donor.visual.training: fail.append(f'{variant}: wrapped.train() put donor/visual in train mode')
    with torch.no_grad(): g1 = wrapped.auxiliary_heads.scale_donor(b, tower_state())
    if not torch.equal(g0, g1): fail.append(f'{variant}: donor grid changed after FSDP wrap')
    if D.tensor_pins(donor.state_dict()) != pins0: fail.append(f'{variant}: donor tensors changed by wrap')
    print(variant, 'groups', {g['name']: len(g['params']) for g in groups}, 'wd', wd, 'donor params', len(list(donor.parameters())),
          'fsdp units', sum(isinstance(x, FSDP) for x in wrapped.modules()))
print('PASS' if not fail else 'FAIL', fail)
(W / 'FSDP_MINE.json').write_text(json.dumps(dict(status='PASS' if not fail else 'FAIL', failures=fail), indent=1))
