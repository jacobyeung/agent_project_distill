"""Compare R0-dev journal answer scores with the supplied f32 constants."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

from parity_kit.common import key, read, rows, sha
from parity_kit.r0dev import DEFAULT_OUT, SUMMARY, json_bytes, write_new


def report(journals, tasks_path=DEFAULT_OUT / 'TASKS_R0DEV.jsonl', summary_path=SUMMARY):
    """Aggregate completed answer scores; missing and unscored items stay explicit.

    Constants describe the full dev set, even when a journal is partial. This
    summary checks keys and scores, but does not authenticate run receipts.
    """
    tasks = rows(tasks_path)
    by_key = {key(t): t for t in tasks}
    if len(by_key) != len(tasks):
        raise ValueError('duplicate task keys')
    constants = read(summary_path)['constants']
    completed, arms = {}, set()
    for journal in journals:
        for row in rows(journal):
            k = row['key']
            if k not in by_key:
                raise ValueError('unknown journal key: ' + k)
            if k in completed:
                raise ValueError('duplicate journal key: ' + k)
            if row.get('question_type', by_key[k]['question_type']) != by_key[k]['question_type']:
                raise ValueError('journal question_type mismatch: ' + k)
            if 'arm' in row:
                arms.add(row['arm'])
            score = row['scores']['answer']
            if score is not None and (type(score) not in (int, float)
                                      or not math.isfinite(score) or not 0 <= score <= 1):
                raise ValueError('invalid answer score: ' + k)
            completed[k] = score
    if len(arms) > 1:
        raise ValueError('journals mix reader arms')
    grouped = defaultdict(list)
    for task in tasks:
        grouped[task['question_type']].append(key(task))
    per_type = {}
    for kind, keys in sorted(grouped.items()):
        constant = constants[kind]
        metric = 'dev_mra_f32' if 'dev_mra_f32' in constant else 'dev_acc'
        missing = [k for k in keys if k not in completed]
        unscored = [k for k in keys if k in completed and completed[k] is None]
        values = [completed[k] for k in keys if k in completed and completed[k] is not None]
        per_type[kind] = dict(n_expected=len(keys), n_completed=len(keys) - len(missing),
                              n_scored=len(values), n_missing=len(missing),
                              n_unscored=len(unscored), missing_keys=missing, unscored_keys=unscored,
                              mean_score=math.fsum(values) / len(values) if values else None,
                              constant_dev_score=constant[metric] / 100,
                              constant_metric=metric, constant_n_dev=constant['n_dev'],
                              constant_value=constant['value'])
    return dict(schema='r0dev-constants-v1', score_scale='0..1',
                coverage='full' if len(completed) == len(tasks) else 'partial',
                n_expected=len(tasks), n_completed=len(completed),
                n_scored=sum(s is not None for s in completed.values()),
                missing_keys=[key(t) for t in tasks if key(t) not in completed],
                arm=next(iter(arms)) if arms else None, per_type=per_type,
                inputs=dict(tasks=dict(path=str(tasks_path), sha256=sha(tasks_path)),
                            summary=dict(path=str(summary_path), sha256=sha(summary_path)),
                            journals=[dict(path=str(p), sha256=sha(p)) for p in journals]))


def table(result):
    lines = ['R0-dev f32: mean scores and full-dev constants (%)',
             'Partial means use scored items only; constants use the full dev set.',
             'question_type | mean % | constant % | scored/completed/expected | missing | unscored']
    for kind, row in result['per_type'].items():
        mean = 'NA' if row['mean_score'] is None else f"{100 * row['mean_score']:.6f}"
        lines.append(f"{kind} | {mean} | {100 * row['constant_dev_score']:.6f} | "
                     f"{row['n_scored']}/{row['n_completed']}/{row['n_expected']} | "
                     f"{row['n_missing']} | {row['n_unscored']}")
    lines.append('Missing keys: ' + json.dumps(result['missing_keys']))
    unscored = [k for r in result['per_type'].values() for k in r['unscored_keys']]
    lines.append('Unscored keys: ' + json.dumps(unscored))
    return '\n'.join(lines) + '\n'


def save_report(result, out_dir):
    out = Path(out_dir)
    for name in ('REPORT.json', 'TABLE.txt'):
        if (out / name).exists():
            raise FileExistsError(out / name)
    write_new(out / 'REPORT.json', json_bytes(result))
    write_new(out / 'TABLE.txt', table(result).encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journals', nargs='+', type=Path, required=True)
    parser.add_argument('--tasks', type=Path, default=DEFAULT_OUT / 'TASKS_R0DEV.jsonl')
    parser.add_argument('--summary', type=Path, default=SUMMARY)
    parser.add_argument('--out', type=Path, required=True, help='New report directory')
    args = parser.parse_args()
    result = report(args.journals, args.tasks, args.summary)
    save_report(result, args.out)
    print(table(result), end='')


if __name__ == '__main__':
    main()
