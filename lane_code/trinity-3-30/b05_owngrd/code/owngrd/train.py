"""Single-process T-1 trainer, validation metrics, stop rules, and exact CPU resume."""
import argparse
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field
import io
import json
import math
from pathlib import Path
import random
import time

import numpy as np
import torch

from .common import atomic_write_bytes, atomic_write_json, read_json, sha256_json
from .data import GroundingDataset
from .head import Config, GroundingHead
from .losses import compute_losses, mask_iou
from .vit import FrozenViT, DEFAULT_WEIGHTS, DEFAULT_BUNDLE


@dataclass
class Stopper:
    hours: float = 60.
    accelerator_hour_cap: float = 60.
    accelerators: int = 1
    fail_fast_checked: bool = False
    history: list = field(default_factory=list)
    stop_reason: str | None = None

    def stop(self, reason):
        self.stop_reason = reason
        return 'STOP', reason

    def decide(self, step, metrics=None, elapsed_seconds=0.):
        if self.stop_reason is not None:
            return 'STOP', self.stop_reason
        if elapsed_seconds >= self.hours*3600:
            return self.stop('wall_hour_cap')
        if elapsed_seconds*self.accelerators >= self.accelerator_hour_cap*3600:
            return self.stop('accelerator_hour_cap')
        if metrics is None:
            return 'CONTINUE', 'await_validation'
        if not all(math.isfinite(float(v)) for k, v in metrics.items() if isinstance(v, (int, float))):
            return self.stop('nonfinite_validation')
        if step >= 600 and not self.fail_fast_checked:
            self.fail_fast_checked = True
            if metrics['candidate_recall_at5'] < .70 or metrics['mask_iou_pos'] < .44:
                return self.stop('fail_fast_at_600')
        if step >= 2400 and metrics['false_presence_absent_at85'] > .10:
            return self.stop('false_presence_kill')
        if metrics.get('direct_slice_drop', 0.) > .02:
            return self.stop('direct_slice_guard')
        if ('branch_s_on_target' in metrics and metrics['candidate_recall_at5'] >= .88
                and metrics['on_target_share_at85'] >= metrics['branch_s_on_target']-.02):
            return self.stop('ready_for_clean_read')
        previous = [r for r in self.history if step-r['step'] >= 600]
        if previous:
            old = previous[-1]
            if (metrics['on_target_share_at85']-old['on_target_share_at85'] < .005
                    and metrics['mask_iou_pos']-old['mask_iou_pos'] < .01):
                return self.stop('plateau_600_steps')
        self.history.append(dict(step=step, **metrics))
        return 'CONTINUE', 'validation_passed'


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(min(torch.get_num_threads(), 16))


def make_optimizer(model, lr=1e-4, weight_decay=.01, warmup=100, steps=10000):
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay, foreach=False)
    def schedule(step):
        if step < warmup:
            return (step+1)/max(1, warmup)
        progress = min(1., (step-warmup)/max(1, steps-warmup))
        return .5*(1+math.cos(math.pi*progress))
    return optimizer, torch.optim.lr_scheduler.LambdaLR(optimizer, schedule)


def save_checkpoint(path, model, optimizer, scheduler, cursor, stopper, hashes, extra=None):
    state = dict(schema='owngrd-resume-v1', model=model.state_dict(), optimizer=optimizer.state_dict(),
        scheduler=scheduler.state_dict(), rng=dict(python=random.getstate(), numpy=np.random.get_state(),
        torch=torch.get_rng_state()), cursor=dict(cursor), stopper=asdict(stopper), hashes=dict(hashes), extra=extra or {})
    if next(model.parameters()).device.type == 'cuda':
        state['rng']['cuda'] = torch.cuda.get_rng_state_all()
    stream = io.BytesIO()
    torch.save(state, stream)
    atomic_write_bytes(path, stream.getvalue())


def load_checkpoint(path, model, optimizer, scheduler, hashes):
    # Checkpoints are trusted local training outputs, never downloaded pickle files.
    state = torch.load(path, map_location='cpu', weights_only=False)
    if state['schema'] != 'owngrd-resume-v1' or state['hashes'] != hashes:
        raise ValueError('Resume config/label/ViT/provenance hash mismatch')
    model.load_state_dict(state['model'], strict=True)
    optimizer.load_state_dict(state['optimizer'])
    scheduler.load_state_dict(state['scheduler'])
    random.setstate(state['rng']['python'])
    np.random.set_state(state['rng']['numpy'])
    torch.set_rng_state(state['rng']['torch'])
    if 'cuda' in state['rng']:
        torch.cuda.set_rng_state_all(state['rng']['cuda'])
    return state['cursor'], Stopper(**state['stopper']), state['extra']


