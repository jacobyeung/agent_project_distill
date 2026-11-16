"""Trace ruling grammar. Replace this module atomically with the reviewed rows-lane copy.

SOURCE_SHA256 hashes RULES (canonical JSON); the tree inventory pins this code too.
This conservative syntax gate cannot prove that a pictured relation is true. Scene,
frame and row membership evidence is checked separately by r2_contract.
"""
import ast
import hashlib
import json
import math
import operator
import re

RULES = {
    'schema': 'r2-trace-grammar-v1',
    'line_kinds': ['Locate', 'Relate', 'Step', 'Call'],
    'program_types': ['object_abs_distance', 'camera_displacement', 'camera_movement_direction', 'camera_rotation'],
    'numbers': ['frame index', 'listed item count', 'printed response value', 'explicit arithmetic', 'question constant'],
    'direct_answer': 'Numeric estimates only after </think>; never in a trace.',
    'locate': 'Object is seen in frame N; one frame per named object, N is a one-based student slot.',
    'count': 'Step: list [item; item]; count = N. Items must name previously located objects.',
    'arithmetic': 'Step: compute EXPR = VALUE. Operands must already be supported.',
    'unit_factors_from_meters': {'centimeters': 100, 'centimetres': 100, 'feet': 3.28084, 'inches': 39.3701},
    'forbid': ['tool tags in direct targets', 'empty think', 'answer restatement', 'filler-only steps',
               'glued units', 'number words except question constants and half turn', 'seconds for frames',
               'exhaustive frame lists', 'absent in'],
}
SOURCE_SHA256 = hashlib.sha256(json.dumps(RULES, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
PROGRAM_TYPES = frozenset(RULES['program_types'])
NUMBER = r'(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])'
WORDS = r'\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|half|quarter|dozen|couple)\b'
RELATION = r'\b(left|right|ahead|behind|front|above|below|nearest|farthest|before|after|between|longest|shortest|larger|smaller|closer|farther|nearer|inside|outside|next|opposite)\b'
STEP = r'\b(face|facing|turn|swap|threshold|closest|farthest|longest|dimension|waypoint|heading|forward|combined|list|compute|count)\b'


def numbers(text):
    return {float(x) for x in re.findall(NUMBER, text)}


def arithmetic(expression, allowed):
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float) and node.value in allowed:
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            return operations[type(node.op)](evaluate(node.left), evaluate(node.right))
        raise ValueError('Arithmetic uses unsupported operands or operations')
    try:
        value = evaluate(ast.parse(expression, mode='eval').body)
    except (SyntaxError, ZeroDivisionError) as error:
        raise ValueError('Invalid explicit arithmetic') from error
    if not math.isfinite(value):
        raise ValueError('Nonfinite arithmetic')
    return value


def validate_direct(target, question, frame_count):
    match = re.fullmatch(r'<think>\s*\n(.*?)\n</think>\s*(\S[\s\S]*)', target, re.S)
    if not match:
        raise ValueError('Missing trace or answer')
    think, answer = match.groups()
    if not think.strip():
        raise ValueError('Empty think block')
    if re.search(r'<(?!/?answer\b)[^>]+>', answer) or '<' in think or '<tool_response' in target:
        raise ValueError('Direct target carries a call or response tag')
    if re.search(r'\d(?:\.\d+)?\s*(?:seconds?|secs?\b)|\babsent in\b|\bframes\s+\d', think, re.I):
        raise ValueError('Seconds, exhaustive visibility or absence statements are forbidden')
    if re.search(r'\d(?:cm|mm|km|ft|inches|meters|metres|m\b|deg)', think, re.I):
        raise ValueError('Integers or decimals glued to units')
    question_words = set(re.findall(WORDS, question.lower()))
    word_text = re.sub(r'\bhalf turn\b', '', think.lower())
    if set(re.findall(WORDS, word_text)) - question_words:
        raise ValueError('Unsupported number words')
    allowed, located = numbers(question), set()
    for line in think.strip().splitlines():
        parsed = re.fullmatch(r'(Locate|Relate|Step):\s*(\S.*)', line.strip())
        if not parsed:
            raise ValueError('Trace line must be Locate, Relate or Step')
        kind, body = parsed.groups()
        if re.search(r'\b(?:the answer is|so the answer|option [A-Z] is correct)\b', body, re.I):
            raise ValueError('Answer restatement is not reasoning')
        residual = body
        if kind == 'Locate':
            found = re.fullmatch(r'(.+?) (?:is (?:first )?seen|is visible|appears) in frame (\d+)(?:[.,] (?:at|in) the [a-z -]+)?\.?', body, re.I)
            if not found or not 1 <= int(found[2]) <= frame_count:
                raise ValueError('Locate requires one valid frame per object')
            obj = found[1].casefold()
            if obj in located:
                raise ValueError('An object has an exhaustive or duplicate frame list')
            located.add(obj)
            residual = re.sub(r'frame \d+', 'frame', body)
        elif kind == 'Relate':
            if (not re.search(RELATION, body, re.I) or not located
                    or not any(obj.removeprefix('the ') in body.casefold() for obj in located)):
                raise ValueError('Relate must relate located objects')
        else:
            listing = re.fullmatch(r'list \[(.+)\]; count = (\d+)\.?', body)
            computation = re.fullmatch(r'compute (.+?) = (-?\d+(?:\.\d+)?)\.?', body)
            if listing:
                items = [s.strip().casefold() for s in listing[1].split(';')]
                if len(set(items)) != len(items) or not set(items) <= located or len(items) != int(listing[2]):
                    raise ValueError('Count differs from the listed located items')
                allowed.add(float(len(items)))
            elif computation:
                value = arithmetic(computation[1], allowed)
                if not math.isclose(value, float(computation[2]), rel_tol=1e-9, abs_tol=1e-9):
                    raise ValueError('Explicit arithmetic result differs')
                allowed.add(value)
            elif not re.search(STEP, body, re.I) or not (set(re.findall(r'[a-z]{4,}', body.lower())) & set(re.findall(r'[a-z]{4,}', question.lower()))):
                raise ValueError('Filler Step does not express the question logic')
        if numbers(residual) - allowed:
            raise ValueError('Trace contains an unsupported number')
        if re.search(r'\d\s*(?:m|cm|ft|meters?|metres?|degrees?|square)\b', residual, re.I) and kind != 'Step':
            raise ValueError('Direct trace states a measurement')
    return answer.strip()


def validate_program(row):
    from .carrier_c1_routing import check_row
    if row.get('question_type') not in PROGRAM_TYPES:
        raise ValueError('Call on a direct type; room size is direct')
    target, spans = check_row(row)
    if not spans or not re.search(r'</think>\s*<answer>.+</answer>\s*$', target, re.S):
        raise ValueError('Program needs masked responses and an <answer> ending')
    response_ranges = [(m.start(), m.end()) for m in re.finditer(r'<tool_response>.*?</tool_response>', target, re.S)]
    if (response_ranges != [(s['start'], s['end']) for s in spans]
            or target.count('<tool_response>') != len(spans) or target.count('</tool_response>') != len(spans)):
        raise ValueError('Every response must be an event with a masked span')
    # Canonical sealed events define Call lines; responses are external text, never targets.
    calls = [e.get('call_id') for e in row['events'] if e['kind'] in ('tool_call', 'calculator_call', 'ground_call')]
    if any(s['call_id'] not in calls for s in spans):
        raise ValueError('Response has no corresponding call')
    allowed = numbers(row['question'])
    for event in row['events']:
        kind = event['kind']
        if kind in ('tool_response', 'ground_response', 'calculator_response'):
            printed = event['response']['text'] if kind == 'calculator_response' else event['text']
            allowed.update(numbers(printed))
        elif kind in ('plan', 'canonical_text', 'correction'):
            prose = event['text'].split('</think>')[0].replace('<think>', '')
            prose = re.sub(r'frame \d+', 'frame', prose)
            for unit, factor in RULES['unit_factors_from_meters'].items():
                if unit in row['question'].lower() and any(re.search(r'\d\s*m\b', row['target'][s['start']:s['end']]) for s in spans):
                    allowed.add(factor)
            for expr, result in re.findall(r'compute ([\d. +*/()-]+) = (-?\d+(?:\.\d+)?)', prose):
                value = arithmetic(expr, allowed)
                if not math.isclose(value, float(result), rel_tol=1e-9, abs_tol=1e-9):
                    raise ValueError('Program arithmetic result differs')
                allowed.add(value)
            if numbers(prose) - allowed:
                raise ValueError('Program prose states an unprinted number')
    return target, spans
