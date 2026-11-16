"""Validate the renderings: validator a41ba191 on every row (and the first 100 away rows reported apart),
label equality with the source twins, and an independent re-derivation of the answer from each away trace.
Usage: check_renderings.py --validator DIR --src facing_v5.jsonl.gz --rendered facing_rX.jsonl --out CHECK_rX.json
"""
import argparse
import collections
import gzip
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import classify_away as C  # noqa: E402

PIN = 'a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268'


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--validator', required=True)
    p.add_argument('--src', required=True)
    p.add_argument('--rendered', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args(argv)
    vpath = os.path.join(a.validator, 'trace_grammar.py')
    vsha = hashlib.sha256(open(vpath, 'rb').read()).hexdigest()
    if vsha != PIN:
        raise SystemExit('validator sha mismatch ' + vsha)
    sys.path.insert(0, a.validator)
    import trace_grammar as V
    src = {}
    with gzip.open(a.src, 'rt') as fh:
        for line in fh:
            d = json.loads(line)
            src[d['i']] = d['row']
    rules = collections.Counter()
    failed = first100_failed = first100 = away_seen = 0
    label_diff = derive_diff = 0
    examples = []
    n = 0
    with open(a.rendered) as fh:
        for line in fh:
            d = json.loads(line)
            row, s = d['row'], src[d['i']]
            n += 1
            errs = V.validate_row(row)
            if row['facing'] == 'away':
                away_seen += 1
                if away_seen <= 100:
                    first100 += 1
                    first100_failed += bool(errs)
            if errs:
                failed += 1
                for e in errs:
                    rules[e.rule_id] += 1
                if len(examples) < 5:
                    examples.append(dict(i=d['i'], errs=[e._asdict() for e in errs][:3]))
            if (row['answer'], row['student_input']['options'], row['pair_id'], row['qid'], row['facing']) != \
                    (s['answer'], s['student_input']['options'], s['pair_id'], s['qid'], s['facing']):
                label_diff += 1
            if row['facing'] == 'away':
                # independent: the conclusion line, read by the classifier's parser, names the answer content
                level = C.level_of(dict(options=row['student_input']['options'], id=row['qid']))
                body = row['target'].split('</think>')[0]
                concl = C.conclusion_content(body, level)
                ans = C.option_contents(dict(options=row['student_input']['options']))[row['answer']]
                fwd = C.stated_forward(body, level)
                ok = concl == ans and fwd is not None and C.content(C.half_turn(fwd, level), level) == ans \
                    and C.clause_kind(body) == 'turn'
                derive_diff += not ok
            elif row != s:
                label_diff += 1
    res = dict(rendered=a.rendered, rendered_sha256=hashlib.sha256(open(a.rendered, 'rb').read()).hexdigest(),
               validator_sha256=vsha, rows=n, validator_failed=failed, per_rule=dict(rules), examples=examples,
               first100_away_rows=first100, first100_away_failed=first100_failed,
               label_differences_vs_source=label_diff, away_rederivation_failures=derive_diff)
    with open(a.out, 'w') as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print(json.dumps(res, sort_keys=True))
    return int(bool(failed or label_diff or derive_diff))


if __name__ == '__main__':
    sys.exit(main())
