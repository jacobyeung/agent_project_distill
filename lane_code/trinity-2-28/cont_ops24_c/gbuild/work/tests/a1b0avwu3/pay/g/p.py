"""Registered 150-item discrete parity and paired printed-gap tolerance."""
from decimal import Decimal
import re


def printed(text):
    if not isinstance(text, str):
        return dict(kind='status', text=text)
    gap = re.fullmatch(r'distance ([0-9]+(?:\.[0-9]+)?) m', text)
    if gap:
        return dict(kind='gap', value=Decimal(gap[1]))
    frames = re.search(r': frames ([0-9,]+) \(best ([0-9]+)\)', text)
    if frames:
        # Numeric box coordinates are intentionally outside the registered rule.
        return dict(kind='ground', frames=frames[1].split(','), best=frames[2],
                    text=text[:frames.start()])
    return dict(kind='status', text=text)


def compare(expected, actual):
    match = actual is not None and len(expected) == len(actual)
    gaps = []
    for i, a in enumerate(expected):
        b = actual[i] if actual is not None and i < len(actual) else None
        x = printed(a.get('response')); y = printed(b.get('response')) if b else None
        same = (b is not None and a['call'] == b.get('call') and a['served'] == b.get('served')
                and {k:v for k,v in x.items() if k != 'value'} ==
                    {k:v for k,v in (y or {}).items() if k != 'value'})
        match = match and same
        if x['kind'] == 'gap' or (y and y['kind'] == 'gap'):
            av = x.get('value'); bv = (y or {}).get('value')
            gaps.append(dict(call_index=i, call=a['call'], expected=av, actual=bv,
                             difference=None if av is None or bv is None else bv-av))
    return bool(match), gaps


def evaluate(references, main, repeat):
    """Missing repeats or gaps cannot certify a numeric tolerance."""
    if len(references) != 150 or len({r['item_id'] for r in references}) != 150:
        raise ValueError('require 150 distinct references')
    chosen = [r for r in references if r['calls']][:10]
    paired = []; repeat_complete = len(chosen) == 10
    for r in chosen:
        key = r['item_id']; first = main.get(key); second = repeat.get(key)
        repeat_complete &= first is not None and second is not None
        _, gaps = compare(r['calls'], first)
        _, other = compare(r['calls'], second)
        by_index = {g['call_index']:g for g in other}
        for g in gaps:
            a = g['actual']; b = by_index.get(g['call_index'], {}).get('actual')
            valid = a is not None and b is not None
            repeat_complete &= valid
            paired.append(dict(item_id=key, call_index=g['call_index'], call=g['call'],
                               run1=a, run2=b, difference=b-a if valid else None))
    repeat_complete &= bool(paired)
    tolerance = 2*max(abs(g['difference']) for g in paired) if repeat_complete else None
    flags = []; differences = []; gap_ok = repeat_complete
    for r in references:
        key = r['item_id']; match, gaps = compare(r['calls'], main.get(key))
        item_gap_ok = True
        for g in gaps:
            within = tolerance is not None and g['difference'] is not None and abs(g['difference']) <= tolerance
            differences.append(dict(item_id=key, discrete_match=match, within_tolerance=bool(within), **g))
            if match: item_gap_ok &= within
        if match: gap_ok &= item_gap_ok
        flags.append(dict(item_id=key, completed=key in main, discrete_match=match,
                          gaps_match=bool(item_gap_ok) if match else None))
    count = sum(r['discrete_match'] for r in flags)
    result = dict(trusted=count >= 143 and bool(gap_ok), items=len(main), expected=150,
                  discrete_matches=count, discrete_required=143, discrete_pass=count >= 143,
                  gap_pass=bool(gap_ok), repeat_complete=bool(repeat_complete),
                  repeat_items=[r['item_id'] for r in chosen], gap_atol_m=tolerance,
                  per_item=flags, baseline_differences=differences, repeat_differences=paired)
    def plain(v):
        if isinstance(v, Decimal): return float(v)
        if isinstance(v, dict): return {k:plain(x) for k,x in v.items()}
        if isinstance(v, list): return [plain(x) for x in v]
        return v
    return plain(result)
