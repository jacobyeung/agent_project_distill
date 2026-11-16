"""Item-paired scores, scene bootstrap and the preregistered routing decision."""
from student_pilot.r2_policy import unsupported_entry
unsupported_entry('rk/report.py:import')
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from .programs import T, sha256
from . import sets


def score(typ, pred, truth):
    if pred is None:
        return 0.0
    try:
        return T.score(typ, float(pred) if typ in T.NUMERIC else pred, truth)
    except (TypeError, ValueError):
        return 0.0


def bootstrap(rows, samples=4000, seed=17):
    """Resample scenes; retain item weighting within each sampled scene."""
    groups = defaultdict(list)
    for row in rows:
        groups[row['scene']].append(row['delta'])
    if not groups:
        return [None, None]
    values = [groups[k] for k in sorted(groups)]
    sums = np.array([sum(v) for v in values])
    counts = np.array([len(v) for v in values])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(values), size=(samples, len(values)))
    means = sums[draws].sum(1)/counts[draws].sum(1)
    return np.quantile(means, [.025, .975]).tolist()


def decision(types, expected=None):
    expected = tuple(expected or sets.DEV_TYPES)
    wins = [t for t in expected if t in types and types[t]['ci'][0] is not None and types[t]['ci'][0] > 0]
    complete = all(t in types and types[t]['n'] > 0 for t in expected)
    return dict(wins=wins, n_wins=len(wins), complete=complete,
                decision='GO' if complete and len(wins) >= 3 else 'NO-GO' if complete else 'INCOMPLETE')


def keyed(rows, name):
    result = {}
    for row in rows:
        qid = str(row.get('qid', row.get('example_id')))
        if qid == 'None':
            raise ValueError(name+' row lacks qid/example_id')
        if qid in result:
            raise ValueError(name+' has duplicate item '+qid)
        result[qid] = row
    return result


def make_report(routed, direct, truths, which='dev', samples=4000, seed=17):
    routed = keyed(routed, 'routed')
    # A dev direct file can also contain VSI-500 benchmark rows.
    direct = keyed([r for r in direct if str(r.get('qid', r.get('example_id'))) in routed], 'direct')
    paired = sorted(routed.keys() & direct.keys() & truths.keys())
    groups, item_scores = defaultdict(list), []
    for qid in paired:
        r, d = routed[qid], direct[qid]
        ds = float(d['score']) if 'score' in d else score(r['type'], d.get('pred'), truths[qid])
        if not np.isfinite(ds) or not 0 <= ds <= 1:
            raise ValueError('Invalid direct score for '+qid)
        refused = r.get('pred') is None or bool(r.get('refusal'))
        rs = 0.0 if refused else score(r['type'], r['pred'], truths[qid])
        fb = ds if refused else rs
        record = dict(qid=qid, scene=r['scene'], type=r['type'], direct=ds, routed=rs,
                      routed_fb=fb, delta=fb-ds, refused=refused)
        groups[r['type']].append(record)
        item_scores.append(record)
    types = {}
    for typ, rows in groups.items():
        types[typ] = dict(n=len(rows), n_scenes=len({r['scene'] for r in rows}),
                          **{k: float(np.mean([r[k] for r in rows])) for k in
                             ('direct', 'routed', 'routed_fb', 'delta')},
                          ci=bootstrap(rows, samples, seed),
                          refusal_rate=float(np.mean([r['refused'] for r in rows])))
    oracle = any(r.get('gt_substitution') for r in routed.values())
    return dict(set=which, label='ORACLE' if oracle else 'ROUTED', n=len(paired),
                n_routed=len(routed), n_direct=len(direct), unpaired_routed=len(routed)-len(paired),
                bootstrap=dict(samples=samples, seed=seed, unit='scene'), types=types,
                rule=decision(types, sets.DEV_TYPES if which == 'dev' else sets.REVSI_TYPES),
                item_scores=item_scores)


def markdown(report):
    lines = [f"# {report['label']} {report['set']} paired read", '',
             'Scores and differences are percentage points. Refused programs score zero; routed+fb uses the direct answer on refusal.', '',
             '| Type | direct | routed | routed+fb | routed+fb − direct [95% CI] | refusal rate | n |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for typ, row in report['types'].items():
        lines.append(f"| {typ} | {100*row['direct']:.2f} | {100*row['routed']:.2f} | {100*row['routed_fb']:.2f} | "
                     f"{100*row['delta']:+.2f} [{100*row['ci'][0]:+.2f}, {100*row['ci'][1]:+.2f}] | "
                     f"{100*row['refusal_rate']:.2f}% | {row['n']} |")
    lines += ['', f"Decision: **{report['rule']['decision']}**; {report['rule']['n_wins']} of four types have a CI lower bound above zero.", '',
              f"Paired items: {report['n']}; excluded routed items without a direct/GT match: {report['unpaired_routed']}.",
              f"The scene bootstrap uses {report['bootstrap']['samples']:,} draws and seed {report['bootstrap']['seed']}."]
    if report['label'] == 'ORACLE':
        lines += ['', 'ORACLE: this diagnostic substitutes ScanNet GT masks for MDG predictions. It does not establish an MDG routing win.']
    return '\n'.join(lines)+'\n'


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--routed', required=True)
    parser.add_argument('--direct', required=True)
    parser.add_argument('--set', choices=['dev', 'revsi'])
    parser.add_argument('--samples', type=int, default=4000)
    parser.add_argument('--exclude-scenes', help='comma list of <ds>/<scene> keys left out (train/eval overlap audit)')
    parser.add_argument('--out', nargs='+', required=True)
    args = parser.parse_args()
    rows = read_jsonl(args.routed)
    if args.exclude_scenes:
        drop = set(args.exclude_scenes.split(','))
        before = len(rows)
        rows = [r for r in rows if r.get('scene') not in drop]
        print(f'excluded {before-len(rows)} items of {sorted(drop)}')
    which = args.set or (rows[0].get('set') if rows else None)
    if which not in ('dev', 'revsi'):
        raise ValueError('Specify --set for rows without set metadata')
    report = make_report(rows, read_jsonl(args.direct), sets.answers(which), which, args.samples)
    report['input_pins'] = {str(Path(p).resolve()): sha256(p) for p in (args.routed, args.direct)}
    if len(args.out) == 1:
        root = Path(args.out[0])
        md, js = (root, root.with_suffix('.json')) if root.suffix == '.md' else (root/'REPORT.md', root/'REPORT.json')
    elif len(args.out) == 2:
        md, js = map(Path, args.out)
    else:
        raise ValueError('--out requires a directory or REPORT.md REPORT.json')
    for path in (md, js):
        path.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(markdown(report))
    js.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(markdown(report))


if __name__ == '__main__':
    main()
