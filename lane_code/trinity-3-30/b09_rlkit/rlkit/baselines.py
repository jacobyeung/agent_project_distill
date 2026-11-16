"""No-information baselines, reported every round.

    python -m rlkit.baselines constants --fit TRAIN_PROMPTS.jsonl --pool POOL.jsonl --out CONST.json
    python -m rlkit.baselines shuffle   --pool POOL.jsonl --seed 17 --out POOL_SHUFFLED.jsonl
    python -m rlkit.baselines collapse  --pool POOL.jsonl --select SELECT_DIR --out COLLAPSE.json

constants: per type, the train-fitted constant answer: the option letter that is most often right
  (option types), or the value v maximising mean MRA over the fitting set's answers (numeric types;
  candidates are the fitting answers themselves). Reported on the pool as c (score only) and as
  r = c * g with g = 0, because an answer-only trace fails the gate (no-answer-only rule); the
  score column says how much a policy can earn without looking.
shuffle: each pool prompt gets the video (student_input frames, frame_indices, fps, totals and
  video identity) of another pool prompt of the same frame count from a different scene, chosen
  by a seeded derangement; question, options and answer stay. Sample these with the round's
  sampler config and score them with the same reward: reward on shuffled videos.
collapse: share of kept rollouts per path and per answer bin against the pool's answer
  histogram (options by letter, numbers by the pool's per-type quintile bins), with the total
  variation distance per type. A rising distance flags collapse onto a few answers.
"""
import argparse
import copy
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np

from .common import atomic_write_json, read_jsonl, write_jsonl_atomic
from .score import mra

VIDEO_KEYS = ('frames', 'frame_indices', 'fps', 'total_num_frames', 'video_identity', 'geometry_dense')


def is_option(prompt):
    return bool(prompt.get('options'))


def fit_constants(fit_prompts):
    by_type = {}
    for p in fit_prompts:
        by_type.setdefault(p['type'], []).append(p)
    out = {}
    for qtype, ps in sorted(by_type.items()):
        if all(is_option(p) for p in ps):
            counts = Counter(str(p['gt_answer']).strip().upper() for p in ps)
            letter, _ = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
            out[qtype] = dict(kind='option', answer=letter, fit_n=len(ps))
        elif not any(is_option(p) for p in ps):
            gts = np.array([float(p['gt_answer']) for p in ps])
            cands = np.unique(gts)
            scores = [np.mean([mra(v, g) for g in gts]) for v in cands]
            best = int(np.argmax(scores))
            out[qtype] = dict(kind='numeric', answer=float(cands[best]), fit_n=len(ps), fit_score=float(scores[best]))
        else:
            raise ValueError(f'type {qtype} mixes option and numeric prompts')
    return out


def constant_report(constants, pool):
    rows = {}
    for p in pool:
        k = constants.get(p['type'])
        if k is None:
            continue
        c = (1.0 if k['answer'] == str(p['gt_answer']).strip().upper() else 0.0) if k['kind'] == 'option' \
            else mra(k['answer'], p['gt_answer'])
        rows.setdefault(p['type'], []).append(c)
    return {t: dict(n=len(v), c=float(np.mean(v)), r=0.0, constant=constants[t]['answer']) for t, v in sorted(rows.items())}


def shuffle_videos(pool, seed=17):
    """Seeded derangement within (type-independent) frame-count groups, never the same scene."""
    rng = random.Random(seed)
    groups = {}
    for i, p in enumerate(pool):
        groups.setdefault(len(p['row']['student_input'].get('frame_indices') or []), []).append(i)
    donor = {}
    for idx in groups.values():
        scenes = {pool[i]['scene_key'] for i in idx}
        if len(scenes) < 2:
            raise ValueError('shuffle needs at least two scenes per frame-count group')
        for _ in range(1000):
            perm = idx[:]
            rng.shuffle(perm)
            if all(pool[a]['scene_key'] != pool[b]['scene_key'] for a, b in zip(idx, perm)):
                donor.update(zip(idx, perm))
                break
        else:
            raise ValueError('no scene-disjoint derangement found (one scene dominates a group)')
    out = []
    for i, p in enumerate(pool):
        d = pool[donor[i]]
        q = copy.deepcopy(p)
        si, dsi = q['row']['student_input'], d['row']['student_input']
        for k in VIDEO_KEYS:
            si.pop(k, None)
            if k in dsi:
                si[k] = copy.deepcopy(dsi[k])
        q['prompt_id'] = p['prompt_id'] + '~shuf'
        q['shuffled_from'] = dict(prompt_id=d['prompt_id'], scene_key=d['scene_key'], seed=seed)
        out.append(q)
    return out


