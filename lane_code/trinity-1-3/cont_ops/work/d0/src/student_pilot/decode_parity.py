"""Persist decode evidence and separate semantic failures from suffix arithmetic."""
import json
from pathlib import Path
import re

from .carrier_c1_canary import answer_of


def parsed_answer(record):
    # A tool response is never a final answer, including when decoding stops there.
    tail = record['text'].rsplit('</tool_response>', 1)[-1]
    tail = re.sub(r'<\|[^|]*\|>|</s>', '', tail)
    return answer_of(tail)


def call_parts(record):
    parts = []
    for call in record['calls']:
        match = re.fullmatch(r'<([\w]+)(.*?)>', call['call'], re.S)
        parts.append((match[1], match[2]) if match else (None, call['call']))
    return parts


def compare(single, batched, ids=None):
    results = []
    for row in range(max(len(single), len(batched))):
        item = dict(row=row, id=ids[row] if ids is not None and row < len(ids) else row)
        if row >= min(len(single), len(batched)):
            results.append(dict(item, missing_record=True, strict_equal=False, semantic_equal=False,
                                acceptance_equal=False))
            continue
        a, b = single[row], batched[row]
        x, y = a['tokens'], b['tokens']
        index = next((i for i in range(max(len(x), len(y)))
                      if (x[i] if i < len(x) else None) != (y[i] if i < len(y) else None)), None)
        ca, cb = call_parts(a), call_parts(b)
        names_equal = [c[0] for c in ca] == [c[0] for c in cb]
        arguments_equal = [c[1] for c in ca] == [c[1] for c in cb]
        responses_equal = [c['response'] for c in a['calls']] == [c['response'] for c in b['calls']]
        aa, ab = parsed_answer(a), parsed_answer(b)
        answer_equal = aa is not None and aa == ab
        finish_equal = a['finish'] == b['finish']
        clean = not a.get('errors', 0) and not b.get('errors', 0) and a['finish'] == b['finish'] == 'eos'
        # at_token is the consumed call length; forced_tokens includes its response.
        boundaries = [max((c['at_token'] + c['forced_tokens'] for c in r['calls']), default=0) for r in (a, b)]
        suffix_only = index is None or index >= max(boundaries)
        strict = all(a[k] == b[k] for k in ('tokens', 'text', 'calls', 'finish'))
        semantic = names_equal and arguments_equal and responses_equal and answer_equal and clean
        results.append(dict(item, missing_record=False, tokens_equal=index is None,
            first_differing_token=index,
            token_ids=[v[index] if index is not None and index < len(v) else None for v in (x, y)],
            token_mismatches=sum((x[i] if i < len(x) else None) != (y[i] if i < len(y) else None)
                                 for i in range(max(len(x), len(y)))), token_positions=max(len(x), len(y)),
            text_equal=a['text'] == b['text'], calls_equal=a['calls'] == b['calls'],
            tool_names_equal=names_equal, tool_arguments_equal=arguments_equal,
            responses_equal=responses_equal, parsed_answers=[aa, ab], parsed_answers_equal=answer_equal,
            finish_equal=finish_equal, last_response_end=boundaries, divergence_after_last_response=suffix_only,
            strict_equal=strict, full_records_equal=a == b, semantic_equal=semantic,
            acceptance_equal=semantic and suffix_only))
    return results


def pooled(rows):
    tokens = sum(r.get('token_positions', 0) for r in rows)
    different = sum(r.get('token_mismatches', 0) for r in rows)
    return dict(rows=len(rows), strict_failures=sum(not r['strict_equal'] for r in rows),
        full_record_failures=sum(not r.get('full_records_equal', False) for r in rows),
        acceptance_failures=sum(not r['acceptance_equal'] for r in rows),
        semantic_failures=sum(not r['semantic_equal'] for r in rows),
        pre_response_divergences=sum(not r.get('divergence_after_last_response', False) for r in rows),
        call_name_failures=sum(not r.get('tool_names_equal', False) for r in rows),
        call_argument_failures=sum(not r.get('tool_arguments_equal', False) for r in rows),
        response_failures=sum(not r.get('responses_equal', False) for r in rows),
        parsed_answer_failures=sum(not r.get('parsed_answers_equal', False) for r in rows),
        token_mismatches=different, token_positions=tokens,
        token_mismatch_fraction=different / tokens if tokens else 0.)


def save_comparison(out, single, batched, *, ids=None, strict=True, full_records=False, labels=None):
    """Write both arms and diagnostics even for missing rows; callers assert later."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, records in [('b1', single), ('b4', batched)]:
        (out / (name + '.json')).write_text(json.dumps(records) + '\n')
    rows = compare(single, batched, ids)
    summary = pooled(rows)
    failures = (sum(not r.get('full_records_equal', False) for r in rows) if full_records else
                summary['strict_failures'] if strict else summary['acceptance_failures'])
    report = dict(status='PASS' if rows and not failures else 'FAIL', comparisons=rows,
                  pooled=summary, strict_verdict='FAIL' if summary['full_record_failures' if full_records else 'strict_failures'] else 'PASS',
                  gate='full-record' if full_records else 'strict' if strict else 'call-answer-and-prefix',
                  labels=labels or ['B1', 'B4'])
    (out / 'COMPARISON.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def noise_report(single, repeat, batched, ids=None):
    floor = pooled(compare(single, repeat, ids))
    observed = pooled(compare(single, batched, ids))
    return dict(repeatability=floor, batch_comparison=observed,
        strict_verdict='FAIL' if observed['strict_failures'] else 'PASS',
        bounds=dict(semantic_failures=0, pre_response_divergences=0,
                    post_response_token_mismatch_fraction=None),
        bf16_batch_arithmetic_floor_measured=False,
        limitation='B1 repeated on one card measures repeatability, not cross-shape bf16 arithmetic. '
                   'Token counts are pooled and descriptive; no numerical batch-noise bound is inferred. '
                   'Every row must retain identical calls, arguments, responses, parsed answer and EOS; '
                   'any token divergence must follow the last complete response.')