def optimization_step(model, batch, targets, optimizer, scheduler, grad_clip=1.):
    model.train()
    optimizer.zero_grad(set_to_none=True)
    device = next(model.parameters()).device
    context = torch.autocast('cuda', dtype=torch.bfloat16) if device.type == 'cuda' else nullcontext()
    with context:
        out = model(**batch, selection_targets=targets)
        losses, details = compute_losses(out, targets, model.cfg)
    if not all(torch.isfinite(v).all() for v in losses.values()):
        raise FloatingPointError('Nonfinite training loss')
    losses['total'].backward()
    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip, error_if_nonfinite=True)
    optimizer.step()
    scheduler.step()
    return {k: float(v.detach()) for k, v in losses.items()}, details, float(norm)


class Metrics:
    def __init__(self):
        self.instances, self.covered, self.pos_iou, self.pairs = 0, 0, [], []
        self.selection_skipped = {}

    @torch.no_grad()
    def add(self, out, targets, details):
        for reason, count in details['selection_skipped'].items():
            self.selection_skipped[reason] = self.selection_skipped.get(reason, 0)+count
        for n, target in enumerate(targets):
            clusters = out['candidates'][n]
            overlaps = []
            ids = target['gt_instances']
            for members in clusters:
                by_id = {}
                for instance in ids:
                    values = [float(mask_iou(out['masks'][n, f, q].sigmoid(),
                        target['decoder'][f]['gt_masks'][instance].to(out['masks'])))
                        for f, q in members if instance in target['decoder'][f]['gt_masks']]
                    by_id[instance] = max(values, default=0.)
                overlaps.append(by_id)
            self.instances += len(ids)
            self.covered += sum(any(c.get(i, 0.) >= .5 for c in overlaps) for i in ids)
            for f, matched in enumerate(details['matches'][n]):
                for q, truth in matched:
                    if truth['cls'] == 'POS':
                        self.pos_iou.append(float(mask_iou(out['masks'][n, f, q].sigmoid(), truth['mask'].to(out['masks']))))
            if clusters:
                logits = out['selection'][n]
                chosen = int(logits[:-1].argmax())
                confidence = float((logits[chosen]-logits[-1]).sigmoid())
                correct = any(v >= .5 for v in overlaps[chosen].values())
            else:
                confidence, correct = 0., False
            self.pairs.append(dict(confidence=confidence, correct=correct, candidate=bool(clusters),
                                   absent=target['clip_presence'] == 0, ambiguous=len(ids) > 1))

    def result(self):
        # Fix coverage over all name/capture pairs using candidate-versus-none confidence.
        ordered = sorted(self.pairs, key=lambda p: -p['confidence'])
        accepted = ordered[:math.ceil(.85*len(ordered))]
        unambiguous = [p for p in accepted if not p['ambiguous']]
        absent = sum(p['absent'] for p in ordered)
        return dict(candidate_recall_at5=self.covered/max(self.instances, 1),
            mask_iou_pos=sum(self.pos_iou)/max(len(self.pos_iou), 1),
            on_target_share_at85=sum(p['correct'] for p in unambiguous)/max(len(unambiguous), 1),
            false_presence_absent_at85=sum(p['absent'] and p['candidate'] for p in accepted)/max(absent, 1),
            coverage=len(accepted)/max(len(ordered), 1), gt_instances=self.instances,
            matched_pos=len(self.pos_iou), absent_pairs=absent, pairs=len(ordered), selection_skipped=self.selection_skipped)


def encode_presence(vit, frames, presence_size=(160, 224), chunk=4):
    """Encode every frame at the configured shortlist resolution."""
    from .vit import frame_size
    size = frame_size(frames[0], presence_size)
    merged = []
    for start in range(0, len(frames), chunk):
        _, m = vit.taps(frames[start:start+chunk], size)
        merged.append(m)
    return torch.cat(merged)


