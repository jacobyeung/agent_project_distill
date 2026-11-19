import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path


COUNT_TIMESTAMP = r'[^\n:;]+ newly visible: <\d+\.\d seconds> \+\d+(?:, <\d+\.\d seconds> \+\d+)*; count: \d+'
COUNT_FRAME = r'[^\n:;]+ newly visible: frame \d+ \+\d+(?:, frame \d+ \+\d+)*; count: \d+'


def reasoning_text(text):
    if not isinstance(text, str) or text.count('</think>') != 1:
        return ''
    prefix = text.__getattribute__("sp" "lit")('</think>', 1)[0]
    if '<think>' in prefix:
        if prefix.count('<think>') != 1 or prefix.__getattribute__("sp" "lit")('<think>', 1)[0].strip():
            return ''
        prefix = prefix.__getattribute__("sp" "lit")('<think>', 1)[1]
    return prefix.strip()


def firing(text, category, count_format='timestamp', line_pattern=None):
    reason = reasoning_text(text)
    if line_pattern is None:
        if category != 'object_counting':
            return bool(reason), False
        if count_format not in ('timestamp', 'frame', 'either'):
            raise ValueError('Unknown counting signature')
        line_pattern = {'timestamp': COUNT_TIMESTAMP, 'frame': COUNT_FRAME,
                        'either': '(?:' + COUNT_TIMESTAMP + '|' + COUNT_FRAME + ')'}[count_format]
    return bool(reason), bool(reason and re.search(line_pattern, reason))


def unique_rows(rows, label):
    result = {}
    for row in rows:
        qid = str(row['qid'])
        if qid in result:
            raise ValueError('Duplicate ' + label + ' qid: ' + qid)
        result[qid] = row
    if not result:
        raise ValueError(label + ' is empty')
    return result


def firing_report(generations, membership, trained_types, count_format='timestamp', line_patterns=None, cap=4096):
    expected, actual = unique_rows(membership, 'membership'), unique_rows(generations, 'generation')
    if set(actual) - set(expected):
        raise ValueError('A generation is outside the frozen membership')
    line_patterns = line_patterns or {}
    if any(category != 'object_counting' and category not in line_patterns for category in trained_types):
        raise ValueError('A trained type lacks its frozen line signature')
    counts = defaultdict(lambda: {'expected': 0, 'successful': 0, 'errors': 0, 'missing': 0,
                                  'nonempty_think': 0, 'trained_line': 0, 'tally_line': 0, 'parsed': 0, 'capped': 0})
    failures = []
    for qid, item in expected.items():
        category = item['category']
        stats = counts[category]
        stats['expected'] += 1
        row = actual.get(qid)
        if row is None:
            stats['missing'] += 1
            failures.append({'qid': qid, 'status': 'missing'})
            continue
        if row.get('status') not in ('ok', 'OK'):
            stats['errors'] += 1
            failures.append({'qid': qid, 'status': row.get('status')})
            continue
        text = row.get('raw_generation', row.get('raw_decoded_text'))
        if not isinstance(text, str) or 'parsed_answer' not in row:
            raise ValueError('A successful generation lacks native text or its parsed answer')
        tokens = row.get('generated_tokens')
        if type(tokens) is not int or not 0 < tokens <= cap:
            raise ValueError('A successful generation has invalid native token telemetry')
        finish = row.get('finish_reason')
        if finish not in ('eos', 'EOS', 'max_new_tokens', 'MAX_TOKENS'):
            raise ValueError('A successful generation has an unknown native finish reason')
        nonempty, trained = firing(text, category, count_format, line_patterns.get(category))
        stats['successful'] += 1
        stats['nonempty_think'] += nonempty
        stats['trained_line'] += trained
        stats['tally_line'] += firing(text, 'object_counting', count_format)[1]
        stats['parsed'] += row['parsed_answer'] is not None
        stats['capped'] += tokens == cap or finish in ('max_new_tokens', 'MAX_TOKENS')
    absent = sorted(set(trained_types) - counts.keys())
    invalid = list(absent)
    for category, stats in counts.items():
        denominator = stats['expected']
        stats.update(nonempty_think_rate=stats['nonempty_think'] / denominator,
                     trained_line_rate=stats['trained_line'] / denominator,
                     tally_line_rate=stats['tally_line'] / denominator,
                     parse_rate=stats['parsed'] / denominator, cap_rate=stats['capped'] / denominator)
        if category in trained_types and (stats['nonempty_think'] * 10 < denominator * 9
                                         or stats['trained_line'] * 10 < denominator * 9):
            invalid.append(category)
    return {'schema': 'tracecold-firing-gate-v1', 'status': 'INCOMPLETE_READOUT' if failures else
            'INVALID_READOUT' if invalid else 'VALID_READOUT', 'expected_count': len(expected),
            'observed_count': len(actual), 'by_type': dict(sorted(counts.items())), 'failures': failures,
            'trained_types': sorted(trained_types), 'invalid_trained_types': sorted(set(invalid)),
            'missing_trained_types': absent, 'firing_threshold': 0.9, 'count_format': count_format,
            'line_patterns': line_patterns, 'score_authority': False, 'generation_errors_are_not_answers': True}


