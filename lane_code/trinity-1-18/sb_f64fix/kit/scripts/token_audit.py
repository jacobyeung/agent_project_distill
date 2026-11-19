"""Pre-launch token audit of every distinct row a run's plan will fetch, on CPU, before any GPU.

The R1 trainer aborts on the first row that fails check_row (carrier_c1_run.py fetch: "R1 row failure
forbids substituting the pinned row plan"), and nested 64-viewpoint input adds 4,424 tokens (4:3) or
4,880 tokens (16:9) to every video row. The routing build admits suffixes up to 9,600 tokens, so the
16,384-token ceiling no longer bounds a 64-viewpoint routing row. This audit encodes each planned row
through the trainer's own Rows.get and check_row and flags rows over the ceiling and rows over the
memory tripwire length (default 11,500 tokens; an unmeasured planning bound until the GPU pilot runs).

Each shard file starts with a header that binds the run by sha256 (config file, preparation receipt,
sampler, stores, horizon, limits, code, the complete plan and this shard's rows) and ends with a footer
that counts and hashes its records; a shard without its footer is incomplete. `summarize` returns
launch_ready only when the shards come from one run, every shard 0..n-1 appears exactly once, they cover
every planned row exactly once over the whole run horizon, every record carries its required fields,
and no row fails check_row or passes the tripwire.

Usage
  token_audit.py run --config BOUND_CFG.json --out shard_0.jsonl --shard 0/8 [--steps N]
  token_audit.py summarize --config BOUND_CFG.json --out SUMMARY.json shard_*.jsonl
Run one process per shard, each with OMP_NUM_THREADS=1. --steps audits only the first N steps of the
horizon, which summarize reports as horizon_short. summarize exits 2 unless launch_ready.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

TREE = Path(os.environ.get('F64_TREE', '/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_f64'))
sys.path[:0] = [str(TREE)]
TRIPWIRE_TOKENS = 11500
SCHEMA = 'f64-token-audit-v2'
LONGEST = 256
ROW_FIELDS = {'kind': str, 'stream': str, 'index': int, 'first_step': int, 'rank': int, 'check_row': str,
              'seconds': (int, float)}
OK_FIELDS = {'tokens': int, 'over_ceiling': bool, 'over_tripwire': bool, 'grid': (list, type(None)),
             'qid': (str, type(None))}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_sha256(path):
    with open(path, 'rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def horizon(cfg, recipe):
    """The trainer's first and last step for a fresh launch (carrier_c1_run.train and run_steps)."""
    start = 0
    if 'r1_training' in cfg:
        from student_pilot.r1_training import start as r1_start
        start = r1_start(cfg)
    end = recipe['steps']
    stop = (cfg.get('r1_training') or {}).get('stop_after_step')
    if stop is not None:
        end = min(end, stop)
    return start, end


def planned_rows(cfg, receipt, recipe, start, end):
    """Distinct (stream, index) rows of steps start+1..end, as run_steps enumerates them."""
    from student_pilot import carrier_c1_data as data
    counts = {k: v['count'] for k, v in receipt['streams'].items()}
    offset = cfg.get('row_start_step', 0)
    plans = data.mixed_indices(counts, offset + end, start_step=offset + start,
                               training_mode=cfg.get('training_mode', 'mixed'), mix=recipe['mix'],
                               world=recipe['world_size'], r2_sampling=cfg.get('r2_sampling'),
                               require_r2='r2_identity' in cfg)
    seen = {}
    for step, plan in enumerate(plans, start + 1):
        for stream, indices in plan:
            for rank, index in enumerate(indices):
                seen.setdefault((stream, int(index)), (step, rank))
    return sorted(seen.items())


def keys(items):
    return [[stream, index, step, rank] for (stream, index), (step, rank) in items]


