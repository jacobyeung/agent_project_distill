"""Frozen-C1 grounding training, training-scene calibration and retained checkpoints."""
import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch import distributed as dist, nn
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data import DataLoader, Dataset, Sampler

from .grounding_features import capture, phrase_embeddings
from .p3_provenance import digest, file_pin, load, pinned, sha256, write

QUESTION = 'Locate the objects in the video.'


def bind_frames(cfg):
    from . import orchard_paths
    if cfg.get('frame_root'):
        root = Path(cfg['frame_root'])
        existing = os.environ.get('STUDENT_FRAME_ROOT_MAP')
        pairs = json.loads(existing) if existing and existing.startswith('{') else {}
        if existing and not existing.startswith('{'):
            source, destination = existing.split('=', 1)
            pairs[source] = destination
        if '/data2' in pairs and Path(pairs['/data2']) != root:
            raise ValueError('Configured frame root differs from the active data2root binding')
        pairs['/data2'] = str(root)
        os.environ['STUDENT_FRAME_ROOT_MAP'] = json.dumps(pairs)
        orchard_paths.resolve_read('/data2/k8pd')


def load_runtime(cfg, device):
    from . import carrier_c1_run as c1
    value = cfg['c1_config']
    native = load(pinned(value) if isinstance(value, dict) else value)
    from .trace_version import resolve
    resolve(load(pinned(cfg['base_artifact'])),cfg)
    receipt, manifest = c1.prepared(native, admission=True)
    if (native.get('frame_layout') != 'duplicate' or not native.get('frame_markers')
            or native.get('training_mode') != 'final' or not native.get('depth_enabled', True)
            or native.get('carrier_placement') != 'append_after_temporal_group_video_tokens_v1'):
        raise ValueError('GH0 requires final C1_A, duplicate frames, markers and private depth')
    processor = c1.processor_for_receipt(manifest, receipt)
    model = c1.load_model(manifest, receipt, processor)
    artifact = c1.load_artifact(model, cfg['base_artifact'])
    if artifact['base_identity'] != native['base_identity'] or artifact['config_sha256'] != c1.identity(native):
        raise ValueError('GH base artifact/config identity differs')
    from .trace_version import bind, resolve
    if native.get('trace_program_version') is not None:resolve(artifact,native)
    bind(model,artifact,cfg)
    model.to(device).eval().requires_grad_(False)
    return model, processor, native


def clip_row(clip):
    indices, hashes = clip['frame_indices'], clip['frame_sha256']
    if len(indices) != 32 or len(hashes) != 32 or any(type(i) is not int or i < 0 for i in indices):
        raise ValueError('GH rows require 32 original frame identities')
    if any(len(h) != 64 or any(c not in '0123456789abcdef' for c in h) for h in hashes):
        raise ValueError('Invalid RGB SHA256')
    row = dict(qid=str(clip['qid']), scene=clip['scene'], category='pointing', student_input=dict(
        frames=[dict(path=f'/data2/k8pd/{h[:2]}/{h}.png', sha256=h) for h in hashes],
        frame_indices=indices, timestamps=[i / 24 for i in indices], fps=24,
        total_num_frames=clip.get('total_num_frames', max(indices) + 1), question=QUESTION, options=[]))
    if clip.get('student_input'):
        source = clip['student_input']
        if source['frame_indices'] != indices or [f['sha256'] for f in source['frames']] != hashes:
            raise ValueError('Grounding RGB pins differ from the clip')
        row['student_input'] = {**source, 'question': QUESTION, 'options': []}
    return row


