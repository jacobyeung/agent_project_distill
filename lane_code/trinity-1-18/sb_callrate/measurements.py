"""Trace metrics: type-specific calls, response agreement, and wording strata."""
import math
import re
from collections import Counter
import numpy as np
from wording import TEMPL

CAPS = ('max_calls', 'max_new_tokens', 'length')
UNITS = {1.: 'm', 100.: 'cm', 1/.3048: 'ft', 1/.0254: 'in', 1000.: 'mm'}


def capped(output):
    return output.get('finish') in CAPS


def call_matches(record, item, sc):
    name, args = sc.signature(record.get('call', ''))
    kind = item['question_type']
    if kind in ('camera_displacement', 'camera_movement_direction'):
        return name == 'move'
    if kind == 'camera_rotation':
        return name == 'turn'
    if kind == 'object_abs_distance':
        return name == 'gap' or (name == 'ground' and args.get('mode') != 'room' and args.get('obj') != 'room')
    if kind == 'room_size_estimation':
        return (name == 'ground' and (args.get('mode') == 'room' or args.get('obj') == 'room')) or record.get('family') == 'room'
    # Additional types require routing evidence from the package or the item itself.
    if record.get('question_type') == kind:
        return True
    from rows.expected_calls import expected_calls, actual_calls
    expected = expected_calls(item['question'], kind)
    routing = item.get('row', item).get('routing', {})
    if routing.get('events') or routing.get('ground_record'):
        expected += actual_calls(routing)
    if expected:
        return name in {sc.signature(c)[0] for c in expected}
    return None


def final_answer(output, sc):
    """Require a final segment; reasoning-only text is never an answer."""
    if output.get('finish') == 'max_calls':
        return ''
    text = output.get('text', '')
    if re.search(r'<answer>.*?</answer>', text, re.S):
        return sc.answer_text(output)
    if '</think>' in text:
        return sc.answer_text(output)
    # The supplied prompts pre-open thinking, so a missing closer is unfinished.
    return ''


def unit(item, sc):
    try:
        return UNITS[sc.unit_factor(item['question'])]
    except ValueError:
        return 'N/A'


def question_template(item, sc):
    text = item['question']
    names = set()
    from rows.expected_calls import expected_calls
    try:
        for call in expected_calls(text, item['question_type']):
            _, args = sc.signature(call)
            names.update(args[k] for k in ('obj', 'a', 'b') if k in args)
    except ValueError:
        pass
    routing = item.get('row', item).get('routing', {})
    from rows.expected_calls import actual_calls
    if routing.get('events') or routing.get('ground_record'):
        for call in actual_calls(routing):
            _, args = sc.signature(call)
            names.update(args[k] for k in ('obj', 'a', 'b') if k in args)
    for name in sorted(names, key=len, reverse=True):
        text = re.sub(r'(?<!\w)' + re.escape(name) + r'(?!\w)', '<object>', text, flags=re.I)
    text = re.sub(sc.NUM, '<number>', text)
    return ' '.join(text.lower().split())


def wording(output, item, sc):
    text = re.sub(r'<tool_response>.*?</tool_response>', '', output.get('text', ''), flags=re.S)
    tags = sorted(k for k, rx in TEMPL.items() if rx.search(text)) if item['question_type'] == 'object_abs_distance' else []
    return tags or ['template: ' + question_template(item, sc)]


def decision(output, item, sc):
    """Use the package's fixed math, never infer an operation from the answer."""
    if item['question_type'] == 'room_size_estimation':
        from trace_format.room_v314 import parse_response
        values = []
        for record in sc.records(output) or []:
            if call_matches(record, item, sc) and record.get('served') is not False and record.get('response'):
                try:
                    values.append(parse_response(record['response'])['area_m2'])
                except ValueError:
                    pass
        return values[-1] * sc.unit_factor(item['question'])**2 if values else None
    return sc.program_decision(output, item)


def follows(answer, expected, item, sc):
    if isinstance(expected, str):
        return sc.answer_equals(answer, expected)
    # Normalize explicit answer units to the requested unit. Bare values already
    # use that unit. Scorer.answer_equals supplies its 5% tolerance (exact at zero).
    match = re.fullmatch(r'\s*(' + sc.NUM + r')\s*(.*?)\s*', answer)
    if not match:
        return False
    value, suffix = float(match[1]), match[2].strip()
    if not math.isfinite(value):
        return False
    kind = item['question_type']
    if suffix and kind in ('camera_displacement', 'object_abs_distance', 'room_size_estimation'):
        power = 2 if kind == 'room_size_estimation' else 1
        normalized = re.sub(r'\^?2|²|square\s+', '', suffix)
        if normalized.lower() == 'in':
            normalized = 'inches'
        try:
            factor = sc.unit_factor(normalized)
        except ValueError:
            return False
        value *= (sc.unit_factor(item['question']) / factor)**power
    elif suffix and kind == 'camera_rotation' and suffix.lower() not in ('deg', 'degree', 'degrees', '°'):
        return False
    return sc.answer_equals(str(value), expected)


