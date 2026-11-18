#!/usr/bin/env python3
"""Compare camera journals with the pinned H1 measurements and room bootstrap."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import sys
import tarfile

# Importing the evaluator does not load a model or run inference.
sys.dont_write_bytecode = True
PACKAGE = Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin/out/production')
sys.path[:0] = [str(PACKAGE / 'b'), str(PACKAGE / 'tree'), str(PACKAGE)]
import numpy as np
from h1eval.runner import measure
from h1eval import statistics
from h1eval.modes import mode_key

WORKSPACE = Path(__file__).resolve().parent.parent
TYPES = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')
ERROR = dict(zip(TYPES, ('absolute_error_m', 'error_deg', 'correct')))
MODES = {
    'camera_displacement': ('none', 'scale_translation:0.5', 'scale_translation:2'),
    'camera_rotation': ('none', 'negate_turn'),
    'camera_movement_direction': ('none', 'rotate_translation:180'),
}


def manifest_items():
    manifest = json.loads((PACKAGE / 'items/devs1_routed.json').read_text())
    return {r['id']: r for r in manifest['items'] if r['question_type'] in TYPES}


def journal_name(name):
    parts = PurePosixPath(name).parts
    return len(parts) >= 4 and parts[-4] == 'journals' and parts[-1] == 'items.jsonl'


def read_rows(path):
    """Stream journals without extracting archives; ignore non-camera/other arms."""
    path = Path(path).resolve()
    if not path.is_relative_to(WORKSPACE):
        raise ValueError('Inputs must be inside ' + str(WORKSPACE))
    rows, ignored = [], 0

    def consume(stream, source):
        nonlocal ignored
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except (ValueError, UnicodeError) as exc:
                raise ValueError(f'{source}:{number}: invalid JSONL') from exc
            if row.get('type') not in TYPES or row.get('arm') != 'own':
                ignored += 1
                continue
            if row.get('complete') is not True:
                raise ValueError(f'{source}:{number}: incomplete record')
            rows.append(row)

    if path.is_dir():
        roots = (path / 'metadata/journals', path / 'journals', path)
        files = []
        for root in roots:
            files = sorted(root.glob('*/*/items.jsonl'))
            if files:
                break
        if not files and (path / 'items.jsonl').is_file():
            files = [path / 'items.jsonl']
        for file in files:
            if not file.resolve().is_relative_to(WORKSPACE):
                raise ValueError('Journal symlink leaves workspace: ' + str(file))
            with file.open('rb') as stream:
                consume(stream, str(file))
    elif path.suffix == '.jsonl':
        with path.open('rb') as stream:
            consume(stream, str(path))
    else:
        with tarfile.open(path, 'r|*') as archive:
            for member in archive:
                if journal_name(member.name):
                    if not member.isfile():
                        raise ValueError('Journal archive member is not a regular file')
                    with archive.extractfile(member) as stream:
                        consume(stream, member.name)
    if not rows:
        raise ValueError(f'{path}: no own camera records')
    return rows, dict(path=str(path), camera_reads=len(rows), ignored_reads=ignored)


def index_rows(rows, label):
    indexed = {}
    for row in rows:
        key = (row['id'], row['mode'])
        if key in indexed:
            raise ValueError(f'{label}: duplicate item/arm/mode: {key}')
        indexed[key] = row
    return indexed


def pairing(a, b):
    left, right = index_rows(a, 'A'), index_rows(b, 'B')
    counts = {}
    for kind in TYPES:
        x = {r['id'] for r in a if r['type'] == kind}
        y = {r['id'] for r in b if r['type'] == kind}
        counts[kind] = dict(a_items=len(x), b_items=len(y), shared_items=len(x & y),
                            a_reads=sum(r['type'] == kind for r in a),
                            b_reads=sum(r['type'] == kind for r in b),
                            only_a=sorted(x - y), only_b=sorted(y - x))
    if any(c['only_a'] or c['only_b'] for c in counts.values()):
        raise ValueError('Item sets differ: ' + json.dumps(counts, sort_keys=True))
    if left.keys() != right.keys():
        raise ValueError('Read sets differ: ' + json.dumps(dict(
            counts=counts, a_reads=len(left), b_reads=len(right),
            only_a=sorted(left.keys() - right.keys()),
            only_b=sorted(right.keys() - left.keys()))))
    return left, right, counts


def measured(indexed, items):
    result = {}
    for key, row in sorted(indexed.items()):
        identifier, mode = key
        if identifier not in items:
            raise ValueError('Unknown manifest item: ' + identifier)
        item = items[identifier]
        if row['type'] != item['question_type'] or row['room_key'] != item['room_key']:
            raise ValueError('Item type/room differs from manifest: ' + identifier)
        if mode not in MODES[row['type']] or mode_key(row['intervention']) != mode:
            raise ValueError('Unexpected intervention: ' + str(key))
        required = {(identifier, m) for m in MODES[row['type']]}
        if not required <= indexed.keys():
            raise ValueError('Incomplete mode plan: ' + str(sorted(required - indexed.keys())))
        baseline = indexed[(identifier, 'none')]['output'] if mode != 'none' else None
        values = measure(row['output'], item, baseline)
        result[key] = dict(id=identifier, type=row['type'], arm='own', mode=mode,
                           room_key=row['room_key'], measurements=values)
    return result


def finite(value):
    return value is not None and math.isfinite(float(value))


def paired_bootstrap(values):
    """Extend statistics.bootstrap to two denominators on the same room draw.

    Each tuple is (room, A scalar or None, B scalar or None). The package's
    room ordering, RNG, batching, ratio estimator and percentiles are preserved.
    Missing calls / M3 ineligibility retain each side's own denominator.
    """
    groups = defaultdict(lambda: [[], []])
    for room, a, b in values:
        for side, value in enumerate((a, b)):
            if finite(value):
                groups[room][side].append(float(value))
    groups = [groups[k] for k in sorted(groups)]
    n_both = sum(finite(a) and finite(b) for _, a, b in values)
    if not groups or any(not any(g[s] for g in groups) for s in (0, 1)):
        return dict(value=None, ci95=None, n_both=n_both, rooms=len(groups),
                    valid_draws=0, undefined_draws=statistics.DRAWS)
    sums = np.array([[sum(v) for v in g] for g in groups])
    counts = np.array([[len(v) for v in g] for g in groups])
    point = sums.sum(0) / counts.sum(0)
    rng = np.random.default_rng(statistics.SEED)
    samples = []
    for start in range(0, statistics.DRAWS, 200):
        indices = rng.integers(0, len(groups), size=(min(200, statistics.DRAWS-start), len(groups)))
        draw_counts = counts[indices].sum(1)
        valid = np.all(draw_counts > 0, axis=1)
        means = sums[indices].sum(1)[valid] / draw_counts[valid]
        samples.extend((means[:, 1] - means[:, 0]).tolist())
    undefined = statistics.DRAWS - len(samples)
    # Do not silently condition the requested interval on nonempty draws.
    ci = np.quantile(samples, [.025, .975]).tolist() if not undefined else None
    return dict(value=float(point[1]-point[0]), ci95=ci, n_both=n_both,
                rooms=len(groups), valid_draws=len(samples), undefined_draws=undefined)


def compare(a, b, items=None):
    left, right, counts = pairing(a, b)
    items = manifest_items() if items is None else items
    left, right = measured(left, items), measured(right, items)
    groups = defaultdict(list)
    per_item = []
    for key in sorted(left):
        x, y = left[key], right[key]
        if x['room_key'] != y['room_key'] or x['type'] != y['type']:
            raise ValueError('Paired item metadata differs: ' + str(key))
        groups[(x['type'], x['mode'])].append((x, y))
        per_item.append({k: x[k] for k in ('id', 'type', 'arm', 'mode', 'room_key')} | {
            side: {m: row['measurements'][m] for m in ('M1', 'M2', 'M3')
                   if m in row['measurements']} for side, row in (('a', x), ('b', y))})
    result = {}
    for (kind, mode), rows in sorted(groups.items()):
        names = (['M1.call_rate', 'M1.exact', 'M1.answer_before_first_call',
                  'M2.' + ERROR[kind], 'M2.task_accuracy'] if mode == 'none'
                 else ['M3.follow', 'M3.stick'])
        scalars = [(x['room_key'], statistics.scalar_metrics(x), statistics.scalar_metrics(y))
                   for x, y in rows]
        metrics = {}
        for name in names:
            values = [(room, x.get(name), y.get(name)) for room, x, y in scalars]
            side_a = statistics.bootstrap([(room, x) for room, x, _ in values])
            side_b = statistics.bootstrap([(room, y) for room, _, y in values])
            delta = paired_bootstrap(values)
            ci = delta['ci95']
            differs = (ci[0] > 0 or ci[1] < 0) if ci is not None else None
            metrics[name] = dict(a=side_a, b=side_b, b_minus_a=delta, differs=differs)
        result.setdefault(kind, {})[mode] = dict(paired_items=len(rows), metrics=metrics)
    return dict(schema='m2pair-v1', arm='own', difference='B minus A',
                bootstrap=dict(draws=statistics.DRAWS, seed=statistics.SEED, interval=.95,
                               unit='room', estimator='item-weighted ratio of room sums/counts'),
                counts=counts, per_type=result, per_item=per_item)


def markdown(result):
    def number(value):
        return '—' if value is None else f'{value:.4f}'
    lines = ['B minus A; paired room bootstrap, 10,000 draws, seed 20261115, 95% interval.',
             'Rates use fractions. Displacement uses metres; rotation uses degrees.', '']
    for kind, modes in result['per_type'].items():
        c = result['counts'][kind]
        lines += [f"**{kind}** — A: {c['a_items']} items/{c['a_reads']} reads; "
                  f"B: {c['b_items']} items/{c['b_reads']} reads; {c['shared_items']} paired items.", '',
                  '| Mode / metric | A | B | B−A [95% CI] | Differs |',
                  '|---|---:|---:|---:|:---:|']
        for mode, record in modes.items():
            for name, metric in record['metrics'].items():
                delta = metric['b_minus_a']
                ci = delta['ci95']
                interval = f'[{number(ci[0])}, {number(ci[1])}]' if ci is not None else '[unavailable]'
                flag = {True: 'yes', False: 'no', None: 'unavailable'}[metric['differs']]
                lines.append(f"| {mode} / {name} | {number(metric['a']['value'])} | "
                             f"{number(metric['b']['value'])} | {number(delta['value'])} {interval} | {flag} |")
        lines.append('')
    lines += ['JSON includes per-side intervals, scoring denominators, and per-read measurements.',
              'M2 averages scored calls within each item. M3 uses each side’s eligible reads.',
              'An interval is unavailable if either mean is undefined on any room draw.', '']
    return '\n'.join(lines)


def output_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to(WORKSPACE / 'out'):
        raise ValueError('Outputs must be under ' + str(WORKSPACE / 'out'))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--a', required=True)
    parser.add_argument('--b', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--md')
    args = parser.parse_args()
    try:
        destination = output_path(args.output)
        md = output_path(args.md) if args.md else None
        if md == destination:
            raise ValueError('JSON and Markdown paths must differ')
        a, source_a = read_rows(args.a)
        b, source_b = read_rows(args.b)
        result = compare(a, b)
        result['sources'] = dict(a=source_a, b=source_b, package=str(PACKAGE),
                                 evaluator_sha256={name: hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest()
                                 for name in ('h1eval/runner.py', 'h1eval/scorers.py',
                                              'h1eval/statistics.py', 'items/devs1_routed.json')})
        text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)
        if md:
            md.parent.mkdir(parents=True, exist_ok=True)
            md.write_text(markdown(result))
        print(json.dumps(dict(output=str(destination), counts=result['counts']), sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, tarfile.TarError) as exc:
        parser.exit(2, f'm2pair: {exc}\n')


if __name__ == '__main__':
    main()
