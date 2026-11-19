#!/usr/bin/env python3
"""Stream stored corpus scores; never rescore generated text."""
import argparse
import collections
import gzip
import json
import math
import sys


def collect(path, arm=None, by=None, family=None, stratum=None, question_type=None, mean_of_types=False):
    totals, groups, type_groups = {}, {}, {}
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            row = json.loads(line)
            if family is not None and row['family'] != family:
                continue
            if stratum is not None and row['truth']['stratum'] != stratum:
                continue
            if question_type is not None and row['question_type'] != question_type:
                continue
            for name, value in row['arms'].items():
                if arm is not None and name != arm:
                    continue
                buckets = [totals.setdefault(name, [0, 0, 0.0])]
                if by:
                    group = row.get(by)
                    buckets.append(groups.setdefault(name, {}).setdefault('null' if group is None else str(group), [0, 0, 0.0]))
                if mean_of_types:
                    group = ('null' if row.get(by) is None else str(row[by])) if by else '__all__'
                    key = (group, str(row.get('question_type')))
                    buckets.append(type_groups.setdefault(name, {}).setdefault(key, [0, 0, 0.0]))
                score = value.get('score')
                for bucket in buckets:
                    bucket[0] += 1
                    if score is not None:
                        if not isinstance(score, (int, float)) or not math.isfinite(score):
                            raise ValueError('Non-numeric or non-finite score')
                        bucket[1] += 1
                        bucket[2] += score
    def summary(bucket):
        items, scored, total = bucket
        return dict(items=items, scored=scored, mean_score=total / scored if scored else None)
    result = {name: dict(overall=summary(bucket)) for name, bucket in totals.items()}
    for name, values in groups.items():
        result[name]['groups'] = {key: summary(bucket) for key, bucket in values.items()}
    if mean_of_types:
        for name, values in type_groups.items():
            grouped = collections.defaultdict(list)
            for (group, typ), bucket in values.items():
                if bucket[1]:
                    grouped[group].append(bucket[2] / bucket[1])
            means = {g: sum(v) / len(v) for g, v in grouped.items()}
            overall = result[name]['overall']
            overall['item_mean_score'] = overall['mean_score']
            overall['mean_score'] = sum(means.values()) / len(means) if means else None
            if by:
                for g, mean in means.items():
                    bucket = result[name]['groups'][g]
                    bucket['item_mean_score'] = bucket['mean_score']
                    bucket['mean_score'] = mean
    if arm is not None and arm not in result:
        raise ValueError('No items for arm/filter: ' + arm)
    return dict(by=by, mean_of_types=mean_of_types, arms=result)


def compare(result, summary, key):
    expected = summary
    for part in key.split('.'):
        expected = expected[int(part)] if isinstance(expected, list) else expected[part]
    if not isinstance(expected, (int, float)) or not math.isfinite(expected):
        raise ValueError('Comparison key must select a finite number')
    # Field names disambiguate percentages below 1%; otherwise scores >1 are percentages.
    percent = key.split('.')[-1].endswith(('pct', 'percent')) or expected > 1
    scaled = expected / 100.0 if percent else expected
    return {name: dict(corpus=value['overall']['mean_score'], reported=expected,
                       reported_fraction=scaled, reported_units='percent' if percent else 'fraction',
                       result='MATCH' if value['overall']['mean_score'] is not None and
                       abs(value['overall']['mean_score'] - scaled) <= 1e-6 else 'DIFF')
            for name, value in result['arms'].items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('read')
    parser.add_argument('--arm')
    parser.add_argument('--by', choices=['question_type', 'category', 'family', 'set'])
    parser.add_argument('--mean-of-types', action='store_true',
                        help='Average type means within each --by group, then average group means')
    parser.add_argument('--compare')
    parser.add_argument('--key')
    for flag in ('family', 'stratum', 'question-type'):
        parser.add_argument('--' + flag)
    args = parser.parse_args(argv)
    if bool(args.compare) != bool(args.key):
        parser.error('--compare and --key are required together')
    try:
        result = collect(args.read, args.arm, args.by, args.family, args.stratum, args.question_type, args.mean_of_types)
        if args.compare:
            with open(args.compare, encoding='utf-8') as f:
                result['comparison'] = compare(result, json.load(f), args.key)
        print(json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, IndexError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