def parsed_answer(answer, item, sc):
    """Use the scorer's numeric parser and require a listed option for choices."""
    from evalpath import official
    meta = sc.metadata(item)
    kind = meta.get('answer_type', 'multiple_choice' if item['question_type'] == 'camera_movement_direction' else 'numeric')
    value = official.official_fuzzy_matching(answer)
    if kind == 'multiple_choice':
        options = meta.get('options') or []
        labels = [re.match(r'([A-Z])[.)]', opt.strip()) for opt in options]
        allowed = {m[1].lower() if m else chr(97+i) for i,m in enumerate(labels)}
        return value if value.lower() in allowed else None
    return official.official_to_float(value)


def response_category(answer, expected, item, sc):
    if expected is None:
        return None
    # Correct conversion takes precedence at zero, where copying is indistinguishable.
    if follows(answer, expected, item, sc):
        return 'follow_converted'
    if item['question_type'] in ('camera_displacement', 'object_abs_distance', 'room_size_estimation'):
        factor = sc.unit_factor(item['question'])
        power = 2 if item['question_type'] == 'room_size_estimation' else 1
        if factor != 1 and follows(answer, expected / factor**power, item, sc):
            return 'copied_unconverted'
    return 'other'


def measure(row, item, sc):
    output = row['output']
    records = sc.records(output) or []
    matches = [call_matches(r, item, sc) for r in records]
    known = item['question_type'] in ('camera_displacement', 'camera_rotation', 'camera_movement_direction', 'object_abs_distance', 'room_size_estimation')
    if not known:
        from rows.expected_calls import expected_calls
        known = bool(expected_calls(item['question'], item['question_type'])) or bool(item.get('row', item).get('routing'))
    call = any(m is True for m in matches) if known or any(m is not None for m in matches) else None
    answer = final_answer(output, sc)
    selected = [r for r, m in zip(records, matches) if m is True and r.get('served') is not False]
    filtered = {**output, 'calls': {'records': selected}}
    reason = 'no_matching_call' if not call else 'no_parsed_response'
    expected = None
    if call:
        try:
            expected = decision(filtered, item, sc)
        except (ValueError, TypeError, KeyError) as exc:
            reason = 'unparsed_response: ' + str(exc)
    if isinstance(expected, (int, float)) and not math.isfinite(expected):
        expected, reason = None, 'nonfinite_response'
    eligible = expected is not None
    category = response_category(answer, expected, item, sc)
    from evalpath.official import extract_q35_final_answer
    scorer_answer = extract_q35_final_answer(output.get('text', ''), enable_thinking=True)[0] if output.get('finish') != 'max_calls' else ''
    parsed = parsed_answer(scorer_answer, item, sc)
    visible_answer = scorer_answer or answer
    not_seen = bool(visible_answer) and visible_answer.strip().lower().rstrip('.') == 'not seen'
    conversion_required = eligible and item['question_type'] in ('camera_displacement', 'object_abs_distance', 'room_size_estimation') and sc.unit_factor(item['question']) != 1
    score = sc.accuracy(output, item)['task_accuracy']
    if score is not None and not math.isfinite(score):
        raise ValueError('Non-finite score: ' + row['id'])
    return dict(id=row['id'], room=item['room_key'], type=item['question_type'],
                call=None if call is None else int(call), capped=int(capped(output)),
                answer=int(parsed is not None), parsed_answer=parsed,
                not_seen=int(not_seen), non_numeric=int(bool(answer) and parsed is None),
                other_non_numeric=int(bool(answer) and parsed is None and not not_seen),
                score=score, usage=int(category != 'other') if eligible else None,
                usage_category=category,
                follow_converted=int(category == 'follow_converted') if eligible else None,
                copied_unconverted=int(category == 'copied_unconverted') if eligible else None,
                other=int(category == 'other') if eligible else None,
                conversion_failure=int(category == 'copied_unconverted') if conversion_required else None,
                source_read=item.get('_source_read', 'MISSING'),
                usage_reason='eligible' if eligible else reason, response_decision=expected,
                unit=unit(item, sc), wording=wording(output, item, sc),
                call_status='OK' if call is not None else 'MISSING: type routing specification',
                finish=output.get('finish'))


def summarize(rows, expected_ids):
    n = len(rows)
    result = dict(n=n, expected=len(expected_ids), missing_ids=sorted(set(expected_ids)-{r['id'] for r in rows}))
    result['status'] = 'MISSING' if result['missing_ids'] else 'OK'
    for name in ('call', 'capped', 'answer', 'not_seen', 'non_numeric', 'other_non_numeric', 'score', 'usage', 'follow_converted', 'copied_unconverted', 'other', 'conversion_failure'):
        values = [r[name] for r in rows if r[name] is not None]
        key = name + '_rate' if name in ('call', 'capped', 'answer', 'not_seen', 'non_numeric', 'other_non_numeric') else name
        result[key] = (float(np.mean(values)) if name == 'score' else sum(values)/len(values)) if values and (name not in ('call', 'score') or len(values) == n) else None
        result[name + '_n'] = len(values)
        if name != 'score':
            result[name + '_count'] = sum(values)
        result[key + '_status'] = 'OK' if result[key] is not None else 'MISSING'
    result['usage_reasons'] = dict(Counter(r['usage_reason'] for r in rows))
    result['finishes'] = dict(Counter(r['finish'] for r in rows))
    return result
