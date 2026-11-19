"""Own K1 two-step invariance + live-dependency check on the two authenticated K1 captures.

Usage: python k1_check.py <tree>. Writes K1_<tree>.json. Tiny native weights; fixture RGB at 4x4.
"""
import copy, hashlib, json, os, sys, tempfile, types
from pathlib import Path
import numpy as np
import torch
from PIL import Image

W = Path(__file__).resolve().parent; NAME = sys.argv[1]; T = W / NAME
OUT = W / ('k1_' + NAME); OUT.mkdir(exist_ok=True)
os.environ.update(LANE_TEST_OUTPUT=str(OUT), TMPDIR=str(OUT), CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
tempfile.tempdir = str(OUT); os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
torch.set_num_threads(8)
from tests.test_carrier_c1_final import final_fixture
from tests.test_carrier_c1 import Tokenizer
from student_pilot import scale_donor as D, carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups, RECIPE
from student_pilot.carrier_c1_data import insert_frame_carriers
from student_pilot.carrier_c1_decode import HeadState
from student_pilot.p3_provenance import digest, file_pin
from student_pilot.tower_read import TowerState, GRID_UV
from student_pilot.tower_scale import estimate_scale
from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
from transformers.video_utils import VideoMetadata

SEL = json.loads(Path('/scratch/jjyeung/orch_n30/fb_pack/donor2/out/K1_SELECTION.json').read_text())
fails = []
def need(ok, msg):
    if not ok:
        fails.append(msg)
    return bool(ok)


def capture_batch(c, vision):
    assert c['k1_split'] == 'train' and len(c['anchor_slots']) == 32
    side = vision.patch_size * vision.spatial_merge_size
    imgs = []
    for slot, idx in zip(c['anchor_slots'], c['anchor_indices']):
        f = c['dense_frames'][slot]; assert f['index'] == idx
        raw = Path(f['path']).read_bytes(); assert hashlib.sha256(raw).hexdigest() == f['sha256']
        with Image.open(f['path']) as im:
            imgs.append(np.asarray(im.convert('RGB').resize((side, side), Image.Resampling.BILINEAR)))
    proc = Qwen3VLVideoProcessor(patch_size=vision.patch_size, temporal_patch_size=vision.temporal_patch_size,
                                 merge_size=vision.spatial_merge_size)
    arr = np.repeat(np.stack(imgs), vision.temporal_patch_size, 0).astype(np.float32) / 255.
    arr = (arr - np.asarray(proc.image_mean, np.float32)) / np.asarray(proc.image_std, np.float32)
    v = proc(videos=[arr], video_metadata=[VideoMetadata(total_num_frames=len(arr), fps=2., frames_indices=list(range(len(arr))))],
             do_sample_frames=False, do_resize=False, do_convert_rgb=False, do_normalize=False, do_rescale=False,
             input_data_format='channels_last', return_tensors='pt')
    ids = torch.tensor([[2] + [x for _ in range(32) for x in (62, 61, 63)] + [10, 11, 12, 13]])
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                 mm_token_type_ids=torch.where(ids == 61, 2, 0), **v)
    batch['labels'][0, -2:] = ids[0, -2:]
    batch = insert_frame_carriers(batch, Tokenizer(), frame_layout='duplicate')
    g = np.random.default_rng(1000 + int(c['anchor_indices'][2]))
    pose = np.zeros((32, 9)); pose[1:, :3] = g.normal(size=(31, 3)); pose[:, 6] = 1.
    pose[:, 7:9] = SEL['fovs'][c['canonical']]['fov_hw_rad']
    st = TowerState(pose, g.uniform(.4, 5., (32, 51, 51)), g.uniform(0., 1., (32, 51, 51)), np.asarray(c['anchor_indices']), np.arange(32))
    batch.update(tower_frame_indices=torch.tensor(st.frame_indices.copy()), tower_anchor_slots=torch.tensor(st.anchor_slots.copy()),
                 tower_lm_frame_indices=torch.tensor(st.frame_indices.copy()))
    return batch, st


@torch.no_grad()
def read(model, batch, st):
    """Full decode path: own HeadState, then tower HeadState through apply_tower."""
    model.eval()
    hidden = model.hidden(batch)
    own = HeadState(model, batch, hidden)
    a = torch.as_tensor(GRID_UV.copy()); yy, xx = torch.meshgrid(a, a, indexing='ij')
    uv = torch.stack((xx, yy), -1).reshape(1, -1, 2).expand(32, -1, -1)
    live = own.depth_head.query(own.depth_map, uv).reshape(32, 51, 51).clone()
    direct = model.auxiliary_heads.scale_donor(batch, st).clone()
    tower = HeadState(model, batch, hidden, pose_source='tower', tower_state=st)
    s_direct = estimate_scale(st.depth_grid, st.depth_conf_grid, direct.double().numpy())[0]
    return dict(live=live, direct=direct, tower_scale=float(tower.tower_scale), direct_scale=float(s_direct),
                own_pose=own.pose9.copy(), tower_pose=tower.pose9.copy())