def identity_for(config_sha256, cfg, receipt, recipe, items, start, end, run_end, limit, tripwire, shards, preparation):
    """Everything the audited plan depends on, by sha256; the run id is the digest of this value."""
    from student_pilot import carrier_c1_data, carrier_c1_run, r2_mix
    sampler = dict(function='carrier_c1_data.mixed_indices', seed=17, training_mode=cfg.get('training_mode', 'mixed'),
                   mix=recipe['mix'], world=recipe['world_size'], row_start_step=cfg.get('row_start_step', 0),
                   r2_sampling_sha256=digest(cfg['r2_sampling']) if cfg.get('r2_sampling') else None,
                   require_r2='r2_identity' in cfg)
    return dict(
        schema=SCHEMA, config_sha256=config_sha256, preparation=preparation,
        sampler=dict(sampler, sha256=digest(sampler)),
        stores={k: dict(sha256=digest(v), count=v['count'], database_sha256=(v.get('database') or {}).get('sha256'))
                for k, v in sorted(receipt['streams'].items())},
        horizon=dict(start_step=start, end_step=end, run_end_step=run_end),
        limits=dict(max_row_tokens=limit, tripwire_tokens=tripwire,
                    max_routing_suffix_tokens=recipe.get('max_routing_suffix_tokens')),
        code={Path(m.__file__).name: file_sha256(m.__file__) for m in (carrier_c1_data, carrier_c1_run, r2_mix)}
             | {'token_audit.py': file_sha256(__file__)},
        plan=dict(rows=len(items), sha256=digest(keys(items))), shards=shards)


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


def write_shard(out, identity, shard, items, run_audit):
    """Header (run id, identity, this shard's rows), one line per audited row, then the footer."""
    if not items:
        raise ValueError('shard has no planned rows; use fewer shards')
    run_id = digest(identity)
    header = dict(kind='header', schema=SCHEMA, run_id=run_id, identity=identity,
                  shard=dict(index=shard, count=identity['shards'], rows=len(items), sha256=digest(keys(items))))
    hasher, written = hashlib.sha256(), [0]
    with Path(out).open('x') as handle:
        handle.write(json.dumps(header, sort_keys=True) + '\n')

        def sink(record):
            line = json.dumps(dict(record, kind='row'), sort_keys=True) + '\n'
            handle.write(line)
            handle.flush()
            hasher.update(line.encode())
            written[0] += 1
        run_audit(items, sink)
        handle.write(json.dumps(dict(kind='footer', run_id=run_id, shard=shard, records=written[0],
                                     records_sha256=hasher.hexdigest()), sort_keys=True) + '\n')


def run(args):
    from student_pilot.carrier_c1_run import (MAX_TOKENS, Rows, file_pin, prepared, processor_for_receipt,
                                              recipe_for, validate)
    cfg = json.loads(Path(args.config).read_text())
    validate(cfg)
    if not cfg.get('preparation'):
        cfg = {**cfg, 'preparation': file_pin(Path(cfg['preparation_output']) / 'receipt.json')}
    receipt, manifest = prepared(cfg, admission=True)
    recipe = recipe_for(cfg)
    start, run_end = horizon(cfg, recipe)
    end = run_end if args.steps is None else min(run_end, start + args.steps)
    items = planned_rows(cfg, receipt, recipe, start, end)
    shard, shards = map(int, args.shard.split('/'))
    if not 0 <= shard < shards:
        raise SystemExit('--shard must be k/n with 0 <= k < n')
    limit = recipe.get('max_row_tokens', MAX_TOKENS)
    identity = identity_for(file_sha256(args.config), cfg, receipt, recipe, items, start, end, run_end, limit,
                            args.tripwire, shards, cfg['preparation'])
    if Path(args.out).exists():
        raise SystemExit(f'{args.out} exists; choose a fresh path')
    rows = Rows(receipt, processor_for_receipt(manifest, receipt))
    try:
        write_shard(args.out, identity, shard, items[shard::shards],
                    lambda part, sink: audit(rows, recipe, receipt, part, sink, args.tripwire))
    finally:
        rows.close()


