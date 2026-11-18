"""Refuse rule-authored supervision at row admission; never edit sealed rows."""
import re
import unicodedata

PATTERNS = {
    'gravity_guard': r'reference_camera_up_opposes_gravity|gravity[_ -]guard',
    'heading_threshold_status': r'heading\s*unavailable',
    'runtime_box_status': r'box\s*unavailable|not\s*seen|unresolved',
    'tower_scale_rule': r'tower_scale_rule|scaled_g3t_metric|tower[_ -]scale[_ -]rule',
}


def normalized_text(text):
    # Unicode Default_Ignorable_Code_Point includes non-Cf combining marks and fillers.
    ranges = ((0x115F,0x1160),(0x17B4,0x17B5),(0x180B,0x180F),(0x200B,0x200F),
              (0x202A,0x202E),(0x2060,0x206F),(0xFE00,0xFE0F),(0xFFF0,0xFFF8),
              (0x1BCA0,0x1BCA3),(0x1D173,0x1D17A),(0xE0000,0xE0FFF))
    text = unicodedata.normalize('NFKD', text).translate({0x435:'e',0x415:'E'})
    stripped = ''.join(c for c in text if unicodedata.category(c) not in ('Cf','Mn','Me')
        and ord(c) not in (0xAD,0x34F,0x61C,0x3164,0xFEFF,0xFFA0)
        and not any(lo <= ord(c) <= hi for lo,hi in ranges))
    return ' '.join(stripped.split())
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
        return bool(responses) and (printed is None or responses == printed)
    except (KeyError, IndexError, TypeError, ValueError):
        return False


def reasons(row):
    text='\n'.join(str(row.get(k,'')) for k in ('target','suffix','response','trace'))
    # Authenticate each field separately; delimiters cannot span unrelated fields.
    fields = [str(row.get(k, '')) for k in ('target','suffix','response','trace')]
    authored='\n'.join(re.sub(r'<tool_response>[^<]*</tool_response>', '', value)
                       if recorded_responses(row, value) else value for value in fields)
    found=[key for key,pattern in PATTERNS.items()
           if re.search(pattern,normalized_text(authored if key == 'runtime_box_status' else text),re.I)]
    record=row.get('ground_record',{})
    if record.get('geometry_mode') in ('tower','scaled_g3t_metric') and record.get('scale_source')!='pose_head':
        found.append('tower_scale_provenance_not_from_head')
    return sorted(set(found))


def check(row, family):
    # The reader owns its normalization and patterns; it never calls the gate oracle.
    def normalize(value):
        value = unicodedata.normalize('NFKD',value).replace('е','e').replace('Е','E')
        value = ''.join(c for c in value if not unicodedata.combining(c))
        value = re.sub('[\u00ad\u034f\u061c\u115f-\u1160\u17b4-\u17b5\u180b-\u180f'
                       '\u200b-\u200f\u202a-\u202e\u2060-\u206f\u3164\ufe00-\ufe0f'
                       '\ufeff\uffa0\ufff0-\ufff8\U0001bca0-\U0001bca3'
                       '\U0001d173-\U0001d17a\U000e0000-\U000e0fff]', '', value)
        return re.sub(r'\s+', ' ', ''.join(c for c in value if unicodedata.category(c) != 'Cf'))
    fields = [str(row.get(k,'')) for k in ('target','suffix','response','trace')]
    text = normalize('\n'.join(fields))
    authored = normalize('\n'.join(re.sub(r'<tool_response>[^<>]*</tool_response>', '', s)
        if recorded_responses(row,s) else s for s in fields))
    found=[]
    for name,pattern,content in (
        ('gravity_guard',r'reference_camera_up_opposes_gravity|gravity[_ -]guard',text),
        ('heading_threshold_status',r'heading *unavailable',text),
        ('runtime_box_status',r'box *unavailable|not *seen|unresolved',authored),
        ('tower_scale_rule',r'tower_scale_rule|scaled_g3t_metric|tower[_ -]scale[_ -]rule',text)):
        if re.search(pattern,content,re.I):found.append(name)
    record=row.get('ground_record',{})
    if record.get('geometry_mode') in ('tower','scaled_g3t_metric') and record.get('scale_source')!='pose_head':
        found.append('tower_scale_provenance_not_from_head')
    if found: raise ValueError('rows_lane_rule_only_text:'+family+':'+','.join(found))
    return row
