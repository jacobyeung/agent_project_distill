"""Frozen-T0 mask-decoder training and training-scene threshold calibration."""
import argparse
import datetime
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import random
import resource
import time
from types import SimpleNamespace

import numpy as np
import torch
from torch import distributed as dist, nn
from torch.nn import functional as F
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data import DataLoader

from . import grounding_train as gh
from .grounding_train import (QUESTION, bind_frames, clip_row, EpochSampler, IgnoredClip,
    one_item, presence_auroc, rank_zero_action, all_rank_action, checkpoint, restore,
    latest_checkpoint, restore_journals, training_identity, append_metric)
from .p3_provenance import digest, load, pinned, sha256, write


def load_runtime(cfg, device):
    from .mdg_runtime import load_runtime as runtime
    model, processor, native = runtime(cfg, device)
    freeze_runtime(model, processor, device, offload_depth=cfg.get('offload_depth', False))
    return model, processor, native


def freeze_runtime(model, processor, device, offload_depth=False):
    # Keep T0's loaded dtypes (bf16 base, native fp32 buffers and heads): casting would change RoPE and the heads.
    model.mdg_tokenizer = processor.tokenizer
    model.mdg_video_processor = getattr(processor, 'video_processor', None)
    model.to(device=device).eval().requires_grad_(False)
    if offload_depth and hasattr(model.auxiliary_heads, 'depth'):
        model.auxiliary_heads.depth.to('cpu')


def split_index(index, cfg):
    index = {**index}
    if 'tau' not in index:
        scenes = sorted({r['scene'] for r in index['train']},
                        key=lambda s: (hashlib.sha256(s.encode()).hexdigest(), s))
        selected = set(scenes[:math.ceil(.05 * len(scenes))])
        index['tau'] = [r for r in index['train'] if r['scene'] in selected]
        index['train'] = [r for r in index['train'] if r['scene'] not in selected]
    groups = [{r['scene'] for r in index[k]} for k in ('train', 'tau', 'val')]
    if (not all(groups) or any(groups[i] & groups[j] for i in range(3) for j in range(i))
            or set.union(*groups) & set(cfg.get('exclude_scenes', []))):
        raise ValueError('MDG requires nonempty disjoint train/tau/val scenes without excluded scenes')
    return index


def make_index(cfg):
    return split_index(gh.make_index({**cfg, 'holdout_fraction': .05}), cfg)


def confuser_table(cfg):
    value = cfg['confusers']
    table = load(pinned(value) if isinstance(value, dict) else value)
    if cfg.get('confusers_sha256', digest(table)) != digest(table):
        raise ValueError('Confuser table changed after preparation')
    return table


class ClipDataset(gh.ClipDataset):
    def __init__(self, entries, vocab, processor, native, cfg, *, cache=False):
        super().__init__(entries, vocab, processor, native, cfg)
        self.confusers = confuser_table(cfg)
        self.cache = {} if cache else None

    def _item(self, index):
        from .carrier_c1_canary import prompt_batch
        from .mdg_targets import mdg_units_for_clip, to_tensors
        from .orchard_paths import resolve_read
        if self.cache is not None and index in self.cache:
            return self.cache[index]
        clip = self.entries[index]
        path = resolve_read(clip['path'])
        if sha256(path) != clip['sha256']:
            raise ValueError('r7 raster hash differs')
        self.validate_targets({**clip, 'path': str(path)})
        with np.load(path, allow_pickle=False) as data:
            n_used = int(data['used'].sum())
        if n_used < 8:
            raise IgnoredClip('Clip requires at least eight used frames')
        batch = prompt_batch(self.processor, clip_row(clip), self.native)
        frames, h, w = map(int, batch['video_grid_thw'][0])
        if frames != 32 or h % 2 or w % 2:
            raise ValueError('MDG requires 32 equal complete frame grids')
        units = mdg_units_for_clip({**clip, 'path': str(path)}, self.vocab, self.confusers,
            max_visible=self.cfg.get('max_visible', 24), absent_share=self.cfg.get('absent_share', .30),
            confuser_share=.5, seed_key=str(clip['qid']))
        if not units.labels or not (units.frame_presence == 1).any():
            raise IgnoredClip('Clip has no eligible MDG labels')
        item = dict(batch=batch, targets=to_tensors(units), labels=units.labels, units=units,
                    path=str(path), clip=clip, n_used=n_used)
        if self.cache is not None:
            self.cache[index] = item
        return item