def make_index(cfg):
    from .grounding_targets import build_index
    paths = cfg['clips_jsonl']
    if isinstance(paths, str):
        paths = [paths]
    index = build_index(paths, exclude_scenes=cfg.get('exclude_scenes', []),
                        holdout_fraction=cfg.get('holdout_fraction', .05), seed=17,
                        remove_files=cfg.get('remove_files', ()),
                        ground_target_filter=cfg.get('ground_target_filter', False))
    roots = {}
    for path in paths:
        with Path(path).open() as stream:
            for line in stream:
                row = json.loads(line)
                key = (row['scene'], str(row['qid']))
                source = Path(row['path'])
                resolved = source if source.is_absolute() else Path(path).resolve().parent / source
                if key in roots and roots[key] != resolved:
                    raise ValueError('Ambiguous r7 clip identity')
                roots[key] = resolved
    for split in ('train', 'val'):
        index[split] = [{**row, 'path': str(roots[(row['scene'], str(row['qid']))])} for row in index[split]]
    train, val = ({row['scene'] for row in index[key]} for key in ('train', 'val'))
    if not train or not val or train & val or (train | val) & set(cfg.get('exclude_scenes', [])):
        raise ValueError('GH requires nonempty scene-disjoint, evaluation-excluded splits')
    return index


class IgnoredClip(ValueError):
    """An intact raster has no eligible supervision."""


