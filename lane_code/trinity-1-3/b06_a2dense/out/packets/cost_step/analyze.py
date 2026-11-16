"""Measured GF-1 step cost, online tower vs cached bank (stdlib only).

usage: analyze.py --online METRICS.jsonl --cached METRICS.jsonl --world 4 [--writer WRITER.log --writer-seconds S]
       [--clips 2741] [--skip 2] OUT.json
METRICS: the trainer's per-step metrics JSONL (ddp_training.write_metric records; field 'seconds' per optimizer
step, 'step'). The first --skip steps (warm-up, compile, allocator growth) are dropped; the median of the rest is
the step time. GPU-hours per 1,000 steps = median seconds x world x 1000 / 3600 (the replaced guesses: 345 online,
190 cached). WRITER.log: gf1_cache.main stdout (one JSON per clip, then a totals line); --writer-seconds is its wall
time on one GPU; the cache cost for --clips clips is extrapolated from it."""
import argparse, json, statistics


def steps(path, skip):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    rows = [r for r in rows if 'seconds' in r and 'step' in r]
    rows.sort(key=lambda r: r['step'])
    kept = [r['seconds'] for r in rows[skip:]]
    if len(kept) < 3:
        raise SystemExit(f'{path}: fewer than 3 timed steps after skipping {skip}')
    return dict(steps=len(rows), timed=len(kept), median_s=statistics.median(kept), min_s=min(kept), max_s=max(kept))


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--online', required=True); a.add_argument('--cached', required=True)
    a.add_argument('--world', type=int, required=True); a.add_argument('--skip', type=int, default=2)
    a.add_argument('--writer'); a.add_argument('--writer-seconds', type=float); a.add_argument('--clips', type=int, default=2741)
    a.add_argument('out')
    x = a.parse_args()
    res = dict(world=x.world, skip=x.skip)
    for name in ('online', 'cached'):
        s = steps(getattr(x, name), x.skip)
        s['gpu_hours_per_1000_steps'] = round(s['median_s'] * x.world * 1000 / 3600, 1)
        res[name] = s
    res['cached_over_online'] = round(res['cached']['median_s'] / res['online']['median_s'], 3)
    if x.writer:
        recs = [json.loads(l) for l in open(x.writer) if l.startswith('{"clip_key"')]
        if not recs or not x.writer_seconds:
            raise SystemExit('writer log needs clip lines and --writer-seconds')
        per = x.writer_seconds / len(recs)
        res['writer'] = dict(clips=len(recs), seconds_per_clip=round(per, 2), mean_MB=round(statistics.mean(r['bytes'] for r in recs) / 1e6, 1),
                             gpu_hours_all_clips=round(per * x.clips / 3600, 1), clips_extrapolated=x.clips,
                             GB_all_clips=round(statistics.mean(r['bytes'] for r in recs) * x.clips / 1e9, 1))
        res['cached_total_gpu_hours_1000_steps'] = round(res['cached']['gpu_hours_per_1000_steps'] + res['writer']['gpu_hours_all_clips'], 1)
    json.dump(res, open(x.out, 'w'), indent=1)
    print(json.dumps(res))


if __name__ == '__main__':
    main()