def make_loader(dataset, rank, world, position, workers):
    kwargs = dict(timeout=60, multiprocessing_context='fork', prefetch_factor=2) if workers else {}
    return DataLoader(dataset, batch_size=1,
        sampler=EpochSampler(len(dataset), rank, world, position, with_fallback=True), collate_fn=one_item,
        num_workers=workers, generator=torch.Generator().manual_seed(17000 + rank), **kwargs)


class TrainHead(nn.Module):
    def __init__(self, head):
        super().__init__()
        self.head = head

    def forward(self, taps, vit, pixels, grid, query, phrase, phrase_mask, targets=None):
        video = self.head.encode_video(taps, vit, pixels, grid)
        outs = self.head(video, query, phrase, phrase_mask)
        return outs if targets is None else self.head.loss(outs, targets)


def new_head(model, cfg):
    from .mask_grounding_head import MDGConfig, MaskGroundingHead
    settings = {**cfg.get('head', {}), 'lm_dim': model.config.text_config.hidden_size,
                'vit_dim': model.config.vision_config.hidden_size}
    if cfg.get('stem_weights'):
        settings['stem_weights'] = cfg['stem_weights']
    return MaskGroundingHead(MDGConfig(**settings)).float()


def synchronize(device):
    if device.type == 'cuda':
        torch.cuda.synchronize(device)


@torch.no_grad()
def capture_clip(model, item, device, chunk=8):
    from .carrier_c1_run import move
    from .mdg_features import capture_prefix, suffix_states
    synchronize(device)
    tick = time.monotonic()
    with torch.autocast(device_type=device.type, enabled=False):
        prefix = capture_prefix(model, move(item['batch'], device))
        synchronize(device)
        prefill = time.monotonic() - tick
        tick = time.monotonic()
        suffix = suffix_states(model, prefix, item['labels'], chunk=chunk)
        synchronize(device)
    inputs = (prefix.taps, prefix.vit, prefix.pixels, prefix.grid,
              suffix.query, suffix.phrase, suffix.phrase_mask)
    info = dict(prefill=prefill, suffix=time.monotonic() - tick,
                prompt_tokens=prefix.prefix_len, grid=list(prefix.grid))
    # Keep only head inputs; neither the full hidden state nor the KV/GDN cache survives.
    del prefix, suffix
    return inputs, info


def forward_clip(model, wrapped, item, device, cfg, targets=None):
    inputs, info = capture_clip(model, item, device, cfg.get('label_chunk', 8))
    return wrapped(*inputs, targets=targets), info


def lr_multiplier(step, budget, warmup=300):
    if warmup < 0:
        raise ValueError('Warmup must be nonnegative')
    if step < warmup:
        return (step + 1) / warmup
    progress = min(1., (step - warmup) / max(1, budget - warmup))
    return .5 * (1 + math.cos(math.pi * progress))


def evaluation_units(item):
    from .grounding_targets import _raster
    _, _, inst, _, labels, rgb_wh = _raster({**item['clip'], 'path': item['path']})
    label_ids = {}
    for iid, label in labels.items():
        label_ids.setdefault(label, []).append(iid)
    return SimpleNamespace(labels=item['labels'], _inst=inst, _label_ids=label_ids, _rgb_wh=rgb_wh)


