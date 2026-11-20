"""Compare every recorded ground/gap call; never infer parity from a mean."""
import math
import re


def printed(text):
    if text is None:
        return dict(kind='status', text=None)
    f = re.search(r': frames ([0-9,]+) \(best ([0-9]+)\)', text)
    gap = re.fullmatch(r'distance ([0-9]+(?:\.[0-9]+)?) m', text)
    if f:
        return dict(kind='ground', frames=[int(x) for x in f[1].split(',')], best=int(f[2]))
    if gap:
        return dict(kind='gap', value=float(gap[1]))
    return dict(kind='status', text=text)


def check(expected, actual, tolerance):
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('invalid gap tolerance')
    if len(expected) != len(actual):
        raise ValueError('call count mismatch')
    for i, (a, b) in enumerate(zip(expected, actual)):
        if a['call'] != b['call'] or a['served'] != b['served']:
            raise ValueError(f'call/status mismatch at {i}')
        x,y=printed(a['response']),printed(b['response'])
        if x['kind'] != y['kind']:
            raise ValueError(f'response status mismatch at {i}')
        if x['kind']=='gap':
            if abs(x['value']-y['value']) > tolerance+1e-12:
                raise ValueError(f'gap mismatch at {i}: {x} vs {y}')
        elif x!=y:
            raise ValueError(f'ground frames/best/status mismatch at {i}')
    return True