def fields_missing(record):
    wanted = dict(ROW_FIELDS, **(OK_FIELDS if record.get('check_row') == 'ok' else {}))
    if record.get('check_row') == 'ok' and record.get('stream') == 'routing':
        wanted['suffix_tokens'] = int
    return sorted(k for k, kind in wanted.items()
                  if k not in record or not isinstance(record[k], kind)
                  or (kind is int and isinstance(record[k], bool)))


def count(record, key):
    value = record.get(key)
    return value if type(value) is int else 0


def identity_complete(identity):
    try:
        return (all(isinstance(identity[k], str) for k in ('schema', 'config_sha256'))
                and isinstance(identity['sampler']['sha256'], str) and isinstance(identity['stores'], dict)
                and all(type(identity['horizon'][k]) is int for k in ('start_step', 'end_step', 'run_end_step'))
                and isinstance(identity['limits'], dict) and isinstance(identity['code'], dict)
                and type(identity['plan']['rows']) is int and isinstance(identity['plan']['sha256'], str)
                and type(identity['shards']) is int and 'preparation' in identity)
    except (KeyError, TypeError):
        return False


def read_shard(path, errors):
    """(header, records) of one complete shard, or None with the reason appended to errors."""
    lines = Path(path).read_text().splitlines(keepends=True)
    if not lines:
        errors.append(f'shard_empty:{path}')
        return None
    try:
        parsed = [json.loads(line) for line in lines]
    except ValueError:
        errors.append(f'shard_unparseable:{path}')
        return None
    header, body = parsed[0], parsed[1:]
    if (not isinstance(header, dict) or header.get('kind') != 'header' or header.get('schema') != SCHEMA
            or not isinstance(header.get('identity'), dict) or not isinstance(header.get('shard'), dict)):
        errors.append(f'shard_header_missing:{path}')
        return None
    if digest(header['identity']) != header.get('run_id'):
        errors.append(f'shard_identity_digest_differs:{path}')
        return None
    footer = body[-1] if body and isinstance(body[-1], dict) and body[-1].get('kind') == 'footer' else None
    if footer is None:
        errors.append(f'shard_incomplete:{path}')
        return None
    records = body[:-1]
    shard = header['shard']
    if (footer.get('run_id') != header['run_id'] or footer.get('shard') != shard.get('index')
            or footer.get('records') != len(records)
            or footer.get('records_sha256') != hashlib.sha256(''.join(lines[1:-1]).encode()).hexdigest()):
        errors.append(f'shard_footer_differs:{path}')
        return None
    if not all(isinstance(r, dict) and r.get('kind') == 'row' for r in records):
        errors.append(f'shard_record_kind:{path}')
        return None
    if not records or shard.get('rows') != len(records) or shard.get('count') != header['identity'].get('shards'):
        errors.append(f'shard_rows_differ:{path}')
        return None
    if digest([[r.get('stream'), r.get('index'), r.get('first_step'), r.get('rank')] for r in records]) != shard.get('sha256'):
        errors.append(f'shard_rows_differ_from_plan:{path}')
        return None
    return header, records


