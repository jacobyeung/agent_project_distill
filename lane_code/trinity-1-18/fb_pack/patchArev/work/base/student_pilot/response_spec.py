"""Versioned text grammar for printed tool responses; preserves bound-row bytes."""
import hashlib
import json
from pathlib import Path
import re

VERSION = 'tool-response-text-v1'
N = r'-?\d+\.\d{2}'
S = r'[+-]\d+\.\d{2}'
V = r'\('+N+r', '+N+r', '+N+r'\)'
NAME = r'[^\n<>:]+'
RULES = {
    'scalar_distance': N+r' m',
    'area': r'area '+N+r' m\^2',
    'point': r'P\d+: cam\d+ '+V+r' m; f1 '+V+r' m; spread '+N,
    'minimum': r'min [^\n<>]+ '+N+r' m',
    'camera_distances': r'(?:P\d+ '+N+r' m\n)+min P\d+ '+N+r' m',
    'gap_distances': r'(?:'+NAME+r': '+N+r' m\n)+min [^\n<>]+ '+N+r' m',
    'angle': r'u \('+N+r', '+N+r'\); v \('+N+r', '+N+r'\); dot -?\d+\.\d{4}; cross -?\d+\.\d{4}; theta -?\d+ deg; (?:left|right|back|front-left|front-right|back-left|back-right|Turn Left|Turn Right|Turn Back)',
    'ground_probability': NAME+r': f\d+ \[\d+,\d+\] '+N+r'(?: \| f\d+ \[\d+,\d+\] '+N+r')*',
    'distance': r'distance '+N+r' m',
    'move': r'dx = '+S+r' m, dy = '+S+r' m, dz = '+S+r' m, distance = '+N+r' m',
    'turn': r'turn = [+-]\d+ deg',
    'pose': r'f1 centre '+V+r' m, yaw -?\d+ deg',
    'box': NAME+r': frames \d+(?:,\d+)* \(best \d+\)\nB\d+: f1 centre '+V+r' m\nsize '+N+r' x '+N+r' x '+N+r' m\nyaw -?\d+ deg \(0 = \+x; positive \+x toward -z about \+y\)',
    'status': r'(?:'+NAME+r': )?(?:not seen|box unavailable)',
    'error': r'error: [^\n<>]+',
}
RULES['points'] = RULES['point']+r'(?:\n'+RULES['point']+r')*'
SPEC = dict(version=VERSION, encoding='UTF-8', newline='LF',
    envelope=dict(inline=['<tool_response>','</tool_response>'],
                  multiline=['<tool_response>\n','\n</tool_response>']),
    units=dict(position='m', size='m', distance='m', area='m^2', yaw='deg', turn='deg'),
    number_format=dict(metric='fixed two decimals', signed_delta='explicit sign and two decimals', angle='integer degrees'),
    field_order=dict(box=['name','frames','best','box_label','f1_centre','size','yaw'],
                     pose=['f1_centre','yaw'],move=['dx','dy','dz','distance'],turn=['turn'],distance=['distance']),
    rules=RULES,
    compatibility='Inline camera/calculator and newline-delimited ground envelopes are distinct bound-row variants. Neither is normalized.')


def document():
    return (json.dumps(SPEC, sort_keys=True, indent=2)+'\n').encode()


def sha256():
    return hashlib.sha256(document()).hexdigest()


def parse(text):
    if not text.startswith('<tool_response>') or not text.endswith('</tool_response>'):
        raise ValueError('response_envelope')
    body=text[len('<tool_response>'):-len('</tool_response>')]
    multiline=body.startswith('\n') and body.endswith('\n')
    body=body[1:-1] if multiline else body
    for kind,pattern in RULES.items():
        if re.fullmatch(pattern,body): return dict(version=VERSION,kind=kind,body=body,multiline=multiline)
    # These grammars already define field order, exact units and precision.
    from trace_format import room_v314, box_v313
    for kind,parser in (('room',room_v314.parse_response),('box_contract',box_v313.parse)):
        try:
            parser(body)
            return dict(version=VERSION,kind=kind,body=body,multiline=multiline)
        except (ValueError,TypeError,KeyError,IndexError,AssertionError): pass
    raise ValueError('unregistered_response_format')


def format_response(record):
    if record.get('version') != VERSION: raise ValueError('response_version')
    pad='\n' if record['multiline'] else ''
    result='<tool_response>'+pad+record['body']+pad+'</tool_response>'
    if parse(result) != record: raise ValueError('response_fields')
    return result


def check(text):
    record=parse(text)
    if format_response(record)!=text: raise ValueError('response_not_byte_canonical')
    return record
