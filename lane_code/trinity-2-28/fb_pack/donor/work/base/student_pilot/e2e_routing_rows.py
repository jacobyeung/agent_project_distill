"""Import generated v3.12 text into the C1 event/span training contract."""
import copy
import re

from . import carrier_c1_routing as routing


REVISIONS = ('3.12', '3.12.1', '3.12.2', '3.13', '3.14')


def adapt_generated(source, student_input, *, dataset, scene):
    """Preserve source admission and text; adapt only the native closing delimiter."""
    if source.get('spec_version') not in REVISIONS:
        raise ValueError('Expected a supported generated trace revision')
    text = source['suffix']
    if source['spec_version'] == '3.12.2' and re.search(r'\(best \d+, p [^)]+\)', text):
        raise ValueError('v3.12.2 row carries the retired probability field')
    if not text.startswith(routing.THINK):
        raise ValueError('Ground suffix must start with the native think opener')
    answer = '<answer>' + str(source['answer']) + '</answer>'
    if text.endswith('\n</think>\n' + answer):
        body = text[len(routing.THINK):-len('\n</think>\n' + answer)]
    elif text.endswith('\n</think>\n\n' + answer):
        body = text[len(routing.THINK):-len('\n</think>\n\n' + answer)]
    else:
        raise ValueError('Ground suffix must end with its supplied answer envelope')
    events, cursor = [], 0
    for number, event in enumerate(source['events'], 1):
        call, response = event['call'], event['response']
        start = body.find(call, cursor)
        if start < cursor or not response.startswith('<tool_response>') or not response.endswith('</tool_response>'):
            raise ValueError('Ground event differs from its suffix')
        if start > cursor:
            events.append(dict(kind='canonical_text', text=body[cursor:start]))
        call_id = 'e2e' + str(number)
        name = call[1:].split(' ', 1)[0]
        head = name in ('ground', 'gap')
        events.append(dict(kind='tool_call' if head else 'calculator_call', call_id=call_id,
                           **(dict(token=call, name=name) if head else dict(command=call))))
        at = start + len(call)
        response_at = body.find(response, at)
        if response_at < at or body[at:response_at] != '\n':
            raise ValueError('Ground call and response must occupy adjacent lines')
        events.append(dict(kind='canonical_text', text='\n'))
        inside = response[len('<tool_response>'):-len('</tool_response>')]
        events.append(dict(kind='tool_response' if head else 'calculator_response', call_id=call_id,
                           **(dict(name=name, text=inside) if head else dict(response={'text': inside}))))
        cursor = response_at + len(response)
    if cursor < len(body):
        events.append(dict(kind='canonical_text', text=body[cursor:]))
    target, spans, _ = routing.render_full(events, answer)
    if target != routing.THINK + body + '\n</think>\n\n' + answer:
        raise ValueError('Native event import changed ground-row text')
    admitted = source.get('training_admitted') is True and source.get('diagnostic_only') is False
    raw = dict(schema='derivgen-row-v2', form='spec-v3.8-calculator-v2',
               trace_revision=source['spec_version'], infrastructure_only=not admitted,
               category='route', qid=source['qid'], question_type=source['type'],
               events=events, answer=answer, answer_value=source['answer'], target=target,
               tool_output_spans=spans)
    return dict(qid=source['qid'], dataset=dataset, scene=scene, category='routing_trace',
                question_type=source['type'], student_input=copy.deepcopy(student_input), target=target,
                routing=raw, ground_build={k: copy.deepcopy(source[k]) for k in (
                    'spec_version', 'diagnostic_only', 'training_admitted', 'geometry_source',
                    'mask_source', 'scene_gt_sha256', 'gt_authority', 'simulated_misses') if k in source})