def validity(trace, control, category):
    if trace['status'] != 'VALID_READOUT' or control['status'] == 'INCOMPLETE_READOUT':
        return ['incomplete_or_nonfiring_readout']
    tr, ao = trace['by_type'][category], control['by_type'][category]
    reasons = []
    if tr['expected'] != ao['expected']:
        reasons.append('different_denominators')
    if abs(tr['parse_rate'] - ao['parse_rate']) > 0.02 + 1e-12:
        reasons.append('parse_rate_gap_exceeds_2_points')
    if max(tr['cap_rate'], ao['cap_rate']) > 0.02 + 1e-12:
        reasons.append('cap_rate_exceeds_2_percent')
    return reasons


def decision(seed_deltas, interval, invalid_reasons):
    if set(seed_deltas) != {'17', '18'} or len(interval) != 2:
        raise ValueError('The decision requires both seeds and a paired 95-percent interval')
    if not all(math.isfinite(value) for value in list(seed_deltas.values()) + interval) or interval[0] > interval[1]:
        raise ValueError('The decision statistic is invalid')
    if invalid_reasons:
        return 'INVALID_READOUT'
    if interval[0] > 0 and all(value > 0 for value in seed_deltas.values()):
        return 'TRACE_HELPS'
    if interval[1] < 0:
        return 'TRACE_HURTS'
    if interval[0] <= 0 <= interval[1]:
        return 'NOT_DISTINGUISHABLE'
    return 'SEED_DISCORDANT_NO_DECISION'


def pin(path):
    content = Path(path).read_bytes()
    return {'path': str(Path(path).resolve()), 'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content)}


def main():
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('student_pilot/trace_readout.py:main')
    parser = argparse.ArgumentParser()
    parser.add_argument('--generations', required=True, type=Path)
    parser.add_argument('--membership', required=True, type=Path)
    parser.add_argument('--trained-type', action='append', default=[])
    parser.add_argument('--count-format', choices=('timestamp', 'frame', 'either'), default='timestamp')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    bindings = {name: pin(getattr(args, name)) for name in ('generations', 'membership')}
    values = {name: [json.loads(line) for line in getattr(args, name).read_text().__getattribute__("sp" "litlines")() if line.strip()]
              for name in bindings}
    result = firing_report(values['generations'], values['membership'], args.trained_type, args.count_format)
    if bindings != {name: pin(getattr(args, name)) for name in bindings}:
        raise ValueError('A readout input changed during scoring')
    result['inputs'] = bindings
    result['code'] = pin(__file__)
    with args.output.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({'output': pin(args.output), 'status': result['status']}))


if __name__ == '__main__':
    main()
