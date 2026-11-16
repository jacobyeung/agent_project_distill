"""Dev-only summaries around the unchanged kit admission and item scorers."""
from collections import Counter, defaultdict
from contextlib import contextmanager
import importlib
import re

DEV_ONLY = frozenset(('relative_count', 'relative_size_object'))
VERSION = 'devs1-summary-v1'


def option_parse_failed(row, official):
    """Use the kit's extracted first token; accept only a displayed option letter."""
    pred = official.official_fuzzy_matching(row.get('response_text', '')).upper()
    letters = set()
    for i, value in enumerate(row.get('options', [])):
        match = re.match(r'^\s*([A-Za-z])[.)]\s*', str(value))
        letters.add(match[1].upper() if match else chr(65 + i))
    return pred not in letters


def dev_summary(rows, tasks, parity, original, official):
    if not tasks or any(t['benchmark'] != 'devrows' for t in tasks):
        return original(rows, tasks, parity)
    allowed = official.OFFICIAL_MCA_TYPES | official.OFFICIAL_NA_TYPES | DEV_ONLY
    if any(t['question_type'] not in allowed for t in tasks):
        raise ValueError('Unknown dev question type')
    completed = [r for r in rows if r.get('status') == 'complete']
    official_rows = [r for r in completed if r['question_type'] not in DEV_ONLY]
    # Rescore official types with the unchanged official function, including its MRA.
    checked = official.score_official_vsibench(official_rows, expected_count=0)
    scores = {r['key']: r['official_score'] for r in checked['scored_records']}
    for row in completed:
        if row['question_type'] in DEV_ONLY:
            pred = official.official_fuzzy_matching(row['response_text'])
            scores[row['key']] = (0.0 if option_parse_failed(row, official) else
                                 official.official_exact_match(pred, str(row['ground_truth']).strip()))
        if scores[row['key']] != row['score']:
            raise ValueError('Dev summary differs from admitted item score: ' + row['key'])
    by_type = defaultdict(list)
    for row in completed:
        by_type[row['question_type']].append(scores[row['key']])
    return dict(expected=len(tasks), completed=len(completed), errors=len(rows)-len(completed),
                cap_hits=sum(bool(r.get('hit_token_cap')) for r in rows),
                parse_failures=sum(bool(r.get('parse_failed', True)) for r in rows),
                unanswered=sum(not r.get('response_text', '').strip() for r in completed),
                dev_option_parse_failures=sum(option_parse_failed(r, official) for r in completed
                                              if r['question_type'] in DEV_ONLY),
                empty_thinks=sum(bool(r.get('empty_think')) for r in rows),
                generated_tokens=sum(r.get('output_tokens', 0) for r in rows),
                parity_pass=parity,
                numbers_status='eligible' if parity and len(completed)==len(tasks) else 'do not count',
                per_type={k:dict(count=len(v), score=sum(v)/len(v)) for k,v in sorted(by_type.items())},
                overall_score=sum(scores.values())/len(completed) if completed else None,
                aggregation='Item-weighted dev mean; not the official VSI benchmark overall',
                scorer=VERSION, official_subset_metric={k:v for k,v in checked.items() if k!='scored_records'})


@contextmanager
def installed():
    """Scope the sole override to summaries; restore both import aliases afterward."""
    scoring = importlib.import_module('scoring')
    merge = importlib.import_module('merge')
    original, merge_original = scoring.benchmark_summary, merge.benchmark_summary
    def summary(rows, tasks, parity):
        return dev_summary(rows, tasks, parity, original, scoring.official)
    scoring.benchmark_summary = merge.benchmark_summary = summary
    try:
        yield
    finally:
        scoring.benchmark_summary, merge.benchmark_summary = original, merge_original
