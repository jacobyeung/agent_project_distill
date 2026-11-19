"""Independent K1 two-step donor invariance, live-dependency and scale-once checks (CPU, tiny native fixture)."""
import copy, hashlib, json, os, sys, tempfile, types
from pathlib import Path
import numpy as np
import torch
from PIL import Image

W = Path(__file__).resolve().parent; T = W / 'new'
os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
os.environ.setdefault('LANE_TEST_OUTPUT', str(W / 'mine')); tempfile.tempdir = str(W / 'mine'); (W / 'mine').mkdir(exist_ok=True)
torch.set_num_threads(int(os.environ.get('NT', '8')))
from tests.test_carrier_c1_final import final_fixture
from tests.test_carrier_c1 import Tokenizer
from student_pilot import scale_donor as D, carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups, RECIPE
from student_pilot.carrier_c1_data import insert_frame_carriers
from student_pilot.carrier_c1_decode import HeadState
from student_pilot.decoupled_v import features
from student_pilot.p3_provenance import digest, file_pin
from student_pilot.tower_read import TowerState, GRID_UV
from student_pilot.tower_scale import estimate_scale
from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
from transformers.video_utils import VideoMetadata

SEL = json.loads(Path('/scratch/jjyeung/orch_n30/fb_pack/donor/out/K1_SELECTION.json').read_text())
h = lambda t: hashlib.sha256((t.detach().contiguous().numpy() if isinstance(t, torch.Tensor) else np.ascontiguousarray(t)).tobytes()).hexdigest()
fail = []
def check(ok, msg):
    if not ok: fail.append(msg)
    return ok


def k1_batch(c, vis):
    assert c['k1_split'] == 'train' and c['split'] == 'train' and len(c['anchor_slots']) == 32
    pix = []
    for idx, slot in zip(c['anchor_indices'], c['anchor_slots']):
        f = c['dense_frames'][slot]; assert f['index'] == idx
        p = Path(f['path']); assert str(p).startswith('/scratch/jjyeung/k1_frames/')
        b = p.read_bytes(); assert hashlib.sha256(b).hexdigest() == f['sha256'], p
        with Image.open(p) as im:
            side = vis.patch_size * vis.spatial_merge_size
            pix.append(np.asarray(im.convert('RGB').resize((side, side), Image.Resampling.BICUBIC)))
    proc = Qwen3VLVideoProcessor(patch_size=vis.patch_size, temporal_patch_size=vis.temporal_patch_size, merge_size=vis.spatial_merge_size)
    arr = np.repeat(np.stack(pix), vis.temporal_patch_size, axis=0).astype(np.float32) / 255.
    arr = (arr - np.asarray(proc.image_mean, np.float32)) / np.asarray(proc.image_std, np.float32)
    v = proc(videos=[arr], video_metadata=[VideoMetadata(total_num_frames=len(arr), fps=2., frames_indices=list(range(len(arr))))],
             do_sample_frames=False, do_resize=False, do_convert_rgb=False, do_normalize=False, do_rescale=False,
             input_data_format='channels_last', return_tensors='pt')
    assert v['video_grid_thw'].tolist() == [[32, 2, 2]]
    ids = torch.tensor([[2] + [x for _ in range(32) for x in (62, 61, 63)] + [10, 11, 12, 13]])
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                 mm_token_type_ids=torch.where(ids == 61, 2, 0), **v)
    batch['labels'][0, -2:] = ids[0, -2:]
    batch = insert_frame_carriers(batch, Tokenizer(), frame_layout='duplicate')
    rng = np.random.default_rng(int(c['anchor_indices'][1]))
    raw = np.zeros((32, 9)); raw[1:, :3] = rng.normal(size=(31, 3)); raw[:, 6] = 1
    raw[:, 7:9] = SEL['fovs'][c['canonical']]['fov_hw_rad']
    depth = rng.uniform(0.5, 4., size=(32, 51, 51)); conf = rng.uniform(0, 1, size=(32, 51, 51))
    st = TowerState(raw, depth, conf, np.asarray(c['anchor_indices']), np.arange(32))
    batch.update(tower_frame_indices=torch.tensor(st.frame_indices.copy()), tower_anchor_slots=torch.tensor(st.anchor_slots.copy()),
                 tower_lm_frame_indices=torch.tensor(st.frame_indices.copy()))
    return batch, st