class ClipDataset(Dataset):
    def __init__(self, entries, vocab, processor, native, cfg):
        self.entries, self.vocab, self.processor = entries, vocab, processor
        self.native, self.cfg = native, cfg
        rules = next((row['ground_target_filter'] for row in entries if 'ground_target_filter' in row), None)
        self.target_filter = None
        if rules is not None:
            from .ground_target_filter import TargetFilter
            self.target_filter = TargetFilter(rules['removals'], shape_filter=rules['shape_filter'])
            if rules != self.target_filter.settings() or any(row.get('ground_target_filter') != rules for row in entries):
                raise ValueError('Grounding target-filter rules differ across rows')

    def validate_targets(self, clip):
        if self.target_filter is not None:
            actual = self.target_filter.clip(clip)
            if actual['ignored_targets'] != clip['ignored_targets']:
                raise ValueError('Prepared grounding target exclusions differ from native masks/rules')

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, index):
        if isinstance(index, tuple):
            primary, position, rank, world = index
            candidates = iter_with_first(primary, iter(EpochSampler(len(self), rank, world, position + 1)))
        else:
            candidates = ((index + offset) % len(self) for offset in range(len(self)))
        tried = set()
        for candidate in candidates:
            if candidate in tried:
                continue
            tried.add(candidate)
            try:
                return self._item(candidate)
            except IgnoredClip:
                if len(tried) == len(self):
                    break
        raise ValueError('No eligible grounding clips remain in the dataset')

    def _item(self, index):
        from .carrier_c1_canary import prompt_batch
        from .grounding_targets import units_for_clip, to_tensors
        from .orchard_paths import resolve_read
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
            raise ValueError('GH requires 32 equal complete frame grids')
        units = units_for_clip({**clip, 'path': str(path)}, (h // 2, w // 2), self.vocab,
            max_visible=self.cfg.get('max_visible', 24), absent_share=self.cfg.get('absent_share', .10),
            seed_key=str(clip['qid']))
        if not units.labels or not (units.presence == 1).any():
            raise IgnoredClip('Clip has no eligible grounding labels')
        return dict(batch=batch, targets=to_tensors(units), labels=units.labels, units=units,
                    path=str(path), clip=clip, n_used=n_used)


def iter_with_first(first, rest):
    yield first
    yield from rest


class EpochSampler(Sampler):
    def __init__(self, size, rank, world_size, position=0, with_fallback=False):
        if size < 1 or not 0 <= rank < world_size:
            raise ValueError('Invalid GH sampler topology')
        self.size, self.rank, self.world = size, rank, world_size
        self.position = position
        self.with_fallback = with_fallback

    def __len__(self):
        return math.ceil(self.size / self.world)

    def __iter__(self):
        epoch_size = len(self)
        epoch, offset = divmod(self.position, epoch_size)
        while True:
            generator = torch.Generator().manual_seed(17 + epoch)
            order = torch.randperm(self.size, generator=generator).tolist()
            count = epoch_size * self.world
            order = (order * math.ceil(count / self.size))[:count]
            for local, index in enumerate(order[self.rank:count:self.world][offset:], offset):
                yield ((index, epoch * epoch_size + local, self.rank, self.world)
                       if self.with_fallback else index)
            epoch, offset = epoch + 1, 0


def one_item(items):
    return items[0]


def make_loader(dataset, rank, world, position, workers):
    sampler = EpochSampler(len(dataset), rank, world, position, with_fallback=True)
    generator = torch.Generator().manual_seed(17000 + rank)
    kwargs = {'timeout': 60} if workers else {}
    if workers and torch.cuda.is_initialized(): kwargs['multiprocessing_context'] = 'spawn'
    return DataLoader(dataset, batch_size=1, sampler=sampler, collate_fn=one_item,
                      num_workers=workers, generator=generator, **kwargs)


class TrainHead(nn.Module):
    def __init__(self, head):
        super().__init__()
        self.head = head

    def forward(self, taps, vit, grid, embeds, mask):
        memory = self.head.encode_video(taps, vit, grid)
        query = self.head.encode_query(embeds, mask)
        return self.head(memory, query)


def new_head(model, cfg):
    from .grounding_head import GHConfig, GroundingHead
    settings = {**cfg.get('head', {}), 'lm_dim': model.config.text_config.hidden_size,
                'vit_dim': model.config.vision_config.hidden_size}
    return GroundingHead(GHConfig(**settings)).float()


def capture_clip(model, processor, item, device):
    from .carrier_c1_run import move
    features = capture(model, move(item['batch'], device))
    embeds, mask = phrase_embeddings(model, processor.tokenizer, item['labels'])
    return features, embeds, mask


def forward_clip(model, processor, wrapped, item, device):
    features, embeds, mask = capture_clip(model, processor, item, device)
    return wrapped(features.taps, features.vit, features.grid, embeds, mask), features


def lr_multiplier(step, budget):
    warmup = max(1, math.ceil(.03 * budget))
    if step < warmup:
        return (step + 1) / warmup
    progress = min(1., (step - warmup) / max(1, budget - warmup))
    return .5 * (1 + math.cos(math.pi * progress))


def rng_state(device):
    return dict(python=random.getstate(), numpy=np.random.get_state(), torch=torch.get_rng_state(),
                cuda=torch.cuda.get_rng_state(device) if device.type == 'cuda' else None)


def set_rng(state, device):
    random.setstate(state['python'])
    np.random.set_state(state['numpy'])
    torch.set_rng_state(state['torch'].cpu())
    if device.type == 'cuda':
        torch.cuda.set_rng_state(state['cuda'].cpu(), device)


def checkpoint(root, head, optimizer, scheduler, step, elapsed, tau, best, checked, cfg, device, rank, world):
    states = [None] * world
    state = rng_state(device)
    if world > 1:
        dist.all_gather_object(states, state)
    else:
        states[0] = state
    def save():
        directory = Path(root) / 'checkpoints' / f'step_{step:08d}'
        directory.mkdir(parents=True, exist_ok=False)
        journals = {name: (Path(root) / name).read_bytes() for name in ('metrics.jsonl', 'validation.jsonl')
                    if (Path(root) / name).exists()}
        payload = dict(head=head.state_dict(), optimizer=optimizer.state_dict(), scheduler=scheduler.state_dict(),
            step=step, sampler_position=step, rng=states, world_size=world, config_sha256=training_identity(cfg),
            elapsed=elapsed, tau=tau, best=best, failfast_checked=checked, head_config=asdict(head.cfg), journals=journals)
        with (directory / 'state.pt').open('xb') as stream:
            torch.save(payload, stream)
        write(directory / 'complete.json', dict(step=step, state=file_pin(directory / 'state.pt')))
    rank_zero_action(save, rank, world)


def training_identity(cfg):
    return digest({k: v for k, v in cfg.items() if k not in ('output', 'resume', 'device')})


def latest_checkpoint(root):
    candidates = sorted((Path(root) / 'checkpoints').glob('step_*/complete.json'))
    return candidates[-1] if candidates else None


def restore(path, head, optimizer, scheduler, cfg, device, rank, world):
    receipt = load(path)
    state = torch.load(pinned(receipt['state']), map_location=device, weights_only=False)
    if state['config_sha256'] != training_identity(cfg) or state['world_size'] != world:
        raise ValueError('Checkpoint configuration or rank topology differs')
    if receipt['step'] != state['step'] or state['sampler_position'] != state['step']:
        raise ValueError('Checkpoint sampler position differs')
    head.load_state_dict(state['head'], strict=True)
    optimizer.load_state_dict(state['optimizer'])
    scheduler.load_state_dict(state['scheduler'])
    set_rng(state['rng'][rank], device)
    return state


def restore_journals(root, state):
    for name in ('metrics.jsonl', 'validation.jsonl'):
        path = Path(root) / name
        prefix = state['journals'].get(name, b'')
        current = path.read_bytes() if path.exists() else b''
        if not current.startswith(prefix):
            raise ValueError('Checkpoint journal prefix changed: ' + name)
        if current != prefix:
            path.rename(path.with_name(f'{name}.superseded-{time.time_ns()}'))
            with path.open('xb') as stream:
                stream.write(prefix)


def presence_auroc(labels, scores):
    labels, scores = np.asarray(labels, bool), np.asarray(scores, float)
    positive, negative = int(labels.sum()), int((~labels).sum())
    if not positive or not negative:
        return None
    order = np.argsort(scores, kind='stable')
    sorted_scores = scores[order]
    ranks = np.empty(len(scores), float)
    start = 0
    while start < len(scores):
        end = start + 1
        while end < len(scores) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2
        start = end
    return float((ranks[labels].sum() - positive * (positive + 1) / 2) / (positive * negative))


def choose_tau(labels, scores):
    labels, scores = np.asarray(labels, bool), np.asarray(scores, float)
    if not len(labels) or not labels.any() or labels.all() or not np.isfinite(scores).all():
        raise ValueError('Training calibration requires finite positive and negative presence entries')
    if (scores < 0).any() or (scores > 1).any():
        raise ValueError('Calibration scores must be probabilities')
    order = np.argsort(scores, kind='stable')
    positives = np.r_[0, np.cumsum(labels[order])]
    negatives = np.r_[0, np.cumsum(~labels[order])]
    candidates = np.unique(np.r_[0., scores, 1.])
    cuts = np.searchsorted(scores[order], candidates, side='left')
    balanced = .5 * ((positives[-1] - positives[cuts]) / positives[-1] + negatives[cuts] / negatives[-1])
    best = int(balanced.argmax())
    return float(candidates[best]), float(balanced[best])


@torch.no_grad()
def calibrate_training(model, processor, head, dataset, device, n_clips):
    if n_clips < 1:
        raise ValueError('Calibration requires a nonempty training-scene slice')
    wrapped = TrainHead(head).eval()
    labels, scores = [], []
    clip_ids, n_frames = [], 0
    for index in range(min(n_clips, len(dataset))):
        item = dataset[index]
        clip_ids.append(dict(scene=item['clip']['scene'], qid=str(item['clip']['qid'])))
        n_frames += item['n_used']
        out, _ = forward_clip(model, processor, wrapped, item, device)
        probability = head.decode(out)['prob'].detach().cpu().numpy()
        presence = item['units'].presence
        valid = np.isfinite(presence)
        labels.extend((presence[valid] == 1).tolist())
        scores.extend(probability[valid].tolist())
    tau, balanced = choose_tau(labels, scores)
    return tau, dict(split='train', clips=len(clip_ids), entries=len(labels), balanced_accuracy=balanced,
                     tau_slice=dict(clip_ids_sha256=digest(clip_ids), n_frames=n_frames,
                                    n_clips=len(clip_ids), val_used=False))


@torch.no_grad()
def validate(model, processor, head, dataset, device, tau, limit=200):
    from .grounding_targets import eval_masks, in_mask
    wrapped = TrainHead(head).eval()
    labels, scores = [], []
    hits = visible = absent = nulls = recalled = items = 0
    for index in range(len(dataset)):
        if items >= limit:
            break
        item = dataset[index]
        out, _ = forward_clip(model, processor, wrapped, item, device)
        decoded = head.decode(out)
        prob = decoded['prob'].detach().cpu().numpy()
        uv = decoded['uv'].detach().cpu().numpy()
        units = item['units']
        for q in range(min(len(item['labels']), limit - items)):
            items += 1
            valid = np.isfinite(units.presence[q])
            truth = units.presence[q] == 1
            predicted = prob[q] >= tau
            labels.extend(truth[valid].tolist())
            scores.extend(prob[q, valid].tolist())
            visible += int((valid & truth).sum())
            recalled += int((valid & truth & predicted).sum())
            absent += int((valid & ~truth).sum())
            nulls += int((valid & ~truth & ~predicted).sum())
            for f in np.flatnonzero(valid & truth & predicted):
                hits += int(in_mask(uv[q, f], eval_masks(units, q, f)))
    return dict(items=items, visible_frames=visible, absent_frames=absent,
                in_mask=hits / visible if visible else 0., null_on_absent=nulls / absent if absent else 0.,
                presence_auroc=presence_auroc(labels, scores), presence_recall=recalled / visible if visible else 0., tau=tau)


def export_artifact(directory, head, cfg, step, tau, metrics):
    from .grounding_head import save_artifact
    if not math.isfinite(tau):
        raise ValueError('Artifact requires a calibrated finite tau')
    assert metrics.get('step') == step, 'Artifact metrics must describe its own step'
    if metrics.get('tau') != tau:
        raise ValueError('Artifact metrics and export tau differ')
    tau_slice = metrics['calibration']['tau_slice']
    if metrics['calibration']['split'] != 'train' or tau_slice['val_used'] is not False:
        raise ValueError('Tau requires a training-only calibration slice')
    pinned(cfg['base_artifact'])
    save_artifact(directory, head, dict(schema='grounding-head-v1', config=asdict(head.cfg), tau=tau,
        tau_slice=tau_slice, tau_val_used=False, tau_frozen=True,
        filtered_clips=cfg.get('filtered_clips', {}), data_identity=cfg['data_identity'],
        base_artifact=cfg['base_artifact'], trainer_commit=cfg['trainer_commit'], step=step, metrics=metrics))


def evaluate_weights(model, processor, head, training, heldout, device, cfg, step):
    """Freeze training-slice tau for these weights before reading internal validation."""
    if {c['scene'] for c in training.entries} & {c['scene'] for c in heldout.entries}:
        raise ValueError('Calibration and validation scenes overlap')
    tau, calibration = calibrate_training(model, processor, head, training, device, cfg.get('calibration_clips', 20))
    metrics = validate(model, processor, head, heldout, device, tau)
    return tau, {**metrics, 'step': step, 'tau': tau, 'calibration': calibration}


def fail_fast(metrics, cfg):
    rule = cfg.get('fail_fast', {})
    return (not math.isfinite(metrics['in_mask']) or metrics['in_mask'] < rule.get('in_mask', .50)
            or metrics['presence_auroc'] is None or not math.isfinite(metrics['presence_auroc'])
            or metrics['presence_auroc'] < rule.get('auroc', .85))


def append_metric(path, value):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')
        stream.flush()


def rank_zero_action(action, rank, world):
    message = [None]
    if rank == 0:
        try:
            message[0] = {'value': action()}
        except Exception as exc:
            message[0] = {'error': f'{type(exc).__name__}: {exc}'}
    if world > 1: dist.broadcast_object_list(message, src=0)
    if 'error' in message[0]: raise RuntimeError(message[0]['error'])
    return message[0]['value']


def all_rank_action(action, world):
    result, error = None, None
    try:
        result = action()
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
    errors = [error]
    if world > 1:
        errors = [None] * world
        dist.all_gather_object(errors, error)
    if any(errors):
        raise RuntimeError('; '.join(f'rank {rank}: {value}' for rank, value in enumerate(errors) if value))
    return result


def train(cfg, *, runtime=None, index=None, stop_after_steps=None):
    from .carrier_c1_run import move
    rank, world = int(os.environ.get('RANK', 0)), int(os.environ.get('WORLD_SIZE', 1))
    device = torch.device(cfg.get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
    own_group = world > 1 and not dist.is_initialized()
    if device.type == 'cuda':
        device = torch.device('cuda', int(os.environ.get('LOCAL_RANK', rank)))
        torch.cuda.set_device(device)
        if world != 8:
            raise ValueError('GH0 GPU training requires eight one-node ranks')
        if int(os.environ.get('LOCAL_WORLD_SIZE', world)) != world:
            raise ValueError('GH0 supports one replicated-LM node')
    if own_group:
        dist.init_process_group('nccl' if device.type == 'cuda' else 'gloo')
    try:
        bind_frames(cfg)
        random.seed(17); np.random.seed(17); torch.manual_seed(17)
        model, processor, native = runtime or load_runtime(cfg, device)
        model.to(device).eval().requires_grad_(False)
        index = index or make_index(cfg)
        cfg = {**cfg, 'data_identity': digest(index), 'filtered_clips': index.get('filtered_clips', {})}
        training = ClipDataset(index['train'], index['vocab'], processor, native, cfg)
        heldout = ClipDataset(index['val'], index['vocab'], processor, native, cfg)
        head = new_head(model, cfg).to(device)
        optimizer = torch.optim.AdamW(head.parameters(), lr=1e-4, weight_decay=.01)
        budget = int(cfg['steps'])
        if budget < 1 or cfg.get('wall_minutes', 180) <= 0 or cfg.get('checkpoint_minutes', 10) <= 0:
            raise ValueError('Training budgets must be positive')
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: lr_multiplier(step, budget))
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
        iterator = iter(make_loader(training, rank, world, step, int(cfg.get('num_workers', 0))))
        started, saved_at, saved_step = time.monotonic(), time.monotonic(), step if latest else -1
        fail_minutes = cfg.get('fail_fast_minutes', 30)
        stopped = False
        while step < budget and (stop_after_steps is None or step < stop_after_steps):
            tick = time.monotonic()
            wrapped.train()
            if device.type == 'cuda': torch.cuda.reset_peak_memory_stats(device)
            item = all_rank_action(lambda: next(iterator), world)
            optimizer.zero_grad(set_to_none=True)
            features, embeds, mask = all_rank_action(lambda: capture_clip(model, processor, item, device), world)
            out = wrapped(features.taps, features.vit, features.grid, embeds, mask)
            def loss():
                parts = head.loss(out, move(item['targets'], device))
                if not all(bool(torch.isfinite(value)) for value in parts.values()):
                    raise ValueError('Nonfinite GH loss')
                return parts
            parts = all_rank_action(loss, world)
            parts['total'].backward()
            grad = nn.utils.clip_grad_norm_(head.parameters(), 1., error_if_nonfinite=True)
            optimizer.step(); scheduler.step(); step += 1
            values = torch.tensor([float(parts[k].detach()) for k in ('total', 'presence', 'heat', 'point')], device=device)
            if world > 1:
                dist.all_reduce(values); values /= world
            if device.type == 'cuda': torch.cuda.synchronize(device)
            total_elapsed = elapsed + time.monotonic() - started
            def record_metric():
                append_metric(output / 'metrics.jsonl', dict(step=step,
                    **dict(zip(('loss', 'presence', 'heat', 'point'), values.tolist())), seconds=time.monotonic() - tick,
                    peak_memory=torch.cuda.max_memory_allocated(device) if device.type == 'cuda' else 0,
                    grad_norm=float(grad), prompt_tokens=features.hidden.shape[1], grid=list(features.grid), labels=len(item['labels'])))
            rank_zero_action(record_metric, rank, world)
            due = (cfg.get('eval_every', 100) > 0 and (step % cfg.get('eval_every', 100) == 0 or step == budget))
            due = due or (not checked and total_elapsed >= fail_minutes * 60)
            due = rank_zero_action(lambda: due, rank, world)
            if due:
                message = [None]
                if rank == 0:
                    try:
                        tau, metrics = evaluate_weights(model, processor, head, training, heldout, device, cfg, step)
                        if metrics['in_mask'] > best:
                            best = metrics['in_mask']
                            export_artifact(output / 'best' / f'step_{step:08d}', head, cfg, step, tau,
                                            metrics)
                        if not checked and total_elapsed >= fail_minutes * 60:
                            checked = True
                            stopped = cfg.get('fail_fast', {}).get('enabled', True) and fail_fast(metrics, cfg)
                            if stopped:
                                write(output / 'FAILFAST.json', dict(step=step, elapsed_seconds=total_elapsed, metrics=metrics))
                        append_metric(output / 'validation.jsonl', metrics)
                        message[0] = dict(tau=tau, best=best, checked=checked, stopped=stopped)
                    except Exception as exc:
                        message[0] = dict(error=f'{type(exc).__name__}: {exc}')
                if world > 1: dist.broadcast_object_list(message, src=0)
                if 'error' in message[0]: raise RuntimeError(message[0]['error'])
                tau, best, checked, stopped = (message[0][k] for k in ('tau', 'best', 'checked', 'stopped'))
            limit, save = rank_zero_action(lambda: (
                elapsed + time.monotonic() - started >= cfg.get('wall_minutes', 180) * 60,
                time.monotonic() - saved_at >= cfg.get('checkpoint_minutes', 10) * 60), rank, world)
            if save or step == budget or stopped or limit or step == stop_after_steps:
                checkpoint(output, head, optimizer, scheduler, step, elapsed + time.monotonic() - started,
                           tau, best, checked, cfg, device, rank, world)
                saved_at, saved_step = time.monotonic(), step
            if stopped or limit: break
        if step != saved_step:
            checkpoint(output, head, optimizer, scheduler, step, elapsed + time.monotonic() - started,
                       tau, best, checked, cfg, device, rank, world)
        def final_export():
            if not stopped:
                destination = output / 'final' / f'step_{step:08d}'
                if not destination.exists():
                    final_tau, final_metrics = evaluate_weights(model, processor, head, training, heldout, device, cfg, step)
                    export_artifact(destination, head, cfg, step, final_tau, final_metrics)
        rank_zero_action(final_export, rank, world)
        return dict(step=step, failfast=bool(stopped))
    finally:
        if own_group: dist.destroy_process_group()


def first_batch(cfg, device=torch.device('cpu'), *, runtime=None, index=None):
    from .carrier_c1_run import move
    bind_frames(cfg)
    random.seed(17); np.random.seed(17); torch.manual_seed(17)
    model, processor, native = runtime or load_runtime(cfg, device)
    model.to(device).eval().requires_grad_(False)
    index = index or make_index(cfg)
    dataset = ClipDataset(index['train'], index['vocab'], processor, native, cfg)
    head = new_head(model, cfg).to(device)
    reports = []
    for rank in range(cfg.get('world_size', 8)):
        tick = time.monotonic()
        try:
            item = next(iter(make_loader(dataset, rank, cfg.get('world_size', 8), 0, cfg.get('num_workers', 0))))
            head.zero_grad(set_to_none=True)
            out, features = forward_clip(model, processor, TrainHead(head), item, device)
            parts = head.loss(out, move(item['targets'], device))
            parts['total'].backward()
            finite = dict(loss=all(bool(torch.isfinite(v)) for v in parts.values()),
                gradients=all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in head.parameters()),
                frozen=all(p.grad is None for p in model.parameters()),
                features=all(bool(torch.isfinite(v).all()) for v in [*features.taps, features.vit]))
            reports.append(dict(rank=rank, prompt_tokens=features.hidden.shape[1], grid=list(features.grid),
                labels=len(item['labels']), loss_parts={k: float(v.detach()) for k, v in parts.items()}, finite=finite,
                seconds=time.monotonic() - tick, ok=all(finite.values())))
        except Exception as exc:
            reports.append(dict(rank=rank, ok=False, error=f'{type(exc).__name__}: {exc}', seconds=time.monotonic() - tick))
    result = dict(schema='grounding-first-batch-v1', ranks=reports, ok=all(r['ok'] for r in reports))
    write(Path(cfg['output']) / 'FIRST_BATCH.json', result)
    return result


