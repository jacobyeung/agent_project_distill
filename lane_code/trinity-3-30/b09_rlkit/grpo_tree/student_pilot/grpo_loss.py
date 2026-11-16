"""GRPO loss for mode (b) of the RL kit: group-normalised advantages, a clipped policy-gradient
surrogate on the model's own sampled tokens, and a k3 KL term to the SFT export.

Batch fields (aligned with `input_ids`, read through the same `[:, 1:]` shift as `labels`):
  aux_pg_advantage [B]      float  group-normalised advantage of the row's rollout
  aux_pg_mask      [B, T]   bool   positions whose token carries the policy-gradient term:
                                    sampled tokens only; forced first-span tokens, the budget EOS,
                                    printed tool responses and the prompt carry none
  aux_old_logp     [B, T]   float  log prob of the token under the sampling policy (export r)
  aux_ref_logp     [B, T]   float  log prob of the token under the reference (SFT) export
  aux_pg_reserved  [K]      long   token ids the decoder sets to -inf before choosing
                                    (`carrier_c1_batch_decode.Row.reserved`: the response
                                    delimiters and the carrier id); the loss applies the same
                                    mask, so its policy is the distribution the sampler drew from
Every aux_pg_mask position must be a supervised label position (labels != -100); response
spans are already -100 in routing rows, so they never enter the loss.

Settings come from the model recipe's `grpo` block (inside the run configuration hash):
  clip_low 0.2, clip_high 0.2, kl_beta 0.04, temperature 0.7 (the sampler default), norm 'token'
  aux_pg_temperature [B] float must equal the setting: the rows' sampling temperature
  norm 'token': sum over the microbatch's PG tokens / their count;
  norm 'seq'  : mean over rows of each row's token mean (rows with no PG token weigh zero).
The temperature must equal the sampler's, and aux_old_logp must be the tempered log prob the
sampler recorded (logp_tempered), so the ratio starts at 1 on the export that sampled.
"""
import torch

SETTINGS = dict(clip_low=0.2, clip_high=0.2, kl_beta=0.04, temperature=0.7, norm='token')  # temperature = the sampler's
FIELDS = ('aux_pg_advantage', 'aux_pg_mask', 'aux_old_logp', 'aux_ref_logp', 'aux_pg_reserved', 'aux_pg_temperature')


def settings(recipe):
    raw = dict((recipe or {}).get('grpo') or {})
    unknown = set(raw) - set(SETTINGS)
    if unknown:
        raise ValueError(f'unknown grpo settings {sorted(unknown)}')
    out = {**SETTINGS, **raw}
    if out['norm'] not in ('token', 'seq'):
        raise ValueError('grpo norm must be token or seq')
    if not out['temperature'] > 0:
        raise ValueError('grpo temperature must be positive')
    return out


def is_pg_batch(batch):
    present = [k in batch for k in FIELDS]
    if any(present) and not all(present):
        raise ValueError(f'a GRPO batch needs every field {FIELDS}')
    return all(present)


def check_reserved(batch, carrier_id):
    if int(carrier_id) not in batch['aux_pg_reserved'].tolist():
        raise ValueError('aux_pg_reserved omits the carrier id the decoder masks')


def group_advantages(rewards, eps=1e-6, scale_std=True):
    """(r - mean) / (std + eps) within one prompt's group (population std); a tied group gives zeros."""
    r = torch.as_tensor(rewards, dtype=torch.float64)
    if r.numel() == 0:
        return r
    centred = r - r.mean()
    if not scale_std:
        return centred
    std = r.std(unbiased=False)
    return torch.zeros_like(r) if float(std) <= eps else centred / (std + eps)


def k3(new_logp, ref_logp):
    """Unbiased, non-negative KL(pi || ref) estimate per token: exp(d) - d - 1, d = ref - new."""
    d = ref_logp - new_logp
    return torch.exp(d) - d - 1.0