def summarize(paths, config_sha256=None):
    errors, shards, seen = [], {}, set()
    for path in paths:
        resolved = str(Path(path).resolve())
        if resolved in seen:
            errors.append(f'shard_file_repeated:{path}')
            continue
        seen.add(resolved)
        value = read_shard(path, errors)
        if value is None:
            continue
        index = value[0]['shard']['index']
        if index in shards:
            errors.append(f'shard_duplicate:{index}')
            continue
        shards[index] = value
    run_ids = sorted({header['run_id'] for header, _ in shards.values()})
    identity = shards[min(shards)][0]['identity'] if shards else None
    if not shards:
        errors.append('no_complete_shard')
    if len(run_ids) > 1:
        errors.append(f'mixed_runs:{run_ids}')
    records = [r for _, (_, part) in sorted(shards.items()) for r in part]
    incomplete = [dict(stream=r.get('stream'), index=r.get('index'), missing=fields_missing(r))
                  for r in records if fields_missing(r)]
    if incomplete:
        errors.append(f'record_fields_missing:{len(incomplete)}')
    records = [r for r in records if not set(fields_missing(r)) & set(ROW_FIELDS)]
    coverage = dict(planned=None, audited=len(records), unique=len({(r['stream'], r['index']) for r in records}))
    if identity is not None and not identity_complete(identity):
        errors.append('identity_incomplete')
    elif identity is not None:
        if config_sha256 is not None and identity['config_sha256'] != config_sha256:
            errors.append('config_differs')
        if not (identity['preparation'] or {}).get('sha256'):
            errors.append('preparation_unbound')
        expected = set(range(identity['shards']))
        if not expected or set(shards) != expected:
            errors.append(f'shards_missing:{sorted(expected - set(shards))}')
        coverage['planned'] = identity['plan']['rows']
        if coverage['unique'] != coverage['audited']:
            errors.append('rows_duplicated')
        ordered = [[s, i, step, rank] for (s, i), (step, rank) in
                   sorted(((r['stream'], r['index']), (r['first_step'], r['rank'])) for r in records)]
        if len(ordered) != identity['plan']['rows'] or digest(ordered) != identity['plan']['sha256']:
            errors.append('plan_not_covered')
        span = identity['horizon']
        if span['end_step'] != span['run_end_step']:
            errors.append(f'horizon_short:{span["end_step"]}<{span["run_end_step"]}')
    streams, longest = {}, {}
    for record in records:
        entry = streams.setdefault(record['stream'], dict(rows=0, max_tokens=0, max_suffix_tokens=0, over_ceiling=0,
                                                          over_tripwire=0, failed=0))
        entry['rows'] += 1
        entry['max_tokens'] = max(entry['max_tokens'], count(record, 'tokens'))
        entry['max_suffix_tokens'] = max(entry['max_suffix_tokens'], count(record, 'suffix_tokens'))
        entry['over_ceiling'] += bool(record.get('over_ceiling'))
        entry['over_tripwire'] += bool(record.get('over_tripwire'))
        entry['failed'] += record['check_row'] != 'ok'
        if record['check_row'] == 'ok' and not fields_missing(record):
            longest.setdefault(record['stream'], []).append(
                {k: record.get(k) for k in ('index', 'tokens', 'suffix_tokens', 'first_step', 'rank', 'qid')})
    for stream, values in longest.items():
        longest[stream] = sorted(values, key=lambda r: (-r['tokens'], r['index']))[:LONGEST]
    failures = [r for r in records if r['check_row'] != 'ok' or r.get('over_tripwire')]
    return dict(schema=SCHEMA + '-summary', run_id=run_ids[0] if len(run_ids) == 1 else None, identity=identity,
                launch_ready=not errors and not failures, errors=errors, coverage=coverage, streams=streams,
                incomplete_records=incomplete[:50], flagged=sorted(failures, key=lambda r: -count(r, 'tokens'))[:200],
                longest=longest, shard_files={str(p): file_sha256(p) for p in paths if Path(p).is_file()})


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='mode', required=True)
    one = sub.add_parser('run')
    one.add_argument('--config', required=True)
    one.add_argument('--out', required=True)
    one.add_argument('--steps', type=int, default=None)
    one.add_argument('--shard', default='0/1')
    one.add_argument('--tripwire', type=int, default=TRIPWIRE_TOKENS)
    two = sub.add_parser('summarize')
    two.add_argument('--config', required=True)
    two.add_argument('--out', required=True)
    two.add_argument('shards', nargs='+')
    args = parser.parse_args()
    if args.mode == 'run':
        import torch
        torch.set_num_threads(int(os.environ.get('OMP_NUM_THREADS', '1')))
        run(args)
        return
    summary = summarize(args.shards, file_sha256(args.config))
    Path(args.out).write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps({k: summary[k] for k in ('launch_ready', 'errors', 'coverage', 'streams')}))
    sys.exit(0 if summary['launch_ready'] else 2)


if __name__ == '__main__':
    main()
