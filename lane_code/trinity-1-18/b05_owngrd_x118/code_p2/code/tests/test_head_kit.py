"""CPU contracts for the T-1 kit; real weights are opt-in through OWNGRD_REAL_VIT=1."""
import copy
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import resource
import time

import numpy as np
import pytest
import torch

from conftest import AUTH, TEACHER_K1
from test_teacher import small_manifest, run
from owngrd import labels
from owngrd.common import atomic_write_json, read_json, sha256_json
from owngrd.data import GroundingDataset, choose_frames, room_validation
from owngrd.eligibility import canon
from owngrd.export import save_head, load_head
from owngrd.head import Config, GroundingHead, PresenceHead, cluster_candidates
from owngrd.losses import compute_losses, selection_target
from owngrd.train import Stopper, Metrics, seed_all, make_optimizer, optimization_step, save_checkpoint, load_checkpoint
from owngrd.vit import pack_qwen, unpack_qwen, FrozenViT

TORCH_THREADS = 4
# Small models run faster with four threads; this remains below the sixteen-thread ceiling.
torch.set_num_threads(TORCH_THREADS)


@pytest.fixture(scope='module')
def stub_data(tmp_path_factory):
    root = tmp_path_factory.mktemp('head_labels')
    manifest = small_manifest(root, n_caps=12, n_names=3)
    teacher, label = root/'teacher', root/'labels'
    assert run(manifest, teacher) == 0
    assert labels.main(['--manifest', str(manifest), '--teacher-root', str(teacher), '--out', str(label)]) == 0
    assert len(read_json(manifest)['captures']) == 12
    return manifest, label, teacher


def tiny_batch(cfg, frames=4, names=1, hw=(32, 32)):
    return dict(taps=[torch.randn(frames, 2, 2, cfg.vit_dim) for _ in range(4)],
        merged=torch.randn(frames, 1, 1, cfg.vit_dim), pixels=torch.rand(frames, 3, *hw),
        name_tokens=torch.randn(names, 3, cfg.name_dim), name_mask=torch.ones(names, 3, dtype=torch.bool),
        frame_ids=torch.arange(frames))


def synthetic_target(frames=4):
    mask = torch.zeros(8, 8)
    mask[1:6, 1:6] = 1
    other = torch.zeros(8, 8)
    other[5:, 5:] = 1
    rows, decoder = [], []
    for f in range(frames):
        presence = 1 if f < 2 else None
        rows.append(dict(presence=presence, why='pos' if presence else 'uncertain_absent',
                         teacher_presence=.8, pos_inst=[7], gt_visible=[7]))
        decoder.append(dict(presence=presence, teacher_presence=.8,
            targets=[dict(mask=mask, instance=7, weight=1., low_resolution=False, cls='POS'),
                     dict(mask=other, instance=9, weight=labels.MISS_WEIGHT, low_resolution=True, cls='MISS')],
            gt_masks={7: mask}, hardneg=[dict(mask=other, instance=10, weight=1., selection_only=False)],
            soft=[dict(mask=other, joint=.6)], proposals=[dict(mask=mask, instance=7, weight=1., joint=.8,
                selection_only=False, cls='POS')]))
    return dict(name='chair', role='gt', clip_presence=1, frames=rows, decoder=decoder, gt_instances=[7])


def test_stub_dataset_full_path_and_twenty_steps(stub_data):
    seed_all(27)
    cfg = Config.tiny()
    ds = GroundingDataset(*stub_data, split='inspect', size_hw=(32, 32))
    assert len(ds.captures) >= 3
    for index in (0, 3, 6):
        item = ds[index]
        assert item['frame_count'] == 32 and len(item['frame_ids']) == 4
        assert all(t['weight'] == labels.MISS_WEIGHT and t['low_resolution']
                   for f in item['target']['decoder'] for t in f['targets'] if t['cls'] == 'MISS')
    item = ds[0]
    batch = tiny_batch(cfg)
    batch['merged'] = torch.randn(item['frame_count'], 1, 1, cfg.vit_dim)
    batch['frame_ids'], batch['pixels'] = item['frame_ids'], item['pixels']
    head = GroundingHead(cfg)
    opt, scheduler = make_optimizer(head, lr=.002, warmup=0, steps=100)
    history = []
    for step in range(20):
        loss, _, _ = optimization_step(head, batch, [item['target']], opt, scheduler)
        assert all(np.isfinite(v) for v in loss.values())
        history.append(loss['total'])
    assert np.mean(history[-5:]) < np.mean(history[:5]), history


