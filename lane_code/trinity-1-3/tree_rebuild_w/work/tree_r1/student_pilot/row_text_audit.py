"""Refuse rule-authored supervision at row admission; never edit sealed rows."""
import re

PATTERNS = {
    'gravity_guard': r'reference_camera_up_opposes_gravity|gravity[_ -]guard',
    'heading_threshold_status': r'heading unavailable',
    'runtime_box_status': r'box unavailable|not seen|unresolved',
    'tower_scale_rule': r'tower_scale_rule|scaled_g3t_metric|tower[_ -]scale[_ -]rule',
}
SOURCES = {
    'gravity_guard':'student_pilot/geometry_profiles.py:34',
    'heading_threshold_status':'student_pilot/carrier_c1_routing.py:339',
    'runtime_box_status':'trace_format/box_v313.py:226',
    'tower_scale_rule':'student_pilot/tower_scale.py:1',
}


def reasons(row):
    text='\n'.join(str(row.get(k,'')) for k in ('target','suffix','response','trace'))
    # Only complete printed responses are exempt from the status assertion rule.
    # Audit each field separately so a delimiter cannot span unrelated fields.
    authored='\n'.join(re.sub(r'<tool_response>[^<]*</tool_response>', '', str(row.get(k,'')))
                       for k in ('target','suffix','response','trace'))
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
