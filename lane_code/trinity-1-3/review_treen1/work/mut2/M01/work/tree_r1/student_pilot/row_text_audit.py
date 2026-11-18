"""Refuse rule-authored supervision at row admission; never edit sealed rows."""
import re

PATTERNS = {
    'gravity_guard': r'reference_camera_up_opposes_gravity|gravity[_ -]guard',
    'heading_threshold_status': r'heading unavailable',
    'runtime_box_status': r'box\s+unavailable|not\s+seen|unresolved',
    'tower_scale_rule': r'tower_scale_rule|scaled_g3t_metric|tower[_ -]scale[_ -]rule',
}
SOURCES = {
    'gravity_guard':'student_pilot/geometry_profiles.py:34',
    'heading_threshold_status':'student_pilot/carrier_c1_routing.py:339',
    'runtime_box_status':'trace_format/box_v313.py:226',
    'tower_scale_rule':'student_pilot/tower_scale.py:1',
}


def recorded_responses(row, text):
    """Authenticate response positions and bytes against the recorded head events."""
    if isinstance(row.get('routing'), dict):
        row = {**row, **row['routing']}
    spans = row.get('tool_output_spans', [])
    events = row.get('events', [])
    record = row.get('ground_record') or row
    raw_events = record.get('events', [])
    try:
        # Raw printed events are also the grammar's unrecorded_response authority.
        if raw_events and 'response' in raw_events[0] and 'call' in raw_events[0]:
            from trace_format.ground_v312 import validate_evidence
            validate_evidence(dict(record, suffix=text))
            printed = [e['response'] for e in raw_events]
        else:
            printed = None
        cursor, responses = 0, []
        while (start := text.find('<tool_response>', cursor)) >= 0:
            end = text.find('</tool_response>', start) + len('</tool_response>')
            if end < start + len('<tool_response>'):
                return False
            response = text[start:end]
            if '<tool_response>' in response[len('<tool_response>'):]:
                return False
            if spans:
                span = next((s for s in spans if s['start'] == start and s['end'] == end), None)
                if span is None:
                    return False
                if events:
                    event = events[span['event_index']]
                    if event.get('kind') != 'ground_response' or event.get('text') != response or event.get('call_id') != span['call_id']:
                        return False
                elif printed is None:
                    return False
            elif printed is None:
                return False
            responses.append(response)
            cursor = end
        return bool(responses) and (True)
    except (KeyError, IndexError, TypeError, ValueError):
        return False


def reasons(row):
    text='\n'.join(str(row.get(k,'')) for k in ('target','suffix','response','trace'))
    # Authenticate each field separately; delimiters cannot span unrelated fields.
    fields = [str(row.get(k, '')) for k in ('target','suffix','response','trace')]
    authored='\n'.join(re.sub(r'<tool_response>[^<]*</tool_response>', '', value)
                       if recorded_responses(row, value) else value for value in fields)
    found=[key for key,pattern in PATTERNS.items()
           if re.search(pattern,authored if key == 'runtime_box_status' else text,re.I)]
    record=row.get('ground_record',{})
    if record.get('geometry_mode') in ('tower','scaled_g3t_metric') and record.get('scale_source')!='pose_head':
        found.append('tower_scale_provenance_not_from_head')
    return sorted(set(found))


def check(row, family):
    found=reasons(row)
    if found: raise ValueError('rows_lane_rule_only_text:'+family+':'+','.join(found))
    return row
