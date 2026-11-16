"""CPU-only comparison on 32 authenticated training rows and one frozen ViT pass.

This diagnostic fits rotation on the training rows; it is not held-out evidence.
Both heads use width 256 instead of production 2048 to bound CPU work. The ViT
input width, four trunk blocks/refinements and spatial frontend are unchanged.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import resource
import sqlite3
import time

import torch
from torch.nn import functional as F

from .camera_head import CameraSupervision
from .decoupled_v import features, learning_rate, load_vision, tensor_identity, target_tensors
from .p3_provenance import write
from .spatial_pose import pool_grid

ROWS, STEPS, WIDTH, MIN_GROUPS = 32, 200, 256, 4


def selected_indices(count):
    """Seed-17 candidate order; the first 32 eligible 32-frame rows are used."""
    if count < ROWS:
        raise ValueError('The real-row check requires at least 32 training rows')
    return random.Random(17).sample(range(count), count)


def eligible(row, target):
    return (row.get('category') == 'camera_pose_only' and len(row['student_input']['frames']) == 32
            and sum(bool(v) for v in target['camera_mask']) >= MIN_GROUPS)


def rotation_metrics(prediction, target, mask):
    q = F.normalize(prediction[..., 3:7], dim=-1)
    qt = F.normalize(target[..., 3:7], dim=-1)
    errors = (2 * torch.acos((q * qt).sum(-1).abs().clamp(max=1)) * (180 / math.pi))[mask]
    if errors.numel() == 0 or not bool(torch.isfinite(errors).all()):
        raise ValueError('Missing or nonfinite rotation errors')
    return dict(mean_deg=float(errors.mean()), median_deg=float(errors.quantile(.5)), count=errors.numel())


def fit_variant(settings, states, grids, targets, masks, recipe, steps=STEPS, width=WIDTH):
    """Full-batch optimizer steps over the same rows; only rotation is supervised."""
    cfg = {**copy.deepcopy(settings), 'embed_dim': width, 'num_heads': min(16, width // 4),
           'point_depth': None, 'weight_gravity': 0., 'weight_scale': 0.,
           'weight_trans': 0., 'weight_focal': 0., 'trajectory_balance': False}
    cfg.pop('freeze_modules', None)
    torch.manual_seed(31)
    head = CameraSupervision(states.shape[-1], cfg).cpu().train()
    all_frames = states.shape[1] == 32
    if all_frames:
        head.frame_queries = torch.nn.Parameter(torch.zeros(32, states.shape[-1]))
    cfg = head.settings
    # Equal common parameters despite the new frontend consuming RNG at init.
    common = {**cfg}
    common.pop('pose_input', None)
    torch.manual_seed(31)
    baseline = CameraSupervision(states.shape[-1], common)
    head.load_state_dict(baseline.state_dict(), strict=False)
    del baseline
    optimizer = torch.optim.AdamW(head.parameters(), lr=recipe['learning_rate'],
                                  weight_decay=recipe['weight_decay'])
    def predict():
        inputs = dict(spatial_grids=grids)
        value = states
        if all_frames:
            if head.spatial_pose is None:
                value = value + head.frame_queries[None]
            else:
                inputs['frame_queries'] = head.frame_queries
        return head.predict_all(value, **inputs)[0]
    start = time.perf_counter()
    with torch.no_grad():
        initial = rotation_metrics(predict()[-1], targets, masks)
    losses = []
    for step in range(1, steps + 1):
        stages = predict()
        count = len(stages)
        loss = cfg['weight'] * sum(cfg['stage_gamma'] ** (count - i - 1) *
            head.stage_loss(p, targets, masks, torch.ones(states.shape[0]))
            for i, p in enumerate(stages)).mean() / count
        if not bool(torch.isfinite(loss)):
            raise ValueError('Nonfinite overfit loss')
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(head.parameters(), 1., error_if_nonfinite=True)
        for group in optimizer.param_groups:
            group['lr'] = learning_rate(step, recipe)
        optimizer.step()
        if step == 1 or step % 25 == 0:
            losses.append(dict(step=step, loss=float(loss.detach()), grad_norm=float(norm)))
    with torch.no_grad():
        final = rotation_metrics(predict()[-1], targets, masks)
    return dict(initial=initial, final=final, seconds=time.perf_counter()-start,
                steps=steps, width=width, settings=cfg, losses=losses,
                parameters=sum(p.numel() for p in head.parameters()))


def real_row_overfit(cfg, report_path):
    from .decoupled_v_run import SPATIAL_CAMERA, encode, identity, prepared, processor_for, update_smoke
    if os.environ.get('CUDA_VISIBLE_DEVICES', '') != '':
        raise ValueError('The overfit diagnostic requires CUDA hidden')
    if Path(report_path).exists():
        raise ValueError('Refusing to overwrite an overfit report')
    started = time.perf_counter()
    report = dict(schema='pose-real-row-overfit-v1', status='FAIL',
                  config_sha256=identity(cfg), rows=ROWS, steps=STEPS,
                  scope='training-row rotation fit; frozen base ViT; no held-out claim',
                  phase='preparation', variants={})
    report_path = Path(report_path)
    write(report_path, report)  # Claim this unique report before any expensive work.
    try:
        threads = min(32, int(os.environ.get('SLURM_CPUS_PER_TASK', '32')))
        if threads < 1:
            raise ValueError('Invalid CPU allocation')
        # Use the allocation for the large ViT; fit-thread policy is set below.
        torch.set_num_threads(threads)
        report['allocated_cpus'] = threads
        report['feature_threads'] = torch.get_num_threads()
        receipt, manifest = prepared(cfg, require_admission=True)
        if cfg.get('camera_overrides') != SPATIAL_CAMERA:
            raise ValueError('The comparison must bind spatial_tokens_v1 in camera_overrides')
        report['preparation'] = cfg['preparation']
        report['database'] = receipt['database']
        candidates = selected_indices(receipt['count'])
        report['selection'] = ('seed-17 order over all prepared rows; first 32 camera_pose_only rows with 32 frames '
                               'and at least %d supervised camera groups' % MIN_GROUPS)
        settings = copy.deepcopy(receipt['settings'])
        report['production_width'] = settings['camera']['embed_dim']
        report['cpu_width'] = WIDTH
        report['reduction_reason'] = 'Both pose trunks use width 256 for the one-hour CPU budget; spatial frontend is production width 256.'
        settings['feature_backing'] = 'decoupled_v'
        settings['camera'].update(embed_dim=WIDTH, num_heads=16)
        report['phase'] = 'load_vision'
        model = load_vision(manifest, settings).requires_grad_(False).eval()
        report['phase'] = 'processor'
        processor = processor_for(manifest['root'])
        states, grids, targets, masks, rows = [], [], [], [], []
        feature_start = time.perf_counter()
        report['phase'] = 'features'
        report['feature_forward_count'] = 0
        with sqlite3.connect('file:'+receipt['database']['path']+'?mode=ro', uri=True) as db, torch.no_grad():
            skipped = 0
            for index in candidates:
                if len(rows) == ROWS:
                    break
                record = db.execute('SELECT row,target FROM rows WHERE i=?', (index,)).fetchone()
                if record is None:
                    raise ValueError('Selected training row is absent')
                raw, raw_target = record
                row, target = json.loads(raw), json.loads(raw_target)
                if not eligible(row, target):
                    skipped += 1
                    continue
                batch = encode(processor, row)
                capture = features(model, batch)
                states.append(capture.states[0].float().clone())
                grid = capture.vits[0][-1]
                if cfg.get('all_frames'):
                    grid = grid[::2]
                grids.append(pool_grid(grid).detach().clone())
                tensors = target_tensors(target, all_frames=cfg.get('all_frames', False))
                targets.append(tensors['aux_camera_target'][0])
                masks.append(tensors['aux_camera_mask'][0])
                rows.append(dict(index=index, row_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                                 target_sha256=hashlib.sha256(raw_target.encode()).hexdigest(),
                                 grid=batch['video_grid_thw'].tolist(), pooled_shape=list(grids[-1].shape)))
                report['feature_forward_count'] += 1
                if len(rows) % 8 == 0:
                    report['wall_seconds'] = time.perf_counter()-started
                    update_smoke(report_path, report)
                del capture, batch
        if len(rows) != ROWS:
            raise ValueError('Fewer than 32 eligible 32-frame training rows')
        report['feature_seconds'] = time.perf_counter()-feature_start
        report['feature_forward_count'] = len(rows)
        report['indices'] = [r['index'] for r in rows]
        report['skipped_rows'] = skipped
        report['row_bindings'] = rows
        states, targets, masks = torch.stack(states), torch.stack(targets), torch.stack(masks)
        if states.requires_grad or any(g.requires_grad for g in grids):
            raise ValueError('Diagnostic feature cache is not frozen')
        if not bool(masks.any(1).all()) or not bool(torch.isfinite(targets[masks]).all()):
            raise ValueError('Invalid rotation supervision')
        cache = {'states': states, 'target': targets, 'mask': masks,
                 **{str(i): g for i, g in enumerate(grids)}}
        report['feature_target_sha256'] = tensor_identity(cache)
        report['feature_cache_bytes'] = sum(t.numel()*t.element_size() for t in cache.values())
        del model, processor, cache
        # The 64-cell spatial fit is too slow on one thread; fit on the allocation.
        torch.set_num_threads(threads)
        report['fit_threads'] = torch.get_num_threads()
        camera = copy.deepcopy(receipt['settings']['camera'])
        for variant in ('pooled', 'spatial_tokens_v1'):
            report['phase'] = 'fit_'+variant
            if variant == 'pooled':
                camera.pop('pose_input', None)
            else:
                camera['pose_input'] = variant
            report['variants'][variant] = fit_variant(camera, states, grids, targets, masks, cfg['recipe'])
            report['wall_seconds'] = time.perf_counter()-started
            update_smoke(report_path, report)
        pooled, spatial = (report['variants'][k]['final'] for k in ('pooled', 'spatial_tokens_v1'))
        report['spatial_better_mean_and_median'] = all(spatial[k] < pooled[k] for k in ('mean_deg', 'median_deg'))
        report['within_one_hour'] = time.perf_counter()-started < 3600
        report['status'] = 'PASS' if report['within_one_hour'] else 'OVER_BUDGET'
        report['phase'] = 'complete'
        return report
    except Exception as error:
        report['error_type'] = type(error).__name__
        raise
    finally:
        report['wall_seconds'] = time.perf_counter()-started
        report['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        update_smoke(report_path, report)