def answer_bins(pool):
    """Per numeric type, the pool's quintile edges."""
    edges = {}
    for qtype in sorted({p['type'] for p in pool if not is_option(p)}):
        v = np.array([float(p['gt_answer']) for p in pool if p['type'] == qtype])
        edges[qtype] = np.unique(np.quantile(v, [.2, .4, .6, .8])).tolist()
    return edges


def bin_of(prompt, answer, edges):
    if answer is None:
        return 'none'
    if is_option(prompt):
        return str(answer).strip().upper()
    return 'q%d' % int(np.searchsorted(edges[prompt['type']], float(answer), side='right'))


def collapse_table(pool, kept):
    """kept: [(prompt_id, path, answer)] of the selected rollouts."""
    by_id = {p['prompt_id']: p for p in pool}
    edges = answer_bins(pool)
    table = {}
    for qtype in sorted({p['type'] for p in pool}):
        ps = [p for p in pool if p['type'] == qtype]
        pool_hist = Counter(bin_of(p, p['gt_answer'], edges) for p in ps)
        ks = [(path, ans) for pid, path, ans in kept if by_id[pid]['type'] == qtype]
        kept_hist = Counter(bin_of(by_id[pid], ans, edges) for pid, path, ans in kept if by_id[pid]['type'] == qtype)
        bins = sorted(set(pool_hist) | set(kept_hist))
        ps_n, ks_n = sum(pool_hist.values()), max(1, sum(kept_hist.values()))
        tv = 0.5 * sum(abs(pool_hist[b] / ps_n - kept_hist[b] / ks_n) for b in bins) if ks else None
        table[qtype] = dict(pool=ps_n, kept=len(ks), keep_rate=len(ks) / ps_n,
                            path_share={k: v / max(1, len(ks)) for k, v in sorted(Counter(p for p, _ in ks).items())},
                            pool_bins={b: pool_hist[b] / ps_n for b in bins},
                            kept_bins={b: kept_hist[b] / ks_n for b in bins}, tv_distance=tv)
    return dict(bins=edges, types=table)


def kept_from_select(select_dir):
    d = Path(select_dir)
    kept = [(r['rl_selection']['prompt_id'], 'direct', r['answer']) for r in read_jsonl(d / 'vqa_rows.jsonl')]
    kept += [(r['prompt_id'], 'head', r['rl_selection']['answer']) for r in read_jsonl(d / 'own_rows.jsonl')]
    for name in ('barred', 'quarantine'):
        if (d / f'{name}.jsonl').exists():
            kept += [(r['prompt_id'], 'head', r['answer']) for r in read_jsonl(d / f'{name}.jsonl')]
    return kept


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('constants')
    c.add_argument('--fit', required=True)
    c.add_argument('--pool', required=True)
    c.add_argument('--out', required=True)
    s = sub.add_parser('shuffle')
    s.add_argument('--pool', required=True)
    s.add_argument('--seed', type=int, default=17)
    s.add_argument('--out', required=True)
    k = sub.add_parser('collapse')
    k.add_argument('--pool', required=True)
    k.add_argument('--select', required=True)
    k.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    pool = read_jsonl(a.pool)
    if a.cmd == 'constants':
        fit = read_jsonl(a.fit)
        if {p['prompt_id'] for p in fit} & {p['prompt_id'] for p in pool}:
            raise ValueError('fitting prompts overlap the pool')
        consts = fit_constants(fit)
        result = dict(constants=consts, pool=constant_report(consts, pool))
    elif a.cmd == 'shuffle':
        rows = shuffle_videos(pool, a.seed)
        write_jsonl_atomic(a.out, rows)
        result = dict(rows=len(rows), seed=a.seed)
    else:
        result = collapse_table(pool, kept_from_select(a.select))
    if a.cmd != 'shuffle':
        atomic_write_json(a.out, result)
    print(json.dumps(result, sort_keys=True)[:4000])


if __name__ == '__main__':
    main()
