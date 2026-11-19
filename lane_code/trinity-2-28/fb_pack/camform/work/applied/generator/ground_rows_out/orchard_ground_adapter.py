"""Grounding forms for Orchard's existing c1_row/build_routing_stream reader.

Call install(student_pilot.carrier_c1_routing) before building a grounding set.
The adapter preserves suffix bytes and masks complete forced tool responses.
It does not implement inference from the model's own geometry heads.
"""
import copy
import re

FORMS = {'3.14': 'spec-v3.14-ground-v1', '3.13': 'spec-v3.13-ground-v1', '3.12.2': 'spec-v3.12-ground-v1'}


def is_ground(events):
    return bool(events and events[0].get('kind') == 'ground_trace_start')


def render_ground(events, answer):
    if not is_ground(events):
        raise ValueError('missing grounding event header')
    text, spans, segments, cursor = [], [], [], 0
    for i, e in enumerate(events[1:], 1):
        kind = e['kind']
        value = e.get('text', e.get('token'))
        if kind not in ('canonical_text', 'ground_call', 'ground_response') or not isinstance(value, str):
            raise ValueError('invalid grounding event')
        start = cursor
        cursor += len(value)
        text.append(value)
        if kind == 'ground_response':
            if not value.startswith('<tool_response>') or not value.endswith('</tool_response>'):
                raise ValueError('unwrapped grounding response')
            spans.append(dict(start=start, end=cursor, call_id=e['call_id'], event_index=i))
            segments.append((start, cursor, 'tool'))
        elif kind == 'ground_call':
            m = re.match(r'<(?:ground|gap|angle|dist|turn)', value)
            if not m:
                raise ValueError('unknown grounding call')
            segments.extend([(start, start+m.end(), 'opener' if value.startswith('<ground') else 'calculator'),
                             (start+m.end(), cursor, 'arguments')])
        else:
            segments.append((start, cursor, 'answer' if '<answer>' in value else 'prose'))
    target = ''.join(text)
    if not target.startswith('<think>\n') or not target.endswith('\n</think>\n<answer>'+str(answer)+'</answer>'):
        raise ValueError('grounding final answer mismatch')
    return target, spans, segments


def pack(row, provenance):
    from derivgen.ground_v312 import validate_evidence
    validate_evidence(row)
    events = [dict(kind='ground_trace_start', trace_revision=row['spec_version'])]
    cursor = 0
    for i, e in enumerate(row['events']):
        block = e['call']+'\n'+e['response']
        start = row['suffix'].index(block, cursor)
        if start > cursor:
            events.append(dict(kind='canonical_text', text=row['suffix'][cursor:start]))
        events.append(dict(kind='ground_call', token=e['call']+'\n', call_id=f'ground-{i}'))
        events.append(dict(kind='ground_response', text=e['response'], call_id=f'ground-{i}'))
        cursor = start+len(block)
    events.append(dict(kind='canonical_text', text=row['suffix'][cursor:]))
    target, spans, _ = render_ground(events, row['answer'])
    if target != row['suffix']:
        raise ValueError('packing changed suffix')
    return dict(schema='derivgen-row-v2', form=FORMS[row['spec_version']],
                trace_revision=row['spec_version'], qid=row['qid'], source_qid=row['qid'],
                candidate_id=row['candidate_id'], question_type=row['type'], question=row['question'],
                options=row['options'], answer=row['answer'], gt_answer=row['gt_answer'],
                target=target, events=events, tool_output_spans=spans,
                provenance=copy.deepcopy(provenance), category='route', head_layout='ground_aggregate',
                infrastructure_only=False, training_admitted=False, gt_accepted=True,
                ground_record={k: v for k, v in row.items() if k != 'suffix'})


def validate(row):
    from derivgen.ground_v312 import validate_evidence, option_map
    if row.get('schema') != 'derivgen-row-v2' or row.get('form') != FORMS.get(row.get('trace_revision')):
        raise ValueError('invalid grounding schema/form/revision')
    if row.get('infrastructure_only') is not False or row.get('gt_accepted') is not True:
        raise ValueError('unadmitted grounding record')
    record = dict(row['ground_record'], suffix=row['target'])
    for key in ('qid', 'answer', 'gt_answer', 'question', 'options', 'candidate_id'):
        if row[key] != record[key]:
            raise ValueError('packed grounding field mismatch: '+key)
    if row['question_type'] != record['type'] or record['spec_version'] != row['trace_revision']:
        raise ValueError('packed grounding type mismatch')
    if record.get('not_seen') or record.get('gt_agrees') is not True or record.get('training_admitted') is not False:
        raise ValueError('grounding membership flags differ')
    validate_evidence(record)
    target, spans, _ = render_ground(row['events'], row['answer'])
    if target != row['target'] or spans != row['tool_output_spans']:
        raise ValueError('packed grounding target/spans mismatch')
    # Match every forced span to its audited native event, including delimiters.
    if [target[s['start']:s['end']] for s in spans] != [e['response'] for e in record['events']]:
        raise ValueError('packed response audit mismatch')
    if record['type'] == 'object_abs_distance':
        from derivgen.ground_v313_distance import agrees
        if not agrees(record['answer'], record['gt_answer']):
            raise ValueError('absolute label mismatch')
    elif record['type'] == 'absolute_direction_object':
        from derivgen.gaps_v314 import circular_error
        if circular_error(record['answer'], record['gt_answer']) > 15:
            raise ValueError('rotation label mismatch')
    elif record['type'] == 'room_size_estimation':
        from derivgen.room_rows_v314 import validate_computation
        validate_computation(record)
    elif (str(record['answer']) != str(record['gt_answer']) or
          (record['options'] and option_map(record['options'])[record['answer']] != record['answer_content'])):
        raise ValueError('categorical label mismatch')
    return target, spans


def install(module):
    """Extend the actual Orchard reader; leave all existing forms on its native path."""
    if getattr(module, '_ground_rows_installed', False):
        return module
    old_check, old_render, old_row, old_own = module.check_row, module.render_full, module.c1_row, module.rerender

    def check_row(row):
        return validate(row) if row.get('form') in FORMS.values() else old_check(row)

    def render_full(events, answer):
        return render_ground(events, answer) if is_ground(events) else old_render(events, answer)

    def c1_row(raw, rgb, path_map=None):
        row = old_row(raw, rgb, path_map)
        if raw.get('form') in FORMS.values():
            row['routing']['ground_record'] = raw['ground_record']
            row['routing']['candidate_id'] = raw['candidate_id']
            row['routing']['training_admitted'] = raw['training_admitted']
        return row

    def rerender(row, geometry):
        if row.get('routing', {}).get('form') in FORMS.values():
            raise ValueError('grounding own-head execution requires the ground_backend integration')
        return old_own(row, geometry)

    module.check_row, module.render_full, module.c1_row, module.rerender = check_row, render_full, c1_row, rerender
    module.OPENERS = tuple(dict.fromkeys((*module.OPENERS, '<ground', '<gap')))
    module._ground_rows_installed = True
    return module
