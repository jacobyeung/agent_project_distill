"""Reserved LM ids for codec symbols (design record 1.5: "the rarest vocabulary ids that are neither
special nor digits", with the map and its sha recorded).

BPE assigns ids in merge order, so the highest ordinary ids are the rarest merges. `rare_ids` walks
the base vocabulary downward, skipping special and added tokens and any token whose text holds a
digit, and returns the first n. `save_ids` / `load_ids` write and verify {ids, sha256}.
"""
import hashlib
import json
from pathlib import Path


def rare_ids(tokenizer, n):
    special = set(getattr(tokenizer, 'all_special_ids', []) or [])
    added = set(getattr(tokenizer, 'added_tokens_decoder', {}) or {})
    base = getattr(tokenizer, 'vocab_size', None) or len(tokenizer)
    out = []
    for i in range(base - 1, -1, -1):
        if i in special or i in added:
            continue
        text = tokenizer.decode([i])
        if any(c.isdigit() for c in text) or not text.strip():
            continue
        out.append(i)
        if len(out) == n:
            return sorted(out)
    raise ValueError(f'Only {len(out)} eligible ids, {n} requested')


def ids_sha256(ids):
    return hashlib.sha256(json.dumps([int(i) for i in ids]).encode()).hexdigest()


def save_ids(path, ids, source=''):
    ids = [int(i) for i in ids]
    Path(path).write_text(json.dumps(dict(kind='reserved_ids_v1', source=source, n=len(ids), ids=ids,
                                          sha256=ids_sha256(ids))) + '\n')


def load_ids(path, n=None):
    meta = json.loads(Path(path).read_text())
    if meta.get('kind') != 'reserved_ids_v1' or ids_sha256(meta['ids']) != meta['sha256']:
        raise ValueError('Reserved-id file is malformed or its sha256 does not match')
    if n is not None and len(meta['ids']) < n:
        raise ValueError(f'Reserved-id file holds {len(meta["ids"])} ids, {n} needed')
    return meta['ids'][:n] if n is not None else meta['ids']
