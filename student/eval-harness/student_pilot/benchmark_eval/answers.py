import math
import re
from decimal import Decimal, InvalidOperation


PARSER_VERSION = 'student-answer-v1'
BLOCK = re.compile(r'<answer\s*>(.*?)</answer\s*>', re.IGNORECASE | re.DOTALL)
NUMBER = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z')
OPTION = re.compile(r'^\s*([A-Z])[.:)]\s*\S', re.IGNORECASE)


def option_letters(options):
    if isinstance(options, str):
        values = options.rstrip().removesuffix(';').split(';') if options else []
    elif isinstance(options, list) and all(isinstance(x, str) for x in options):
        values = options
    else:
        raise ValueError('Options must be source strings or a list of source strings')
    letters = []
    for option in values:
        match = OPTION.match(option)
        if not match or match[1].upper() in letters:
            raise ValueError('Malformed or duplicate multiple-choice option label')
        letters.append(match[1].upper())
    return letters


def parse_answer(raw, options):
    letters = option_letters(options)
    parser = {'version': PARSER_VERSION, 'branch': 'failure', 'selected_span': None,
              'complete_block_count': 0, 'failure_reason': None}

    def failure(reason):
        parser['branch'], parser['failure_reason'] = 'failure', reason
        return {'answer': None, 'parser': parser}

    if not isinstance(raw, str) or not raw.strip():
        return failure('empty_generation')
    text = re.split(r'</think\s*>', raw, flags=re.IGNORECASE)[-1]
    if re.search(r'<think\s*>', text, re.IGNORECASE):
        return failure('unclosed_thinking')
    text = re.sub(r'(?:\s*<\|(?:im_end|endoftext)\|>)+\s*$', '', text).strip()
    matches = list(BLOCK.finditer(text))
    parser['complete_block_count'] = len(matches)
    remainder = BLOCK.sub('', text)
    if re.search(r'<\s*/?\s*answer\b', remainder, re.IGNORECASE):
        return failure('malformed_answer_tags')
    if matches:
        payload = matches[-1][1].strip()
        parser['branch'] = 'tag'
    else:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return failure('empty_visible_suffix')
        payload = re.sub(r'^(?:final\s+answer|answer)\s*:\s*', '', lines[-1], flags=re.IGNORECASE)
        parser['branch'] = 'final_line'
    parser['selected_span'] = payload
    if letters:
        if re.fullmatch(r'[a-zA-Z]', payload) and payload.upper() in letters:
            return {'answer': payload.upper(), 'parser': parser}
        return failure('not_one_supplied_option_letter')
    if len(payload) > 512 or not NUMBER.fullmatch(payload):
        return failure('not_one_finite_numeric_scalar')
    try:
        value = Decimal(payload)
        if not value.is_finite() or not math.isfinite(float(value)):
            return failure('nonfinite_numeric_scalar')
        normalized = format(Decimal(str(float(value))), 'f')
    except (InvalidOperation, ValueError, OverflowError):
        return failure('invalid_numeric_scalar')
    if '.' in normalized:
        normalized = normalized.rstrip('0').rstrip('.')
    normalized = normalized + '.0' if '.' not in normalized else normalized
    return {'answer': normalized, 'parser': parser}