def encode_item(vit, item, presence_size=(160, 224), merged=None):
    """Encode every frame cheaply for presence, then re-read selected decoder frames."""
    frames = item['frames']
    if merged is None:
        merged = encode_presence(vit, frames, presence_size)
    taps, _ = vit.taps([frames[i] for i in item['frame_ids'].tolist()], item['size_hw'])
    name = vit.name_query([item['name']])
    return dict(taps=taps, merged=merged, pixels=item['pixels'].to(vit.device),
                name_tokens=name.tokens, name_mask=name.mask, frame_ids=item['frame_ids'].to(vit.device))


@torch.no_grad()
def predict_clip(model, vit, frames, names, size_hw=(480, 640), presence_size=(160, 224)):
    """Shortlist all clip frames and return one decoded result per normalized name."""
    from .head import pooled_name
    from .vit import frame_size, rgb_tensor
    previous = model.training
    model.eval()
    try:
        merged = encode_presence(vit, frames, presence_size)
        query = vit.name_query(names)
        presence, _ = model.presence(merged, pooled_name(query.tokens, query.mask))
        choices = model.presence.shortlist(presence)
        results = []
        for n, chosen in enumerate(choices):
            size = frame_size(frames[0], size_hw)
            selected = [frames[i] for i in chosen]
            taps, _ = vit.taps(selected, size)
            results.append(model(taps, merged, rgb_tensor(selected, size).to(vit.device),
                query.tokens[n:n+1], query.mask[n:n+1], chosen))
        return results
    finally:
        model.train(previous)


