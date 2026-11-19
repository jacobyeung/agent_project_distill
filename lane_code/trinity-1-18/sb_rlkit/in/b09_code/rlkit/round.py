"""One mode (b) update of a round, plus export and reload checks (library; the production update
runs inside the sealed trainer once its loader feeds GRPO rows, see RUN.md).

  items  = build_items(prompts, groups, scored, prompt_batch, reserved)   # tied groups dropped
  stats  = grpo_update(model, ref_model, optimizer, items, temperature)  # one optimiser step
  digest = export(model, out_dir, meta); reload(model_factory, out_dir) -> model with equal weights

A row's stream is 'routing' when its rollout holds a tool response (head path), else 'vqa'.
Gradients are averaged over rows (each row's loss is its token-normalised GRPO loss).
"""
import hashlib
import json
from pathlib import Path

import torch

from .common import atomic_write_json
from .grpo import attach, fill_reference, group_rows


def build_items(prompts, groups, scored, prompt_batch, reserved, *, drop_tied=True, scale_std=True):
    items = []
    for prompt in prompts:
        pid = prompt['prompt_id']
        for rec, adv, r in group_rows(scored[pid], groups[pid], drop_tied=drop_tied, scale_std=scale_std):
            if 's' not in rec['kinds']:
                continue
            stream = 'routing' if 'r' in rec['kinds'] else 'vqa'
            items.append(dict(prompt_id=pid, draw=rec['draw'], stream=stream, advantage=adv, reward=r,
                              batch=attach(prompt_batch(prompt), rec, adv, reserved)))
    return items


def grpo_update(model, ref_model, optimizer, items, temperature):
    if not items:
        return dict(rows=0, stepped=False)
    model.train()
    optimizer.zero_grad(set_to_none=True)
    metrics = []
    for item in items:
        batch = fill_reference(item['batch'], ref_model, item['stream'], temperature)
        out = model(batch, stream=item['stream'])
        (out['loss'] / len(items)).backward()
        metrics.append(dict(out['metrics'].get('grpo', {}), stream=item['stream'], loss=float(out['loss'].detach())))
    optimizer.step()
    return dict(rows=len(items), stepped=True, per_row=metrics)


def state_digest(model):
    h = hashlib.sha256()
    for name, t in sorted(model.state_dict().items()):
        h.update(name.encode())
        h.update(t.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def export(model, out_dir, meta):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out / 'model_state.pt')
    digest = state_digest(model)
    atomic_write_json(out / 'EXPORT.json', dict(meta, state_sha256=digest))
    return digest


def reload(model_factory, out_dir):
    out = Path(out_dir)
    meta = json.loads((out / 'EXPORT.json').read_text())
    model = model_factory()
    model.load_state_dict(torch.load(out / 'model_state.pt', weights_only=True))
    if state_digest(model) != meta['state_sha256']:
        raise ValueError('reloaded export differs from its manifest')
    return model, meta
