"""Pinned, answer-preserving Locate targets for GT-mask pointing rows."""
import json
import re
import sqlite3

from .p3_provenance import digest, pinned


RULE = {
    'rule_id': 'pointing-locate-v1',
    'visible': '<think>\nLocate the {label} in frame {frame}.\n</think>\n\n{answer}',
    'absent': '<think>\nLocate the {label} in frame {frame}: it is not visible in that frame.\n</think>\n\n{answer}',
    'answer': 'Unchanged JSON bytes returned by mask_target; point_2d is a point or null.',
    'label': 'Exact pointing.label, including digits; must match the question.',
    'decision': 'Token containing the period or colon immediately after the frame index.',
    'source_sha256': '20e6bac0646697300e79322653fe1cf0291e10f0498105bc89cb388463412b27',
}
RULE_PIN = {'rule_id': RULE['rule_id'], 'sha256': digest(RULE)}


def validate_pin(value):
    if value != RULE_PIN:
        raise ValueError('pointing_locate requires the exact Locate rule id/SHA256 pin')
    return dict(RULE_PIN)


def validate_config(cfg):
    return validate_pin(cfg['pointing_locate']) if 'pointing_locate' in cfg else None


def render(row, answer):
    """Use validated row metadata and append the mask answer without serializing it."""
    point, inputs = row['pointing'], row['student_input']
    label, frame = point.get('label'), point.get('frame')
    if (not isinstance(label, str) or not label or any(c in label for c in '\r\n<>')
            or type(frame) is not int or not 1 <= frame <= len(inputs['frames'])):
        raise ValueError('Locate requires an exact label and valid frame index')
    question = inputs['question']
    match = re.match(r'Point to the (.+?) in frame ([0-9]+)\.', question)
    if (match is None or match[1] != label or int(match[2]) != frame
            or f'If there is no {label} in frame {frame}, output ' not in question):
        raise ValueError('Locate label/frame differs from the pointing question')
    value = json.loads(answer)
    if not isinstance(value, dict) or set(value) != {'point_2d'}:
        raise ValueError('Locate requires the native point_2d answer')
    xy = value['point_2d']
    absent = xy is None
    if (point['kind'] not in ('gt_absent', 'gt_instance_mask')
            or absent != (point['kind'] == 'gt_absent')
            or (not absent and (not isinstance(xy, list) or len(xy) != 2
                or any(type(v) is not int or not 0 <= v <= 1000 for v in xy)))):
        raise ValueError('Locate answer disagrees with GT-mask kind or point format')
    return RULE['absent' if absent else 'visible'].format(label=label, frame=frame, answer=answer)


def assert_target(row):
    target = row.get('target', '')
    if target.count('</think>\n\n') != 1:
        raise ValueError('Pointing target lacks exactly one Locate block')
    answer = target.split('</think>\n\n', 1)[1]
    if target != render(row, answer):
        raise ValueError('Pointing target differs from the pinned Locate form')


def assert_store(receipt, rule_pin):
    validate_pin(rule_pin)
    if receipt.get('pointing_locate') != rule_pin:
        raise ValueError('Pointing receipt lacks the pinned Locate rule')
    path = pinned(receipt['database'])
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as conn:
        count = 0
        for raw, in conn.execute('SELECT row FROM rows ORDER BY i'):
            assert_target(json.loads(raw))
            count += 1
    if count != receipt['count'] or count == 0:
        raise ValueError('Locate store count differs from receipt')


def decision_offset(text):
    match = re.match(r'\A<think>\nLocate the [^\r\n<>]+ in frame [1-9][0-9]*'
                     r'(?P<decision>\.|: it is not visible in that frame\.)\n</think>\n\n', text)
    if match is None:
        raise ValueError('Pointing weights require the complete pinned Locate trace')
    return match.start('decision')
