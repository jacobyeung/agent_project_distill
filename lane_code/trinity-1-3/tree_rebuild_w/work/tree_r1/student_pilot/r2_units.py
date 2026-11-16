"""Asked-unit membership and ordered metric score reports."""
import math
import re

DISTANCE = ('object_abs_distance', 'absolute_distance_object', 'absolute_distance',
            'camera_displacement', 'camera_object_abs_distance', 'camera_obj_abs_dist')
ROOM = ('room_size_estimation', 'absolute_size_room', 'room_size')
ORDER = ('m', 'm2', 'cm', 'ft', 'in', 'ft2')


def asked_unit(item):
    kind = item.get('question_type', item.get('type'))
    if kind not in (*DISTANCE, *ROOM):
        return None
    question = item.get('student_input', {}).get('question', item.get('question', '')).lower()
    patterns = [('ft2', r'\b(?:square (?:feet|foot)|sq\.?\s*ft|ft2)\b'),
                ('m2', r'\b(?:square met(?:er|re)s?|m2)\b'),
                ('cm', r'\b(?:centimet(?:er|re)s?|cm)\b'),
                ('in', r'\b(?:inches|inch)\b'), ('ft', r'\b(?:feet|foot|ft)\b'),
                ('m', r'\b(?:met(?:er|re)s?|m)\b')]
    unit = next((u for u, pattern in patterns if re.search(pattern, question)), None)
    if unit is None or (kind in ROOM) != (unit in ('m2', 'ft2')):
        raise ValueError('Metric question has no unambiguous asked unit')
    return unit


def metric_units(items):
    result = {}
    for item in items:
        unit = asked_unit(item)
        if unit:
            kind = 'room' if item.get('question_type', item.get('type')) in ROOM else 'distance'
            result.setdefault(kind, set()).add(unit)
    return {kind: [u for u in ORDER if u in units] for kind, units in result.items()}


def score_by_unit(items):
    groups = {}
    for item in items:
        unit = asked_unit(item)
        if unit is None:
            continue
        score = item['score']
        if type(score) not in (int, float) or not math.isfinite(score):
            raise ValueError('Metric score must be finite')
        kind = 'room' if item.get('question_type', item.get('type')) in ROOM else 'distance'
        groups.setdefault(kind, {}).setdefault(unit, []).append(score)
    return {kind: {u: dict(count=len(values[u]), score=sum(values[u])/len(values[u]))
                   for u in ORDER if u in values} for kind, values in groups.items()}
