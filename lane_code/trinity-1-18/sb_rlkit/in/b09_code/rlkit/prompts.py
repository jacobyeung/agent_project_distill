"""RL prompt pool from reserve question rows (brief 10, R0-rl) in the native VQA row schema.

    python -m rlkit.prompts --rows R0_RL_ROWS.jsonl --allow-scenes R0_RL_SCENES.txt --frames 32 \
        [--types counting,...] [--limit N --seed 17] --out POOL.jsonl

Each row (qid, scene, question_type, answer, student_input{question, options, frame_indices, ...})
becomes one rlkit-prompt-v1 prompt; the row minus its target is what the sampler decodes from.
Frame count is a parameter: every row must carry exactly --frames frame indices (32 or 64; the
read must match the training layout). Rows outside the allowed scene list, rows without an
answer, and duplicate qids are refused, never dropped silently; benchmark sources are refused
again by the sampler. Objects for forced head openers come from row['roles'] (a, b, ...).
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from .common import read_jsonl, write_jsonl_atomic

SCHEMA = 'rlkit-prompt-v1'


class PoolError(ValueError):
    pass


def to_prompt(row, frames, source):
    si = row.get('student_input') or {}
    n = len(si.get('frame_indices') or [])
    if n != frames:
        raise PoolError(f'{row.get("qid")}: {n} frames, pool wants {frames}')
    if row.get('answer') in (None, ''):
        raise PoolError(f'{row.get("qid")}: no answer')
    clean = {k: copy.deepcopy(v) for k, v in row.items() if k != 'target'}
    roles = row.get('roles') or {}
    objects = [roles[k] for k in sorted(roles)] if isinstance(roles, dict) else []
    return dict(schema=SCHEMA, prompt_id=row['qid'], type=row['question_type'], question=si['question'],
                options=si.get('options') or None, gt_answer=str(row['answer']), row=clean, scene_key=row['scene'],
                source=source, row_source=row.get('source'), dataset=row.get('dataset'), objects=objects, frames=frames)


def build(rows, allow_scenes, frames, *, types=None, limit=None, seed=17, source='reserve_r0_rl'):
    allow, seen, out, refused = set(allow_scenes), set(), [], []
    for row in rows:
        try:
            if row.get('scene') not in allow:
                raise PoolError(f'{row.get("qid")}: scene {row.get("scene")} is not in the reserve list')
            if row.get('qid') in seen:
                raise PoolError(f'duplicate qid {row.get("qid")}')
            if types and row.get('question_type') not in types:
                continue
            from .sampler import benchmark_source
            bad = benchmark_source(row)
            if bad is not None:
                raise PoolError(f'{row.get("qid")}: source {bad} is a benchmark')
            out.append(to_prompt(row, frames, source))
            seen.add(row['qid'])
        except PoolError as exc:
            refused.append(dict(qid=row.get('qid'), reason=str(exc)))
    if limit is not None:
        key = lambda p: hashlib.sha256(f'{seed}|{p["prompt_id"]}'.encode()).hexdigest()  # noqa: E731
        out = sorted(out, key=key)[:limit]
    return out, refused


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--rows', required=True)
    ap.add_argument('--allow-scenes', required=True)
    ap.add_argument('--frames', type=int, required=True, choices=(32, 64))
    ap.add_argument('--types')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--seed', type=int, default=17)
    ap.add_argument('--source', default='reserve_r0_rl')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    scenes = [s.strip() for s in Path(a.allow_scenes).read_text().split() if s.strip()]
    out, refused = build(read_jsonl(a.rows), scenes, a.frames, types=set(a.types.split(',')) if a.types else None,
                         limit=a.limit, seed=a.seed, source=a.source)
    write_jsonl_atomic(a.out, out)
    write_jsonl_atomic(a.out + '.refused.jsonl', refused)
    print(json.dumps(dict(prompts=len(out), refused=len(refused)), sort_keys=True))


if __name__ == '__main__':
    main()