def uv_grid():
    a = torch.as_tensor(GRID_UV.copy()); yy, xx = torch.meshgrid(a, a, indexing='ij')
    return torch.stack((xx, yy), -1).reshape(1, -1, 2).expand(32, -1, -1)


@torch.no_grad()
def reference_grid(ref_depth, batch, st, variant):
    """Recompute from a separate copy of the checkpoint's depth path; never touches the donor."""
    cap = features(ref_depth, batch, allow_short=True)
    if variant == 'V1':
        fov = (1e-4 + (np.pi - 2e-4) * ref_depth.fov(cap.states.float()).sigmoid())[0]
    else:
        fov = torch.tensor(st.raw_pose9[st.anchor_slots, 7:9], dtype=torch.float32)
    pd = ref_depth.auxiliary_heads.camera.point_depth
    return pd.query(pd.encode(cap.grids[0], cap.vits[0], fov.float()), uv_grid()).reshape(32, 51, 51)


@torch.no_grad()
def observe(model, batch, st):
    model.eval()
    hidden = model.hidden(batch)
    own = HeadState(model, batch, hidden)
    live = own.depth_head.query(own.depth_map, uv_grid()).reshape(32, 51, 51).clone()
    donor_grid = model.auxiliary_heads.scale_donor(batch, st).clone()
    tower = HeadState(model, batch, hidden, pose_source='tower', tower_state=st)
    s = estimate_scale(st.depth_grid, st.depth_conf_grid, donor_grid.double().numpy())[0]
    check(tower.tower_scale == s, 'tower scale is not the donor median')
    raw = st.raw_pose9[st.anchor_slots]
    check(np.array_equal(tower.pose9[:, :3], raw[:, :3] * s), 'translations not scaled exactly once')
    check(np.array_equal(tower.pose9[:, 3:], raw[:, 3:]), 'rotation/FoV changed')
    check(np.array_equal(tower.depth_map[:, 0].numpy(), st.depth_grid * s), 'tower depth not G3T*s once')
    pts = [[GRID_UV[7], GRID_UV[30]], [GRID_UV[50], GRID_UV[0]]]
    q = tower.depth(3, pts)
    check(np.allclose(q, [st.depth_grid[2, 30, 7] * s, st.depth_grid[2, 0, 50] * s], rtol=0, atol=1e-12), 'tower depth query not scaled grid')
    check(own.depth_head is model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth, 'own arm lost live head')
    return dict(hidden=hidden.clone(), own_pose=own.pose9.copy(), live=live, donor=donor_grid, scale=s,
                tower_pose=tower.pose9.copy(), own_depth=own.depth(3, pts).copy(), tower_depth=q.copy())