def calibrate_export(cfg, artifact=None, checkpoint_path=None, output=None):
    from .grounding_head import GHConfig, GroundingHead, load_artifact
    device = torch.device(cfg.get('device', 'cpu'))
    bind_frames(cfg)
    model, processor, native = load_runtime(cfg, device)
    index = make_index(cfg)
    cfg = {**cfg, 'data_identity': digest(index), 'filtered_clips': index.get('filtered_clips', {})}
    if artifact:
        head, meta = load_artifact(artifact)
        if meta['base_artifact'] != cfg['base_artifact']:
            raise ValueError('GH artifact has another base pin')
        if meta.get('data_identity') != cfg['data_identity']:
            raise ValueError('GH artifact was trained on another train/val split')
        step = meta['step']
    else:
        selected = Path(checkpoint_path) if checkpoint_path else latest_checkpoint(cfg['output'])
        if selected is None: raise ValueError('No GH checkpoint to export')
        state = torch.load(pinned(load(selected)['state']), map_location='cpu', weights_only=False)
        if state['config_sha256'] != training_identity(cfg): raise ValueError('Export checkpoint configuration differs')
        head = GroundingHead(GHConfig(**state['head_config']))
        head.load_state_dict(state['head'], strict=True)
        step = state['step']
    head.to(device).eval()
    training = ClipDataset(index['train'], index['vocab'], processor, native, cfg)
    heldout = ClipDataset(index['val'], index['vocab'], processor, native, cfg)
    tau, metrics = evaluate_weights(model, processor, head, training, heldout, device, cfg, step)
    export_artifact(output or Path(cfg['output']) / 'calibrated' / f'step_{step:08d}', head, cfg, step, tau,
                    metrics)
    return tau


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('train', 'first-batch', 'calibrate', 'export'):
        command = commands.add_parser(name)
        command.add_argument('--config', required=True)
        if name == 'first-batch': command.add_argument('--device', default='cpu')
        if name in ('calibrate', 'export'):
            command.add_argument('--artifact')
            command.add_argument('--checkpoint')
            command.add_argument('--output')
    args = parser.parse_args()
    cfg = load(args.config)
    if args.command == 'train':
        result = train(cfg)
        if result['failfast']: raise SystemExit(2)
    elif args.command == 'first-batch':
        if not first_batch(cfg, torch.device(args.device))['ok']: raise SystemExit(1)
    else:
        calibrate_export(cfg, args.artifact, args.checkpoint, args.output)


if __name__ == '__main__':
    main()