@torch.no_grad()
def collect_outputs(model, head, dataset, device, cfg, *, limit=None, n_clips=None, predictor=None):
    from .grounding_targets import eval_masks, in_mask
    wrapped = TrainHead(head).eval()
    records = dict(labels=[], scores=[], point_hits=[], null_scores=[], mask_ious=[],
                   clip_labels=[], clip_scores=[], clips=[], items=0)
    count = len(dataset) if n_clips is None else min(n_clips, len(dataset))
    for index in range(count):
        if limit is not None and records['items'] >= limit:
            break
        item = dataset[index]
        if predictor is None:
            outs, _ = forward_clip(model, wrapped, item, device, cfg)
        else:
            outs = predictor(item)
        final = outs[-1]
        decoded = head.decode(final)
        prob = decoded['prob'].detach().float().cpu().numpy()
        uv = decoded['uv'].detach().cpu().numpy()
        masks = decoded['mask'].detach().cpu()
        units = item['units']
        evaluation = evaluation_units(item)
        records['clips'].append(dict(scene=item['clip']['scene'], qid=str(item['clip']['qid'])))
        q_count = len(item['labels']) if limit is None else min(len(item['labels']), limit - records['items'])
        for q in range(q_count):
            records['items'] += 1
            presence = units.frame_presence[q]
            valid = np.isfinite(presence)
            truth = presence == 1
            records['labels'].extend(truth[valid].tolist())
            records['scores'].extend(prob[q, valid].tolist())
            hits = np.zeros(len(presence), bool)
            for f in np.flatnonzero(truth):
                hits[f] = bool(in_mask(uv[q, f], eval_masks(evaluation, q, f)))
            records['point_hits'].extend(hits[valid].tolist())
            null = np.asarray(units.used) & ~units.masks[q].any(axis=(-2, -1))
            records['null_scores'].extend(prob[q, null].tolist())
            if truth.any():
                target = torch.from_numpy(units.masks[q, truth]).float()[:, None]
                target = F.interpolate(target, size=masks.shape[-2:], mode='nearest')[:, 0].bool()
                prediction = masks[q, torch.from_numpy(truth)]
                intersection = (target & prediction).sum((-2, -1)).float()
                union = (target | prediction).sum((-2, -1)).clamp_min(1)
                records['mask_ious'].extend((intersection / union).tolist())
            records['clip_labels'].append(bool(units.clip_present[q]))
            records['clip_scores'].append(float(final['clip_logit'][q].sigmoid()))
    if not np.isfinite(records['scores'] + records['null_scores'] + records['clip_scores']).all():
        raise ValueError('Nonfinite MDG evaluation probabilities')
    return records


def metrics_at(records, tau):
    labels = np.asarray(records['labels'], bool)
    scores = np.asarray(records['scores'], float)
    hits = np.asarray(records['point_hits'], bool)
    null = np.asarray(records['null_scores'], float)
    positive = int(labels.sum())
    return dict(items=records['items'], visible_frames=positive, absent_frames=len(null),
        in_mask=float((hits & labels & (scores >= tau)).sum() / positive) if positive else 0.,
        null_on_absent=float((null < tau).mean()) if len(null) else 0.,
        presence_recall=float((scores[labels] >= tau).mean()) if positive else 0.,
        presence_auroc=presence_auroc(labels, scores),
        mask_iou=float(np.mean(records['mask_ious'])) if records['mask_ious'] else 0.,
        clip_presence_auroc=presence_auroc(records['clip_labels'], records['clip_scores']), tau=float(tau))


def choose_tau(records):
    if not any(records['labels']) or not records['null_scores']:
        raise ValueError('Tau calibration requires positive and null training frames')
    labels = np.asarray(records['labels'], bool)
    hits = np.asarray(records['point_hits'], bool)[labels]
    scores = np.asarray(records['scores'], float)[labels]
    nulls = np.asarray(records['null_scores'], float)
    if not np.isfinite(np.r_[scores, nulls]).all():
        raise ValueError('Tau calibration requires finite probabilities')
    candidates = [(float(min((hits & (scores >= t)).mean(), (nulls < t).mean())), float(t))
                  for t in np.linspace(0., 1., 101)]
    objective, tau = max(candidates, key=lambda pair: pair[0])
    return tau, objective


