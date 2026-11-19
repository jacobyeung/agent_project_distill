"""Strict inline grammar. Argument text is data, never executable code."""
import math
import re
import json

OPENERS = ('<depth_at', '<move', '<pose', '<box_3d')
RESPONSE_TOKENS = ('<tool_response>', '</tool_response>')
TOKENS = OPENERS + RESPONSE_TOKENS
NUMBER = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z')


class ToolError(ValueError):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f'{code}: {detail}')


def number(text):
    if not NUMBER.fullmatch(text):
        raise ToolError('invalid_number', text)
    value = float(text)
    if not math.isfinite(value):
        raise ToolError('nonfinite', text)
    return int(value) if value.is_integer() else value


def frame(value, nframes=32):
    if type(value) is not int or not 1 <= value <= nframes:
        raise ToolError('bad_frame', f'{value!r}; expected 1..{nframes}')
    return value


def pixel(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1000:
        raise ToolError('bad_grid', str(value))
    return value


def parse(text, nframes=32):
    match = re.fullmatch(r'<(depth_at|move|pose|box_3d)\s+([^<>]+)>', text)
    if not match:
        raise ToolError('malformed_call', text)
    name, body = match.groups()
    args = {}
    cursor=0
    while cursor<len(body):
        if body[cursor].isspace():cursor+=1;continue
        argument=re.match(r'([A-Za-z_][A-Za-z_0-9]*)=',body[cursor:])
        if argument is None:raise ToolError('malformed_argument',body[cursor:])
        key=argument.group(1);cursor+=argument.end()
        if key in args:
            raise ToolError('duplicate_argument', key)
        if key == 'pts':
            try:
                pairs,used=json.JSONDecoder(parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s))).raw_decode(body[cursor:])
                cursor+=used
                if (not isinstance(pairs,list) or not pairs or any(not isinstance(p,list) or len(p)!=2 for p in pairs)):
                    raise ValueError()
                args[key] = [[pixel(x),pixel(y)] for x,y in pairs]
            except ValueError as exc:
                raise ToolError('bad_points', body[cursor:]) from exc
        else:
            end=cursor
            while end<len(body) and not body[end].isspace():end+=1
            val=body[cursor:end];cursor=end
            args[key] = number(val)
        if cursor<len(body) and not body[cursor].isspace():
            raise ToolError('malformed_argument',body[cursor:])
    required = {'move': {'from', 'to'}, 'pose': {'frame'},
                'box_3d': {'frame', 'x1', 'y1', 'x2', 'y2'}}
    if name == 'depth_at':
        fields = {'frame', 'pts'} if 'pts' in args else {'frame', 'x', 'y'}
    else:
        fields = required[name]
    optional = {'image_frame'} if name in ('depth_at', 'box_3d') else set()
    if set(args) - optional != fields or set(args) - (fields | optional):
        raise ToolError('unknown_or_missing_argument', str(sorted(args)))
    for key in ('frame', 'from', 'to', 'image_frame'):
        if key in args:
            frame(args[key], nframes)
    for key in ('x', 'y', 'x1', 'y1', 'x2', 'y2'):
        if key in args:
            pixel(args[key])
    if name == 'box_3d' and (args['x1'] >= args['x2'] or args['y1'] >= args['y2']):
        raise ToolError('malformed_box', 'require x1<x2 and y1<y2')
    if 'pts' in args:args['points']=args.pop('pts')
    return {'name': name, **args}


def format_call(call):
    name = call['name']
    parts = []
    for key, value in call.items():
        if key == 'name':
            continue
        if key == 'points':
            key='pts'
            value=json.dumps(value,separators=(',',':'),allow_nan=False)
        parts.append(f'{key}={value}')
    text = '<' + name + ' ' + ' '.join(parts) + '>'
    parse(text)
    return text


def token_table(tokenizer):
    result = {tag: tokenizer.encode(tag, add_special_tokens=False) for tag in TOKENS}
    if any(len(v) != 1 for v in result.values()) or len({v[0] for v in result.values()}) != len(TOKENS):
        raise ValueError('Routing openers and output delimiters must be distinct dedicated tokens')
    return {tag: v[0] for tag, v in result.items()}


def add_tokens(tokenizer, model=None):
    existing = list(getattr(tokenizer, 'additional_special_tokens', []))
    tokenizer.add_special_tokens({'additional_special_tokens': list(dict.fromkeys(existing+list(TOKENS)))})
    if model is not None:
        model.resize_token_embeddings(len(tokenizer))
        model.config.p3['token_ids'] = token_table(tokenizer)
    return token_table(tokenizer)