def test_every_loss_has_targets_and_gradients():
    seed_all(101)
    cfg = Config.tiny()
    head = GroundingHead(cfg)
    batch = tiny_batch(cfg)
    target = synthetic_target()
    out = head(**batch, selection_targets=[target])
    loss, details = compute_losses(out, [target], cfg)
    assert set(loss) == set(cfg.weights) | {'total'}
    assert all(torch.isfinite(v) and float(v.detach()) > 0 for v in loss.values()), loss
    loss['total'].backward()
    for module in (head.presence, head.decoder, head.selector):
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in module.parameters())
    assert len(details['matches'][0]) == 4


def test_empty_targets_are_finite():
    cfg = Config.tiny()
    out = GroundingHead(cfg)(**tiny_batch(cfg))
    target = synthetic_target()
    target['clip_presence'], target['gt_instances'] = None, []
    for row, frame in zip(target['frames'], target['decoder']):
        row['presence'] = None
        frame.update(targets=[], hardneg=[], soft=[], proposals=[], gt_masks={}, presence=None)
    loss, _ = compute_losses(out, [target], cfg)
    assert all(torch.isfinite(v) for v in loss.values())
    for term in ('mask_focal', 'mask_dice', 'box_l1', 'box_giou', 'identity', 'clip', 'selection', 'iou', 'presence'):
        assert loss[term].item() == 0


@pytest.mark.parametrize('frames', [32, 64])
def test_presence_frame_count(frames):
    cfg = Config.tiny()
    head = PresenceHead(cfg)
    frame, clip = head(torch.randn(frames, 2, 3, cfg.vit_dim), torch.randn(2, cfg.name_dim))
    assert frame.shape == (2, frames) and clip.shape == (2,)
    slots = head.shortlist(frame)
    assert all(len(s) == 4 and all(abs(a-b) >= 2 for i, a in enumerate(s) for b in s[i+1:]) for s in slots)


def test_clustering_selection_and_metrics():
    score = torch.tensor([[.9, .8], [.85, .75], [.7, .6]])
    identity = torch.tensor([[[1., 0.], [0., 1.]]]*3)
    clusters, features = cluster_candidates(score, identity, torch.ones(3), torch.ones(3, 2))
    assert clusters == [[(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)]]
    assert features.shape == (2, 6) and features[0, 2] == 1
    target = synthetic_target(3)
    masks = torch.full((3, 2, 8, 8), -10.)
    masks[:, 0, 1:6, 1:6] = 10
    candidates = [dict(source='decoder', members=c) for c in clusters]
    assert selection_target(candidates, masks, target) == (0, 'covered')
    target['clip_presence'], target['gt_instances'] = 0, []
    assert selection_target(candidates, masks, target) == (2, 'absent')
    target['gt_instances'] = [7, 8]
    assert selection_target(candidates, masks, target) == (None, 'multiple_instances')
    metric = Metrics()
    metric.instances, metric.covered, metric.pos_iou = 10, 8, [.5, .7]
    metric.names, metric.names_covered = 10, 8
    metric.pairs = [dict(confidence=1-i/10, correct=i < 7, absent=i >= 8, candidate=True,
                         selected=True, present=i < 8, ambiguous=False) for i in range(10)]
    result = metric.result()
    assert result['candidate_recall_at5'] == .8 and result['mask_iou_pos'] == .6
    assert result['false_presence_absent_at85'] == .5