def calibrate_training(model, head, dataset, device, cfg):
    n_clips = cfg.get('tau_clips', len(dataset))
    if not isinstance(n_clips, int) or n_clips < 1:
        raise ValueError('tau_clips must be a positive count within the frozen tau scenes')
    records = collect_outputs(model, head, dataset, device, cfg, n_clips=n_clips)
    tau, objective = choose_tau(records)
    return tau, dict(split='train', objective=objective, tau_slice=dict(
        clip_ids_sha256=digest(records['clips']), n_clips=len(records['clips']),
        scenes=sorted({r['scene'] for r in dataset.entries}), val_used=False, sampler_used=False))


def validate(model, head, dataset, device, tau, cfg):
    return metrics_at(collect_outputs(model, head, dataset, device, cfg,
                                     limit=cfg.get('val_items', 300)), tau)


def evaluate_weights(model, head, calibration, heldout, device, cfg, step):
    if {r['scene'] for r in calibration.entries} & {r['scene'] for r in heldout.entries}:
        raise ValueError('Tau and validation scenes overlap')
    tau, fit = calibrate_training(model, head, calibration, device, cfg)
    return tau, {**validate(model, head, heldout, device, tau, cfg), 'step': step, 'calibration': fit}


def fail_fast(metrics, cfg):
    return any(metrics.get(key) is None or not math.isfinite(metrics[key]) or metrics[key] < bar
               for key, bar in (('in_mask', .60), ('presence_auroc', .85), ('mask_iou', .35)))


def export_artifact(directory, head, cfg, step, tau, metrics):
    from .mask_grounding_head import save_artifact
    fit = metrics['calibration']
    if (not math.isfinite(tau) or not 0 <= tau <= 1 or metrics['step'] != step
            or metrics['tau'] != tau or fit['split'] != 'train'
            or fit['tau_slice']['val_used'] is not False or fit['tau_slice']['sampler_used'] is not False):
        raise ValueError('Export requires matching weights and training-only calibrated tau')
    pinned(cfg['base_artifact'])
    save_artifact(directory, head, dict(schema='mdg-head-v1', config=asdict(head.cfg), tau=tau,
        tau_slice=fit['tau_slice'], tau_val_used=False, tau_frozen=True,
        base_artifact=cfg['base_artifact'], trainer_commit=cfg['trainer_commit'], step=step,
        metrics=metrics, split_identity=cfg['split_identity'], data_identity=cfg['data_identity']))


def prepare(cfg, index):
    index = split_index(index, cfg)
    confusers = confuser_table(cfg)
    identity = digest(index)
    cfg = {**cfg, 'data_identity': identity, 'confusers_sha256': digest(confusers),
           'trainer_commit': cfg.get('trainer_commit', os.environ.get('TRAINER_COMMIT')),
           'split_identity': {k: dict(scenes=sorted({r['scene'] for r in index[k]}),
                                      clips_sha256=digest(index[k])) for k in ('train', 'tau', 'val')}}
    if cfg.get('stem_weights'):
        cfg['stem_weights_sha256'] = sha256(cfg['stem_weights'])
    return cfg, index


def datasets(index, processor, native, cfg):
    return tuple(ClipDataset(index[k], index['vocab'], processor, native, cfg, cache=k != 'train')
                 for k in ('train', 'tau', 'val'))