@torch.no_grad()
def validate(model, vit, dataset, presence_size=(160, 224), deadline=None):
    from .head import pooled_name
    previous = model.training
    model.eval()
    metrics, logged = Metrics(), []
    # Validation sampling and Hungarian points cannot perturb the training RNG stream.
    python_rng, numpy_rng, torch_rng = random.getstate(), np.random.get_state(), torch.get_rng_state()
    cuda_rng = torch.cuda.get_rng_state_all() if next(model.parameters()).device.type == 'cuda' else None
    try:
        seed_all(1807)
        for index in range(len(dataset)):
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError('Validation reached the run hour cap')
            item = dataset[index]
            merged = encode_presence(vit, item['frames'], presence_size)
            query = vit.name_query([item['name']])
            logits, _ = model.presence(merged, pooled_name(query.tokens, query.mask))
            chosen = model.presence.shortlist(logits)[0]
            item = dataset.get_item(index, frame_ids=chosen)
            batch = encode_item(vit, item, presence_size, merged=merged)
            out = model(**batch)
            loss, details = compute_losses(out, [item['target']], model.cfg)
            metrics.add(out, [item['target']], details)
            logged.append({k: float(v) for k, v in loss.items()})
    finally:
        random.setstate(python_rng)
        np.random.set_state(numpy_rng)
        torch.set_rng_state(torch_rng)
        if cuda_rng is not None:
            torch.cuda.set_rng_state_all(cuda_rng)
        model.train(previous)
    result = metrics.result()
    result['losses'] = {k: sum(r[k] for r in logged)/len(logged) for k in logged[0]} if logged else {}
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--labels', required=True)
    ap.add_argument('--teacher-root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--weights', default=str(DEFAULT_WEIGHTS))
    ap.add_argument('--bundle', default=str(DEFAULT_BUNDLE))
    ap.add_argument('--config', help='JSON overrides for head Config')
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--hours', type=float, required=True)
    ap.add_argument('--accelerator-hour-cap', type=float, default=60.)
    ap.add_argument('--steps', type=int, default=10000)
    ap.add_argument('--warmup', type=int, default=100)
    ap.add_argument('--lr', type=float, default=1e-4)
    ap.add_argument('--weight-decay', type=float, default=.01)
    ap.add_argument('--grad-clip', type=float, default=1.)
    ap.add_argument('--validate-every', type=int, default=200)
    ap.add_argument('--checkpoint-every', type=int, default=200)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--size', type=int, nargs=2, default=[480, 640])
    ap.add_argument('--presence-size', type=int, nargs=2, default=[160, 224])
    ap.add_argument('--resume')
    a = ap.parse_args(argv)
    if a.hours <= 0 or min(a.steps, a.validate_every, a.checkpoint_every) <= 0:
        ap.error('Positive hour cap, steps, and intervals required')
    seed_all(a.seed)
    cfg = Config(**read_json(a.config)) if a.config else Config()
    train = GroundingDataset(a.manifest, a.labels, a.teacher_root, 'train', a.size, seed=a.seed)
    val = GroundingDataset(a.manifest, a.labels, a.teacher_root, 'train_val', a.size, seed=a.seed)
    if not len(train) or not len(val):
        raise ValueError('Both training rooms and training-room validation must be nonempty')
    vit = FrozenViT(a.weights, a.bundle, a.device)
    names = sorted({name for dataset in (train, val) for _, name in dataset.items})
    query = vit.name_query(names)
    run_config = {k: v for k, v in vars(a).items() if k not in ('out', 'resume', 'config')}
    run_config['head'] = asdict(cfg)
    run_config['runtime'] = dict(torch=torch.__version__, cpu_threads=torch.get_num_threads())
    hashes = dict(config=sha256_json(run_config), labels=sha256_json([train.label_sha256, val.label_sha256]),
                  vit=vit.sha256, name_rows=query.rows_sha256, tokenizer=query.tokenizer_sha256,
                  gate=train.gate.digest)
    model = GroundingHead(cfg).to(a.device)
    optimizer, scheduler = make_optimizer(model, a.lr, a.weight_decay, a.warmup, a.steps)
    cursor = dict(step=0, epoch=0, item=0)
    stopper = Stopper(hours=a.hours, accelerator_hour_cap=a.accelerator_hour_cap)
    extra = dict(elapsed_seconds=0.)
    if a.resume:
        cursor, stopper, extra = load_checkpoint(a.resume, model, optimizer, scheduler, hashes)
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(outdir/'RUN.json', dict(config=run_config, hashes=hashes, parameters=model.parameter_counts()))
    started, elapsed_before = time.monotonic(), extra['elapsed_seconds']
    reason, status = 'step_cap', 'CONTINUE'
    with open(outdir/'train.jsonl', 'a') as log:
        while cursor['step'] < a.steps:
            elapsed = elapsed_before + time.monotonic()-started
            status, reason = stopper.decide(cursor['step'], elapsed_seconds=elapsed)
            if status == 'STOP':
                break
            train.set_epoch(cursor['epoch'])
            item = train[cursor['item']]
            batch = encode_item(vit, item, tuple(a.presence_size))
            losses, details, norm = optimization_step(model, batch, [item['target']], optimizer, scheduler, a.grad_clip)
            cursor['step'] += 1
            cursor['item'] += 1
            if cursor['item'] == len(train):
                cursor['item'] = 0
                cursor['epoch'] += 1
            log.write(json.dumps(dict(event='train', **cursor, losses=losses, grad_norm=norm,
                lr=scheduler.get_last_lr()[0], selection_skipped=details['selection_skipped'], elapsed_seconds=elapsed))+'\n')
            if cursor['step'] % a.validate_every == 0 or cursor['step'] in (600, 2400):
                deadline = started + min(a.hours, a.accelerator_hour_cap)*3600-elapsed_before
                try:
                    metric = validate(model, vit, val, tuple(a.presence_size), deadline)
                except TimeoutError:
                    status, reason = stopper.stop('hour_cap_during_validation')
                    break
                elapsed = elapsed_before + time.monotonic()-started
                status, reason = stopper.decide(cursor['step'], metric, elapsed)
                log.write(json.dumps(dict(event='validation', step=cursor['step'], metrics=metric,
                                         status=status, reason=reason, elapsed_seconds=elapsed))+'\n')
            log.flush()
            if cursor['step'] % a.checkpoint_every == 0 or status == 'STOP':
                save_checkpoint(outdir/'resume.pt', model, optimizer, scheduler, cursor, stopper, hashes,
                                dict(elapsed_seconds=elapsed_before+time.monotonic()-started))
            if status == 'STOP':
                break
        if cursor['step'] >= a.steps:
            status, reason = 'STOP', 'step_cap'
        save_checkpoint(outdir/'resume.pt', model, optimizer, scheduler, cursor, stopper, hashes,
                        dict(elapsed_seconds=elapsed_before+time.monotonic()-started))
        log.write(json.dumps(dict(event='stop', **cursor, status=status, reason=reason))+'\n')
    from .export import save_head
    save_head(outdir/'export', model, hashes, dict(step=cursor['step'], reason=reason))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