def run_variant(variant):
    model, _, targets = final_fixture()
    model.frame_layout = 'duplicate'; model.auxiliary_heads.depth.config.p3['frame_layout'] = 'duplicate'
    depth = model.auxiliary_heads.depth
    depth.model.visual.requires_grad_(False)   # N freezes the private visual by requires_grad only
    if os.environ.get('FILM', '1') == '1':
        # The fixture zero-initialises FoV FiLM, which makes every FoV path inert; trained heads are not.
        g = torch.Generator().manual_seed(5)
        with torch.no_grad():
            depth.auxiliary_heads.camera.point_depth.fov_film[-1].weight.copy_(
                torch.randn(depth.auxiliary_heads.camera.point_depth.fov_film[-1].weight.shape, generator=g) * 0.5)
    root = Path(tempfile.mkdtemp(prefix='k1_' + variant + '_', dir=W / 'mine'))
    torch.save(model.auxiliary_heads.state_dict(), root / 'heads.pt')
    (root / 'artifact.json').write_text(json.dumps(dict(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm', step=400,
                                                         fixture=True, heads=file_pin(root / 'heads.pt'))))
    src = torch.load(root / 'heads.pt', weights_only=True)
    ref_depth = copy.deepcopy(depth)
    cfg = dict(schema=D.SCHEMA, checkpoint=file_pin(root / 'artifact.json'), fov_source=variant,
               visual_sha256=D.visual_identity(depth.model.visual), feature_contract_sha256=digest(D.feature_contract(depth)))
    batches = [k1_batch(c, model.config.vision_config) for c in SEL['captures']]
    # Live path must move off the source before attach: the donor has to load the file, not the live module.
    with torch.no_grad():
        for p in depth.auxiliary_heads.camera.point_depth.parameters(): p.add_(1e-3)
        depth.fov.weight.add_(1e-2); depth.auxiliary_heads.frame_queries.add_(1e-2)
    donor = D.attach(model, cfg)
    for k, v in donor.state_dict().items():
        sk = ('depth.auxiliary_heads.camera.point_depth.' + k[len('point_depth.'):] if k.startswith('point_depth.') else
              'depth.auxiliary_heads.frame_queries' if k == 'frame_queries' else 'depth.' + k)
        check(torch.equal(v, src[sk]), f'{variant}: donor tensor {k} differs from checkpoint')
    check(donor.visual is depth.model.visual, 'visual not shared by reference')
    check(not any('visual' in k for k in donor.state_dict()), 'visual registered twice')
    check(set(k.split('.')[0] for k in donor.state_dict()) == ({'point_depth', 'frame_queries', 'fov'} if variant == 'V1' else {'point_depth', 'frame_queries'}),
          f'{variant}: donor tensor set {sorted(set(k.split(".")[0] for k in donor.state_dict()))}')
    for b, st in batches:
        check(torch.equal(reference_grid(ref_depth, b, st, variant), donor(b, st)), f'{variant}: donor grid != reference checkpoint path')
    pins0 = D.tensor_pins(donor.state_dict()); vis0 = D.visual_identity(depth.model.visual)
    live0 = D.tensor_pins(depth.auxiliary_heads.camera.point_depth.state_dict())
    pose0 = D.tensor_pins(model.auxiliary_heads.pose.state_dict())
    before = [observe(model, b, st) for b, st in batches]

    class Rows:
        def count(self, s): return 1
        def get(self, s, i): return {k: v for k, v in batches[0][0].items() if isinstance(v, torch.Tensor)}, targets, {}
    model.train()
    check(not donor.training and not depth.model.visual.training, 'donor/visual left train mode')
    groups = parameter_groups(model)
    ids = {id(p) for g in groups for p in g['params']}
    frozen = {id(p) for p in donor.parameters()} | {id(p) for p in depth.model.visual.parameters()}
    check(not (ids & frozen), 'donor/visual parameter in an optimizer group')
    opt = torch.optim.AdamW(groups, weight_decay=RECIPE['weight_decay'])
    losses = [run.optimize_step(model, opt, Rows(), [('pose', [0])], 0, torch.device('cpu'), s, distributed=False)[0] for s in (1, 2)]
    check(not any(id(p) in frozen for g in opt.param_groups for p in g['params']), 'frozen param entered optimizer after step')
    check(not any(p.grad is not None for p in donor.parameters()), 'donor received gradients')
    pins1 = D.tensor_pins(donor.state_dict()); live1 = D.tensor_pins(depth.auxiliary_heads.camera.point_depth.state_dict())
    pose1 = D.tensor_pins(model.auxiliary_heads.pose.state_dict())
    check(pins0 == pins1 and vis0 == D.visual_identity(depth.model.visual), f'{variant}: donor/visual tensors changed')
    changed = [k for k in live0 if live0[k] != live1[k]]
    check(bool(changed), 'live head did not move'); check(pose0 != pose1, 'pose head (live FoV source) did not move')
    after = [observe(model, b, st) for b, st in batches]
    caps = []
    for c, a, b in zip(SEL['captures'], before, after):
        check(torch.equal(a['donor'], b['donor']), f'{variant} {c["canonical"]}: donor grid drifted')
        check(np.float64(a['scale']).tobytes() == np.float64(b['scale']).tobytes(), f'{variant}: scale drifted')
        check(np.array_equal(a['tower_pose'], b['tower_pose']) and np.array_equal(a['tower_depth'], b['tower_depth']), f'{variant}: tower outputs drifted')
        check(not torch.equal(a['live'], b['live']), f'{variant}: live grid did not move')
        check(not np.array_equal(a['own_pose'], b['own_pose']), f'{variant}: own pose did not move')
        caps.append(dict(capture=c['canonical'], donor_grid=h(a['donor']), donor_grid_after=h(b['donor']), live_grid=h(a['live']),
                         live_grid_after=h(b['live']), scale=a['scale'], scale_after=b['scale'],
                         own_pose_after_differs=not np.array_equal(a['own_pose'], b['own_pose'])))
    # Perturb every live dependency the donor must not read.
    b0, st0 = batches[0]; g0 = donor(b0, st0).clone()
    with torch.no_grad():
        for mod in (model.auxiliary_heads.pose, depth.auxiliary_heads.camera.point_depth, depth.fov):
            for p in mod.parameters(): p.add_(0.3)
        depth.auxiliary_heads.frame_queries.add_(0.3)
        for p in model.model.language_model.parameters(): p.add_(0.01)
        for p in model.model.visual.parameters(): p.add_(0.01)
    check(torch.equal(g0, donor(b0, st0)), f'{variant}: donor reads a live module (pose/point-depth/fov/queries/LM/base visual)')
    st_fov = TowerState(np.concatenate([st0.raw_pose9[:, :7], st0.raw_pose9[:, 7:] * 0.9], 1), st0.depth_grid, st0.depth_conf_grid, st0.frame_indices, st0.anchor_slots)
    dep = not torch.equal(g0, donor(b0, st_fov))
    check(dep == (variant == 'V2' and os.environ.get('FILM', '1') == '1'), f'{variant}: tower-FoV dependency is {dep}')
    # Negative control: a donor that reads the live FoV module must be caught by the same perturbation.
    if variant == 'V1':
        orig = donor.point_depth.encode
        probe = torch.zeros(1, 32, depth.fov.in_features)
        def leaky(grid, vits, fov):
            return orig(grid, vits, (1e-4 + (np.pi - 2e-4) * depth.fov(probe).sigmoid())[0].detach())
        donor.point_depth.encode = leaky
        g1 = donor(b0, st0).clone()
        with torch.no_grad():
            depth.fov.bias.sub_(0.5)
        caught = not torch.equal(g1, donor(b0, st0))
        del donor.point_depth.encode
        check(caught == (os.environ.get('FILM', '1') == '1'), f'negative control (leaky V1 FoV) caught={caught}')
        neg_control_caught = caught
    else:
        neg_control_caught = None
    # Shared visual is the one deliberate shared dependency: drift must be refused.
    with torch.no_grad():
        p = next(depth.model.visual.parameters()); keep = p.detach().clone(); p.view(-1)[0] += 1.
    try:
        donor.metadata(); check(False, 'changed shared visual accepted by metadata()')
    except ValueError: pass
    with torch.no_grad(): p.copy_(keep)
    donor.metadata()
    return dict(variant=variant, film=os.environ.get('FILM', '1'), negative_control_caught=neg_control_caught,
                tower_fov_dependency=dep, donor_tensors=len(pins0), live_tensors=len(live0), live_changed=len(changed),
                losses=[float(x) if not isinstance(x, dict) else str(x)[:80] for x in losses],
                groups=[dict(name=g['name'], n=len(g['params']), wd=g.get('weight_decay', RECIPE['weight_decay'])) for g in opt.param_groups],
                captures=caps)


res = [run_variant(v) for v in ('V1', 'V2')]
out = dict(status='PASS' if not fail else 'FAIL', failures=fail, variants=res,
           inputs={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), T / 'student_pilot/scale_donor.py', T / 'student_pilot/tower_read.py']})
(W / ('K1_MINE_FILM%s.json' % os.environ.get('FILM', '1'))).write_text(json.dumps(out, indent=1, default=str))
print(out['status'], fail[:10])
for r in res: print(r['variant'], r['donor_tensors'], r['live_tensors'], r['live_changed'], [c['scale'] for c in r['captures']])