def train(cfg, *, runtime=None, index=None, stop_after_steps=None):
    from .carrier_c1_run import move
    rank, world = int(os.environ.get('RANK', 0)), int(os.environ.get('WORLD_SIZE', 1))
    device = torch.device(cfg.get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
    if device.type == 'cuda':
        device = torch.device('cuda', int(os.environ.get('LOCAL_RANK', rank)))
        torch.cuda.set_device(device)
    own_group = world > 1 and not dist.is_initialized()
    if own_group:
        # Rank-zero validation and tau fits hold the other ranks in a collective; allow it an hour.
        dist.init_process_group('nccl' if device.type == 'cuda' else 'gloo', timeout=datetime.timedelta(minutes=60))
    try:
        bind_frames(cfg)
        random.seed(17); np.random.seed(17); torch.manual_seed(17)
        model, processor, native = runtime or load_runtime(cfg, device)
        freeze_runtime(model, processor, device, offload_depth=cfg.get('offload_depth', False))
        cfg, index = prepare(cfg, index or make_index(cfg))
        training, calibration, heldout = datasets(index, processor, native, cfg)
        head = new_head(model, cfg).to(device)
        optimizer = torch.optim.AdamW(head.parameters(), lr=cfg.get('lr', 2e-4), weight_decay=cfg.get('wd', .05))
        budget = int(cfg.get('steps', 7000))
        if budget < 1 or cfg.get('wall_budget_minutes', 180) <= 0 or cfg.get('checkpoint_minutes', 20) <= 0:
            raise ValueError('Training budgets must be positive')
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer,
            lambda step: lr_multiplier(step, budget, cfg.get('warmup', 300)))
        output = Path(cfg['output']); output.mkdir(parents=True, exist_ok=True)
        step, elapsed, tau, best, checked = 0, 0., .5, -1., False
        latest = latest_checkpoint(output)
        if latest and cfg.get('resume', True):
            state = restore(latest, head, optimizer, scheduler, cfg, device, rank, world)
            step, elapsed, tau, best, checked = (state[k] for k in ('step', 'elapsed', 'tau', 'best', 'failfast_checked'))
            rank_zero_action(lambda: restore_journals(output, state), rank, world)
        elif latest or (output / 'metrics.jsonl').exists():
            raise ValueError('Existing training output requires checkpoint resume')
        if (output / 'FAILFAST.json').exists():
            raise ValueError('A fail-fast run cannot resume')
        wrapped = TrainHead(head)
        if world > 1:
            wrapped = DistributedDataParallel(wrapped, device_ids=[device.index] if device.type == 'cuda' else None)
        iterator = iter(make_loader(training, rank, world, step, int(cfg.get('num_workers', 2))))
        started, saved_at, saved_step = time.monotonic(), time.monotonic(), step if latest else -1
        stopped = False
        while step < budget and (stop_after_steps is None or step < stop_after_steps):
            tick = time.monotonic()
            wrapped.train()
            if device.type == 'cuda': torch.cuda.reset_peak_memory_stats(device)
            item = all_rank_action(lambda: next(iterator), world)
            optimizer.zero_grad(set_to_none=True)
            inputs, info = all_rank_action(lambda: capture_clip(model, item, device, cfg.get('label_chunk', 8)), world)
            head_tick = time.monotonic()
            with torch.autocast(device_type=device.type, enabled=False):
                parts = wrapped(*inputs, targets=move(item['targets'], device))
            def check_loss():
                if not all(bool(torch.isfinite(value)) for value in parts.values()):
                    raise ValueError('Nonfinite MDG loss')
            all_rank_action(check_loss, world)
            parts['total'].backward()
            grad = all_rank_action(lambda: nn.utils.clip_grad_norm_(head.parameters(),
                cfg.get('clip', 1.), error_if_nonfinite=True), world)
            synchronize(device)
            head_seconds = time.monotonic() - head_tick
            optimizer.step(); scheduler.step(); step += 1
            keys = ('total', 'bce', 'dice', 'frame', 'clip', 'iou')
            values = torch.tensor([float(parts[k].detach()) for k in keys], device=device)
            if world > 1:
                dist.all_reduce(values); values /= world
            synchronize(device)
            rank_zero_action(lambda: append_metric(output / 'metrics.jsonl', dict(step=step,
                **dict(zip(('loss', *keys[1:]), values.tolist())), seconds=time.monotonic() - tick,
                seconds_prefill=info['prefill'], seconds_suffix=info['suffix'], seconds_head=head_seconds,
                peak_memory=torch.cuda.max_memory_allocated(device) if device.type == 'cuda' else 0,
                grad_norm=float(grad), prompt_tokens=info['prompt_tokens'], grid=info['grid'],
                labels=len(item['labels']), tau=tau, trainable_parameters=sum(p.numel() for p in head.parameters()
                    if p.requires_grad))), rank, world)
            del inputs, parts, item
            eval_every = cfg.get('eval_every', 200)
            due = eval_every > 0 and (step % eval_every == 0 or step == budget)
            if due:
                def evaluate():
                    nonlocal tau, best, checked, stopped
                    tau, metrics = evaluate_weights(model, head, calibration, heldout, device, cfg, step)
                    if metrics['in_mask'] > best:
                        best = metrics['in_mask']
                        export_artifact(output / 'best' / f'step_{step:08d}', head, cfg, step, tau, metrics)
                    if not checked and step >= cfg.get('failfast_step', 600):
                        checked = True
                        stopped = fail_fast(metrics, cfg)
                        if stopped:
                            write(output / 'FAILFAST.json', dict(step=step, metrics=metrics))
                    append_metric(output / 'validation.jsonl', metrics)
                    return dict(tau=tau, best=best, checked=checked, stopped=stopped)
                result = rank_zero_action(evaluate, rank, world)
                tau, best, checked, stopped = (result[k] for k in ('tau', 'best', 'checked', 'stopped'))
            limit, save = rank_zero_action(lambda: (
                elapsed + time.monotonic() - started >= cfg.get('wall_budget_minutes', 180) * 60,
                time.monotonic() - saved_at >= cfg.get('checkpoint_minutes', 20) * 60), rank, world)
            if save or step == budget or stopped or limit or step == stop_after_steps:
                checkpoint(output, head, optimizer, scheduler, step, elapsed + time.monotonic() - started,
                           tau, best, checked, cfg, device, rank, world)
                saved_at, saved_step = time.monotonic(), step
            if stopped or limit:
                break
        if step != saved_step:
            checkpoint(output, head, optimizer, scheduler, step, elapsed + time.monotonic() - started,
                       tau, best, checked, cfg, device, rank, world)
        def final_export():
            if not stopped:
                destination = output / 'final' / f'step_{step:08d}'
                if not destination.exists():
                    final_tau, metrics = evaluate_weights(model, head, calibration, heldout, device, cfg, step)
                    export_artifact(destination, head, cfg, step, final_tau, metrics)
        rank_zero_action(final_export, rank, world)
        return dict(step=step, failfast=bool(stopped))
    finally:
        if own_group:
            dist.destroy_process_group()


