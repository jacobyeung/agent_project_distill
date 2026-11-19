"""Pre-launch token audit of every distinct row a run's plan will fetch, on CPU, before any GPU.

The R1 trainer aborts on the first row that fails check_row (carrier_c1_run.py fetch: "R1 row failure
forbids substituting the pinned row plan"), and nested 64-viewpoint input adds 4,424 tokens (4:3) or
4,880 tokens (16:9) to every video row. The routing build admits suffixes up to 9,600 tokens, so the
16,384-token ceiling no longer bounds a 64-viewpoint routing row. This audit encodes each planned row
through the trainer's own Rows.get and check_row and flags rows over the ceiling and rows over the
H100 memory tripwire length (default 11,500 tokens at world 4; F64_REPORT.md).

Usage
  token_audit.py run --config BOUND_CFG.json --out shard_0.jsonl [--steps 1000] [--shard 0/8]
  token_audit.py summarize --out SUMMARY.json shard_*.jsonl
Run one process per shard, each with OMP_NUM_THREADS=1; shards partition the distinct rows.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

TREE = Path(os.environ.get('F64_TREE', '/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_f64'))
sys.path[:0] = [str(TREE)]
TRIPWIRE_TOKENS = 11500


def planned_rows(cfg, receipt, recipe, steps):
    from student_pilot import carrier_c1_data as data
    counts = {k: v['count'] for k, v in receipt['streams'].items()}
    plans = data.mixed_indices(counts, steps, training_mode=cfg.get('training_mode', 'mixed'), mix=recipe['mix'],
                               world=recipe['world_size'], r2_sampling=cfg.get('r2_sampling'),
                               require_r2='r2_identity' in cfg)
    seen = {}
    for step, plan in enumerate(plans, 1):
        for stream, indices in plan:
            for rank, index in enumerate(indices):
                seen.setdefault((stream, int(index)), (step, rank))
    return sorted(seen.items())


class Stub:
    """The model attributes check_row reads for the pose, vqa, routing and pointing streams."""
    def __init__(self, recipe, receipt):
        self.recipe = recipe
        self.frame_count = receipt.get('frame_count', 32)
        self.training_mode = receipt.get('training_mode')
        self.geometry_online = receipt.get('geometry_online')


def audit(rows, recipe, receipt, items, sink, tripwire=TRIPWIRE_TOKENS):
    from student_pilot.carrier_c1_run import MAX_TOKENS, check_row
    stub = Stub(recipe, receipt)
    limit = recipe.get('max_row_tokens', MAX_TOKENS)
    for (stream, index), (step, rank) in items:
        tick = time.perf_counter()
        record = dict(stream=stream, index=index, first_step=step, rank=rank)
        try:
            batch, targets, row_audit = rows.get(stream, index)
            tokens = int(batch['input_ids'].shape[-1])
            record.update(tokens=tokens, qid=(row_audit or {}).get('qid'),
                          grid=batch['video_grid_thw'].tolist() if 'video_grid_thw' in batch else None)
            if 'aux_suffix_start' in batch:
                record['suffix_tokens'] = tokens - int(batch['aux_suffix_start'].item())
            record.update(over_ceiling=tokens > limit, over_tripwire=tokens > tripwire)
            check_row(batch, targets, stream, stub)
            record['check_row'] = 'ok'
        except Exception as exc:
            record['check_row'] = f'{type(exc).__name__}: {str(exc)[:200]}'
        record['seconds'] = round(time.perf_counter() - tick, 2)
        sink(record)


def run(args):
    from student_pilot.carrier_c1_run import Rows, file_pin, prepared, processor_for_receipt, recipe_for, validate
    cfg = json.loads(Path(args.config).read_text())
    validate(cfg)
    if not cfg.get('preparation'):
        cfg = {**cfg, 'preparation': file_pin(Path(cfg['preparation_output']) / 'receipt.json')}
    receipt, manifest = prepared(cfg, admission=True)
    recipe = recipe_for(cfg)
    items = planned_rows(cfg, receipt, recipe, args.steps)
    shard, shards = map(int, args.shard.split('/'))
    items = items[shard::shards]
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f'{out} exists; choose a fresh path')
    rows = Rows(receipt, processor_for_receipt(manifest, receipt))
    with out.open('x') as handle:
        def sink(record):
            handle.write(json.dumps(record) + '\n')
            handle.flush()
        try:
            audit(rows, recipe, receipt, items, sink, args.tripwire)
        finally:
            rows.close()


def summarize(args):
    records = [json.loads(line) for path in args.shards for line in Path(path).read_text().splitlines() if line]
    streams = {}
    for record in records:
        entry = streams.setdefault(record['stream'], dict(rows=0, max_tokens=0, max_suffix_tokens=0, over_ceiling=0,
                                                          over_tripwire=0, failed=0))
        entry['rows'] += 1
        entry['max_tokens'] = max(entry['max_tokens'], record.get('tokens', 0))
        entry['max_suffix_tokens'] = max(entry['max_suffix_tokens'], record.get('suffix_tokens', 0))
        entry['over_ceiling'] += bool(record.get('over_ceiling'))
        entry['over_tripwire'] += bool(record.get('over_tripwire'))
        entry['failed'] += record['check_row'] != 'ok'
    failures = [r for r in records if r['check_row'] != 'ok' or r.get('over_tripwire')]
    summary = dict(rows=len(records), streams=streams, launch_ready=not failures,
                   flagged=sorted(failures, key=lambda r: -r.get('tokens', 0))[:200])
    Path(args.out).write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(dict(rows=len(records), streams=streams, launch_ready=not failures)))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='mode', required=True)
    one = sub.add_parser('run')
    one.add_argument('--config', required=True)
    one.add_argument('--out', required=True)
    one.add_argument('--steps', type=int, default=1000)
    one.add_argument('--shard', default='0/1')
    one.add_argument('--tripwire', type=int, default=TRIPWIRE_TOKENS)
    two = sub.add_parser('summarize')
    two.add_argument('--out', required=True)
    two.add_argument('shards', nargs='+')
    args = parser.parse_args()
    if args.mode == 'run':
        import torch
        torch.set_num_threads(int(os.environ.get('OMP_NUM_THREADS', '1')))
        run(args)
    else:
        summarize(args)


if __name__ == '__main__':
    main()
