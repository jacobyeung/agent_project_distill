"""Mode (b) bridge: scored groups -> GRPO rows -> batch fields for `student_pilot.grpo_loss`.

A GRPO row is the prompt batch the sampler decoded from, extended by the rollout's own token
ids (never re-tokenised text), with:
  labels           the generated ids at own positions (f, s, b); -100 on prompt and on
                   printed tool responses (r), as in the routing rows
  aux_pg_mask      True only at sampled positions (s); forced first-span tokens (f) and the
                   budget EOS (b) are labels without a policy-gradient term
  aux_old_logp     the sampler's tempered log prob (logp_tempered) at sampled positions
  aux_ref_logp     filled by `grpo_loss.sequence_logprobs` under the reference export
  aux_pg_advantage the group-normalised advantage of the rollout's reward r
  aux_pg_reserved  the ids the decoder masks before choosing (`reserved_ids`)
Groups whose rewards tie carry no signal (all advantages zero) and are dropped by default.
"""
import torch

ROW_SCHEMA = 'rlkit-grpo-row-v1'
TENSOR_KEYS = ('input_ids', 'attention_mask', 'mm_token_type_ids')


def advantages(rewards, eps=1e-6, scale_std=True):
    """Same arithmetic as grpo_loss.group_advantages (kept here so the kit runs without the tree)."""
    r = torch.as_tensor(rewards, dtype=torch.float64)
    centred = r - r.mean()
    if not scale_std:
        return centred.tolist()
    std = r.std(unbiased=False)
    return (torch.zeros_like(r) if float(std) <= eps else centred / (std + eps)).tolist()


def group_rows(scored, records, *, drop_tied=True, scale_std=True):
    """[(record, advantage, reward)] of one prompt; `scored` from reward.score_group (draw order)."""
    if [s['draw'] for s in scored] != [r['draw'] for r in records]:
        raise ValueError('scored rows and records are not in the same draw order')
    adv = advantages([s['r'] for s in scored], scale_std=scale_std)
    if drop_tied and all(a == 0 for a in adv):
        return []
    return [(rec, a, s['r']) for rec, s, a in zip(records, scored, adv)]


def reserved_ids(tokenizer, model):
    """The decoder's masked ids, built as `carrier_c1_batch_decode.Row` builds them."""
    return [tokenizer.convert_tokens_to_ids('<tool_response>'), tokenizer.convert_tokens_to_ids('</tool_response>'),
            model.carrier_id]


def attach(prompt_batch, record, advantage, reserved):
    """Batch of one GRPO row (batch size 1) from the prompt batch the sampler decoded."""
    ids = prompt_batch['input_ids']
    if ids.shape[0] != 1:
        raise ValueError('attach takes the one-row prompt batch the sampler decoded from')
    gen = torch.tensor([record['tokens']], dtype=ids.dtype, device=ids.device)
    kinds = record['kinds']
    if len(kinds) != gen.shape[1]:
        raise ValueError('kinds and tokens differ in length')
    P, n = ids.shape[1], gen.shape[1]
    out = {k: v for k, v in prompt_batch.items() if k not in TENSOR_KEYS and k != 'labels'}
    out['input_ids'] = torch.cat([ids, gen], 1)
    out['attention_mask'] = torch.cat([prompt_batch['attention_mask'], torch.ones_like(gen)], 1)
    if 'mm_token_type_ids' in prompt_batch:
        out['mm_token_type_ids'] = torch.cat([prompt_batch['mm_token_type_ids'], torch.zeros_like(gen)], 1)
    labels = torch.full((1, P + n), -100, dtype=ids.dtype, device=ids.device)
    mask = torch.zeros((1, P + n), dtype=torch.bool, device=ids.device)
    old = torch.zeros((1, P + n), dtype=torch.float32, device=ids.device)
    for i, k in enumerate(kinds):
        if k in ('f', 's', 'b'):
            labels[0, P + i] = gen[0, i]
        if k == 's':
            mask[0, P + i] = True
            old[0, P + i] = float(record['logp_tempered'][i])
    out.update(labels=labels, aux_pg_mask=mask, aux_old_logp=old, aux_ref_logp=torch.zeros_like(old),
               aux_pg_temperature=torch.tensor([float(record.get('temperature', 1.0))]),
               aux_pg_advantage=torch.tensor([float(advantage)], dtype=torch.float32, device=ids.device),
               aux_pg_reserved=torch.tensor(list(reserved), dtype=torch.long, device=ids.device))
    return out


def to_row(prompt, record, advantage, ref_logp, reserved):
    """rlkit-grpo-row-v1 for the trainer's stream databases (grpo_tree student_pilot/grpo_rows.py).
    ref_logp: per generated position (None off sampled positions), from the reference export."""
    from .select import artifact_policy
    kinds = record['kinds']
    reason = artifact_policy(record)
    if reason is not None:
        raise ValueError('GRPO row refused: ' + reason)
    if record.get('temperature') is None:
        raise ValueError('record lacks its sampling temperature')
    if record.get('prompt_ids_sha256') is None:
        raise ValueError('record lacks prompt_ids_sha256 (sampled before rlkit recorded it)')
    old = [record['logp_tempered'][i] if k == 's' else None for i, k in enumerate(kinds)]
    ref = [ref_logp[i] if k == 's' else None for i, k in enumerate(kinds)]
    return dict(schema=ROW_SCHEMA, prompt_row=prompt['row'], stream='routing' if 'r' in kinds else 'vqa',
                tokens=record['tokens'], kinds=kinds, old_logp=old, ref_logp=ref, advantage=float(advantage),
                reserved=[int(i) for i in reserved], prompt_ids_sha256=record['prompt_ids_sha256'],
                temperature=float(record['temperature']), top_p=record.get('top_p'), response_policy='artifact',
                response_sources=record['response_sources'],
                prompt_id=prompt['prompt_id'], draw=record['draw'], seed=record['seed'])


def write_stream_db(path, rows):
    """Trainer stream database: rows(i INTEGER PRIMARY KEY, row TEXT, target TEXT); target is null JSON."""
    import json
    import sqlite3
    from pathlib import Path
    p = Path(path)
    if p.exists():
        raise FileExistsError(f'{p} exists; stream databases are written once')
    conn = sqlite3.connect(p)
    conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
    conn.executemany('INSERT INTO rows VALUES (?, ?, ?)',
                     [(i, json.dumps(r, sort_keys=True), 'null') for i, r in enumerate(rows)])
    conn.commit()
    conn.close()


def fill_reference(batch, ref_model, stream, temperature):
    from student_pilot import grpo_loss
    batch['aux_ref_logp'] = grpo_loss.sequence_logprobs(ref_model, batch, stream, temperature).to(
        batch['aux_old_logp'].device)
    return batch