def first_batch(cfg, device=torch.device('cpu'), *, runtime=None, index=None):
    from .carrier_c1_run import move
    bind_frames(cfg)
    random.seed(17); np.random.seed(17); torch.manual_seed(17)
    model, processor, native = runtime or load_runtime(cfg, device)
    freeze_runtime(model, processor, device, offload_depth=cfg.get('offload_depth', False))
    cfg, index = prepare(cfg, index or make_index(cfg))
    dataset = ClipDataset(index['train'], index['vocab'], processor, native, cfg)
    head = new_head(model, cfg).to(device)
    reports = []
    world = cfg.get('world_size', 1)
    if type(world) is not int or world < 1:
        raise ValueError('first-batch world must be a positive integer')
    for rank in range(world):
        tick = time.monotonic()
        try:
            item = next(iter(make_loader(dataset, rank, world, 0, cfg.get('num_workers', 2))))
            inputs, info = capture_clip(model, item, device, cfg.get('label_chunk', 8))
            head.zero_grad(set_to_none=True)
            parts = TrainHead(head)(*inputs, targets=move(item['targets'], device))
            parts['total'].backward()
            finite = dict(loss=all(bool(torch.isfinite(v)) for v in parts.values()),
                gradients=all(p.grad is not None and bool(torch.isfinite(p.grad).all())
                              for p in head.parameters() if p.requires_grad),
                frozen=all(p.grad is None for p in model.parameters()),
                features=all(bool(torch.isfinite(v).all()) for v in [*inputs[0], *inputs[1],
                    inputs[2], inputs[4], inputs[5]]))
            reports.append(dict(rank=rank, prompt_tokens=info['prompt_tokens'], grid=info['grid'],
                Q=len(item['labels']), loss_parts={k: float(v.detach()) for k, v in parts.items()}, finite=finite,
                seconds=time.monotonic() - tick, peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                ok=all(finite.values())))
        except Exception as exc:
            reports.append(dict(rank=rank, ok=False, error=f'{type(exc).__name__}: {exc}',
                                seconds=time.monotonic() - tick))
    result = dict(schema='mdg-first-batch-v1', ranks=reports, ok=all(r['ok'] for r in reports))
    write(Path(cfg['output']) / 'FIRST_BATCH.json', result)
    return result


