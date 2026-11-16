"""GRPO rows (rlkit-grpo-row-v1) in the trainer's stream databases.

A row holds what the sampler decoded and what the loss needs:
  prompt_row        the native VQA row the sampler decoded from (no target)
  stream            'vqa' (no tool response in the rollout) or 'routing'
  tokens, kinds     the rollout's generated ids and per-position source: f forced first span,
                    s sampled, b budget EOS, r printed tool response
  old_logp          sampler log prob (tempered, reserved ids masked) at s positions, None elsewhere
  ref_logp          reference-export log prob at s positions, computed offline, None elsewhere
  advantage         group-normalised advantage
  reserved          the ids the decoder masked before choosing
  prompt_ids_sha256 sha256 of the prompt input ids the sampler decoded from
The encoder rebuilds the prompt with the same encoder the sampler's reader used
(carrier_c1_canary.prompt_batch: data.encode on the vqa stream with READOUT_TARGET, sliced at the
first label) and refuses a row whose prompt ids differ, so training sees the sampled sequence.
"""
import hashlib
import json

import torch

from . import carrier_c1_data as data

SCHEMA = 'rlkit-grpo-row-v1'
OWN_SCHEMA = 'rlkit-own-row-v1'
KINDS = set('fsbr')


def is_grpo(row):
    return isinstance(row, dict) and row.get('schema') == SCHEMA


def is_own(row):
    """Mode (a) exact-token row: a selected rollout trained by cross-entropy on its own tokens
    (f, s, b), with its printed responses (r) masked, exactly as decoded. Responses must come from
    heads inside the artifact; rlkit.select admits only such rows."""
    return isinstance(row, dict) and row.get('schema') == OWN_SCHEMA


def ids_sha256(ids):
    return hashlib.sha256(json.dumps([int(i) for i in ids]).encode()).hexdigest()


def prompt_batch(processor, row, placement, layout, gap, geometry_online=None):
    batch, _, _ = data.encode(processor, {**row, 'target': data.READOUT_TARGET}, {}, 'vqa', placement, 'final',
                              layout, gap, **(dict(geometry_online=geometry_online) if geometry_online else {}))
    start = int(torch.where(batch['labels'][0] != -100)[0][0])
    return {k: (v[:, :start] if k in ('input_ids', 'attention_mask', 'mm_token_type_ids') else v)
            for k, v in batch.items() if k != 'labels'}


def check_sources(row):
    """Trainer-side re-check of the selector's artifact policy on the row's recorded sources."""
    src = row.get('response_sources')
    if row.get('response_policy') != 'artifact' or not isinstance(src, dict):
        raise ValueError('RL rows need responses from heads inside the artifact')
    if (src.get('donor') or src.get('verify') or src.get('reread') or src.get('tower_state')
            or src.get('mask_source') not in (None, 'mdg') or src.get('geometry_source') not in (None, 'same_checkpoint_own')
            or src.get('pose_source') not in ('own', 'tower')):
        raise ValueError('RL row responses come from outside the artifact')


def check(row):
    check_sources(row)
    if not isinstance(row.get('temperature'), (int, float)) or not row['temperature'] > 0:
        raise ValueError('GRPO row needs its sampling temperature')
    n = len(row['tokens'])
    if row['stream'] not in ('vqa', 'routing'):
        raise ValueError('GRPO rows train only vqa or routing')
    if len(row['kinds']) != n or set(row['kinds']) - KINDS:
        raise ValueError('GRPO row kinds differ from its tokens')
    if (row['stream'] == 'routing') != ('r' in row['kinds']):
        raise ValueError('GRPO routing rows hold tool responses and vqa rows none')
    for name in ('old_logp', 'ref_logp'):
        values = row[name]
        if len(values) != n or any((v is None) != (k != 's') for v, k in zip(values, row['kinds'])):
            raise ValueError(f'GRPO row {name} must be set exactly at sampled positions')
    if 's' not in row['kinds']:
        raise ValueError('GRPO row has no sampled token')
    if not isinstance(row['advantage'], (int, float)) or row['advantage'] != row['advantage']:
        raise ValueError('GRPO row needs a finite advantage')