def one(variant):
    model, _, targets = final_fixture()
    model.frame_layout = 'duplicate'; model.auxiliary_heads.depth.config.p3['frame_layout'] = 'duplicate'
    depth = model.auxiliary_heads.depth
    depth.model.visual.requires_grad_(False)
    pd = depth.auxiliary_heads.camera.point_depth
    with torch.no_grad():  # own nonzero FiLM, independent of donor2's seed/scale
        pd.fov_film[-1].weight.copy_(torch.randn(pd.fov_film[-1].weight.shape, generator=torch.Generator().manual_seed(77)) * .8)
        pd.fov_film[-1].bias.copy_(torch.randn(pd.fov_film[-1].bias.shape, generator=torch.Generator().manual_seed(78)) * .2)
    src = Path(tempfile.mkdtemp(prefix='src_' + variant + '_', dir=OUT))
    torch.save(model.auxiliary_heads.state_dict(), src / 'heads.pt')
    (src / 'artifact.json').write_text(json.dumps(dict(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm', step=400,
                                                       heads=file_pin(src / 'heads.pt'))))
    cfg = dict(schema=D.SCHEMA, checkpoint=file_pin(src / 'artifact.json'), fov_source=variant,
               visual_sha256=D.visual_identity(depth.model.visual), feature_contract_sha256=digest(D.feature_contract(depth)))
    pairs = [capture_batch(c, model.config.vision_config) for c in SEL['captures']]
    donor = D.attach(model, cfg)
    pins0 = D.tensor_pins(donor.state_dict())
    before = [read(model, b, s) for b, s in pairs]

    class Rows:
        def count(self, s): return 1
        def get(self, s, i): return {k: v for k, v in pairs[0][0].items() if isinstance(v, torch.Tensor)}, targets, {}
    model.train()
    opt = torch.optim.AdamW(parameter_groups(model), weight_decay=RECIPE['weight_decay'])
    for step in (1, 2):
        run.optimize_step(model, opt, Rows(), [('pose', [0])], 0, torch.device('cpu'), step, distributed=False)
    need(D.tensor_pins(donor.state_dict()) == pins0, f'{variant}: donor tensors changed by training')
    after = [read(model, b, s) for b, s in pairs]
    rec = []
    for c, x, y in zip(SEL['captures'], before, after):
        tag = f"{variant} {c['canonical']}"
        need(torch.equal(x['direct'], y['direct']), tag + ': donor grid drifted over two steps')
        need(x['tower_scale'] == y['tower_scale'], tag + ': tower scale drifted over two steps')
        need(x['tower_scale'] == x['direct_scale'] and y['tower_scale'] == y['direct_scale'], tag + ': decode-path scale != direct donor scale')
        need(not torch.equal(x['live'], y['live']), tag + ': live grid did not move')
        need(not np.array_equal(x['own_pose'], y['own_pose']), tag + ': own pose did not move')
        rec.append(dict(capture=c['canonical'], scale_before=x['tower_scale'], scale_after=y['tower_scale'],
                        direct_scale=x['direct_scale'], own_fov_moved=float(np.abs(x['own_pose'][:, 7:9] - y['own_pose'][:, 7:9]).max())))
    # Explicit perturbation of every live FoV/query source.
    b0, s0 = pairs[0]; ref = read(model, b0, s0)
    with torch.no_grad():
        depth.fov.weight.add_(.5); depth.fov.bias.sub_(.5)
        depth.auxiliary_heads.frame_queries.add_(.5)
        for p in model.auxiliary_heads.pose.parameters(): p.add_(.05)
    pert = read(model, b0, s0)
    need(torch.equal(ref['direct'], pert['direct']), f'{variant}: donor grid reads a live FoV/query source')
    need(ref['tower_scale'] == pert['tower_scale'], f'{variant}: tower scale reads a live FoV/query source')
    need(not np.array_equal(ref['own_pose'][:, 7:9], pert['own_pose'][:, 7:9]), f'{variant}: perturbation did not move live pose FoV')
    s_fov = TowerState(np.concatenate([s0.raw_pose9[:, :7], s0.raw_pose9[:, 7:] * .85], 1), s0.depth_grid, s0.depth_conf_grid, s0.frame_indices, s0.anchor_slots)
    tower_dep = not torch.equal(pert['direct'], model.auxiliary_heads.scale_donor(b0, s_fov))
    need(tower_dep == (variant == 'V2'), f'{variant}: tower-FoV dependency={tower_dep}')
    return dict(variant=variant, captures=rec, tower_fov_dependency=tower_dep)


res = [one(v) for v in ('V1', 'V2')]
need(all(a['scale_before'] != b['scale_before'] for a, b in zip(res[0]['captures'], res[1]['captures'])), 'V1 and V2 scales coincide')
out = dict(tree=NAME, status='PASS' if not fails else 'FAIL', failures=fails, variants=res,
           inputs={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), T / 'student_pilot/scale_donor.py', T / 'student_pilot/tower_read.py')})
(W / f'K1_{NAME}.json').write_text(json.dumps(out, indent=1, default=str))
print(NAME, out['status'], fails[:8])