def calibrate_export(cfg, artifact=None, checkpoint_path=None, output=None):
    from .mask_grounding_head import MDGConfig, MaskGroundingHead, load_artifact
    device = torch.device(cfg.get('device', 'cpu'))
    bind_frames(cfg)
    model, processor, native = load_runtime(cfg, device)
    cfg, index = prepare(cfg, make_index(cfg))
    if artifact:
        head, meta = load_artifact(artifact)
        if meta['base_artifact'] != cfg['base_artifact'] or meta['data_identity'] != cfg['data_identity']:
            raise ValueError('MDG artifact base pin or split identity differs')
        step = meta['step']
    else:
        selected = Path(checkpoint_path) if checkpoint_path else latest_checkpoint(cfg['output'])
        if selected is None:
            raise ValueError('No MDG checkpoint to export')
        state = torch.load(pinned(load(selected)['state']), map_location='cpu', weights_only=False)
        if state['config_sha256'] != training_identity(cfg):
            raise ValueError('Export checkpoint configuration differs')
        head = MaskGroundingHead(MDGConfig(**state['head_config']))
        head.load_state_dict(state['head'], strict=True)
        step = state['step']
    head.to(device).eval()
    _, calibration, heldout = datasets(index, processor, native, cfg)
    tau, metrics = evaluate_weights(model, head, calibration, heldout, device, cfg, step)
    export_artifact(output or Path(cfg['output']) / 'calibrated' / f'step_{step:08d}',
                    head, cfg, step, tau, metrics)
    return tau


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('train', 'first-batch', 'calibrate', 'export'):
        command = commands.add_parser(name)
        command.add_argument('--config', required=True)
        if name == 'first-batch':
            command.add_argument('--device', default='cpu')
            command.add_argument('--world', type=int, default=1)
        if name in ('calibrate', 'export'):
            command.add_argument('--artifact')
            command.add_argument('--checkpoint')
            command.add_argument('--output')
    args = parser.parse_args(argv)
    cfg = load(args.config)
    if args.command == 'train':
        if train(cfg)['failfast']:
            raise SystemExit(2)
    elif args.command == 'first-batch':
        if not first_batch({**cfg, 'world_size': args.world}, torch.device(args.device))['ok']:
            raise SystemExit(1)
    else:
        calibrate_export(cfg, args.artifact, args.checkpoint, args.output)


if __name__ == '__main__':
    main()