def attach(prompt, row):
    ids = prompt['input_ids']
    gen = torch.tensor([row['tokens']], dtype=ids.dtype)
    P, n = ids.shape[1], gen.shape[1]
    out = {k: v for k, v in prompt.items() if k not in ('input_ids', 'attention_mask', 'mm_token_type_ids')}
    out['input_ids'] = torch.cat([ids, gen], 1)
    out['attention_mask'] = torch.cat([prompt['attention_mask'], torch.ones_like(gen)], 1)
    if 'mm_token_type_ids' in prompt:
        out['mm_token_type_ids'] = torch.cat([prompt['mm_token_type_ids'], torch.zeros_like(gen)], 1)
    labels = torch.full((1, P + n), -100, dtype=ids.dtype)
    mask = torch.zeros((1, P + n), dtype=torch.bool)
    old = torch.zeros((1, P + n), dtype=torch.float32)
    ref = torch.zeros((1, P + n), dtype=torch.float32)
    for i, k in enumerate(row['kinds']):
        if k != 'r':
            labels[0, P + i] = gen[0, i]
        if k == 's':
            mask[0, P + i] = True
            old[0, P + i] = float(row['old_logp'][i])
            ref[0, P + i] = float(row['ref_logp'][i])
    out.update(labels=labels, aux_pg_mask=mask, aux_old_logp=old, aux_ref_logp=ref,
               aux_pg_advantage=torch.tensor([float(row['advantage'])]),
               aux_pg_reserved=torch.tensor([int(i) for i in row['reserved']], dtype=torch.long),
               aux_pg_temperature=torch.tensor([float(row.get('temperature', 1.0))]),
               aux_suffix_start=torch.tensor(P))
    return out


def check_own(row):
    n = len(row['tokens'])
    if row['stream'] not in ('vqa', 'routing'):
        raise ValueError('Own rows train only vqa or routing')
    if len(row['kinds']) != n or set(row['kinds']) - KINDS or not n:
        raise ValueError('Own row kinds differ from its tokens')
    if (row['stream'] == 'routing') != ('r' in row['kinds']):
        raise ValueError('Own routing rows hold tool responses and vqa rows none')
    check_sources(row)


def encode_own(processor, row, placement, layout, gap, geometry_online=None):
    check_own(row)
    prompt = prompt_batch(processor, row['prompt_row'], placement, layout, gap, geometry_online)
    if ids_sha256(prompt['input_ids'][0].tolist()) != row['prompt_ids_sha256']:
        raise ValueError('Own row prompt differs from the prompt the sampler decoded')
    row = dict(row, old_logp=[0.] * len(row['tokens']), ref_logp=[0.] * len(row['tokens']), advantage=0., reserved=[])
    batch = attach(prompt, row)
    for key in ('aux_pg_mask', 'aux_old_logp', 'aux_ref_logp', 'aux_pg_advantage', 'aux_pg_reserved', 'aux_pg_temperature'):
        batch.pop(key)
    return batch, dict(qid=row['prompt_row'].get('qid'), own=dict(draw=row.get('draw')))


def encode(processor, row, placement, layout, gap, geometry_online=None):
    if is_own(row):
        return encode_own(processor, row, placement, layout, gap, geometry_online)
    check(row)
    tokenizer = processor.tokenizer
    for token in ('<tool_response>', '</tool_response>'):
        if tokenizer.convert_tokens_to_ids(token) not in row['reserved']:
            raise ValueError('GRPO row reserved ids omit the response delimiters the decoder masks')
    prompt = prompt_batch(processor, row['prompt_row'], placement, layout, gap, geometry_online)
    if ids_sha256(prompt['input_ids'][0].tolist()) != row['prompt_ids_sha256']:
        raise ValueError('GRPO row prompt differs from the prompt the sampler decoded')
    batch = attach(prompt, row)
    return batch, dict(qid=row['prompt_row'].get('qid'), grpo=dict(draw=row.get('draw'), advantage=row['advantage']))