def test_exact_resume_and_export(tmp_path):
    cfg = Config.tiny()
    seed_all(400)
    batch, target = tiny_batch(cfg), synthetic_target()
    seed_all(41)
    model = GroundingHead(cfg)
    initial = copy.deepcopy(model.state_dict())
    hashes = dict(config=cfg.sha256, labels='labels', vit='vit', name_rows='rows', tokenizer='tokenizer', gate='gate')
    optimizer, scheduler = make_optimizer(model, lr=.001, warmup=2, steps=10)
    seed_all(83)
    straight = [optimization_step(model, batch, [target], optimizer, scheduler)[0] for _ in range(10)]
    final = copy.deepcopy(model.state_dict())
    model.load_state_dict(initial)
    optimizer, scheduler = make_optimizer(model, lr=.001, warmup=2, steps=10)
    seed_all(83)
    first = [optimization_step(model, batch, [target], optimizer, scheduler)[0] for _ in range(5)]
    cursor = dict(step=5, epoch=2, item=3)
    stopper = Stopper(history=[dict(step=4, on_target_share_at85=.8, mask_iou_pos=.7)])
    path = tmp_path/'tiny.pt'
    save_checkpoint(path, model, optimizer, scheduler, cursor, stopper, hashes)
    rng_expected = (random.random(), np.random.rand(), torch.rand(1))
    resumed = GroundingHead(cfg)
    opt2, sched2 = make_optimizer(resumed, lr=.001, warmup=2, steps=10)
    for key in ('config', 'labels', 'vit', 'name_rows'):
        with pytest.raises(ValueError, match='hash mismatch'):
            load_checkpoint(path, resumed, opt2, sched2, {**hashes, key: 'changed'})
    got_cursor, got_stopper, _ = load_checkpoint(path, resumed, opt2, sched2, hashes)
    assert got_cursor == cursor and asdict(got_stopper) == asdict(stopper)
    assert random.random() == rng_expected[0] and np.random.rand() == rng_expected[1]
    assert torch.equal(torch.rand(1), rng_expected[2])
    load_checkpoint(path, resumed, opt2, sched2, hashes)
    rest = [optimization_step(resumed, batch, [target], opt2, sched2)[0] for _ in range(5)]
    assert straight == first+rest
    assert all(torch.equal(v, resumed.state_dict()[k]) for k, v in final.items())
    save_head(tmp_path/'export', resumed, hashes)
    loaded, meta = load_head(tmp_path/'export', hashes)
    assert all(torch.equal(v, loaded.state_dict()[k]) for k, v in final.items())
    assert meta['parameter_counts'] == resumed.parameter_counts()
    with pytest.raises(ValueError, match='provenance'):
        load_head(tmp_path/'export', {**hashes, 'vit': 'wrong'})


@pytest.mark.parametrize('authority', ['dev', 'withheld', 'benchmark'])
def test_dataset_refuses_excluded_capture(tmp_path, authority):
    man = read_json(TEACHER_K1)
    pool = read_json(AUTH/'CAPTURES.json')['captures']
    if authority == 'dev':
        bad = {'canonical': canon(read_json(AUTH/'DEVS1_MANIFEST.json')['captures'][0]['scene'])}
    elif authority == 'withheld':
        rooms = {canon(r) for r in read_json(AUTH/'WITHHELD_ROOMS_80.json')['rooms']}
        bad = next(c for c in pool if canon(c['room']) in rooms)
    else:
        scenes = {canon(s) for s in read_json(AUTH/'BENCH_SCENE_EXCLUSIONS_v2.json')['scenes']}
        bad = next(c for c in pool if canon(c['canonical']) in scenes)
    man['captures'] = man['captures'][:1] + [bad]
    path = tmp_path/'manifest.json'
    atomic_write_json(path, man)
    with pytest.raises(ValueError, match='Eligibility gate refuses'):
        GroundingDataset(path, tmp_path, tmp_path)


def test_dataset_refuses_heldout_and_digest(tmp_path):
    man = read_json(TEACHER_K1)
    c = next(c for c in man['captures'] if c['k1_split'] == 'heldout')
    man['captures'] = [c]
    path = tmp_path/'heldout.json'
    atomic_write_json(path, man)
    with pytest.raises(ValueError, match='heldout'):
        GroundingDataset(path, tmp_path, tmp_path)
    man['gate_receipt']['gate_digest'] = 'wrong'
    atomic_write_json(path, man)
    with pytest.raises(ValueError, match='Gate digest'):
        GroundingDataset(path, tmp_path, tmp_path)


def test_frame_choice_and_room_split():
    rows = [dict(presence=None, teacher_presence=.2, pos_inst=[]) for _ in range(64)]
    rows[19]['pos_inst'] = [3]
    rows[37]['teacher_presence'] = .9
    selected = choose_frames(rows, 7, ['capture', 'chair'])
    assert selected == choose_frames(rows, 7, ['capture', 'chair'])
    assert 19 in selected and 37 in selected and len(selected) == 4
    flags = [room_validation('room'+str(i)) for i in range(1000)]
    assert 70 <= sum(flags) <= 130