def policy_logprobs(logits, labels, reserved, temperature):
    """Log prob of each label under the decoder's sampling policy: reserved ids masked, then tempered."""
    logits = logits.float().clone()
    logits[:, reserved.to(logits.device).long()] = -float('inf')
    logp = torch.log_softmax(logits / temperature, -1)
    return logp.gather(-1, labels[:, None])[:, 0]


def token_terms(new_logp, old_logp, ref_logp, advantage, s):
    ratio = torch.exp(new_logp - old_logp)
    clipped = torch.clamp(ratio, 1.0 - s['clip_low'], 1.0 + s['clip_high'])
    surrogate = torch.minimum(ratio * advantage, clipped * advantage)
    kl = k3(new_logp, ref_logp)
    return -surrogate + s['kl_beta'] * kl, ratio, kl


def loss_from_logits(logits, labels, valid, batch, recipe):
    """Loss over the forward's supervised positions. `logits` are the lm_head outputs at
    `valid` positions (the forward's own memory-saving gather); labels/valid are already shifted."""
    s = settings(recipe)
    if (batch['aux_pg_temperature'].float() - s['temperature']).abs().max() > 1e-6:
        raise ValueError('GRPO rows were sampled at another temperature than the loss uses')
    mask = batch['aux_pg_mask'][:, 1:].bool()
    if (mask & ~valid).any():
        raise ValueError('aux_pg_mask marks a position without a label (prompt or tool response)')
    pg = mask[valid]
    rows = torch.arange(labels.shape[0], device=labels.device)[:, None].expand_as(labels)[valid]
    new = policy_logprobs(logits, labels[valid], batch['aux_pg_reserved'], s['temperature'])
    if not pg.any():
        zero = logits.sum() * 0.
        return zero, dict(pg_tokens=0)
    old = batch['aux_old_logp'][:, 1:][valid].to(new.dtype)
    ref = batch['aux_ref_logp'][:, 1:][valid].to(new.dtype)
    adv = batch['aux_pg_advantage'].to(new.device, new.dtype)[rows]
    tok, ratio, kl = token_terms(new[pg], old[pg], ref[pg], adv[pg], s)
    if s['norm'] == 'token':
        loss = tok.sum() / pg.sum()
    else:
        r = rows[pg]
        per_row_sum = torch.zeros(labels.shape[0], dtype=tok.dtype, device=tok.device).index_add(0, r, tok)
        per_row_n = torch.zeros(labels.shape[0], dtype=tok.dtype, device=tok.device).index_add(
            0, r, torch.ones_like(tok))
        has = per_row_n > 0
        loss = (per_row_sum[has] / per_row_n[has]).mean()
    with torch.no_grad():
        clip = ((ratio < 1 - s['clip_low']) | (ratio > 1 + s['clip_high'])).float().mean()
        metrics = dict(pg_tokens=int(pg.sum()), kl=float(kl.mean()), ratio=float(ratio.mean()),
                       clip_fraction=float(clip), advantage=float(adv[pg].mean()))
    return loss, metrics


def sequence_logprobs(model, batch, stream, temperature=1.0, reserved=None):
    """No-grad per-position log prob of each label under `model` ([B, T], aligned with input_ids;
    0 where labels are -100). Used for aux_ref_logp (reference export) and to recompute
    aux_old_logp when the sampler's numbers are not trusted."""
    with torch.no_grad():
        image = 'image_grid_thw' in batch and 'video_grid_thw' not in batch
        hidden = model.hidden(batch, carriers=not image)
        labels = batch['labels'][:, 1:]
        valid = labels != -100
        reserved = batch['aux_pg_reserved'] if reserved is None else torch.as_tensor(reserved)
        lp = policy_logprobs(model.lm_head(hidden[:, :-1][valid]), labels[valid], reserved, temperature)
        out = torch.zeros(batch['labels'].shape, dtype=torch.float32)
        shifted = out[:, 1:].clone()
        shifted[valid.cpu()] = lp.cpu()
        out[:, 1:] = shifted
    return out