def test_stop_rules():
    metrics = dict(candidate_recall_at5=.9, mask_iou_pos=.5, on_target_share_at85=.8, false_presence_absent_at85=.01)
    assert Stopper().decide(600, {**metrics, 'candidate_recall_at5': .69}) == ('STOP', 'fail_fast_at_600')
    assert Stopper().decide(600, {**metrics, 'mask_iou_pos': .43})[0] == 'STOP'
    stopper = Stopper()
    assert stopper.decide(600, metrics)[0] == 'CONTINUE'
    assert stopper.decide(1200, metrics) == ('STOP', 'plateau_600_steps')
    assert Stopper().decide(2400, {**metrics, 'false_presence_absent_at85': .11}) == ('STOP', 'false_presence_kill')
    assert Stopper(hours=1).decide(2, elapsed_seconds=3600) == ('STOP', 'wall_hour_cap')
    assert Stopper(hours=100, accelerators=8).decide(2, elapsed_seconds=8*3600) == ('STOP', 'accelerator_hour_cap')
    stopped = Stopper()
    stopped.decide(600, {**metrics, 'mask_iou_pos': .3})
    restored = Stopper(**asdict(stopped))
    assert restored.decide(601, metrics) == ('STOP', 'fail_fast_at_600')


def test_pack_unpack_geometry():
    rgb = torch.arange(2*3*32*64).reshape(2, 3, 32, 64).float()
    packed, grid = pack_qwen(rgb)
    assert grid.tolist() == [[1, 2, 4], [1, 2, 4]]
    assert packed.shape == (16, 1536)
    maps = torch.arange(16).reshape(16, 1)
    unpacked = unpack_qwen(maps, grid)
    assert unpacked[0, :, :, 0].tolist() == [[0, 1, 4, 5], [2, 3, 6, 7]]


@pytest.mark.skipif(os.environ.get('OWNGRD_REAL_VIT') != '1', reason='Set OWNGRD_REAL_VIT=1 after heavy-I/O approval')
def test_real_vit_first_batch(stub_data):
    torch.set_num_threads(16)
    started = time.monotonic()
    ds = GroundingDataset(*stub_data, split='inspect')
    first = ds[0]
    ids = first['frame_ids'].tolist()
    second = ds.get_item(1, frame_ids=ids)
    assert first['canonical'] == second['canonical']
    vit = FrozenViT()
    frames = [first['frames'][i] for i in ids]
    taps, merged = vit.taps(frames, first['size_hw'])
    h, w = first['size_hw']
    assert all(t.shape == (4, h//16, w//16, 1152) for t in taps)
    assert merged.shape == (4, h//32, w//32, 1152)
    assert not vit.model.training and all(not p.requires_grad for p in vit.model.parameters())
    names = vit.name_query([first['name'], second['name']])
    assert names.tokens.shape[0] == 2 and names.tokens.shape[-1] == 4096
    assert names.rows_sha256 == vit.name_query([first['name'], second['name']]).rows_sha256
    cfg = Config()
    head = GroundingHead(cfg).eval()
    targets = []
    for item in (first, second):
        target = item['target']
        target['frames'] = [target['frames'][i] for i in ids]
        targets.append(target)
    with torch.no_grad():
        out = head(taps, merged, first['pixels'], names.tokens, names.mask)
        losses, _ = compute_losses(out, targets, cfg)
    assert out['masks'].shape == (2, 4, 16, h//4, w//4)
    assert out['boxes'].shape == (2, 4, 16, 4)
    assert out['identity'].shape == (2, 4, 16, 128)
    assert torch.allclose(out['identity'].norm(dim=-1), torch.ones(2, 4, 16), atol=1e-5)
    assert all(torch.isfinite(v) for v in losses.values())
    record = dict(seconds=time.monotonic()-started, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        parameters=head.parameter_counts(), vit_sha256=vit.sha256, vit_state_sha256=vit.state_sha256,
        source_state_sha256=vit.source_state_sha256, subset_sha256=vit.file_sha256,
        name_rows_sha256=names.rows_sha256, tokenizer_sha256=names.tokenizer_sha256,
        size_hw=list(first['size_hw']), names=[first['name'], second['name']], frames=4,
        losses={k: float(v) for k, v in losses.items()})
    destination = Path(os.environ.get('OWNGRD_REAL_REPORT', '/scratch/jjyeung/orch_n30/b05_owngrd/tmp_codex/REAL_VIT.json'))
    atomic_write_json(destination, record)
    print(json.dumps(record))
    torch.set_num_threads(TORCH_THREADS)


def test_selection_only_hardneg_does_not_train_other_terms():
    seed_all(73)
    cfg = Config.tiny()
    head = GroundingHead(cfg)
    target = synthetic_target()
    for frame in target['decoder']:
        frame['hardneg'][0].update(selection_only=True, weight=.25)
    clean = copy.deepcopy(target)
    for frame in clean['decoder']:
        frame['hardneg'] = []
    out = head(**tiny_batch(cfg), selection_targets=[target])
    torch.manual_seed(10)
    left, _ = compute_losses(out, [target], cfg)
    torch.manual_seed(10)
    right, _ = compute_losses(out, [clean], cfg)
    assert all(torch.equal(left[k], right[k]) for k in cfg.weights)


def test_shortlist_drives_inference_without_labels():
    from PIL import Image
    from owngrd.train import predict_clip
    from owngrd.vit import NameQuery
    cfg = Config.tiny()

    class TinyVision:
        device = torch.device('cpu')

        def taps(self, frames, size_hw):
            value = torch.tensor([np.asarray(f).mean()/255 for f in frames], dtype=torch.float32)
            maps = [value[:, None, None, None].expand(-1, 2, 2, cfg.vit_dim) for _ in range(4)]
            return maps, maps[-1][:, :1, :1]

        def name_query(self, names):
            return NameQuery(torch.ones(len(names), 2, cfg.name_dim), torch.ones(len(names), 2, dtype=torch.bool), [], 'rows', 'tok')

    frames = [Image.new('RGB', (32, 32), (i*3, i*3, i*3)) for i in range(64)]
    model = GroundingHead(cfg)
    outputs = predict_clip(model, TinyVision(), frames, ['chair', 'table'], (32, 32), (32, 32))
    assert len(outputs) == 2
    assert model.training
    for out in outputs:
        assert out['presence'].shape == (1, 64)
        assert out['masks'].shape[:3] == (1, 4, 16)
        assert out['frame_ids'].tolist() == model.presence.shortlist(out['presence'])[0]


def test_data_cursor_resume_order(tmp_path):
    cfg = Config.tiny()
    seed_all(91)
    batches = [tiny_batch(cfg) for _ in range(3)]
    target = synthetic_target()
    model = GroundingHead(cfg)
    initial = copy.deepcopy(model.state_dict())
    hashes = dict(config=cfg.sha256, labels='l', vit='v')

    def advance(model, opt, scheduler, cursor, count):
        losses = []
        for _ in range(count):
            losses.append(optimization_step(model, batches[cursor['item']], [target], opt, scheduler)[0])
            cursor['item'] += 1
            cursor['step'] += 1
            if cursor['item'] == len(batches):
                cursor['epoch'] += 1
                cursor['item'] = 0
        return losses

    opt, scheduler = make_optimizer(model, lr=.001, warmup=1, steps=10)
    cursor = dict(step=0, epoch=0, item=0)
    seed_all(53)
    straight = advance(model, opt, scheduler, cursor, 10)
    final = copy.deepcopy(model.state_dict())
    model.load_state_dict(initial)
    opt, scheduler = make_optimizer(model, lr=.001, warmup=1, steps=10)
    cursor = dict(step=0, epoch=0, item=0)
    seed_all(53)
    split = advance(model, opt, scheduler, cursor, 5)
    save_checkpoint(tmp_path/'cursor.pt', model, opt, scheduler, cursor, Stopper(), hashes)
    fresh = GroundingHead(cfg)
    opt, scheduler = make_optimizer(fresh, lr=.001, warmup=1, steps=10)
    cursor, _, _ = load_checkpoint(tmp_path/'cursor.pt', fresh, opt, scheduler, hashes)
    split += advance(fresh, opt, scheduler, cursor, 5)
    assert split == straight and cursor == dict(step=10, epoch=3, item=1)
    assert all(torch.equal(value, fresh.state_dict()[key]) for key, value in final.items())


def test_qwen_tap_wrapper_with_small_local_model():
    from PIL import Image
    from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
    cfg = Qwen3_5VisionConfig(depth=27, hidden_size=16, intermediate_size=32, num_heads=4,
        out_hidden_size=16, num_position_embeddings=16, patch_size=16, temporal_patch_size=2,
        spatial_merge_size=2, deepstack_visual_indexes=[])
    cfg._attn_implementation = 'sdpa'
    vit = FrozenViT.__new__(FrozenViT)
    vit.device = torch.device('cpu')
    vit.model = Qwen3_5VisionModel(cfg).eval().requires_grad_(False)
    maps, merged = vit.taps([Image.new('RGB', (64, 32)), Image.new('RGB', (64, 32), 'red')], (32, 64))
    assert len(maps) == 4 and all(m.shape == (2, 2, 4, 16) for m in maps)
    assert merged.shape == (2, 1, 2, 16)
    assert all(torch.isfinite(m).all() and not m.requires_grad for m in maps)
